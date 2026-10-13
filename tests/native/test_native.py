"""Offline regressions exercising the proposed native methods and real JSON.

No printer connection, Klipper process, motion or debug mode is involved.
Hardware dependencies are stubbed; the proposed methods are compiled unchanged.
"""
import ast
import copy
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import re
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

REVIEW = Path(__file__).resolve().parent
ROOT = REVIEW.parents[1]
MODIFIED = REVIEW / 'modified'
NAMES = ['extruder', 'extruder1', 'extruder2', 'extruder3']
POSITIONS = [
    [10.0, 20.0, -2.0],
    [10.1, 20.1, -2.3],
    [10.5, 19.8, -0.2],
    [9.5, 20.5, -2.1],
]

class Writer:
    def __init__(self):
        self.calls = []
        self.fail = False

    def write(self, reactor, path, content, flush, safe_write):
        self.calls.append((path, json.loads(content), flush, safe_write))
        if self.fail:
            raise OSError('Injected atomic write failure')
        target = Path(path).resolve()
        assert target.is_relative_to(REVIEW.resolve())
        temporary = target.with_suffix('.tmp')
        temporary.write_text(content)
        os.replace(temporary, target)


writer = Writer()
queue = types.ModuleType('queuefile')
queue.sync_write_file = writer.write
scope = {'__name__': 'review_backend'}
with patch.dict('sys.modules', {'queuefile': queue}):
    source = (MODIFIED / 'klippy/extras/extruder_config_bak.py').read_text()
    exec(compile(source, 'review_backend.py', 'exec'), scope)
Backend = scope['ExtruderConfigBak']
REFERENCE_KEY = scope['OFFSET_REFERENCE_KEY']
original_scope = {'__name__': 'review_original_backend'}
with patch.dict('sys.modules', {'queuefile': queue}):
    source = (REVIEW / 'baseline/klippy/extras/extruder_config_bak.py').read_text()
    exec(compile(source, 'original_backend.py', 'exec'), original_scope)
OriginalBackend = original_scope['ExtruderConfigBak']


def native_methods(relative, class_name, method_names, folder=MODIFIED):
    tree = ast.parse((folder / relative).read_text())
    original = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    methods = [n for n in original.body if isinstance(n, ast.FunctionDef) and n.name in method_names]
    if {n.name for n in methods} != set(method_names):
        raise AssertionError('Missing native methods')
    cls = ast.ClassDef(name=class_name, bases=[], keywords=[], body=methods, decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    scope = dict(__name__='review_native', math=math, os=os, logging=logging)
    exec(compile(module, relative, 'exec'), scope)
    return scope[class_name]


Extruder = native_methods('klippy/kinematics/extruder.py', 'PrinterExtruder', [
    'get_center_base_position', 'update_extruder_gcode_offset', '_update_extruder_offset',
    'active_gcode_offset', 'get_extruder_config', 'update_extruder_config',
    '_save_base_position_preserving_reference', 'cmd_SET_EXTRUDER_BASE_POSITION'])
Controller = native_methods('klippy/extras/probe_inductance_coil.py', 'ExtruderOffsetCalibration',
                            ['cmd_EXTRUDER_OFFSET_ACTION_SAVE_RESULT'])
OriginalExtruder = native_methods('klippy/kinematics/extruder.py', 'PrinterExtruder', [
    'get_center_base_position', 'update_extruder_gcode_offset', '_update_extruder_offset',
    'active_gcode_offset', 'get_extruder_config', 'update_extruder_config',
    'cmd_SET_EXTRUDER_BASE_POSITION'], folder=REVIEW / 'baseline')
OriginalController = native_methods('klippy/extras/probe_inductance_coil.py', 'ExtruderOffsetCalibration',
                                   ['cmd_EXTRUDER_OFFSET_ACTION_SAVE_RESULT'], folder=REVIEW / 'baseline')


class Command:
    def __init__(self, **params):
        self.params = params
        self.messages = []

    def get_float(self, name, default=None, **limits):
        value = self.params.get(name, default)
        if value is None:
            return value
        value = float(value)
        for bound, limit in limits.items():
            if (bound == 'minval' and value < limit or bound == 'maxval' and value > limit
                    or bound == 'above' and value <= limit):
                raise ValueError('Parameter outside range')
        return value

    def get_int(self, name, default=None, **limits):
        value = self.get_float(name, default, **limits)
        if value is not None and int(value) != value:
            raise ValueError('Not an integer parameter')
        return None if value is None else int(value)

    def error(self, message):
        return ValueError(message)

    def respond_info(self, message):
        self.messages.append(message)


class Config:
    def __init__(self, printer):
        self.printer = printer

    def get_printer(self):
        return self.printer

    def error(self, message):
        return ValueError(message)


class Fixture:
    def __init__(self, directory, backend_class=Backend, extruder_class=Extruder,
                 controller_class=Controller):
        self.directory = directory
        self.origin = [0., 0., 0.]
        self.scripts, self.config_edits = [], []
        self.reactor = types.SimpleNamespace(monotonic=lambda: 123.)
        self.objects = {
            'gcode': types.SimpleNamespace(register_command=lambda *a, **k: None,
                                          run_script_from_command=self.script),
            'configfile': types.SimpleNamespace(set=lambda *args: self.config_edits.append(args)),
            'print_stats': types.SimpleNamespace(get_status=lambda now: {'state': 'standby'}),
            'virtual_sdcard': types.SimpleNamespace(get_status=lambda now: {'is_active': False}),
            'pause_resume': types.SimpleNamespace(get_status=lambda now: {'is_paused': False}),
            'toolhead': types.SimpleNamespace(get_extruder=lambda: self.active),
        }
        self.config = Config(self)
        self.backend = backend_class(self.config)
        self.objects['extruder_config_bak'] = self.backend
        Path(self.backend.config_path).parent.mkdir(parents=True)
        Path(self.backend.config_path).write_text('{}')
        self.initial_json = {name: {'base_position': copy.deepcopy(position), 'retained_field': name}
                             for name, position in zip(NAMES, POSITIONS)}
        self.store(self.initial_json)
        self.tools = []
        for name, position in zip(NAMES, POSITIONS):
            obj = extruder_class.__new__(extruder_class)
            obj.printer, obj.name, obj.base_position = self, name, position[:]
            self.tools.append(obj)
            self.objects[name] = obj
        self.objects['extruder_list'] = self.tools
        self.active = self.tools[1]
        self.controller = controller_class.__new__(controller_class)
        self.controller.printer = self
        self.controller.lock = threading.Lock()
        self.controller.calibration_step = 'idle'
        self.controller.factory_mode = False
        self.controller.last_xyz_result = {name: None for name in NAMES}
        self.objects['extruder_offset_calibration'] = self.controller
        self.refresh()
        self.scripts.clear()

    def lookup_object(self, name, default=None):
        return self.objects.get(name, default)

    def get_reactor(self):
        return self.reactor

    def get_snapmaker_config_dir(self, kind=None):
        return str(self.directory / 'persistent') if kind else str(self.directory)

    def send_event(self, name):
        assert name == 'probe_inductance_coil: update_extruder_offset'
        self.refresh()

    def script(self, line):
        self.scripts.append(line)
        if line.startswith('SET_GCODE_OFFSET '):
            params = dict(token.split('=', 1) for token in line.split()[1:])
            self.origin = [float(params[a]) for a in 'XYZ']

    def refresh(self):
        for obj in self.tools:
            obj._update_extruder_offset()

    def data(self):
        return json.loads(Path(self.backend.base_position_config_path).read_text())

    def store(self, value):
        Path(self.backend.base_position_config_path).write_text(json.dumps(value))

    def offsets(self):
        return [obj.gcode_offset[:] for obj in self.tools]

    def single(self, tool, delta):
        self.tools[tool].cmd_SET_EXTRUDER_BASE_POSITION(Command(
            PRESERVE_REFERENCE=1, **{axis+'_ADJUST': value for axis, value in zip('XYZ', delta)}))


class NativeChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='review-test-', dir=REVIEW)
        self.directory = Path(self.temp.name).resolve()
        assert self.directory.is_relative_to(REVIEW.resolve())
        self.addCleanup(self.temp.cleanup)
        writer.calls, writer.fail = [], False
        self.f = Fixture(self.directory)

    def assertVectorClose(self, actual, expected, tolerance=1e-12):
        self.assertEqual(len(actual), len(expected))
        for a, b in zip(actual, expected):
            self.assertAlmostEqual(a, b, delta=tolerance)

    def test_independent_xyz_saves_for_all_supported_tools(self):
        for target in (1, 2, 3):
            before, offsets = self.f.data(), self.f.offsets()
            self.f.active = self.f.tools[target]
            delta = [.12, -.08, .04]
            self.f.single(target, delta)
            after = self.f.data()
            for i, name in enumerate(NAMES):
                if i != target:
                    self.assertEqual(after[name], before[name])
                    self.assertEqual(self.f.tools[i].gcode_offset, offsets[i])
                else:
                    self.assertVectorClose(self.f.tools[i].gcode_offset,
                                           [v+d for v, d in zip(offsets[i], delta)])
            self.assertVectorClose(self.f.origin, self.f.tools[target].gcode_offset, 1e-6)
        self.assertEqual(len(writer.calls), 3)
        self.assertTrue(all(call[2:] == (True, True) for call in writer.calls))

    def test_repeated_saves_reuse_original_frame(self):
        frame = self.f.tools[0].get_center_base_position()
        self.f.single(2, [-.2, .1, .05])
        self.f.single(3, [.15, -.1, -.04])
        self.assertEqual(self.f.backend.get_offset_reference(), frame)
        self.assertEqual(self.f.data()[REFERENCE_KEY]['position'], frame)

    def test_restart_loads_frame_and_preserves_offsets(self):
        self.f.single(2, [.2, .3, -.1])
        expected = self.f.offsets()
        self.f.backend._offset_reference = None
        self.f.backend.load_offset_reference(self.f.config)
        saved = self.f.data()
        for obj in self.f.tools:
            obj.base_position = saved[obj.name]['base_position'][:]
        self.f.refresh()
        self.assertEqual(self.f.offsets(), expected)

    def test_native_activation_uses_the_preserved_offsets(self):
        self.f.single(3, [.2, -.15, .1])
        for obj in self.f.tools:
            self.f.active = obj
            obj.active_gcode_offset()
            self.assertVectorClose(self.f.origin, obj.gcode_offset, 1e-6)

    def test_refresh_only_applies_the_active_tool_origin(self):
        for active in self.f.tools:
            self.f.active = active
            self.f.scripts.clear()
            self.f.refresh()
            self.assertEqual(len(self.f.scripts), 1)
            self.assertVectorClose(self.f.origin, active.gcode_offset, 1e-6)

    def test_t0_single_save_is_blocked(self):
        before = self.f.data()
        with self.assertRaisesRegex(ValueError, 'calibrate all four'):
            self.f.single(0, [.1, 0, 0])
        self.assertEqual(self.f.data(), before)
        self.assertFalse(writer.calls)

    def test_printing_paused_active_and_unknown_states_are_blocked(self):
        for state, active, paused in [('printing', False, False), ('paused', False, True),
                ('standby', True, False), ('standby', False, True),
                ('error', False, False), ('standby', None, False), ('standby', False, None),
                ('standby', 0, False), ('standby', False, 0)]:
            self.f.objects['print_stats'].get_status = lambda now, value=state: {'state': value}
            self.f.objects['virtual_sdcard'].get_status = lambda now, value=active: {'is_active': value}
            self.f.objects['pause_resume'].get_status = lambda now, value=paused: {'is_paused': value}
            with self.assertRaises(ValueError):
                self.f.single(2, [.1, 0, 0])
        self.assertFalse(writer.calls)

    def test_unavailable_live_state_and_active_stock_calibration_block(self):
        saved = self.f.objects.pop('print_stats')
        with self.assertRaises(ValueError):
            self.f.single(2, [.1, 0, 0])
        self.f.objects['print_stats'] = saved
        self.f.controller.calibration_step = 'ready'
        with self.assertRaises(ValueError):
            self.f.single(2, [.1, 0, 0])
        self.assertFalse(writer.calls)

    def test_nonfinite_and_excessive_corrections_block(self):
        for delta in ([float('nan'), 0, 0], [float('inf'), 0, 0], [2.01, 0, 0]):
            with self.assertRaises(ValueError):
                self.f.single(2, delta)
        self.assertFalse(writer.calls)

    def test_missing_tool_or_calibration_blocks(self):
        missing = self.f.objects.pop('extruder3')
        with self.assertRaises(ValueError):
            self.f.single(2, [.1, 0, 0])
        self.f.objects['extruder3'] = missing
        missing.base_position = None
        with self.assertRaises(ValueError):
            self.f.single(2, [.1, 0, 0])
        self.assertFalse(writer.calls)

    def test_single_save_requires_json_backend_without_save_config_fallback(self):
        self.f.objects.pop('extruder_config_bak')
        with self.assertRaises(ValueError):
            self.f.single(2, [.1, 0, 0])
        self.assertFalse(self.f.config_edits)
        self.assertFalse(self.f.scripts)

    def test_failed_single_write_keeps_disk_memory_frame_and_origin(self):
        for existing_frame in (False, True):
            if existing_frame:
                writer.fail = False
                self.f.single(1, [.01, 0, 0])
            before = self.f.data(), copy.deepcopy([obj.base_position for obj in self.f.tools]), self.f.offsets(), self.f.origin[:], self.f.backend.get_offset_reference()
            writer.fail = True
            with self.assertLogs(level='ERROR'), self.assertRaisesRegex(ValueError, 'not saved'):
                self.f.single(2, [.1, .1, .1])
            after = self.f.data(), [obj.base_position for obj in self.f.tools], self.f.offsets(), self.f.origin, self.f.backend.get_offset_reference()
            self.assertEqual(after, before)

    def test_stale_saved_table_blocks_single_write(self):
        data = self.f.data()
        data['extruder3']['base_position'][0] += .03
        self.f.store(data)
        with self.assertLogs(level='ERROR'), self.assertRaisesRegex(ValueError, 'not saved'):
            self.f.single(2, [.1, .1, 0])
        self.assertEqual(self.f.data(), data)
        self.assertFalse(writer.calls)

    def test_stale_or_corrupted_reference_blocks_single_write(self):
        self.f.single(2, [.1, 0, 0])
        good = self.f.data()
        original_frame = self.f.backend.get_offset_reference()
        writer.calls.clear()
        for change in ('changed', 'removed', 'invalid'):
            data = copy.deepcopy(good)
            if change == 'changed': data[REFERENCE_KEY]['position'][0] += .01
            if change == 'removed': data.pop(REFERENCE_KEY)
            if change == 'invalid': data[REFERENCE_KEY]['version'] = 999
            self.f.store(data)
            with self.assertLogs(level='ERROR'), self.assertRaisesRegex(ValueError, 'not saved'):
                self.f.single(3, [.1, 0, 0])
            self.assertEqual(self.f.data(), data)
            self.assertEqual(self.f.backend.get_offset_reference(), original_frame)
        self.assertFalse(writer.calls)

    def test_legacy_query_does_not_pin_or_write(self):
        command = Command(PRESERVE_REFERENCE=1)
        self.f.tools[2].cmd_SET_EXTRUDER_BASE_POSITION(command)
        self.assertTrue(command.messages)
        self.assertFalse(writer.calls)
        self.assertIsNone(self.f.backend.get_offset_reference())

    def test_legacy_setter_keeps_dynamic_centering(self):
        self.f.single(2, [.1, 0, 0])
        self.f.tools[3].cmd_SET_EXTRUDER_BASE_POSITION(Command(X_ADJUST=.05))
        self.assertNotIn(REFERENCE_KEY, self.f.data())
        self.assertIsNone(self.f.backend.get_offset_reference())
        positions = [obj.base_position for obj in self.f.tools]
        frame = [(min(v[a] for v in positions)+max(v[a] for v in positions))/2 for a in (0, 1)] + [positions[0][2]]
        for obj in self.f.tools:
            self.assertEqual(obj.gcode_offset, [v-c for v, c in zip(obj.base_position, frame)])

    def test_legacy_file_load_retains_original_center(self):
        frame = self.f.tools[0].get_center_base_position()
        self.f.backend.load_offset_reference(self.f.config)
        self.assertIsNone(self.f.backend.get_offset_reference())
        self.assertEqual(self.f.tools[0].get_center_base_position(), frame)

    def test_default_setter_and_query_match_original_native_code(self):
        original = Fixture(self.directory / 'original', OriginalBackend, OriginalExtruder, OriginalController)
        for params in ({}, {'X_ADJUST': .05, 'Y_ADJUST': -.1, 'Z_ADJUST': .02},
                       {'X': 13.1, 'Y': 235.2, 'Z': -.4}):
            before = Command(**params)
            after = Command(**params)
            original.tools[2].cmd_SET_EXTRUDER_BASE_POSITION(before)
            self.f.tools[2].cmd_SET_EXTRUDER_BASE_POSITION(after)
            self.assertEqual(original.data(), self.f.data())
            self.assertEqual(original.offsets(), self.f.offsets())
            self.assertEqual(before.messages, after.messages)

    def test_complete_stock_save_matches_original_native_values_and_messages(self):
        original = Fixture(self.directory / 'original', OriginalBackend, OriginalExtruder, OriginalController)
        values = [[v+d for v, d in zip(position, [.15, -.1, .04])] for position in POSITIONS]
        before, after = Command(), Command()
        original.controller.last_xyz_result = dict(zip(NAMES, values))
        self.f.controller.last_xyz_result = dict(zip(NAMES, values))
        original.controller.cmd_EXTRUDER_OFFSET_ACTION_SAVE_RESULT(before)
        self.f.controller.cmd_EXTRUDER_OFFSET_ACTION_SAVE_RESULT(after)
        self.assertEqual(original.data(), self.f.data())
        self.assertEqual(original.offsets(), self.f.offsets())
        self.assertEqual(original.controller.calibration_step, self.f.controller.calibration_step)
        self.assertEqual(before.messages, after.messages)

    def test_invalid_or_stale_reference_fails_closed_on_load(self):
        self.f.single(2, [.1, 0, 0])
        good = self.f.data()
        for change in ('version', 'position', 'anchor', 'z'):
            data = copy.deepcopy(good)
            if change == 'version': data[REFERENCE_KEY]['version'] = 2
            if change == 'position': data[REFERENCE_KEY]['position'][0] = float('nan')
            if change == 'anchor': data['extruder']['base_position'][0] += .01
            if change == 'z': data[REFERENCE_KEY]['position'][2] += .01
            self.f.store(data)
            with self.assertRaises(ValueError):
                self.f.backend.load_offset_reference(self.f.config)

    def test_complete_stock_save_retires_reference_in_one_write(self):
        self.f.single(2, [.1, .1, .1])
        writer.calls.clear()
        values = [[v+d for v, d in zip(position, [.2, -.1, .03])] for position in POSITIONS]
        self.f.controller.last_xyz_result = dict(zip(NAMES, values))
        self.f.controller.cmd_EXTRUDER_OFFSET_ACTION_SAVE_RESULT(Command())
        self.assertEqual(len(writer.calls), 1)
        self.assertNotIn(REFERENCE_KEY, self.f.data())
        self.assertEqual([obj.base_position for obj in self.f.tools], values)
        self.assertEqual(self.f.controller.calibration_step, 'save_result_completed')
        frame = self.f.tools[0].get_center_base_position()
        for obj in self.f.tools:
            self.assertEqual(obj.gcode_offset, [v-c for v, c in zip(obj.base_position, frame)])

    def test_failed_stock_save_preserves_existing_reference_and_memory(self):
        self.f.single(2, [.1, .1, 0])
        before = self.f.data(), copy.deepcopy([obj.base_position for obj in self.f.tools]), self.f.backend.get_offset_reference(), self.f.offsets()
        self.f.controller.last_xyz_result = dict(zip(NAMES, POSITIONS))
        writer.fail = True
        with self.assertLogs(level='ERROR'), self.assertRaisesRegex(ValueError, 'not saved'):
            self.f.controller.cmd_EXTRUDER_OFFSET_ACTION_SAVE_RESULT(Command())
        after = self.f.data(), [obj.base_position for obj in self.f.tools], self.f.backend.get_offset_reference(), self.f.offsets()
        self.assertEqual(after, before)
        self.assertEqual(self.f.controller.calibration_step, 'idle')

    def test_incomplete_stock_save_is_still_blocked(self):
        self.f.controller.last_xyz_result['extruder1'] = POSITIONS[1]
        with self.assertRaisesRegex(ValueError, 'not completed'):
            self.f.controller.cmd_EXTRUDER_OFFSET_ACTION_SAVE_RESULT(Command())
        self.assertFalse(writer.calls)

    def test_force_partial_stock_save_keeps_legacy_recentering(self):
        self.f.single(2, [.1, .1, 0])
        self.f.controller.last_xyz_result['extruder3'] = POSITIONS[3]
        self.f.controller.cmd_EXTRUDER_OFFSET_ACTION_SAVE_RESULT(Command(FORCE_SAVE=1))
        self.assertNotIn(REFERENCE_KEY, self.f.data())
        self.assertIsNone(self.f.backend.get_offset_reference())
        self.assertEqual(self.f.tools[3].base_position, POSITIONS[3])

    def test_stock_save_config_fallback_remains_available(self):
        self.f.objects.pop('extruder_config_bak')
        self.f.controller.last_xyz_result = dict(zip(NAMES, POSITIONS))
        self.f.controller.cmd_EXTRUDER_OFFSET_ACTION_SAVE_RESULT(Command())
        self.assertEqual(len(self.f.config_edits), 4)
        self.assertIn('SAVE_CONFIG RESTART=0', self.f.scripts)

    def test_stock_fallback_blocks_if_a_live_frozen_reference_loses_its_file(self):
        self.f.single(2, [.1, .1, 0])
        target = Path(self.f.backend.base_position_config_path).resolve()
        self.assertTrue(target.is_relative_to(REVIEW.resolve()))
        target.unlink()
        before = copy.deepcopy([obj.base_position for obj in self.f.tools])
        self.f.controller.last_xyz_result = dict(zip(NAMES, POSITIONS))
        with self.assertRaisesRegex(ValueError, 'reference file is unavailable'):
            self.f.controller.cmd_EXTRUDER_OFFSET_ACTION_SAVE_RESULT(Command())
        with self.assertRaisesRegex(ValueError, 'reference file is unavailable'):
            self.f.tools[3].cmd_SET_EXTRUDER_BASE_POSITION(Command(X_ADJUST=.1))
        self.assertEqual([obj.base_position for obj in self.f.tools], before)
        self.assertFalse(self.f.config_edits)

    def test_unrelated_json_fields_survive(self):
        data = self.f.data()
        data['unrelated'] = {'keep': ['something', 7]}
        self.f.store(data)
        self.f.single(2, [.01, 0, 0])
        after = self.f.data()
        self.assertEqual(after['unrelated'], data['unrelated'])
        for name in NAMES:
            self.assertEqual(after[name]['retained_field'], data[name]['retained_field'])

    def test_non_calibration_settings_do_not_retire_the_reference(self):
        self.f.single(2, [.1, 0, 0])
        frame, bases = self.f.backend.get_offset_reference(), self.f.data()
        self.assertTrue(self.f.backend.update_extruder_config('extruder', 'xy_park_position', [12., 250.]))
        self.assertEqual(self.f.backend.get_offset_reference(), frame)
        self.assertEqual(self.f.data(), bases)
        self.assertEqual(json.loads(Path(self.f.backend.config_path).read_text()),
                         {'extruder': {'xy_park_position': [12., 250.]}})

    def test_cfg_capability_is_explicit_and_reference_status_is_a_copy(self):
        self.assertEqual(self.f.backend.get_status(0),
                         {'preserve_reference_supported': True, 'offset_reference': None})
        self.f.single(2, [.1, 0, 0])
        status = self.f.backend.get_status(0)
        self.assertTrue(status['preserve_reference_supported'])
        frame = self.f.backend.get_offset_reference()
        status['offset_reference'][0] += 20
        self.assertEqual(self.f.backend.get_offset_reference(), frame)


class PatchChecks(unittest.TestCase):
    def test_only_calibration_functions_are_changed(self):
        def functions(tree, prefix=''):
            result = {}
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    result[prefix + node.name] = ast.dump(node, include_attributes=False)
                elif isinstance(node, ast.ClassDef):
                    result.update(functions(node, prefix + node.name + '.'))
            return result
        expected = {
            'klippy/kinematics/extruder.py': ({
                'PrinterExtruder._update_extruder_offset',
                'PrinterExtruder.get_center_base_position',
                'PrinterExtruder.cmd_SET_EXTRUDER_BASE_POSITION'}, {
                'PrinterExtruder._save_base_position_preserving_reference'}),
            'klippy/extras/extruder_config_bak.py': ({
                'ExtruderConfigBak.__init__', 'ExtruderConfigBak.update_extruder_config', 'load_config'}, {
                'ExtruderConfigBak.validate_base_position', 'ExtruderConfigBak._reference_from_data',
                'ExtruderConfigBak.load_offset_reference', 'ExtruderConfigBak.get_offset_reference',
                'ExtruderConfigBak.get_status', 'ExtruderConfigBak.update_base_positions'}),
            'klippy/extras/probe_inductance_coil.py': ({
                'ExtruderOffsetCalibration.cmd_EXTRUDER_OFFSET_ACTION_SAVE_RESULT'}, set()),
        }
        manifest = json.loads((REVIEW / 'manifest.json').read_text())
        self.assertEqual({item['path'] for item in manifest['files']}, set(expected))
        for relative, (changed, added) in expected.items():
            original = functions(ast.parse((REVIEW / 'baseline' / relative).read_text()))
            modified = functions(ast.parse((MODIFIED / relative).read_text()))
            self.assertEqual(set(original) - set(modified), set())
            self.assertEqual(set(modified) - set(original), added)
            self.assertEqual({name for name in original if original[name] != modified[name]}, changed)

    def test_manifest_hashes_and_all_python_syntax(self):
        manifest = json.loads((REVIEW / 'manifest.json').read_text())
        banner = ('# Project version: %s | Updated: %s'
                  % (manifest['project_version'], manifest['updated']))
        for relative in [manifest['diff'], manifest['macro']['path']]:
            self.assertIn(banner, (ROOT / relative).read_text().splitlines()[:5])
        macro = (ROOT / manifest['macro']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(macro).hexdigest(), manifest['macro']['sha256'])
        for item in manifest['files']:
            for folder, key in [('baseline', 'baseline_sha256'), ('modified', 'modified_sha256')]:
                data = (REVIEW / folder / item['path']).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), item[key])
                compile(data, item['path'], 'exec')
                if folder == 'modified':
                    self.assertIn(banner, data.decode('utf-8').splitlines()[:5])

    def test_unified_diff_applies_exactly_to_baseline(self):
        manifest = json.loads((REVIEW / 'manifest.json').read_text())
        content = (ROOT / manifest['diff']).read_text()
        count = 0
        for block in content.split('diff --git ')[1:]:
            lines = block.splitlines(True)
            relative = lines[0].split()[0].removeprefix('a/')
            original = (REVIEW / 'baseline' / relative).read_text().splitlines(True)
            output, cursor, index = [], 0, 3
            while index < len(lines):
                match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', lines[index])
                self.assertIsNotNone(match)
                start = int(match[1])-1
                output.extend(original[cursor:start])
                cursor, index, removed, added = start, index+1, 0, 0
                while index < len(lines) and not lines[index].startswith('@@ '):
                    marker, value = lines[index][0], lines[index][1:]
                    if marker in ' -':
                        self.assertEqual(original[cursor], value)
                        cursor, removed = cursor+1, removed+1
                    if marker in ' +':
                        output.append(value)
                        added += 1
                    index += 1
                self.assertEqual(removed, int(match[2] or 1))
                self.assertEqual(added, int(match[4] or 1))
            output.extend(original[cursor:])
            self.assertEqual(''.join(output), (MODIFIED / relative).read_text())
            count += 1
        self.assertEqual(count, 3)


if __name__ == '__main__':
    unittest.main()
