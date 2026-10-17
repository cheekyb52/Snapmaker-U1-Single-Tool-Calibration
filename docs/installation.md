---
title: Installation
---

# Installation

## Compatibility

The original implementation was live tested on build `1.4.1.6_20260608141446`; its hashes remain in [tests/native/manifest.json](../tests/native/manifest.json). A separate [PR760 profile](../profiles/paxx-2.0-pr760/manifest.json) is offline tested and installed on one captured Paxx 2.0 source set. It passed the planned live acceptance: startup, independent T1/T2/T3 saves and restarts, stock full calibration, a subsequent independent save, default and tight-limit validation, manual-wait abort, and warnings in both web UIs. The separate usermod image also passed operator-driven flash/20 boot checks, 16 independent T2 save checks, nine settled restart checks and 16 default validation checks. Planned printer testing is complete on the captured source set; measured alignment-artifact acceptance remains outside this completed test scope. See [Firmware compatibility](firmware-compatibility.md) before choosing a profile.

Match all three native baseline SHA-256 values before applying either patch. A matching version label alone is insufficient. A mismatch requires adapting the calibration changes to the actual installed source and reviewing the new diff.

Both native changes and the macro CFG are required for independent saves. Installing only the CFG intentionally blocks single-tool calibration when the native capability is absent. Use authorized access in normal firmware operation. Never enable debug or factory mode.

## Back up the target

1. Verify live `print_stats.state`, `virtual_sdcard.is_active`, and `pause_resume.is_paused` before every printer interaction. A print, paused job, active virtual-SD job, or unavailable state blocks changes. Verify an idle stock calibration controller too.
2. Obtain a timestamped local snapshot of the complete configuration root, including `snapmaker/extruder_base_position.json`, the existing macro files, and their include configuration. Record the file inventory, sizes, and SHA-256 hashes; verify downloads against the source inventory and hashes.
3. Separately back up the native files outside that root: `klippy/kinematics/extruder.py`, `klippy/extras/extruder_config_bak.py`, and `klippy/extras/probe_inductance_coil.py`. Also locate and capture the imported `queuefile.py` for inspection of the stock writer contract (`klippy/queuefile.py` on the captured PR760 build). Preserve relative remote paths, ownership, and permissions in a private manifest.
4. Keep backup originals immutable. Prepare edits in another directory. Keep every snapshot and connection detail outside this repository.

Use the owner's verified backup utility when available. The original deployment used a complete configuration snapshot plus a separately verified native-source snapshot; neither is a whole-device image. A backup error blocks dependent writes.

## Stage a source-matched patch locally

The staging utility only reads local files and writes a new local directory. It cannot connect to a printer or install anything.

```sh
python tools/prepare_install.py --source-root <local-native-working-copy> --output <new-private-staging-directory>
```

The source root must contain the three `klippy/...` files. By default, the utility selects exactly one profile using all three baseline hashes. It applies exact patch hunks, compiles the resulting Python, checks the expected modified hashes, and stages the shared macro CFG under `config/extended/klipper/`. It rejects unknown/mixed sources or an existing output directory. Review the selected manifest, patch and staged files before deployment.

To require the PR760 profile explicitly:

```sh
python tools/prepare_install.py --source-root <local-native-working-copy> --output <new-private-staging-directory> --profile paxx-2.0-pr760
```

Use `--profile stock-1.4.1.6` to require the original source set. An explicit profile still requires exact source hashes. The original `overlays/mods/tooloffsets/01-native` patch is for 1.4 only; the PR760 patch is separate under `profiles/paxx-2.0-pr760/01-native`. Never apply both patches to one source tree.

Do not force a mismatched patch, copy test fixtures over another firmware build, or patch immutable backups. On a different build, follow [Codex Handoff](codex-handoff.md) to prepare and test an adapted patch instead.

## Deploy using normal authorized access

1. Recheck live idle state immediately before each mutation. Stop if the machine started a job while staging.
2. Upload the three reviewed native files to their existing paths beneath the installed Klipper root, preserving the original owner and mode. Stage temporary siblings, verify hashes, and replace the intended files. Keep service actions explicit and documented for that target.
3. Upload `70_tool_offsets.cfg` to the configuration root's `extended/klipper/` directory. Confirm that the active configuration includes `extended/klipper/*.cfg`; if it does not, back up and review the required include change first. Paxx documents this include location in [Klipper Includes](https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware/blob/develop/docs/klipper_includes.md).
4. Restart the actual Klipper service/process using the target's normal service mechanism. A G-code `RESTART` alone reinitializes objects inside the existing process and cannot be relied on to reload edited Python modules. Do not flash firmware or alter startup flags as part of this procedure.
5. Verify service readiness, installed file hashes, and `extruder_config_bak.preserve_reference_supported == true`. Confirm the saved table and all applied offsets are unchanged by deployment. If reference metadata was already present, verify it and the runtime reference match the backed-up state.

Read `printer/info` readiness before collecting a fresh object snapshot for comparison. A pre-ready snapshot can contain temporary zero offsets even when its keys exist. Readiness can also precede automatic activation of the physically attached tool. Confirm a stable active tool, its matching G-code origin, and stable applied offsets in fresh snapshots after ready. Retain any failed initial snapshot privately and investigate a persistent mismatch before further controls.

If the macro CFG already matches the reviewed shared payload's executable settings, reinstalling it is unnecessary for the native port. Its version label may predate the candidate's native files; the profile manifest records the shared CFG separately.

Deployment itself must not change saved calibration. Installation has no automatic heat, motion, calibration, or save step. The operator decides when to start acceptance cycles.

## First use and acceptance

Read [Macro Work Instructions](work-instructions.md), then acknowledge the locally verified backup using `OFFSET_ARM_SAVE BACKUP=<verified-backup-timestamp>`. This acknowledgement is cleared on restart and does not perform or verify a backup itself.

Capture private before/after evidence for each secondary tool: saved bases, applied offsets, shared-reference metadata, active origin, controller state, and heater targets. Verify that only the selected tool changes. Check persistence across a normal process restart, stock full-calibration reference retirement, and validation with byte-identical saved JSON. See [Validation](validation.md) and [Codex Handoff](codex-handoff.md) for acceptance criteria. Physical cycles require the owner's request and manual confirmations.

If readiness or invariants fail, stop further saves and follow [Rollback](rollback.md).
