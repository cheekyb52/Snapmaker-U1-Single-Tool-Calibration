# Instructions for coding agents

Read `README.md`, `docs/codex-handoff.md`, and `docs/installation.md` before working on this project.

- Scope: independent tool calibration and clean/validate macros only. Do not add unrelated printer, filament, slicer, motion, camera, or account changes.
- Never enable debug mode or factory mode. Use normal firmware operation and authorized access.
- Obtain the owner's target printer, installed build, connection details, and authorization privately. Do not infer them from the test fixture or commit them.
- Check live print state before every printer interaction. Printing, paused, active virtual-SD jobs, and unknown state permit no dependent writes or controls. Do not cancel, pause, or emergency-stop a print automatically.
- Before persistent changes, obtain a timestamped local configuration backup and verify inventory, file sizes, and SHA-256 hashes. Back up native files outside the config root separately. Keep originals immutable and prepare edits in a separate working copy.
- Match the actual target source hashes. If they differ from the tested baseline, stop automatic patch application and adapt the calibration changes to that source with explicit review.
- Keep firmware profiles separate: the original 1.4 payload is live validated; `profiles/paxx-2.0-pr760` has passed offline, startup, independent T1/T2/T3 save tests and post-save restart persistence. Stock full calibration, its restart and a subsequent independent T2 save/new-reference pin/restart have passed; default validation and the tight-limit warning path have passed on PR760, along with Mainsail and Fluidd warning checks. Match all three hashes; do not apply both native patches or treat the PR number as an immutable build identifier. The shared CFG remains version 0.1.0.
- Preserve the other three saved entries and applied offsets during an independent save. T0 single calibration stays disabled. Stock full calibration must retire the pinned reference.
- Keep default stock commands, probing, heating, and docking behavior intact. Do not implement adapters that replace native methods at runtime.
- The operator drives motion, heating, nozzle cleaning, plate removal, and calibration buttons unless explicitly requesting otherwise. Do not infer that a nozzle was cleaned or a plate removed.
- Keep credentials, addresses, serial numbers, calibration tables, backups, screenshots, and raw device logs outside this repository.
- Upstream contributions require the owner's explicit authorization. Keep any authorized usermod contribution under `overlays/mods/cheeky_b52/`; keep personal build workflow changes in the owner's fork on a separate branch. Publishing requires the owner's specific destination and authorization.

Speed tuning is deferred at the owner's request. Preserve six validation ring points, ten calibration ring points, and three XY repeat samples.
