---
title: Implementation
---

# Implementation

## Shared-reference invariant

Stock applied offsets are derived from saved base positions. XY uses the midpoint of the minimum and maximum values across the physical tools; Z uses T0's saved base Z. Updating a tool that defines an XY extreme can therefore change every tool's applied offsets.

An independent save uses:

```text
applied_offset[tool] = saved_base[tool] - shared_reference
correction = (measured_target - measured_reference)
             - (old_applied_target - old_applied_reference)
new_saved_target = old_saved_target + correction
```

The first independent save pins the existing shared reference. Later independent saves keep it fixed. Only the target base entry changes, so the other three saved entries and applied vectors remain unchanged. A common homing translation cancels in the two-tool measurement difference.

## Native command contract

```gcode
SET_EXTRUDER_BASE_POSITION EXTRUDER=extruder2 X_ADJUST=<dx> Y_ADJUST=<dy> Z_ADJUST=<dz> PRESERVE_REFERENCE=1
```

`PRESERVE_REFERENCE=1` is allowed for physical `extruder1`, `extruder2`, and `extruder3`. It requires verified idle print/SD/pause state, an idle stock calibration controller, a complete finite four-tool base table, and the stock JSON backend. Corrections over 2 mm per axis are rejected. The persisted table and reference are checked against the cached state before the write.

The CFG checks `extruder_config_bak.preserve_reference_supported` before heating and again before saving. This is required because older native command handlers can ignore an unknown parameter and perform their ordinary recentering save.

Query-only commands do not pin or write a reference. Existing writes without the new option retain legacy recentering behavior.

## Persistence

The existing `snapmaker/extruder_base_position.json` gains `_offset_reference` metadata containing a format version, the shared XYZ position, and a T0 base-position anchor. There is no separate reference file.

Positions and metadata are committed together through the stock atomic-file writer. New cached reference and target base data are published after a successful write. Other saved fields are retained. Invalid metadata fails closed at load; a missing saved reference file cannot silently fall through to a legacy save.

Stock full calibration commits its four results in one JSON write and retires the reference metadata. Normal centering then derives from the newly saved table. Existing command names, responses, `FORCE_SAVE` behavior, and the eligible `SAVE_CONFIG` fallback remain available.

The stock writer uses temporary-file replacement. This project does not claim a whole-device transactional backup or power-loss durability beyond that native writer's behavior.

## Runtime and workflow integration

Offset refresh recalculates all tools, but applies the G-code origin only for the active tool. The CFG also synchronizes that origin without motion before an exit move and verifies all runtime offset vectors after an independent save.

Cleaning, heating, docking, and probe algorithms remain native. The custom macros invoke private stock G-code components and the raw probe command rather than entering the public stock touchscreen calibration state machine. That prevents a background stock sequence from saving the full buffered result set during a validation-only cycle.

Raw probing publishes transient measurements using `UPDATE_CONFIG=1 SAVE_INFO=0` while the stock controller remains idle. Validation compares all six pairs and never calls a save command. The native controller stays in charge during a separately requested stock full calibration.

## Validated settings

| Setting | Value |
| --- | --- |
| Single-tool ring layout | 10 points |
| Validation ring layout | 6 points |
| XY repeat samples | 3 |
| XYZ validation tolerance | 0.05 mm per axis by default |
| Cleaning temperature | 200 °C by default, with run overrides |
| Probe/cooling temperature | 130 °C |
| Bed target | 55 °C |
| Maximum independent adjustment | 2 mm per axis |

The native XYZ method supports only six- and ten-point layouts. Its Z passes retain 3, 3, and 6 samples, with discards on the final pass; the CFG `SAMPLES` setting controls XY repeats. Speed tuning is deferred at the owner's request.
