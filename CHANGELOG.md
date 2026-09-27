# Changelog

## 1.9C — dynamic-usb-rate revision (2026-09-27)

Both USB streams now advertise only the rate selected on the H4n. Previously, selecting 44.1 kHz could leave macOS at 48 kHz after reconnecting. Automatic 48 → 44.1 → 48 kHz enumeration passed without host rate changes. The numerical version remains 1.9C; the VERSION heading is RATE.

Short duplex trials passed the tone/routing, clipping, callback continuity and connection checks at both rates. Each of two 44.1 kHz trials contained one repeated four-channel frame; a fresh test of the previous installed build also contained one. The cause is unresolved and no bit-perfect claim is made. Installation and normal startup were confirmed on the development recorder.

The package includes updated exact-image patches, a bounded USB descriptor-hook verifier and revised installation/test notes.

## 1.9C — initial public package

Original H4n firmware 1.90 with persistent early auto-mute, REC USB48 shortcut, four 24-bit USB inputs and stereo 16-bit playback, named USB devices, input LEDs, four-channel meters, rate/depth badge, independent input levels, smoother clock correction, and custom version information.

Short duplex hardware trials passed at 44.1 and 48 kHz. The initial public package includes a patcher, exact binary deltas, bounded clock model, synthetic tests and sanitized test summaries. It does not contain Zoom firmware or a bootloader image. The maintainer subsequently confirmed final installation, normal boot and the updated version screen.
