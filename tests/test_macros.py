"""Offline execution model for the deployed macros; no printer access."""
import ast
import configparser
import copy
from pathlib import Path
import re
import shlex
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
from jinja2 import Environment, StrictUndefined

CFG = ROOT / 'overlays/mods/tooloffsets/02-macros/root/usr/local/share/firmware-config/extended/klipper/70_tool_offsets.cfg'
config = configparser.ConfigParser(interpolation=None)
config.read(CFG)
env = Environment('{%', '%}', '{', '}', undefined=StrictUndefined)
# Stock dispatcher parses only an alphabetic/underscore stem and a numeric tail.
parser_source = ast.parse((ROOT / 'tests/fixtures/gcode.py').read_text())
parser_pattern = next(n.value.args[0].value for n in ast.walk(parser_source)
                      if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'args_r' for t in n.targets))
args_r = re.compile(parser_pattern)
extended_pattern = next(n.value.args[0].value for n in ast.walk(parser_source)
                      if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'extended_r' for t in n.targets))
extended_r = re.compile(extended_pattern)
split_node = copy.deepcopy(next(n for n in ast.walk(parser_source)
                    if isinstance(n, ast.FunctionDef) and n.name == '_split_gcode_params'))
split_node.decorator_list = []
scope = {}
exec(compile(ast.Module(body=[split_node], type_ignores=[]), '<stock parameter splitter>', 'exec'), scope)
stock_split = scope['_split_gcode_params']


def parsed_command(line):
    parts = args_r.split(line.upper())
    return parts[1] + parts[2].strip() if len(parts) >= 3 else ''
templates = {s.split(' ', 1)[1]: env.from_string(config[s]['gcode']) for s in config.sections()}
initial = {s: {k[9:]: ast.literal_eval(v) for k, v in config[s].items() if k.startswith('variable_')}
           for s in config.sections()}
NAMES = ['extruder', 'extruder1', 'extruder2', 'extruder3']


class Machine:
    def __init__(self):
        self.p = copy.deepcopy(initial)
        self.base = [[10., 20., -2.], [10.1, 20.1, -2.3],
                     [10.5, 19.8, -.2], [9.5, 20.5, -2.1]]
        self.measurements = copy.deepcopy(self.base)
        self.p.update(print_stats=dict(state='standby'), virtual_sdcard=dict(is_active=False),
                      pause_resume=dict(is_paused=False),
                      print_task_config=dict(filament_type=['PLA'] * 4),
                      extruder_offset_calibration=dict(calibration_step='idle'))
        self.p['extruder_config_bak'] = dict(preserve_reference_supported=True, offset_reference=None)
        self.frame = None
        self.trace, self.writes, self.messages = [], [], []
        self.tool = 0
        self.update_offsets()
        self.p['toolhead'] = dict(extruder=NAMES[self.tool])
        self.p['gcode_move'] = dict(homing_origin=self.p[NAMES[self.tool]]['extruder_offset'][:] + [0.0])

    @property
    def state(self):
        return self.p['gcode_macro _SM_OFFSET_STATE']

    def update_offsets(self):
        frame = [(min(v[a] for v in self.base) + max(v[a] for v in self.base))/2 for a in (0, 1)] + [self.base[0][2]]
        frame = self.frame if self.frame is not None else frame
        for i, name in enumerate(NAMES):
            self.p[name] = dict(extruder_offset=[self.base[i][a] - frame[a] for a in range(3)], nozzle_diameter=0.4)

    def fail(self, message):
        raise ValueError(message)

    def respond(self, message):
        self.messages.append(message)
        return ''

    def run(self, name, **params):
        assert parsed_command(name) == name, 'Stock parser cannot dispatch ' + name
        params = {k: str(v) for k, v in params.items()}
        # Render from a frozen snapshot, then execute emitted commands in order.
        text = templates[name].render(printer=copy.deepcopy(self.p), params=params,
                    rawparams=' '.join(k + '=' + v for k, v in params.items()),
                    action_raise_error=self.fail, action_respond_info=self.respond)
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            command = parsed_command(line)
            m = extended_r.match(line)
            tokens = stock_split(m.group('args')) if m else []
            assert parsed_command(line) == command, 'Stock parser truncates ' + command
            args = dict(t.split('=', 1) for t in tokens if '=' in t)
            if command in templates:
                self.run(command, **args)
                continue
            self.trace.append(line)
            if command == 'SET_GCODE_VARIABLE':
                self.p['gcode_macro ' + args['MACRO']][args['VARIABLE']] = ast.literal_eval(args['VALUE'])
            elif command == 'G28':
                for n in NAMES:
                    self.p['extruder_offset_calibration'][n + '_last_xyz_result'] = None
            elif command.startswith('T') and command[1:].isdigit():
                self.tool = int(command[1:])
                self.p['toolhead']['extruder'] = NAMES[self.tool]
                self.p['gcode_move']['homing_origin'] = self.p[NAMES[self.tool]]['extruder_offset'][:] + [0.0]
            elif command == 'PROBE_XYZ_OFFSET_CALIBRATE':
                self.p['extruder_offset_calibration'][NAMES[self.tool] + '_last_xyz_result'] = self.measurements[self.tool]
                assert args['SAVE_INFO'] == '0' and args['UPDATE_CONFIG'] == '1'
            elif command == 'SET_EXTRUDER_BASE_POSITION':
                i = NAMES.index(args['EXTRUDER'])
                assert args['PRESERVE_REFERENCE'] == '1' and i in [1, 2, 3]
                if self.frame is None:
                    self.frame = [(min(v[a] for v in self.base)+max(v[a] for v in self.base))/2 for a in (0,1)] + [self.base[0][2]]
                self.p['extruder_config_bak']['offset_reference'] = self.frame[:]
                self.writes.append(i)
                self.base[i] = [v + float(args[a + '_ADJUST']) for a, v in zip('XYZ', self.base[i])]
                self.update_offsets()
                # Observed live: stock refresh callbacks end with T3's origin,
                # even when T1 is physically active. The CFG must repair it.
                self.p['gcode_move']['homing_origin'] = self.p['extruder3']['extruder_offset'][:] + [0.0]
            elif command == 'SET_GCODE_OFFSET':
                self.p['gcode_move']['homing_origin'] = [float(args[a]) for a in 'XYZ'] + [0.0]
                assert args.get('MOVE') == '0'
            elif command == '_EXTRUDER_OFFSET_ACTION_EXIT':
                assert self.p['gcode_move']['homing_origin'][:3] == self.p[NAMES[self.tool]]['extruder_offset'], 'Exit would use the wrong tool offset'

    def finish(self):
        for _ in range(6):
            if self.state['stage'] == 'idle':
                return
            self.run('OFFSET_CONTINUE')
        raise AssertionError('Cycle did not finish')


class Checks(unittest.TestCase):
    def test_every_macro_name_dispatches_with_stock_parser(self):
        self.assertEqual(parsed_command('_U1_OFFSET_BEGIN MODE=validate'), '_U1')
        for name in templates:
            self.assertEqual(parsed_command(name), name)

    def test_stock_semicolon_is_comment_even_inside_quoted_value(self):
        bad = 'SET_GCODE_VARIABLE MACRO=X VARIABLE=report VALUE=\'"FAIL; details"\''
        args = dict(t.split('=', 1) for t in stock_split(extended_r.match(bad).group('args')))
        with self.assertRaises((SyntaxError, ValueError)):
            ast.literal_eval(args['VALUE'])

    def test_no_stock_calibration_state_machine_wrappers(self):
        m = Machine()
        m.run('CLEAN_AND_VALIDATE_OFFSETS')
        m.finish()
        self.assertTrue(all(not line.startswith(('EXTRUDER_OFFSET_ACTION_', 'SET_MAIN_STATE')) for line in m.trace))
        self.assertEqual(m.p['extruder_offset_calibration']['calibration_step'], 'idle')

    def test_t0_button_warns_and_returns_without_a_command_error(self):
        m = Machine()
        before = copy.deepcopy(m.p)
        m.run('CALIBRATE_TOOL_0')
        self.assertEqual(len(m.trace), 4)
        self.assertTrue(all(line.startswith('RESPOND TYPE=command ') for line in m.trace))
        self.assertEqual(m.p, before)
        self.assertTrue(any('WARNING: T0' in message and 'all 4 tools' in message for message in m.messages))

    def test_t0_prompt_and_ok_callback_survive_stock_parameter_parser(self):
        m = Machine()
        m.run('CALIBRATE_TOOL_0')
        messages = []
        for line in m.trace:
            args = dict(token.split('=', 1) for token in stock_split(extended_r.match(line).group('args')))
            self.assertEqual(args['TYPE'], 'command')
            messages.append(args['MSG'])
        self.assertTrue(messages[0].startswith('action:prompt_begin '))
        self.assertIn('all 4 tools', messages[1])
        self.assertEqual(messages[-1], 'action:prompt_show')
        footer = messages[2].removeprefix('action:prompt_footer_button ').split('|')
        self.assertEqual(footer, ['OK', 'RESPOND TYPE=command MSG=action:prompt_end', 'info'])
        close_args = dict(token.split('=', 1) for token in stock_split(extended_r.match(footer[1]).group('args')))
        self.assertEqual(parsed_command(footer[1]), 'RESPOND')
        self.assertEqual(close_args, {'TYPE': 'command', 'MSG': 'action:prompt_end'})

    def test_internal_single_t0_entry_is_blocked(self):
        m = Machine()
        with self.assertRaisesRegex(ValueError, 'WARNING: T0.*all 4 tools'):
            m.run('_SM_OFFSET_BEGIN', MODE='single', TOOL=0, REFERENCE=2)
        self.assertFalse(m.trace)

    def test_all_supported_tools_save_z_without_affecting_others(self):
        for target in (1, 2, 3):
            m = Machine()
            m.run('OFFSET_ARM_SAVE', BACKUP='verified-test')
            before = copy.deepcopy(m.base)
            applied = [m.p[n]['extruder_offset'][:] for n in NAMES]
            m.measurements = [[v + d for v, d in zip(p, [0.20, -0.25, 0.1])] for p in m.base]
            m.measurements[target][2] += 0.15
            m.run('CALIBRATE_TOOL_%d' % target)
            self.assertEqual(m.state['stage'], 'manual')
            m.finish()
            self.assertEqual(m.writes, [target])
            for i in range(4):
                if i != target:
                    self.assertEqual(m.base[i], before[i])
                    self.assertEqual(m.p[NAMES[i]]['extruder_offset'], applied[i])

    def test_non_extreme_xy_can_save(self):
        m = Machine()
        m.run('OFFSET_ARM_SAVE', BACKUP='verified-test')
        m.measurements[1][0] += 0.03
        m.measurements[1][1] -= 0.03
        m.run('CALIBRATE_TOOL_1')
        m.finish()
        self.assertEqual(m.writes, [1])

    def test_save_restores_active_origin_before_exit(self):
        for target in (1, 2, 3):
            m = Machine()
            m.run('OFFSET_ARM_SAVE', BACKUP='verified-test')
            m.measurements[target][2] += 0.15
            m.run('CALIBRATE_TOOL_%d' % target)
            m.finish()
            self.assertEqual(m.p['toolhead']['extruder'], NAMES[target])
            self.assertEqual(m.p['gcode_move']['homing_origin'][:3], m.p[NAMES[target]]['extruder_offset'])
            save = next(i for i, line in enumerate(m.trace) if line.startswith('SET_EXTRUDER_BASE_POSITION '))
            sync = next(i for i, line in enumerate(m.trace) if line.startswith('SET_GCODE_OFFSET '))
            exit_index = m.trace.index('_EXTRUDER_OFFSET_ACTION_EXIT')
            self.assertLess(save, sync)
            self.assertLess(sync, exit_index)

    def test_runtime_sync_rejects_unknown_or_invalid_active_tool(self):
        for active, offset in [('missing', None), ('extruder1', [float('nan'), 0, 0]), ('extruder1', [])]:
            m = Machine()
            m.p['toolhead']['extruder'] = active
            if offset is not None:
                m.p[active]['extruder_offset'] = offset
            with self.assertRaises(ValueError):
                m.run('_SM_OFFSET_SYNC_ACTIVE')
            self.assertFalse(m.trace)

    def test_extreme_xy_saves_preserving_all_other_tools(self):
        for target in (1, 2, 3):
            m = Machine()
            before = copy.deepcopy(m.base)
            applied = [m.p[n]['extruder_offset'][:] for n in NAMES]
            m.run('OFFSET_ARM_SAVE', BACKUP='verified-test')
            for axis, delta in enumerate([0.8, -0.4, 0.1]):
                m.measurements[target][axis] += delta
            m.run('CALIBRATE_TOOL_%d' % target)
            m.finish()
            self.assertEqual(m.writes, [target])
            self.assertIn('saved', m.state['report'])
            for i in range(4):
                if i != target:
                    self.assertEqual(m.base[i], before[i])
                    self.assertEqual(m.p[NAMES[i]]['extruder_offset'], applied[i])

    def test_missing_native_capability_blocks_before_heating(self):
        for backend in (None, {}, {'preserve_reference_supported': False}):
            m = Machine()
            m.run('OFFSET_ARM_SAVE', BACKUP='test')
            m.trace.clear()
            if backend is None:
                del m.p['extruder_config_bak']
            else:
                m.p['extruder_config_bak'] = backend
            with self.assertRaisesRegex(ValueError, 'native preserve-reference patch'):
                m.run('CALIBRATE_TOOL_2')
            self.assertFalse(m.trace)

    def test_missing_native_capability_rechecked_before_saving(self):
        m = Machine()
        m.run('OFFSET_ARM_SAVE', BACKUP='test')
        m.run('CALIBRATE_TOOL_3')
        m.p['extruder_config_bak']['preserve_reference_supported'] = False
        with self.assertRaisesRegex(ValueError, 'native preserve-reference patch'):
            m.finish()
        self.assertFalse(m.writes)

    def test_saved_offsets_verified_before_exit(self):
        m = Machine()
        m.run('OFFSET_ARM_SAVE', BACKUP='test')
        m.run('CALIBRATE_TOOL_2')
        m.finish()
        m.state['stage'] = 'probing'
        m.p['extruder1']['extruder_offset'][0] += .01
        with self.assertRaisesRegex(ValueError, 'Runtime offsets do not match'):
            m.run('_SM_OFFSET_VERIFY_SAVE', DX=0, DY=0, DZ=0)

    def test_validation_common_shift_passes_without_any_save(self):
        m = Machine()
        m.measurements = [[v + d for v, d in zip(p, [0.20, -0.25, 0.1])] for p in m.base]
        m.run('CLEAN_AND_VALIDATE_OFFSETS')
        m.finish()
        self.assertIn('PASS', m.state['report'])
        self.assertFalse(m.writes)
        self.assertEqual(sum('PROBE_XYZ_OFFSET_CALIBRATE' in s for s in m.trace), 4)
        self.assertEqual(sum('PROBE_POINTS=6' in s for s in m.trace), 4)

    def test_each_drifting_tool_is_flagged(self):
        for target in range(4):
            m = Machine()
            m.measurements[target][2] += 0.08
            m.run('CLEAN_AND_VALIDATE_OFFSETS')
            m.finish()
            self.assertIn('FAIL', m.state['report'])
            self.assertFalse(m.writes)

    def test_tolerance_override(self):
        m = Machine()
        m.measurements[2][2] += 0.08
        m.run('CLEAN_AND_VALIDATE_OFFSETS', TOL_Z=0.1)
        m.finish()
        self.assertIn('PASS', m.state['report'])

    def test_cleaning_temperature_overrides_and_limits(self):
        m = Machine()
        m.run('CLEAN_AND_VALIDATE_OFFSETS', HEAT_TEMP=210, T2_TEMP=220)
        self.assertEqual(m.state['run_cleaning_temps'], [210, 210, 220, 210])
        for value in ('nan', 160, 310):
            m = Machine()
            with self.assertRaises(ValueError):
                m.run('CLEAN_AND_VALIDATE_OFFSETS', HEAT_TEMP=value)
            self.assertFalse(m.trace)

    def test_backup_is_required(self):
        m = Machine()
        with self.assertRaisesRegex(ValueError, 'verified backup arm'):
            m.run('CALIBRATE_TOOL_1')
        self.assertFalse(m.trace)

    def test_printing_paused_active_and_unknown_block_all_actions(self):
        for state, active, paused in [('printing', False, False), ('paused', False, False),
                ('standby', True, False), ('standby', False, True), ('error', False, False),
                ('standby', None, False), ('standby', False, None)]:
            for name, params in [('CLEAN_AND_VALIDATE_OFFSETS', {}), ('OFFSET_ARM_SAVE', dict(BACKUP='test')), ('OFFSET_ABORT', {}), ('_SM_OFFSET_SYNC_ACTIVE', {})]:
                m = Machine()
                m.p['print_stats']['state'] = state
                m.p['virtual_sdcard']['is_active'] = active
                m.p['pause_resume']['is_paused'] = paused
                with self.assertRaises(ValueError):
                    m.run(name, **params)
                self.assertFalse(m.trace)

    def test_continue_blocks_after_print_starts(self):
        m = Machine()
        m.run('CLEAN_AND_VALIDATE_OFFSETS')
        old = list(m.trace)
        m.p['virtual_sdcard']['is_active'] = True
        with self.assertRaises(ValueError):
            m.run('OFFSET_CONTINUE')
        self.assertEqual(m.trace, old)

    def test_missing_measurement_and_large_adjust_cannot_save(self):
        for value in (None, [18., 235., -2.]):
            m = Machine()
            m.measurements[1] = value
            m.run('OFFSET_ARM_SAVE', BACKUP='test')
            m.run('CALIBRATE_TOOL_1')
            with self.assertRaises(ValueError):
                m.finish()
            self.assertFalse(m.writes)

    def test_abort_exits_and_does_not_save(self):
        m = Machine()
        m.run('CLEAN_AND_VALIDATE_OFFSETS')
        m.run('OFFSET_ABORT')
        self.assertEqual(m.state['stage'], 'idle')
        self.assertFalse(m.writes)



if __name__ == '__main__':
    unittest.main()
