---
title: Development
---

# Development

## Local checks

The current project candidate version/date appears at the top of the README. Native patch/source banners and their manifests identify each payload's version. The original 1.4 native payload remains `0.1.0`; the PR760 native payload remains `0.2.0-dev1`. Project `0.2.0-dev2` uses shared CFG `0.1.1`, which removes mandatory backup arming from default button use. Historical live evidence used CFG `0.1.0`. Update a changed payload's banner and matching manifest together. Do not relabel old live evidence as validation of a new firmware profile. Regenerate the privacy report and package inventory after changes.

Use Python 3.10 or later in a local development environment:

```sh
python -m pip install -r requirements-dev.txt
python -m unittest tests.native.test_native tests.test_macros tests.test_profiles
python tools/audit_project.py
```

The first command runs 64 checks: 32 for the original native profile, 25 shared macro checks and seven profile/staging checks. Run the same 32 native checks in a fresh process with `U1_CALIBRATION_PROFILE=paxx-2.0-pr760` for **96 total**. For example in PowerShell:

```powershell
$env:U1_CALIBRATION_PROFILE = 'paxx-2.0-pr760'
python -m unittest tests.native.test_native
Remove-Item Env:U1_CALIBRATION_PROFILE
```

The suite exercises the actual changed native methods with hardware dependencies stubbed and the actual macro templates with synthetic printer state. It does not connect to a printer or heat/move hardware. All fixture base positions are synthetic. `tests/acceptance.json` records sanitized live results separately.

`tools/prepare_install.py` stages exact tested sources offline; it rejects unmatched hashes and an existing output directory. It is not a remote installer. See [Installation](installation.md).

## Overlay organization

`overlays/mods/tooloffsets` contains two numbered stages: native patches, then the macro template. This layout follows [Paxx's development conventions](https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware/blob/develop/docs/development.md).

That original native stage targets the 1.4 source set. The alternative PR760 native stage lives under `profiles/paxx-2.0-pr760/01-native/` and shares the unchanged macro template. Keeping the alternative outside the original overlay prevents a builder from applying both native patches sequentially. Use the source-matching stager for the selected profile; a full-image integration must explicitly choose one compatible native stage.

The patch directory maps to the installed Klipper root. The native patch uses `a/klippy/...` / `b/klippy/...` paths for `-p1` application there. Its leading version comments are metadata; [GNU patch supports leading headers](https://www.gnu.org/software/diffutils/manual/html_node/Merging-with-patch.html), and the offline staging tool accepts comment-only preambles. The template root mirrors the firmware-config template location. Paxx's [firmware builder](https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware/blob/develop/scripts/create_firmware.sh) applies patch stages without fuzz and copies root payloads. Its [Makefile](https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware/blob/develop/Makefile) treats hyphens as profile/mod separators, hence the mod name `tooloffsets`.

This repository does not include or modify Paxx's firmware builder. The original 1.4 overlay has not been built as a full image. A separately staged seven-file PR760 candidate under `overlays/mods/cheeky_b52/` completed a full image build on 2026-10-17, with exact source guards and five checks against the unpacked image. Its payload uses the PR760 native patch and shared CFG, plus build-time guards and mod documentation. The existing Docker development-image tag was preserved by using a separate tag with the same pinned Dockerfile and Make targets. See [Validation](validation.md) for the commit and result. The operator subsequently flashed this exact image; 20 read-only boot checks verified its native sources, ROM macro template, capability, unchanged calibration and offsets, normal process and idle/off state. A post-flash T2 cycle passed 16 checks and its normal restart passed nine checks after native automatic tool activation settled. Post-flash default validation passed all 16 checks, with six pairs in tolerance and unchanged calibration. Planned printer testing is complete. No upstream submission is implied.

## Publication audit

The reviewed PR760 username mod is published on the author's fork in [usermod/independent-tool-calibration](https://github.com/cheekyb52/SnapmakerU1-Extended-Firmware/tree/usermod/independent-tool-calibration/overlays/mods/cheeky_b52). A separate [build branch](https://github.com/cheekyb52/SnapmakerU1-Extended-Firmware/tree/build/independent-tool-calibration) runs the personal workflow. It builds only `extended-cheeky_b52`, unpacks the generated image and verifies the same five payload hashes, then publishes an experimental prerelease with checksums, source identity, instructions and license files. Its release job is restricted to that personal fork and runs only after the build job succeeds.

The standalone project's original 1.4 overlay is retained for reproducibility. It is not combined with the PR760 native patch. No upstream PR has been submitted; wider community testing is being collected first.

Run `tools/audit_project.py` from the project root. It scans the publishable tree for captured media, private paths/addresses, private-key material, common credentials/tokens, raw dumps/logs, and unwanted project artifacts. Findings identify paths and lines without printing sensitive values. `.gitignore` alone is not the audit: files present in ignored locations are also findings.

`privacy-report.json` records the final automated scan, and `package-manifest.json` records relative file paths, sizes, and SHA-256 hashes. The inventory excludes its own file. Review both and the package's file list before publishing. The audit is a bounded set of checks, not a guarantee against every possible secret format.

Keep private backups and device evidence outside this tree. Required upstream copyright notices are preserved; the upstream authors' public copyright contact is attribution, not the owner's private information. Only this calibration project belongs in the owner's chosen repository.

## Personal fork integration

Keep usermod shell scripts in Unix LF format with executable Git modes. The personal build checks this before compiling; Windows CRLF shebangs cannot run in the Linux firmware builder. When staging text with Python on Windows, write UTF-8 bytes or explicitly use `newline='\n'`.

The fork includes upstream develop commit `b73cfc70e343a0f4bf5b178481818ef1175d3918`. The net upstream changes add the separate multiACE mod and related docs/CI; the calibration sources and normal extended build inputs are unchanged. The calibration build remains `extended-cheeky_b52`. The original source-profile hash guards stay enabled.

The fork's `main` and `develop` branches carry one personal Cloudflare workflow guard: hosting is skipped unless the repository variable `ENABLE_CLOUDFLARE_DEPLOY` is exactly `true`. Enabling it also requires the owner's own Cloudflare credentials and project configuration. The calibration build/release workflow is separate. No hosting credentials were added.

[Six Linux migration checks](https://github.com/cheekyb52/SnapmakerU1-Extended-Firmware/actions/runs/39185718692) exercise the actual usermod guard and stock S49 config startup script with temporary fixtures. They cover hash rejection, idempotent migration registration, packaged-old upgrade, customized-CFG preservation, current-CFG preservation and unrelated-file preservation.
