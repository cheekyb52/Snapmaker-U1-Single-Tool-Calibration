---
title: Validation Results
---

# Validation Results

## PR760 acceptance — 2026-10-16–17

Candidate `0.2.0-dev1` targets the exact source set in [the PR760 manifest](../profiles/paxx-2.0-pr760/manifest.json). It passes 32 native regressions. The unchanged 1.4 profile passes 32, shared macro checks pass 23, and profile/staging checks pass seven: **94 offline checks passed**. Tests cover exact patch application, source-profile selection, rejection of mixed sources and preservation of unrelated newer firmware code.

Fresh configuration and native-source backups were verified before persistent changes. Installed hashes matched the reviewed port. The operator confirmed PLA in all four tools and unchanged nozzle hardware, and drove all calibration buttons, cleaning, plate confirmations and stock Finish actions. Monitoring used read-only requests. No debug or factory mode was used.

| Case | Result |
| --- | --- |
| Installation/startup | 16 checks passed |
| Independent T1/T2/T3 calibration | 16 checks each; only the selected tool changed |
| Normal restart persistence | Nine checks each after T1, T2, T3, stock full and the subsequent independent T2 save |
| Stock full calibration | Ten pre-Finish and eleven post-exit checks; operator confirmed normal completion |
| Independent T2 after stock full | 16 save checks; new stock frame pinned and other three tools preserved |
| T0 warning in Mainsail and Fluidd | 13 checks each; operator confirmed OK dismissal and no touchscreen anomaly |
| Abort at a manual-cleaning wait | 12 checks passed; saved and applied calibration unchanged |
| Default clean/validate | 16 checks; all six pairs within 0.05 mm XYZ limits; no calibration changes |
| Deliberately tight validation | 17 checks; all six pairs correctly flagged at 0.000001 mm XYZ; no calibration changes |

Every independent-save check compared the measured correction with the selected saved base and applied offset. The other three saved entries and offsets, complete reference metadata and unrelated JSON were preserved. Stock full calibration saved all four measurements, retired reference metadata from disk and memory, and restored ordinary XY midpoint/T0-Z centering. Its subsequent independent T2 save started from that exact table and pinned the new frame. Normal process restarts verified identical saved bytes and all four applied offsets after readiness; backup acknowledgement cleared as expected and was rearmed against the verified session backup.

Default validation verified all six console residuals and flags against the measured results. Its maximum absolute pair residuals were:

| Axis | Maximum residual | Limit |
| --- | --- | --- |
| X | 0.0023 mm | 0.05 mm |
| Y | 0.0028 mm | 0.05 mm |
| Z | 0.0035 mm | 0.05 mm |

A separate run at deliberately tiny 0.000001 mm XYZ limits exercised all six failure reports and the aggregate calibration warning without a G-code command error. This expected failure report passed the workflow test. Both validation runs left saved JSON byte-identical, all four applied offsets and the reference unchanged, with correct active origin, idle controllers and zero heater targets.

Mainsail and Fluidd warning display and OK dismissal were operator-confirmed without touchscreen anomalies. The Fluidd title, text and button were visually reviewed from a user-supplied screenshot; no image was saved to the project. Abort acceptance covers a manual-cleaning wait only. Native post-park retries occurred during some independent and stock cycles and recovered; they did not prevent successful completion. They are not attributed to the calibration patch.

The sanitized [PR760 acceptance record](../profiles/paxx-2.0-pr760/validation.json) contains check counts, residual summaries and builder provenance. Raw device logs, actual saved calibration tables, connection details and images remain excluded.

### PR760 optional usermod builder — 2026-10-17

The seven-file candidate under `overlays/mods/cheeky_b52/` completed the normal
extended-firmware build with `PROFILE=extended-cheeky_b52`, pinned to firmware
repository commit `4bd40f7eb4e396d275c7ede0b7f15d0788588696`. Its source guard
matched the three reviewed native baselines and the unchanged atomic writer.
The builder applied the patch without fuzz and verified modified hashes,
Python syntax and the macro template hash.

After packing, the resulting firmware image was unpacked independently. All
five payload checks passed: three modified Python files, the unchanged atomic
writer and the macro template. The output is 253,541,120 bytes; its SHA-256 and
the exact candidate inventory are in [candidate validation](../profiles/paxx-2.0-pr760/validation.json).
The build used Docker on Linux with a separate image tag. It did not flash a
printer, establish boot acceptance, use debug mode or submit upstream changes.

Seventeen additional fixture checks passed for the three build guards: shell syntax, refusal outside the builder, acceptance of valid inputs, and rejection of each altered baseline, patched file and macro template. The guard scripts left their inputs unchanged; the built payload was untouched.

### Usermod image boot — 2026-10-17

The operator flashed the exact image identified above and confirmed it online. All 20 read-only boot checks passed: verified pre-flash backups, readiness, idle print/SD/pause state, native capability, byte-identical saved calibration and persistent macro CFG, unchanged shared reference and all four applied offsets, correct active origin, registered project commands, idle controllers, zero heater targets, cleared backup acknowledgement, four installed native hashes, normal process arguments/rt cgroup, and the ROM macro template hash.

Klipper reports its source version as `HEAD` on this custom build. Identity is established by the recorded image/source hashes and matching installed payload, rather than that source label. The full prior live matrix used the same reviewed native payload deployed manually.

The first independent T2 cycle on the flashed image passed all 16 checks: only T2's saved base and applied offset changed by the measured correction. T0/T1/T3, the complete shared reference and unrelated fields were preserved, with correct active origin and idle/off cleanup. One native T2 post-park retry recovered before probing.

Its normal Klipper restart passed all nine checks after automatic tool activation settled. An initial ready snapshot showed the default active tool and zero origin, before native startup activated the physically attached T2 and applied its origin. The early eight-of-nine result and snapshots are retained privately. Two later snapshots verified stable active tool/origin, identical saved bytes, the shared reference and all four offsets, the same new normal process, capability and idle/off state. No second restart, manual origin correction or firmware change was used. Verification now waits for automatic tool activation and a matching origin as well as readiness. The final default no-save validation passed all 16 checks. All six console residuals and flags matched the measured results and passed the 0.05 mm XYZ limits. Maximum absolute pair residuals were 0.0095 mm X, 0.0040 mm Y and 0.0072 mm Z. Saved JSON remained byte-identical, all four applied offsets and the reference were unchanged, the active origin was correct, controllers were idle and heater targets zero. One native T2 post-park retry recovered before T3 probing. This completes the planned printer testing on the tested machine and source set.

## Original 1.4 tested target

One Snapmaker U1 running build `1.4.1.6_20260608141446` was tested. Its exact installed native sources were captured and hashed. A broader Paxx release label was not established. Compatibility with a different firmware build must be checked against that build's source and APIs.

No debug or factory mode was used. The operator drove calibration buttons, manual cleaning, and plate confirmation. Source/config backups and installed hashes were verified.

Project version `0.1.0` adds comment-only version/date banners to the native sources and CFG after that live acceptance. The manifest records both the live-tested hashes and current versioned hashes. Python AST and parsed macro configuration comparisons confirm the implementation is unchanged; offline staging and regression checks cover the versioned payload. No printer installation was performed for this metadata update.

## Original 1.4 acceptance matrix

| Case | Result | Evidence |
| --- | --- | --- |
| Native offline regressions | 32 passed | Atomic-save failures, stale tables, reference metadata, T0/print guards, stock compatibility, restart load, scope/syntax/diff checks |
| Macro workflow regressions | 23 passed | Actual dispatcher parsing, T0 prompt, calibration/validation, tolerances, abort, capability checks, active origin |
| T2 independent save | 15 live checks passed | Only T2 saved/applied values changed; all other tools preserved |
| T2 restart persistence | 9 live checks passed | Saved data and pinned reference reloaded with identical applied offsets |
| T3 independent save | 15 live checks passed | Only T3 changed; prior T2 correction and complete reference metadata preserved |
| Stock full calibration | 14 live checks passed | Four results saved, reference retired, normal centering restored, successful screen and exit |
| T1 after stock full calibration | 15 live checks passed | Only T1 changed and the new stock reference was correctly re-pinned |
| Clean and validate | 10 workflow checks and 6 pair checks passed | No saved data, applied offset, or cached-reference changes |

The cleaning-wait abort and shortened T0 warning dialog were also verified during the CFG phase. Abort during active probing was not demonstrated. Separate operator-confirmed Mainsail and Fluidd visual checks were subsequently completed on PR760, as recorded above.

## Original 1.4 validation residuals

All six tool pairs passed 0.05 mm per-axis limits. The largest absolute residuals were:

| Axis | Maximum residual | Limit |
| --- | --- | --- |
| X | 0.0111 mm | 0.05 mm |
| Y | 0.0038 mm | 0.05 mm |
| Z | 0.0053 mm | 0.05 mm |

Saved JSON bytes, all four applied offset vectors, and the cached reference were exactly unchanged. The active origin matched the active tool, both controllers returned idle, and every heater target was zero.

Sanitized machine-readable results are in [tests/acceptance.json](../tests/acceptance.json). The repository excludes raw printer dumps, actual calibration tables, connection details, credentials, and images. Regression fixtures use synthetic base positions.

## Limits and deferred work

On 2026-10-17, the owner reported having printed using these macros and that the results looked fine. This records practical visual experience. Print count, artifact, measurements and a firmware-specific print-test procedure were not provided; measured alignment-artifact acceptance remains open.

- These checks establish the save/reference/workflow invariants on the tested build. They do not establish print quality, an alignment-artifact result, or compatibility across all firmware versions.
- Probe failure and write-failure behavior has offline coverage; not every hardware interruption was exercised live.
- Validation detects relative registration, not absolute bed height or a common translation of all tools.
- The original 1.4 standalone overlay has not been built or flashed as a firmware image. A separate PR760 username usermod candidate passed a complete builder run and five checks against its unpacked image; the operator subsequently flashed it and it passed 20 boot, 16 independent T2 save and nine settled restart checks. The complete earlier live matrix uses the backed-up manual deployment; post-flash default validation passed all 16 checks with all six pairs in tolerance and no calibration changes. The planned printer test matrix is complete.
- Performance tuning is deferred. The validated probe phase took about 8.1 minutes in one polling-based observation; total cycle time includes heating, cooling, and operator waits.
