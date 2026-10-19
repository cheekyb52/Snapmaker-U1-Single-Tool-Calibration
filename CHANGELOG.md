# Changelog

## Unreleased

### 0.2.0-dev2 — 2026-10-18

- Sync the personal firmware fork to upstream `b73cfc70e343a0f4bf5b178481818ef1175d3918`; keep native calibration payloads unchanged.
- Gate inherited Cloudflare hosting on personal fork branches, with explicit opt-in through `ENABLE_CLOUDFLARE_DEPLOY=true`.
- Register the exact old packaged CFG hash for stock config migration. Six Linux fixture checks verify upgrades and preservation of custom/unrelated files.

CFG `0.1.1` starts T1/T2/T3 directly without a separate arming command by default. The previous acknowledgement is retained as optional `require_backup_arm`, disabled by default. Invalid target/reference errors are specific. Native source files, offset preservation, probe settings and manual cleaning/plate confirmations are unchanged. Offline coverage exercises unarmed T1/T2/T3 saves with other-tool preservation, optional-policy rejection/acceptance and its pre-save recheck. This revision has not yet been live-tested; the earlier 94-check and printer acceptance records remain historical.


### 0.2.0-dev1 — 2026-10-16 (acceptance updated 2026-10-17)

- Port the calibration changes to the exact captured Paxx 2.0 PR760 source set in the same three native files, preserving newer nozzle properties, filament helpers and tool-change behavior. Keep the original 1.4 payload and shared CFG unchanged.
- Add a separate PR760 patch, source fixtures, hash manifest and sanitized acceptance record. Select staging profiles using all three hashes and reject unmatched or mixed sources.
- Pass 94 offline checks across both native profiles, shared macros and profile/staging tools.
- Verify installed native files and normal startup with 16 checks after complete verified backups. Deployment preserves saved data, the reference, CFG and all applied offsets.
- Complete independent T1/T2/T3 saves with 16 checks each and normal restart persistence with nine checks per run. Only the selected tool changes; other tools and complete reference metadata are preserved. The earlier initial T2 run passed 15 checks.
- Verify stock full calibration with ten pre-Finish and eleven post-exit checks, operator-confirmed completion and nine restart checks. All four measurements save and pinned metadata retires. The subsequent independent T2 save passes 16 checks and nine restart checks, pinning the new stock frame.
- Verify T0 warnings in both Mainsail and Fluidd with 13 checks each, operator-confirmed OK dismissal and no touchscreen anomaly. Manual-cleaning-wait abort passes 12 checks with unchanged calibration.
- Pass default validation with 16 checks and all six pairs within 0.05 mm XYZ. A separate 0.000001 mm run passes 17 checks and correctly flags all six pairs without a G-code error. Both runs preserve saved bytes, applied offsets and reference, with idle controllers and zero heater targets.
- Build a separate seven-file optional `extended-cheeky_b52` usermod candidate against pinned upstream commit `4bd40f7eb4e396d275c7ede0b7f15d0788588696`. Verify all five payload files from the unpacked image and pass 17 build-guard fixture checks.
- Retain explicit limits: one tested printer/source set, no printed alignment-artifact acceptance, no live active-probing abort acceptance, and deferred speed tuning.
- Record owner-reported successful-looking prints using the macros on 2026-10-17. A measured alignment artifact remains untested.
- Operator-flash the built image and pass 20 read-only boot checks, including exact native/ROM-template hashes and unchanged saved calibration, reference and all four applied offsets. Record the custom Klipper source label `HEAD`.
- Pass 16 post-flash independent T2 save checks and nine normal restart checks after automatic tool activation settled. Preserve the initial early origin-check failure and verify recovery through native startup without a firmware change or second restart. Complete the final post-flash default validation with 16 checks, all six pairs within 0.05 mm and unchanged saved calibration, offsets and reference. Planned printer testing is complete.
- Publish the optional username mod and a separate personal CI workflow in the owner's firmware fork, with experimental prereleases and instructions for community testers. Defer upstream submission while wider testing is collected.

## 0.1.0 — 2026-10-12

### File identification

- Add project version/date banners and the repository URL to the macro CFG, native Python patch, and distributed modified Python files; show the version/date at the top of the README.
- Retain the live-tested source hashes in the manifest alongside the versioned package hashes. The new headers are comments; calibration behavior is unchanged.
- Update offline staging to accept the patch's comment header and verify the versioned CFG hash. Future distributed-file changes must update the project version and date together.

### Attribution review — 2026-10-12

- Make the Paxx, Snapmaker, and Klipper acknowledgements prominent in the README.
- Add a dated notice identifying the native calibration modifications and clarify independent maintenance and source provenance.
- Preserve the existing GPL-3.0 license and upstream notices. That attribution review changed documentation and package records only. The later version banners change file hashes without changing executable behavior.

### Added

- Independent T1/T2/T3 saves with a persisted shared reference, guarded native command, atomic persistence, and unchanged other-tool offsets.
- Per-tool calibration buttons, T0 informational warning, manual cleaning/plate confirmations, backup acknowledgement, and waiting-cycle abort.
- Four-tool cleaning and six-pair validation with configurable per-axis tolerances and no calibration save.
- Numbered overlay payloads, offline staging, portable regression tests, sanitized live acceptance results, and installation/operator/recovery/handoff documentation.

### Changed

- Stock full calibration batches results and retires the independent reference, restoring ordinary centering.
- Offset refresh activates the G-code origin only for the active physical tool.

### Verified

- 32 native and 23 macro regressions passed.
- Live T1/T2/T3 saves, restart persistence, stock full calibration, full-to-single transition, and clean/validate invariants passed on `1.4.1.6_20260608141446`.

### Deferred

- Speed tuning, broad firmware compatibility, full-image build/flash validation, and printed alignment-artifact acceptance.
