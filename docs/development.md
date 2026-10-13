---
title: Development
---

# Development

## Local checks

The current project version/date appears at the top of the README, macro CFG, native patch, and modified native source files. Update those labels and `tests/native/manifest.json` together whenever distributed files change. Keep prior live-tested hashes distinct from current package hashes when only headers change, then regenerate the privacy report and package inventory.

Use Python 3.10 or later in a local development environment:

```sh
python -m pip install -r requirements-dev.txt
python -m unittest tests.native.test_native tests.test_macros
python tools/audit_project.py
```

The suite exercises the actual changed native methods with hardware dependencies stubbed and the actual macro templates with synthetic printer state. It does not connect to a printer or heat/move hardware. All fixture base positions are synthetic. `tests/acceptance.json` records sanitized live results separately.

`tools/prepare_install.py` stages exact tested sources offline; it rejects unmatched hashes and an existing output directory. It is not a remote installer. See [Installation](installation.md).

## Overlay organization

`overlays/mods/tooloffsets` contains two numbered stages: native patches, then the macro template. This layout follows [Paxx's development conventions](https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware/blob/develop/docs/development.md).

The patch directory maps to the installed Klipper root. The native patch uses `a/klippy/...` / `b/klippy/...` paths for `-p1` application there. Its leading version comments are metadata; [GNU patch supports leading headers](https://www.gnu.org/software/diffutils/manual/html_node/Merging-with-patch.html), and the offline staging tool accepts comment-only preambles. The template root mirrors the firmware-config template location. Paxx's [firmware builder](https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware/blob/develop/scripts/create_firmware.sh) applies patch stages without fuzz and copies root payloads. Its [Makefile](https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware/blob/develop/Makefile) treats hyphens as profile/mod separators, hence the mod name `tooloffsets`.

This repository does not include or modify Paxx's firmware builder. The overlay has not been integrated into a full firmware image or flashed. A future owner-controlled build must establish compatible sources and inspect its resulting payload. No upstream submission is implied.

## Publication audit

Run `tools/audit_project.py` from the project root. It scans the publishable tree for captured media, private paths/addresses, private-key material, common credentials/tokens, raw dumps/logs, and unwanted project artifacts. Findings identify paths and lines without printing sensitive values. `.gitignore` alone is not the audit: files present in ignored locations are also findings.

`privacy-report.json` records the final automated scan, and `package-manifest.json` records relative file paths, sizes, and SHA-256 hashes. The inventory excludes its own file. Review both and the package's file list before publishing. The audit is a bounded set of checks, not a guarantee against every possible secret format.

Keep private backups and device evidence outside this tree. Required upstream copyright notices are preserved; the upstream authors' public copyright contact is attribution, not the owner's private information. Only this calibration project belongs in the owner's chosen repository.
