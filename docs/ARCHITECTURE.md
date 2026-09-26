# Architecture and reproducibility

## What this repository builds

The official 1.90 image is 1,835,264 bytes. It contains 51 load sections; code addresses are bytes, while C55 data addresses are 16-bit words. Confusing these address units is a common source of incorrect patches. The application entry is 0x03EF88; the load-table terminator is at file offset 0xF2BEE. The checksum at file 0xFC is the big-endian sum of bytes after 0x100, modulo 2^32.

The patch keeps the container size and section layout. `patches/1.9C.json` contains sparse XOR runs over an exact SHA256-identified original. Each run specifies a file offset and changed-byte delta. Two targets reconstruct the installer and the SD-loaded container, each with a required output hash. Their application payloads are identical; their headers differ.

`tools/make_patch.py` deterministically generates the manifest from three local inputs: original, installer and SD image. No prior experimental folders are needed to apply the published patch. This is a reproducible binary patch, not a recovered source tree or a compiler for the whole firmware. Human-readable patch contents are the source artifact for this release; new functionality still requires reverse engineering and hardware validation.

## USB capture and playback

Four-channel capture preserves full-width samples from the microphone pair and combo-input pair. The USB capture format carries 24 significant bits in 32-bit slots, while playback remains stereo 16-bit. Two pairs of staging buffers feed rings with 6000 physical words per pair. Logical write-index increments are two units per four-channel frame; physical ring offsets double that index.

Aligned 32-bit sample fetches are essential to the tested packet path. Earlier experiments using separate 16-bit fetches caused USB failures. They must not be substituted merely because they appear equivalent in an arithmetic model.

macOS exposes capture and playback as separate devices. The names distinguish them; attempts to present them as one macOS device were not successful in the tested configuration.

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
