# Snapmaker U1 Single Tool Calibration

Independent T1/T2/T3 calibration and a guided clean-and-validate workflow for the Snapmaker U1.

This project extends the native offset-saving logic and reuses the stock heating, wiping, docking, and probing routines. Recalibrating one secondary tool preserves the other three tools' saved positions and applied offsets. T0 remains the reference: its button displays a warning to use stock **Multi-Toolhead Calibration** for all four tools.

**Status:** live validated on one U1 running `1.4.1.6_20260608141446`. The native patch targets the exact source hashes recorded in [the manifest](tests/native/manifest.json). Other builds require source review and adaptation. Firmware image packaging has not been built or flashed.

## Features

| Button | Behavior |
| --- | --- |
| `CALIBRATE_TOOL_1`, `CALIBRATE_TOOL_2`, `CALIBRATE_TOOL_3` | Clean the reference and selected tools, measure their relative correction, and save only the selected tool |
| `CALIBRATE_TOOL_0` | Display an informational web UI prompt directing the operator to stock full calibration |
| `CLEAN_AND_VALIDATE_OFFSETS` | Clean all four tools, probe the ring, and compare all six tool pairs against configurable XYZ tolerances; save nothing |
| `OFFSET_CONTINUE` | Advance after manual nozzle cleaning or PEI plate removal |
| `OFFSET_ABORT` | Exit a waiting custom cycle; does not undo an earlier save |

Independent saves persist a shared reference in the existing calibration JSON. Stock full calibration retires it and restores ordinary centering. A native capability check prevents the macros from silently using an older save implementation.

The custom workflow uses the web console for manual confirmations. T0's warning uses the common Fluidd/Mainsail prompt protocol. The stock touchscreen workflow remains available separately.

## Documentation

- [Installation](docs/installation.md) — verified backups, source matching, staging, and deployment checks
- [Macro work instructions](docs/work-instructions.md) — buttons, temperatures, tolerances, and completion
- [Modified files](docs/changes.md) — every printer file changed and its purpose
- [Implementation](docs/implementation.md) — shared-reference and persistence contracts
- [Validation](docs/validation.md) — tested behavior and remaining limits
- [Rollback](docs/rollback.md) — matched code/data recovery
- [Codex handoff](docs/codex-handoff.md) — instructions for implementing on another owner's printer
- [Development](docs/development.md) — portable tests and overlay layout

## Validation

32 native regression tests and 23 macro workflow tests passed. Live checks covered T1, T2, T3, restart persistence, stock full calibration, subsequent independent calibration, and clean/validate without saved or applied offset changes. All six validation pairs passed at 0.05 mm per-axis limits. [Results and limits](docs/validation.md) distinguish these checks from print-quality or cross-version guarantees.

Speed tuning is deferred. The validated settings remain ten calibration ring points, six validation ring points, and three XY repeat samples.

## Repository layout

```text
overlays/mods/tooloffsets/
  01-native/patches/home/lava/klipper/   Native three-file patch
  02-macros/root/usr/local/share/firmware-config/extended/klipper/
                                      Macro template
docs/                                 Operator and developer guides
tests/                                Synthetic fixtures and sanitized acceptance results
tools/                                Offline staging and privacy checks
```

The numbered overlays and documentation organization follow the conventions described in [Paxx's development guide](https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware/blob/develop/docs/development.md). This is an independent project prepared for the owner's GitHub account. Paxx's repository is a reference only; nothing has been submitted there.

## Privacy and license

This package contains calibration-project material only. Device addresses, credentials, personal paths, actual calibration tables, captured images, raw logs, and local backups are excluded. The automated audit and package inventory are documented in [Development](docs/development.md).

GPL-3.0; see [LICENSE](LICENSE) and [NOTICE](NOTICE.md) for upstream source attribution.
