---
title: Documentation
---

# Independent Tool Offset Calibration

| Guide | Purpose |
| --- | --- |
| [Installation](installation.md) | Check compatibility, back up, stage the patch, and activate the macros |
| [Firmware compatibility](firmware-compatibility.md) | Compare the 1.4 and PR760 sources and recover the feature after an update |
| [Work instructions](work-instructions.md) | Operate the buttons, clean nozzles, and interpret results |
| [Implementation](implementation.md) | Understand the shared reference and independent save contract |
| [Changes](changes.md) | Review each modified printer file and its behavior |
| [Validation](validation.md) | Read the offline and live acceptance results |
| [Rollback](rollback.md) | Restore a matched configuration/native snapshot |
| [Codex handoff](codex-handoff.md) | Adapt and verify this project on another owner's printer |
| [Development](development.md) | Understand the overlay layout and run local checks |

The documentation keeps the original 1.4 evidence separate from the PR760 profile, which has completed the planned live acceptance: secondary-tool saves and restarts, stock full calibration and subsequent independent save, both validation paths, manual-wait abort, and warnings in Mainsail and Fluidd. The separate usermod image has built successfully and passed operator-driven flash/20 boot checks, 16 independent T2 save checks and nine settled restart checks. Post-flash default validation passed all 16 checks with all six pairs in tolerance and unchanged calibration. Planned printer testing is complete. Performance tuning is deferred.
