---
title: Modified Files
---

# Modified Files

The printer implementation changes three native Python files and adds one macro CFG. The patch is scoped to this calibration feature.

Project version `0.1.0` adds version/date comments to those distributed files and the patch header. The native manifest preserves the original live-tested hashes alongside the versioned hashes. Executable Python and parsed macro settings remain unchanged; this metadata update was not installed on the test printer.

| Printer file | Change | Result |
| --- | --- | --- |
| `klippy/kinematics/extruder.py` | Add opt-in independent saving, use a persisted shared reference when present, and apply refreshed origins only to the active tool | T1/T2/T3 can change their own saved/applied offsets without recentering the other tools |
| `klippy/extras/extruder_config_bak.py` | Validate and load reference metadata; expose capability/status; atomically commit selected or batched positions and reference state | Independent saves survive restart and reject stale or invalid data |
| `klippy/extras/probe_inductance_coil.py` | Commit stock results together and retire pinned-reference metadata before publishing bases | Stock full calibration remains compatible and restores normal centering |
| `extended/klipper/70_tool_offsets.cfg` | Add calibration buttons, T0 warning, cleaning/continue/abort workflow, backup acknowledgement, runtime checks, and validation-only pair comparisons | Operators can calibrate one secondary tool or clean/check all four without an automatic full save |

## Extruder handling

Changed native methods are `get_center_base_position`, `_update_extruder_offset`, and `cmd_SET_EXTRUDER_BASE_POSITION`; the new independent-save helper validates state and commits only the selected entry. Stock command defaults remain in use when `PRESERVE_REFERENCE` is omitted.

## Configuration backend

New methods validate base coordinates, load and return reference metadata, expose status, and update base positions in one atomic-file operation. Initialization loads reference data after the existing backend setup. A base-position update through the original backend entry point uses the new commit operation; non-calibration settings retain their existing path.

## Stock save

`cmd_EXTRUDER_OFFSET_ACTION_SAVE_RESULT` batches the measured results for the existing JSON backend. It removes the independent reference in that commit and refreshes runtime offsets afterward. It does not alter the native probe, heat, wipe, or docking algorithms.

## Macro integration

The CFG checks native capability before starting an independent cycle and before saving. It snapshots all four applied offsets, derives the selected correction relative to an unchanged reference, checks its limits, and verifies the resulting runtime offsets. Validation retains a read-only save policy. T0's button returns normally with an informational web UI warning.

## Verification

The original native files and config were separately backed up and hash-verified before deployment. Incoming Python compiled on the printer, and installed file hashes were verified. Local tests passed 32 native regressions and 23 macro workflow checks. Live tests covered every secondary tool, reference persistence through restart, stock full calibration, full-to-single transition, and clean/validate invariants. See [Validation](validation.md).

The repository also adds documentation, portable synthetic test fixtures, an offline staging tool, and a privacy audit. These repository files are not printer modifications. No speed-tuning change was deployed.
