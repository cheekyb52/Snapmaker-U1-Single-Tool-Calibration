# Source Attribution

This project is distributed under GPL-3.0. See [LICENSE](LICENSE).

The patch and native/parser test fixtures contain or modify Snapmaker's Klipper-derived firmware source. Original copyright and license headers remain in the fixture files, including public upstream author contact notices. Source projects:

- [Snapmaker U1 Klipper](https://github.com/Snapmaker/U1-klipper)
- [Klipper](https://github.com/Klipper3d/klipper)
- [Paxx Snapmaker U1 Extended Firmware](https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware)

Fixture files were captured from the exact installed build identified in the native manifest; this does not establish that every fixture byte matches the current branch of either public repository. Original and modified forms are included to make the patch reviewable and the regressions reproducible. They contain firmware source, not printer configuration or calibration measurements.

Paxx's numbered-overlay structure and documentation organization informed the repository layout. This project is independent, is not an official Paxx release, and has not been submitted to Paxx. Documentation is written for this calibration project; it does not reproduce unrelated firmware instructions.
