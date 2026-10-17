"""Stage a source-matched calibration profile locally; never install it."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MACRO = ROOT / ('overlays/mods/tooloffsets/02-macros/root/usr/local/share/'
                'firmware-config/extended/klipper/70_tool_offsets.cfg')
PROFILES = {
    'stock-1.4.1.6': 'tests/native/manifest.json',
    'paxx-2.0-pr760': 'profiles/paxx-2.0-pr760/manifest.json',
}
EXPECTED = {'klippy/kinematics/extruder.py',
            'klippy/extras/extruder_config_bak.py',
            'klippy/extras/probe_inductance_coil.py'}


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def apply_exact(original, lines):
    """Apply only this patch's ordinary unified hunks, with no fuzz or offsets."""
    if len(lines) < 4 or not lines[1].startswith('--- a/') or not lines[2].startswith('+++ b/'):
        raise ValueError('Unexpected patch header')
    source = original.decode('utf-8').splitlines(keepends=True)
    result, cursor, index = [], 0, 3
    while index < len(lines):
        hunk = re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n', lines[index])
        if hunk is None:
            raise ValueError('Unexpected patch hunk')
        start = int(hunk[1]) - 1
        if not cursor <= start <= len(source):
            raise ValueError('Invalid source hunk position')
        result.extend(source[cursor:start])
        if int(hunk[3]) - 1 != len(result):
            raise ValueError('Invalid destination hunk position')
        cursor, index, removed, added = start, index + 1, 0, 0
        while index < len(lines) and not lines[index].startswith('@@ '):
            marker, value = lines[index][0], lines[index][1:]
            if marker not in ' +-':
                raise ValueError('Unexpected patch line')
            if marker in ' -':
                if cursor >= len(source) or source[cursor] != value:
                    raise ValueError('Patch context does not match')
                cursor, removed = cursor + 1, removed + 1
            if marker in ' +':
                result.append(value)
                added += 1
            index += 1
        if removed != int(hunk[2] or 1) or added != int(hunk[4] or 1):
            raise ValueError('Invalid patch hunk counts')
    result.extend(source[cursor:])
    return ''.join(result).encode('utf-8')


def select_manifest(source_root, profile='auto'):
    if profile != 'auto' and profile not in PROFILES:
        raise ValueError('Unknown source profile')
    actual = {}
    for relative in EXPECTED:
        source_path = (source_root / relative).resolve()
        if not source_path.is_relative_to(source_root):
            raise ValueError('Source path leaves working copy')
        actual[relative] = sha256(source_path.read_bytes())
    matches = []
    for name, manifest_path in PROFILES.items():
        if profile != 'auto' and name != profile:
            continue
        manifest = json.loads((ROOT / manifest_path).read_text(encoding='utf-8'))
        entries = {item['path']: item for item in manifest['files']}
        if set(entries) != EXPECTED or len(manifest['files']) != len(EXPECTED):
            raise ValueError('Unexpected native manifest scope')
        if all(actual[path] == entries[path]['baseline_sha256'] for path in EXPECTED):
            matches.append((name, manifest))
    if len(matches) != 1:
        raise ValueError('Baseline hash mismatch: no unique matching source profile')
    return matches[0]


def prepare(source_root, output, profile='auto'):
    source_root, output = source_root.resolve(), output.resolve()
    if output.exists():
        raise ValueError('Output already exists; choose a new staging directory')
    if output == source_root or output.is_relative_to(source_root):
        raise ValueError('Output must be outside the source working copy')
    _, manifest = select_manifest(source_root, profile)
    entries = {item['path']: item for item in manifest['files']}
    if set(entries) != EXPECTED:
        raise ValueError('Unexpected native manifest scope')
    patch_path = (ROOT / manifest['diff']).resolve()
    if not patch_path.is_relative_to(ROOT):
        raise ValueError('Patch path leaves project')
    patch_text = patch_path.read_text(encoding='utf-8')
    blocks = patch_text.split('diff --git ')
    if (len(blocks) != 4
            or any(line.strip() and not line.startswith('#')
                   for line in blocks[0].splitlines())):
        raise ValueError('Unexpected patch scope')
    staged = {}
    for block in blocks[1:]:
        lines = block.splitlines(keepends=True)
        headers = lines[0].strip().split()
        if len(headers) != 2 or not headers[0].startswith('a/'):
            raise ValueError('Unexpected patch path')
        relative = headers[0][2:]
        if relative not in entries or relative in staged or headers[1] != 'b/' + relative:
            raise ValueError('Unexpected or duplicate patch target')
        if lines[1].strip() != '--- a/' + relative or lines[2].strip() != '+++ b/' + relative:
            raise ValueError('Inconsistent patch header')
        source_path = (source_root / relative).resolve()
        if not source_path.is_relative_to(source_root):
            raise ValueError('Source path leaves working copy')
        original = source_path.read_bytes()
        if sha256(original) != entries[relative]['baseline_sha256']:
            raise ValueError('Baseline hash mismatch: ' + relative)
        modified = apply_exact(original, lines)
        compile(modified, relative, 'exec')
        if sha256(modified) != entries[relative]['modified_sha256']:
            raise ValueError('Modified hash mismatch: ' + relative)
        staged[relative] = modified
    if set(staged) != EXPECTED:
        raise ValueError('Incomplete patch')
    macro = MACRO.read_bytes()
    if (manifest['macro']['path'] != MACRO.relative_to(ROOT).as_posix()
            or sha256(macro) != manifest['macro']['sha256']):
        raise ValueError('Macro hash differs from the validated payload')
    staged['config/extended/klipper/70_tool_offsets.cfg'] = macro
    # All validation happens before the first write. Existing sources stay untouched.
    output.mkdir(parents=True, exist_ok=False)
    for relative, content in staged.items():
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    return {path: sha256(content) for path, content in staged.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--profile', choices=['auto', *PROFILES], default='auto',
                        help='Default: select one profile by all three exact baseline hashes')
    args = parser.parse_args()
    try:
        result = prepare(args.source_root, args.output, args.profile)
    except (OSError, ValueError, SyntaxError) as error:
        # OS exception messages can include private paths; don't include them.
        print(str(error) if isinstance(error, ValueError) else type(error).__name__, file=sys.stderr)
        return 1
    print(json.dumps({'staged_files': result, 'printer_actions': False}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
