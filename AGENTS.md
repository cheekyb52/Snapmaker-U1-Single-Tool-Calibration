# Instructions for coding agents

Read `README.md`, `docs/codex-handoff.md`, and `docs/installation.md` before working on this project.

- Scope: independent tool calibration and clean/validate macros only. Do not add unrelated printer, filament, slicer, motion, camera, or account changes.
- Never enable debug mode or factory mode. Use normal firmware operation and authorized access.
- Obtain the owner's target printer, installed build, connection details, and authorization privately. Do not infer them from the test fixture or commit them.
- Check live print state before every printer interaction. Printing, paused, active virtual-SD jobs, and unknown state permit no dependent writes or controls. Do not cancel, pause, or emergency-stop a print automatically.
- Before persistent changes, obtain a timestamped local configuration backup and verify inventory, file sizes, and SHA-256 hashes. Back up native files outside the config root separately. Keep originals immutable and prepare edits in a separate working copy.
- Match the actual target source hashes. If they differ from the tested baseline, stop automatic patch application and adapt the calibration changes to that source with explicit review.
- Preserve the other three saved entries and applied offsets during an independent save. T0 single calibration stays disabled. Stock full calibration must retire the pinned reference.
- Keep default stock commands, probing, heating, and docking behavior intact. Do not implement adapters that replace native methods at runtime.
- The operator drives motion, heating, nozzle cleaning, plate removal, and calibration buttons unless explicitly requesting otherwise. Do not infer that a nozzle was cleaned or a plate removed.
- Keep credentials, addresses, serial numbers, calibration tables, backups, screenshots, and raw device logs outside this repository.
- Do not connect this project to, push to, or submit a pull request to Paxx's repository. Its documentation and layout are references only. Publishing requires the owner's specific destination and authorization.

Speed tuning is deferred at the owner's request. Preserve six validation ring points, ten calibration ring points, and three XY repeat samples.
