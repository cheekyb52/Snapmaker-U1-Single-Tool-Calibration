"""Offline compatibility and staging guards for both exact source profiles."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.prepare_install import PROFILES, ROOT, prepare, select_manifest

FIXTURES = {
    'stock-1.4.1.6': ROOT / 'tests/native',
    'paxx-2.0-pr760': ROOT / 'tests/native/pr760',
}


class SourceProfiles(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def test_auto_selects_complete_hash_set_for_each_profile(self):
        for name, fixture in FIXTURES.items():
            self.assertEqual(select_manifest(fixture / 'baseline')[0], name)

    def test_each_profile_stages_exact_native_and_shared_macro_payloads(self):
        for name, fixture in FIXTURES.items():
            manifest = json.loads((ROOT / PROFILES[name]).read_text())
            output = self.directory / name
            staged = prepare(fixture / 'baseline', output)
            expected = {item['path']: item['modified_sha256'] for item in manifest['files']}
            expected['config/extended/klipper/70_tool_offsets.cfg'] = manifest['macro']['sha256']
            self.assertEqual(staged, expected)
            for relative, digest in expected.items():
                self.assertEqual(hashlib.sha256((output / relative).read_bytes()).hexdigest(), digest)

    def test_mixed_firmware_files_are_rejected_before_staging(self):
        source = self.directory / 'mixed'
        shutil.copytree(FIXTURES['stock-1.4.1.6'] / 'baseline', source)
        relative = 'klippy/kinematics/extruder.py'
        shutil.copyfile(FIXTURES['paxx-2.0-pr760'] / 'baseline' / relative, source / relative)
        output = self.directory / 'output'
        with self.assertRaisesRegex(ValueError, 'Baseline hash mismatch'):
            prepare(source, output)
        self.assertFalse(output.exists())

    def test_explicit_wrong_profile_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Baseline hash mismatch'):
            prepare(FIXTURES['paxx-2.0-pr760'] / 'baseline', self.directory / 'output', 'stock-1.4.1.6')
        self.assertFalse((self.directory / 'output').exists())

    def test_existing_output_is_never_overwritten(self):
        output = self.directory / 'output'
        output.mkdir()
        marker = output / 'retained.txt'
        marker.write_text('preserve existing work')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            prepare(FIXTURES['paxx-2.0-pr760'] / 'baseline', output)
        self.assertEqual(marker.read_text(), 'preserve existing work')

    def test_pr760_keeps_new_firmware_code_outside_calibration_methods(self):
        fixture = FIXTURES['paxx-2.0-pr760']
        for relative, class_name, replaced, added in (
            ('klippy/kinematics/extruder.py', 'PrinterExtruder',
             {'_update_extruder_offset', 'get_center_base_position', 'cmd_SET_EXTRUDER_BASE_POSITION'},
             {'_save_base_position_preserving_reference'}),
            ('klippy/extras/probe_inductance_coil.py', 'ExtruderOffsetCalibration',
             {'cmd_EXTRUDER_OFFSET_ACTION_SAVE_RESULT'}, set()),
        ):
            baseline = ast.parse((fixture / 'baseline' / relative).read_text())
            modified = ast.parse((fixture / 'modified' / relative).read_text())
            original_class = next(n for n in baseline.body if isinstance(n, ast.ClassDef) and n.name == class_name)
            changed_class = next(n for n in modified.body if isinstance(n, ast.ClassDef) and n.name == class_name)
            originals = {n.name: n for n in original_class.body if isinstance(n, ast.FunctionDef)}
            restored = []
            for node in changed_class.body:
                if isinstance(node, ast.FunctionDef) and node.name in added:
                    continue
                restored.append(copy.deepcopy(originals[node.name]) if isinstance(node, ast.FunctionDef) and node.name in replaced else node)
            changed_class.body = restored
            self.assertEqual(ast.dump(modified), ast.dump(baseline), relative)

    def test_ported_calibration_methods_match_previously_tested_implementation(self):
        def methods(path):
            tree = ast.parse(path.read_text())
            return {(cls.name, method.name): ast.dump(method)
                    for cls in tree.body if isinstance(cls, ast.ClassDef)
                    for method in cls.body if isinstance(method, ast.FunctionDef)}
        for relative in ('klippy/kinematics/extruder.py', 'klippy/extras/extruder_config_bak.py', 'klippy/extras/probe_inductance_coil.py'):
            old = methods(FIXTURES['stock-1.4.1.6'] / 'modified' / relative)
            new = methods(FIXTURES['paxx-2.0-pr760'] / 'modified' / relative)
            baseline = methods(FIXTURES['stock-1.4.1.6'] / 'baseline' / relative)
            for key in old:
                if key not in baseline or old[key] != baseline[key]:
                    self.assertEqual(new[key], old[key], key)


if __name__ == '__main__':
    unittest.main()
