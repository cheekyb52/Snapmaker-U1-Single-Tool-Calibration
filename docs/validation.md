---
title: Validation Results
---

# Validation Results

## Tested target

One Snapmaker U1 running build `1.4.1.6_20260608141446` was tested. Its exact installed native sources were captured and hashed. A broader Paxx release label was not established. Compatibility with a different firmware build must be checked against that build's source and APIs.

No debug or factory mode was used. The operator drove calibration buttons, manual cleaning, and plate confirmation. Source/config backups and installed hashes were verified.

## Acceptance matrix

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

The cleaning-wait abort and shortened T0 warning dialog were also verified during the CFG phase. Abort during active probing was not demonstrated. The shared prompt protocol is used for Fluidd/Mainsail; independent visual checks on both frontends remain unrecorded.

## Validation residuals

All six tool pairs passed 0.05 mm per-axis limits. The largest absolute residuals were:

| Axis | Maximum residual | Limit |
| --- | --- | --- |
| X | 0.0111 mm | 0.05 mm |
| Y | 0.0038 mm | 0.05 mm |
| Z | 0.0053 mm | 0.05 mm |

Saved JSON bytes, all four applied offset vectors, and the cached reference were exactly unchanged. The active origin matched the active tool, both controllers returned idle, and every heater target was zero.

Sanitized machine-readable results are in [tests/acceptance.json](../tests/acceptance.json). The repository excludes raw printer dumps, actual calibration tables, connection details, credentials, and images. Regression fixtures use synthetic base positions.

## Limits and deferred work

- These checks establish the save/reference/workflow invariants on the tested build. They do not establish print quality, an alignment-artifact result, or compatibility across all firmware versions.
- Probe failure and write-failure behavior has offline coverage; not every hardware interruption was exercised live.
- Validation detects relative registration, not absolute bed height or a common translation of all tools.
- Firmware packaging through the standalone overlay has not been built or flashed. The native patch and CFG were tested through a backed-up manual deployment.
- Performance tuning is deferred. The validated probe phase took about 8.1 minutes in one polling-based observation; total cycle time includes heating, cooling, and operator waits.
