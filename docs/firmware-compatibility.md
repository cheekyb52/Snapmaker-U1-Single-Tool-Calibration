---
title: Firmware Compatibility
---

# Firmware Compatibility

**Candidate version: 0.2.0-dev1 | Updated: 2026-10-17**

## Source profiles

| Profile | Native source | Patch status | Live status |
| --- | --- | --- | --- |
| `stock-1.4.1.6` | Exact `1.4.1.6_20260608141446` fixtures | Original version 0.1.0 | T1/T2/T3, restart, stock full calibration, and validation passed |
| `paxx-2.0-pr760` | Captured `2.0.0-paxx12-test-pr-760` source set | Version 0.2.0-dev1 port; 32 native regressions passed | Planned live acceptance passed: saves/restarts, stock full, full-to-single, both validation paths and both web UI warnings |

[Paxx PR760](https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware/pull/760) is a development PR whose contents can change. Its name does not identify an immutable firmware image. The captured pre-flash Klipper reported `2.0.0-paxx12-test-pr-760`; the [PR760 manifest](../profiles/paxx-2.0-pr760/manifest.json) identifies its reviewed source set by SHA-256. No claim is made that it matches every PR760 download, its current head, or every 2.0 release.

The [original manifest](../tests/native/manifest.json), patch, source fixtures, and live acceptance record remain intact. The shared macro CFG is also unchanged at version 0.1.0. Candidate version 0.2.0-dev1 identifies the new native port and project tooling/documentation.

## What changed in the firmware

| Area | Difference from the original source | Port treatment |
| --- | --- | --- |
| `extruder.py` | New nozzle-volume/property handling, filament-temperature helpers, and changes to initialization, status and tool switching | Retain the new firmware code; modify only the original offset-refresh, centering and setter methods, and add the independent-save helper |
| `extruder_config_bak.py` | Byte-identical to the original unpatched backend | Carry forward the reference/persistence changes without an API redesign |
| `probe_inductance_coil.py` | Filament softness and temperature helpers changed | Retain both newer helpers; modify only the stock result-saving method |
| `klippy/queuefile.py` | Required atomic writer inspected separately | Existing `sync_write_file(reactor, path, content, flush=True, safe_write=True)` contract remains usable; no writer changes |
| Stock macro components | Heating, cleaning, cooling, manual presentation and exit components remain available with the parameters used by this project | Reuse them; do not replace them or start the stock touchscreen state machine |

The pre-patch offset/save methods are structurally identical across the captured baselines. The candidate's modified calibration methods are structurally identical to the previously tested implementation. The PR760 patch therefore changes hunk locations and version comments while retaining the same calibration behavior. Cross-profile tests verify that unrelated PR760 code remains unchanged.

## Firmware-update recovery

A firmware update can leave the custom CFG installed while replacing the native Python support. A process restart also clears the macro's backup authorization. These are separate conditions:

| Symptom | Meaning | Required action |
| --- | --- | --- |
| `Single calibration needs T1/T2/T3, an unchanged reference, and a verified backup arm.` | The single-calibration input/backup guard rejected the request; after a restart the backup acknowledgement is empty | Obtain and verify fresh backups before acknowledging the session |
| `Independent saves require the native preserve-reference patch. Saving is blocked.` | The loaded backend does not expose the independent-save capability | Match/adapt, review and install the native patch; rearming alone cannot fix it |

Do not bypass either guard. An older native setter can ignore `PRESERVE_REFERENCE=1` and use ordinary recentering semantics.

1. Read live print/SD/pause state before every printer interaction. Leave active or paused jobs read-only.
2. Back up and verify the current config and native files, including the calibration JSON and atomic writer. Preserve these as the new firmware's recovery originals.
3. Check whether `_offset_reference` survived. Validate its version and T0 anchor, then compare all four offsets derived from the saved bases/reference with the running offsets. A mismatch requires review before motion or deployment; do not delete metadata or recenter as a shortcut.
4. Match all three source hashes to a supported profile. If any differ, stop automatic patching and adapt to those actual sources.
5. Stage the selected patch locally, compile, review its scope and run tests. Never overwrite new firmware files with the full 1.4 fixtures.
6. When installation is authorized, follow [Installation](installation.md): replace only reviewed files, restart the actual Klipper process, then verify capability, hashes, unchanged saved JSON, all applied offsets and active origin.
7. After restart, acknowledge the verified backup for the current session with `OFFSET_ARM_SAVE BACKUP=<verified-backup-timestamp>`. The operator starts the physical acceptance cycles.

Backups contain private device data and stay outside this repository. Recovery uses the actual firmware build's matched code and calibration data; see [Rollback](rollback.md).

## Offline evidence and remaining acceptance

The candidate passes 32 native regressions, including independent T1/T2/T3 saves, preservation of other tools, restart reload, stock full-save behavior, stale/invalid metadata, and failed persistence. The original profile also passes its 32 regressions. The shared macro suite passes 23 checks and profile/staging tests pass seven checks: **94 total**.

Private inspection also confirmed that the existing pinned metadata loads and produces the same four applied offsets as the captured runtime state. That is an offline compatibility check, not a completed on-printer calibration. The sanitized [candidate record](../profiles/paxx-2.0-pr760/validation.json) contains no actual offsets or device details.

PR760 installation/startup passed 16 checks: installed hashes/ownership/modes, a new normal Klipper process in the existing rt cgroup, readiness and native capability, unchanged saved JSON/CFG/reference/all four offsets, correct active origin, idle controllers and zero heater targets. The verified backup was acknowledged for the operator's manual test, without a calibration save. No debug mode, motion or heating was commanded.

One operator-driven T2 physical cycle then passed all 15 checks. Only T2's saved base and applied offset changed, matching the measured correction. The other three tools, complete pinned-reference metadata and unrelated saved fields stayed unchanged. The active origin was correct, both controllers returned idle, and all heater targets were zero. Monitoring was read-only.

A subsequent normal Klipper process restart passed nine checks: identical saved JSON bytes, shared reference and all four applied offsets, correct active origin, native capability, readiness on the same build, normal new process, idle controllers/zero targets, and cleared backup authorization. Fresh stable snapshots were captured after confirmed ready; a snapshot taken before ready had temporary zero offsets. The verified session backup was reacknowledged without saving calibration.

PR760 subsequently completed default validation (16 checks), tight-limit warning validation (17 checks), independent T1/T3 saves and restarts, stock full calibration and restart, the full-to-single transition and restart, manual-wait abort, and warnings in Mainsail and Fluidd. See [Validation](validation.md) for the consolidated results and remaining limits. The 1.4 live results must not be reported as PR760 results. Probe-point counts, repeat samples and cleaning-temperature defaults are unchanged; speed tuning remains deferred.
