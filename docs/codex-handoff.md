---
title: Codex Handoff
---

# Codex Handoff

## Objective and boundaries

Implement this calibration feature on the owner's Snapmaker U1, preserving all other printer projects. Read [AGENTS.md](../AGENTS.md), [Installation](installation.md), [Implementation](implementation.md), and [Modified Files](changes.md) first.

The test build is `1.4.1.6_20260608141446`; it is evidence, not the new target's identity. Obtain the actual target/build and authorized connection details privately. Never enable debug or factory mode. Never submit anything to Paxx; the owner's explicit GitHub destination is separate.

The requested behavior is:

- T1/T2/T3 each have an independent calibration button. Only the selected tool's saved base and applied offset may change.
- T0 single calibration is disabled with an informational web UI prompt directing the owner to stock full calibration.
- Clean/validate guides manual cleaning of all four tools and evaluates all six pairwise XYZ residuals against configurable limits. It saves nothing.
- Stock full calibration continues to work and retires the pinned reference.
- Probe/heat/wipe/docking algorithms stay native. Speed tuning is deferred; retain 10 calibration points, 6 validation points, and 3 XY repeats.

## Establish access and backups

Before every printer interaction, check live print state, paused state, and virtual-SD activity. Unknown state or an active/paused job blocks dependent writes and controls. Do not cancel a job automatically.

Before persistent changes, obtain and verify a timestamped local config inventory with sizes and SHA-256 hashes. Separately back up native files outside the config root. Include the calibration JSON and all three affected Python sources, plus the stock writer for inspection. Preserve originals, prepare a separate working copy, and recheck idle immediately before each mutation.

Do not commit connection details, credentials, backup manifests with personal paths, actual offsets, raw logs, or camera captures. Inspect needed evidence privately and publish sanitized conclusions only.

## Match or adapt the source

Compare native baseline hashes with [the manifest](../tests/native/manifest.json). Exact matches can use the offline staging utility. For mismatches, identify equivalent methods and adapt only the calibration-related code in these files:

| File | Required behavior |
| --- | --- |
| `klippy/kinematics/extruder.py` | Opt-in `PRESERVE_REFERENCE=1`; physical T1/T2/T3 only; idle guards; finite complete table; <=2 mm per-axis adjustment; disk/cache agreement; publish selected base after successful persistence; use pinned center; activate origins only for the active tool |
| `klippy/extras/extruder_config_bak.py` | Validated versioned `_offset_reference` with T0 anchor; capability/status; atomic selected/batch commit; retain unrelated JSON; cache after success; fail closed on invalid/stale data |
| `klippy/extras/probe_inductance_coil.py` | Batch stock results and retire metadata before publishing bases; preserve defaults, commands, responses, force-save and eligible fallback behavior |
| `extended/klipper/70_tool_offsets.cfg` | Check capability before heat/save; clean reference/target; derive relative correction; check baseline/limits; verify other tools; all-pair validation with no save; manual continuation and cleanup |

Confirm the native atomic writer API and stock private G-code names on the actual build. Do not introduce runtime monkey patches or silently fall back to legacy saves. Do not enter the public stock touchscreen state machine for the custom cycle; earlier CFG-only attempts allowed that controller to advance and save buffered results.

The fixture source is generic firmware code, not a replacement image. Never overwrite an unmatched target with these full fixture files. Review a narrowly scoped diff, compile locally, and run the regression suite. When adapting APIs, update meaningful test coverage and the source manifest.

## Deployment and live acceptance

Stage and review first; deploy only when the owner authorizes target writes. Use a normal process restart to load native Python, verify exact installed hashes, readiness, capability, and unchanged calibration before physical testing. The owner drives the buttons, cleaning, and plate confirmation unless explicitly asking the agent to do so.

For each T1/T2/T3 cycle, privately record and verify:

1. Only the selected saved base changes; the other three entries and unrelated JSON fields match exactly.
2. Only the selected applied offset changes by the intended correction. The shared frame remains identical; the first independent save pins the previously derived frame.
3. Active G-code origin agrees with the active tool, both workflow controllers are idle at completion, and heater targets are zero.
4. A normal process restart reloads the same table, metadata, frame, and all four applied offsets.

For an owner-requested stock full cycle, verify all measured results saved, pinned metadata removed, normal midpoint/T0-Z centering restored, success on the stock screen, and exit after the owner's Done/Finish confirmation. Verify a subsequent independent save pins that new stock frame.

For clean/validate, verify six pair reports and configurable limits. Saved JSON must be byte-identical, all applied offsets and reference unchanged, active origin correct, and controllers/heaters idle/off at exit.

Test the T0 warning without a save or anomaly. Its common web prompt protocol was exercised, but separate visual acceptance on both Fluidd and Mainsail remains open. The cleaning-wait abort was live tested; immediate interruption of active probing is not established. Never treat an abort as rollback of a completed save.

The existing live acceptance record is [tests/acceptance.json](../tests/acceptance.json). It contains sanitized checks, not the new printer's offsets. Probe/save failure guards have offline coverage; cross-build compatibility and print alignment still need target-specific evidence.

## Suggested owner prompt

> Read AGENTS.md and docs/codex-handoff.md in this repository. Implement this calibration project on my U1 using normal firmware operation. Obtain the target build and authorized connection details privately, verify complete local backups before persistent changes, and match or adapt the native sources. Review and test the staged patch before deployment. I will drive calibration buttons, cleaning, and plate confirmation. Preserve every other project and the other three tools during independent saves. Do not enable debug/factory mode or submit anything to Paxx.
