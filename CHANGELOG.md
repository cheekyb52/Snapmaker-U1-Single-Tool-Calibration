# Changelog

## Unreleased

### Attribution review — 2026-10-12

- Make the Paxx, Snapmaker, and Klipper acknowledgements prominent in the README.
- Add a dated notice identifying the native calibration modifications and clarify independent maintenance and source provenance.
- Preserve the existing GPL-3.0 license and upstream notices. This review changes documentation and package records only; native Python and macro payloads remain identical to the validated deployment.

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
