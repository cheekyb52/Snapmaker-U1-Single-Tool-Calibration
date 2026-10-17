---
title: Rollback and Recovery
---

# Rollback and Recovery

## Restore a matched snapshot

The native code and calibration JSON form a matched state. Older code can ignore pinned-reference metadata and recalculate a different shared center from independently updated base values. Restoring only the old Python can therefore change every applied tool offset.

For complete rollback, restore the original three native files, original calibration JSON, and original macro/include configuration from the same verified pre-installation snapshots. For recovery to a validated independent-calibration state, restore that snapshot's patched native files, pinned-reference JSON, and CFG together. Preserve unrelated configuration entries by choosing a reviewed recovery scope; do not combine arbitrary snapshots.

1. Verify live print/SD/pause state before every interaction. If state is unavailable or a job is active, stop dependent actions.
2. Make and verify a new private snapshot of the current editable state before overwriting persistent files. Preserve existing recovery originals.
3. Review the selected snapshot's inventory and hashes, including all three native files and `snapmaker/extruder_base_position.json`.
4. Restore the matched files with original paths, ownership, and permissions through normal authorized access.
5. Restart the actual Klipper process and verify readiness, loaded bases, shared reference, all four applied offsets, and active origin. A macro-only restart is insufficient for native code replacement.

Do not use debug or factory mode for recovery. This procedure restores editable files; it is not a whole-device recovery image.

## Remove the feature after a fresh stock calibration

An owner-requested successful stock four-tool calibration retires the pinned reference and produces a table using normal centering. This offers another route to a conventional state before removing the custom feature. It changes all four calibrations and does not restore the previous measurements.

Back up first, let the owner drive the complete stock cycle, confirm that reference metadata is absent and normal applied offsets are correct, then review removal of the native changes and macro CFG. Restore compatible native code for the actual firmware build; do not mix versions. Verify again after a normal process restart.

## Firmware updates

A firmware update may replace the native patch or macro template. Check installed hashes, native capability, persisted reference, and applied offsets before using the buttons again. Do not blindly reapply the old patch to changed sources. If an update boots legacy code against pinned data, avoid motion until the reference/frame state is understood and a matched recovery or adapted implementation is ready.

Recovery settings in a firmware UI are not a substitute for the verified native-file and calibration snapshot described here.
