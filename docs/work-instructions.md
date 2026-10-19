---
title: Macro Work Instructions
---

# Macro Work Instructions

## Before starting

For troubleshooting, report the project version/date printed at the top of `70_tool_offsets.cfg`, the installed native profile/version, and your firmware build. The PR760 native candidate is version `0.2.0-dev1` and reuses the shared version `0.1.1` CFG; different artifact versions are expected. The profile/package manifests provide exact file hashes. Copies from the original live test may predate these version banners.

After a firmware update, check native support before using the calibration buttons: the CFG can survive while the required Python changes are replaced. A restart clears an optional backup acknowledgement; default button use does not require it. See [Firmware compatibility](firmware-compatibility.md) for the two distinct guards and recovery steps. The exact captured PR760 profile has completed the planned live acceptance; see [Validation](validation.md) for the results and remaining limits.

Use a printer that is idle, with no paused print or active virtual-SD job. Clear the bed and tool-change area. Confirm that the calibration ring is accessible and the tools have suitable filament loaded for the stock wiping routine.

For single-tool calibration, the reference tool must have unchanged hardware and a trustworthy calibration. T0 is the default reference. If T0's hotend or reference calibration changed, use stock **Multi-Toolhead Calibration** for all four tools.

After installation, press the selected calibration button directly. No console command or separate backup acknowledgement is required by the default configuration. Follow the nozzle-cleaning and plate-removal prompts during the cycle.

Verified recovery backups remain part of installation and agent-driven persistent changes; see [Installation](installation.md). The macro does not create or verify those backups. Sites that want the previous acknowledgement requirement can enable `variable_require_backup_arm: True` in `_SM_OFFSET_STATE`; see [Optional backup acknowledgement](#optional-backup-acknowledgement).

## Buttons

| Macro | Action | Saves calibration? |
| --- | --- | --- |
| `CALIBRATE_TOOL_0` | Show the warning to calibrate all four tools through the stock feature | No |
| `CALIBRATE_TOOL_1` | Clean and measure T0 and T1; update only T1 | Yes, T1 only |
| `CALIBRATE_TOOL_2` | Clean and measure T0 and T2; update only T2 | Yes, T2 only |
| `CALIBRATE_TOOL_3` | Clean and measure T0 and T3; update only T3 | Yes, T3 only |
| `CLEAN_AND_VALIDATE_OFFSETS` | Clean and measure all four tools; evaluate all six pairs | No |
| `OFFSET_CONTINUE` | Confirm manual nozzle cleaning or PEI plate removal | No direct save; it may advance a single-tool cycle to its save |
| `OFFSET_ABORT` | Exit a pending macro cycle through the stock cleanup macro | Does not undo an earlier save |
| `OFFSET_ARM_SAVE` | Optional acknowledgement for sites enabling `require_backup_arm` | No |

Tool numbers are physical T0–T3. The workflow bypasses slicer tool mapping.

## Single-tool calibration

1. Press the selected T1, T2, or T3 calibration button.
2. The cycle preheats and homes, then heats and wipes the reference nozzle.
3. Clean the nozzle presented to you. Press **OFFSET_CONTINUE** only after cleaning it.
4. The cycle cools that nozzle and repeats cleaning for the selected tool. Clean it and press **OFFSET_CONTINUE**.
5. When the console requests plate removal, remove the PEI plate and clear the ring. Press **OFFSET_CONTINUE** again.
6. The cycle waits for the bed at 55 °C, checks plate absence, and probes reference then selected tool at 130 °C.
7. The selected correction is saved with the shared reference pinned. Runtime checks confirm that the other tools' applied offsets are preserved, then the cycle exits and turns off heaters.

Read the console result. A successful result identifies the saved tool. A missing result, changed baseline, unsupported native capability, or correction over 2 mm per axis blocks saving. Inspect the cause before another attempt.

The custom workflow uses console messages for cleaning and plate confirmation. The stock touchscreen stays in its ordinary state; use **OFFSET_CONTINUE** in the web UI. T0's warning uses the shared Mainsail/Fluidd prompt protocol and its **OK** button only closes the dialog.

## Clean and validate

1. Press **CLEAN_AND_VALIDATE_OFFSETS**.
2. Clean each presented nozzle in T0, T1, T2, T3 order, pressing **OFFSET_CONTINUE** after each cleaning.
3. Confirm plate removal with one more **OFFSET_CONTINUE**.
4. The cycle probes all four tools with six ring points and reports six pair residuals.
5. Read the final **PASS** or **FAIL** report. No calibration is automatically performed or saved.

A pair passes only when each XYZ residual is within that axis's tolerance. Defaults are 0.05 mm on every axis. Override one run from the console:

```gcode
CLEAN_AND_VALIDATE_OFFSETS TOL_X=0.05 TOL_Y=0.05 TOL_Z=0.03
```

For a failure, inspect the tools named in the failing pairs and their reference condition. Multiple tool changes can make the failing pairs ambiguous. If T0 changed, run the stock four-tool calibration. Validation checks relative tool registration; a common shift of all four tools and absolute bed height are outside this check.

## Temperatures and optional reference

Cleaning defaults to 200 °C. Select a cleaning temperature suitable for the loaded filament:

```gcode
CALIBRATE_TOOL_2 HEAT_TEMP=210
CLEAN_AND_VALIDATE_OFFSETS HEAT_TEMP=210 T2_TEMP=220
```

Per-tool overrides are `T0_TEMP` through `T3_TEMP`. Accepted cleaning temperatures are from 170 °C to below 300 °C. Native soft-filament handling and nozzle-diameter input remain in use. Cooling/probing at 130 °C and the 55 °C bed target are fixed in this validated version.

An unchanged alternative physical reference can be selected from the console:

```gcode
CALIBRATE_TOOL_2 REFERENCE=1
```

The reference must differ from the target. This does not enable T0 single calibration or verify that the alternative reference's hardware is unchanged.

## Abort, completion, and status

At a manual-cleaning or plate-confirmation wait, **OFFSET_ABORT** exits and shuts down heaters. This path was live tested during manual cleaning. It is not a guaranteed immediate interrupt of queued probing or motion, and it does not roll back a correction already saved.

While idle, the console command `_SM_OFFSET_STATE` prints the macro's stage and last report. After a normal macro completion, verify idle state and zero heater targets.

For stock full calibration, use the stock screen and its own confirmations. After it reports completion, press **Done/Finish** to exit and shut down heaters. Do not use **OFFSET_CONTINUE** for that stock touchscreen sequence.

## Optional backup acknowledgement

The default is `variable_require_backup_arm: False`. Leave it unchanged for direct button use. To require an explicit acknowledgement under your own operating policy, set it to `True`, reload the configuration, and acknowledge a verified backup before starting a single-tool cycle:

```gcode
OFFSET_ARM_SAVE BACKUP=<verified-backup-timestamp>
```

This optional acknowledgement does not create or verify a backup and clears on restart. The command remains compatible with older workflows. Validation never requires it. A missing acknowledgement blocks before heating and is checked again before saving when this option is enabled.

## Updating an existing test build

Users of `calibration-test-2-1` already have the required native Python support. They can use the standalone `70_tool_offsets.cfg` asset from the newer release without reflashing firmware: while idle, back up the existing CFG and saved calibration data, review the new CFG against any local temperature/tolerance customizations, replace the existing `extended/klipper/70_tool_offsets.cfg`, and restart Klipper to load it. Then the T1/T2/T3 buttons start directly. The CFG's header must identify version `0.1.1` dated `2026-10-18`.

The new firmware build automatically updates an unmodified packaged CFG 0.1.0 through Paxx's stock checksum-based config cleanup. Customized CFGs are preserved and receive a `.default` copy. A firmware update may therefore preserve a customized older persistent CFG. Compare its header/hash with the release asset after updating; replace a surviving CFG 0.1.0 using the same backed-up procedure. Native capability checks still apply on other firmware builds.

## Community test results

Experimental images and their checksums are distributed through [the author's firmware fork](https://github.com/cheekyb52/SnapmakerU1-Extended-Firmware/releases). Source, build identity and testing instructions accompany each prerelease. Follow the backup and compatibility steps in [Installation](installation.md) before flashing or saving calibration.

Share results in [the calibration project's issues](https://github.com/cheekyb52/Snapmaker-U1-Single-Tool-Calibration/issues). Useful details are:

- Full firmware/test-build identifier and whether the test passed or failed.
- Tool tested, nozzle/hotend changes, filament material and whether the reference tool stayed unchanged.
- Confirmation that the other three tools stayed unchanged and whether a restart retained the result; keep the actual calibration table private.
- Validation tolerances and PASS/FAIL, web UI used, and relevant error text if present.

The project remains an experimental optional usermod while wider testing is collected. Upstream submission is deferred.
