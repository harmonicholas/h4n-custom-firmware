# Maintainer publishing checklist

This folder is the public project. Publish **this folder only**, not the parent research workspace. No remote repository has been created and nothing has been uploaded by this preparation step.

Suggested repository name: `h4n-custom-firmware`.
Suggested description: `Community patches for the original Zoom H4n: four-channel USB24 capture, auto-mute, meters and independent levels.`
Suggested topics: `zoom-h4n`, `firmware`, `audio`, `usb-audio`, `reverse-engineering`, `c55x`.

1. Review the MIT license/NOTICE, feature wording and known limitations. Final installation, normal boot and the version screen have been confirmed by the maintainer.
2. Run tests and `python3 tools/audit_public.py`; reconstruct both variants locally and compare their expected hashes. Keep resulting binaries in ignored `build/`.
3. Create an empty GitHub repository under the chosen account. Select no automatically generated README or license because they are already present here.
4. From this directory, initialize Git if needed (`git init -b main`), stage this folder, inspect `git diff --cached --stat`, and commit with your configured identity. Add the real remote URL, then push `main`.
5. Enable Issues and, optionally, Discussions/private vulnerability reporting. Let CI finish before publishing a release.
6. Tag the reviewed commit, for example `v1.9C`. Use CHANGELOG.md as the release description, including tested rates and limitations. GitHub's source archives contain the patch/tools; do not attach SYSTEM.BIN, BOOT_DATA.BIN, recordings, dumps or research-session archives.

The bundled files are MIT project contributions, with proprietary upstream material excluded. Generated firmware remains a combination with upstream material; do not label the full firmware MIT.

The default CI runs synthetic tests and a public-content audit. It does not download manufacturer firmware or flash hardware. Hardware testing remains a separate, documented maintainer activity.
