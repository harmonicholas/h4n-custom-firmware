# Architecture and reproducibility

## What this repository builds

The official 1.90 image is 1,835,264 bytes. It contains 51 load sections; code addresses are bytes, while C55 data addresses are 16-bit words. Confusing these address units is a common source of incorrect patches. The application entry is 0x03EF88; the load-table terminator is at file offset 0xF2BEE. The checksum at file 0xFC is the big-endian sum of bytes after 0x100, modulo 2^32.

The patch keeps the container size and section layout. `patches/1.9C.json` contains sparse XOR runs over an exact SHA256-identified original. Each run specifies a file offset and changed-byte delta. Two targets reconstruct the installer and the SD-loaded container, each with a required output hash. Their application payloads are identical; their headers differ.

`tools/make_patch.py` deterministically generates the manifest from three local inputs: original, installer and SD image. No prior experimental folders are needed to apply the published patch. This is a reproducible binary patch, not a recovered source tree or a compiler for the whole firmware. Human-readable patch contents are the source artifact for this release; new functionality still requires reverse engineering and hardware validation.

## USB capture and playback

Four-channel capture preserves full-width samples from the microphone pair and combo-input pair. The USB capture format carries 24 significant bits in 32-bit slots, while playback remains stereo 16-bit. Two pairs of staging buffers feed rings with 6000 physical words per pair. Logical write-index increments are two units per four-channel frame; physical ring offsets double that index.

Aligned 32-bit sample fetches are essential to the tested packet path. Earlier experiments using separate 16-bit fetches caused USB failures. They must not be substituted merely because they appear equivalent in an arithmetic model.

macOS exposes capture and playback as separate devices. The names distinguish them; attempts to present them as one macOS device were not successful in the tested configuration.

## USB rate advertisement

The configuration descriptor is 174 bytes. Each stream has one discrete rate instead of two; its format, endpoints and USB device identity are unchanged. A hook at code 0xD79749 reads the existing selection at data word 0x6CB737 (0 = 44100, 1 = 48000). It writes the low/middle rate bytes in both format descriptors at words 0x6D9A07/08 and 0x6D9A3B/3C, replays the displaced AC0 setup, and resumes at 0xD7974D. The rate updates when the host requests the configuration descriptor, not as an in-session sample-rate switch.

The helper occupies retired padding, the shortened VERSION heading tail and compacted descriptor tail. Two formerly executed padding regions have explicit bypass branches. Addresses are recorded in `patches/usb-rate-labels.json`. Changes to those areas must preserve the rate helper, just as audio helper allocations must be preserved.

A same-identity, fixed-44.1 descriptor control made macOS select 44.1 automatically. The dynamic version then passed 48 → 44.1 → 48 reconnects. This supports making the descriptor unambiguous; it does not establish a macOS defect or prove compatibility with every host.

`tools/verify_usb_rate.py` executes the actual hook bytes for 48 alternating selection cases, checks the exact four-word write set and return state, and checks descriptor contents. Its 432 request-length checks model truncation; they do not execute the entire USB control-transfer handler. Audio producer/serializer and smoothing instructions are unchanged from the previous release.

## Clock correction

The producer begins at code 0x03D96D and normally copies 64 frames exactly. The existing occupancy controller requests a positive or negative correction through data word 0x7BD8. A positive correction produces 65 frames; a negative correction produces 63. The packet controller, ring allocation and aligned serializer remain unchanged.

Correction blocks use signed 24-bit linear interpolation:

```text
interpolate(a, b, r) = a + floor((b - a) * r / 32)
```

All four channels share the same phase progression. Positive correction first emits original frame 0, then transforms staging frames 0..31 in ascending order with r=31-k before copying 64 frames. Negative correction processes j=31..0 backward, placing the interpolation with r=j in destination j+1, then copies frames 1..63. The traversal direction avoids overwriting neighbors before they are read.

Five shift/add iterations implement the coefficient. The worker preserves T0, AC0, ST1 and T2, enables signed extension temporarily and restores status. Native CALL uses separate data and system stacks; the worker pushes T0 before the doubleword AC0 save to maintain alignment. Ordinary blocks keep their raw 32 sample values; corrected values are aligned back into the upper 24 bits. Floor quantization error is less than one significant 24-bit LSB.

Linear interpolation attenuates high frequencies during a correction. The design reduces abrupt whole-frame slips; it is not a transparent sample-rate converter or proof of inaudible correction.

Helpers occupy previously unused padding behind returns/tail branches. A branch at 0x03C6FE skips helper bytes after the serializer's hardware repeat has completed at 0x03C6F8. The helper addresses are in `patches/clock-labels.json`. Space is tightly allocated: new code must account for existing UI and audio helpers.

## UI and monitoring

The custom interface adds persistent auto-mute, earlier output muting at REC preparation, independent input levels, four-channel meters and rate/depth information. Combo level-control destinations require a physical-channel correction; changing USB channel ordering or button labels instead would be incorrect. The REC shortcut remains fixed to 48 kHz from the initial USB selection screen.

## References

- [TI C55x CPU guide, SPRU371](https://www.ti.com/lit/ug/spru371f/spru371f.pdf)
- [TI C55x instruction-set guide, SPRU374](https://www.ti.com/lit/ug/spru374g/spru374g.pdf)
- [Zoom H4n support](https://zoomcorp.com/en/us/handheld-recorders/handheld-recorders/h4n/h4n-support/)

Manufacturer documents and firmware are linked, not bundled. Historical analysis used radare2's tms320/c55x decoder; individual instruction semantics and relative branch targets required manual checking.
