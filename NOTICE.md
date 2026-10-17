# Source Attribution

This project is distributed under GPL-3.0. See [LICENSE](LICENSE).

## PR760 port — 2026-10-16

Candidate version `0.2.0-dev1` reapplies this project's calibration modifications to a separately captured Paxx 2.0 source set identified by its [manifest](profiles/paxx-2.0-pr760/manifest.json). The original and modified PR760 firmware sources are included for review and reproducible tests, with their upstream notices preserved. Unrelated newer firmware code is retained. The shared macro and original 1.4 native payload are unchanged. The candidate has completed the planned offline and live acceptance, plus a separate usermod image build, operator-driven flash/boot checks and post-flash T2 save/restart/default validation, with no upstream submission; see [Firmware compatibility](docs/firmware-compatibility.md).

## Notice of modifications — 2026-10-12

The [Snapmaker U1 Single Tool Calibration project](https://github.com/cheekyb52/Snapmaker-U1-Single-Tool-Calibration) modified the following native firmware files for this calibration feature:

| Upstream file | Project modification |
| --- | --- |
| `klippy/kinematics/extruder.py` | Opt-in independent T1/T2/T3 saves, pinned-reference centering, and active-tool origin refresh |
| `klippy/extras/extruder_config_bak.py` | Reference metadata validation, capability/status, and atomic selected or batched calibration persistence |
| `klippy/extras/probe_inductance_coil.py` | Batched stock calibration saving and retirement of pinned-reference metadata |

The project also added the calibration/validation macro CFG, tests, staging/audit utilities, and project-specific documentation. Original and modified native sources accompany the patch. The source manifest identifies the exact tested baseline and modified hashes; [Modified Files](docs/changes.md) details the changes. The modifications and this combined project are released under GPL-3.0. Existing upstream copyright, license, and warranty notices are retained.

## Upstream sources and acknowledgements

The patch and native/parser test fixtures contain or modify Snapmaker's Klipper-derived firmware source. Original copyright and license headers remain in the fixture files, including public upstream author contact notices. Source projects:

- [Snapmaker U1 Klipper](https://github.com/Snapmaker/U1-klipper)
- [Klipper](https://github.com/Klipper3d/klipper)
- [Paxx Snapmaker U1 Extended Firmware](https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware)

Fixture files were captured from the exact installed build identified in the native manifest; this does not establish that every fixture byte matches the current branch of either public repository. Original and modified forms are included to make the patch reviewable and the regressions reproducible. They contain firmware source, not printer configuration or calibration measurements.

Thank you to Paxx and the Snapmaker U1 Extended Firmware contributors. Paxx's numbered-overlay structure and documentation organization informed the repository layout. The documentation was written for this calibration project's own behavior; Paxx's firmware builder and unrelated firmware instructions are not included. Source provenance is described above rather than attributing all vendor source or this project's new calibration logic to Paxx.

This project is independently maintained. It is not an official Paxx, Snapmaker, or Klipper release, and affiliation with or endorsement by those projects is not implied. No upstream submission has been made.
