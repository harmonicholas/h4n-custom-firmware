# Evidence and limits

Development used one original H4n with bootloader 1.01 and a Mac. No broad hardware-revision or host-OS compatibility claim is made.

## Current dynamic-usb-rate revision

Automatic 48 → 44.1 → 48 kHz reconnects passed: live descriptors, available rates and selected Core Audio rates matched the H4n selection for both streams. No host rate-setting commands were used.

| Test | 48 kHz | 44.1 kHz (two trials) | Previous-build 44.1 kHz control |
| --- | --- | --- | --- |
| Capture duration | 60 seconds | 60 seconds each | 60 seconds |
| Simultaneous stereo playback | 28 seconds | 28 seconds each | 28 seconds |
| Expected left/right/both loopback tone sequence | Pass | Pass | Pass |
| Clipped samples | 0 | 0 | 0 |
| Callback timestamp gaps | 0 | 0 | 0 |
| Device route lost | No | No | No |
| Adjacent identical four-channel frames | 0 | 1 each | 1 |

The repeated frames occurred at indices 425077 and 1071182 in the two current 44.1 kHz trials, and 849926 in the previous installed-build control. The cause is unresolved. This observation is not unique to the descriptor change, and no regression was demonstrated; it is not proof of bit-perfect streaming.

Numerical results, including earlier smoothing trials, are in [test-results.json](test-results.json). No recordings are distributed. Tests captured four 24-bit channels with the H4n headphone output looped to its combo inputs, MONITOR OFF. Left 997 Hz and right 1301 Hz tones returned on the expected channels; all playback was explicitly routed to the H4n output. Screen/popup responsiveness was confirmed during the test sequence.

The maintainer confirmed installation of the current SYSTEM.BIN and normal startup with the RATE heading and version 1.9C on 27 September 2026. The installed payload is identical to the tested SD trial; only container headers differ.

## Earlier feature validation

Previous hardware trials confirmed auto-mute, restored playback, persistent settings, LEDs, meter layout and independent input levels. Initial smoothing trials at each rate had zero adjacent identical four-channel frames. An earlier unsmoothed capture had 94; these are not matched A/B measurements or exact counts of clock corrections. The more recent repeated-frame observations above qualify the earlier results.

The retained-rate behavior was reproduced with official 1.90 firmware. A fixed-44.1 descriptor control then made the same USB identity enumerate at 44.1 automatically. No Apple bug report was submitted; an Apple defect was not established.

## Software checks

- Exact input/output hashes, container checksum, size and section layout.
- Synthetic patch tests for reconstruction, wrong inputs, malformed runs, corruption and overwrite refusal.
- Actual smoothing opcodes in a bounded model: 576 producer cases, one disabled-producer case and 16 worker-status cases.
- Actual USB rate hook opcodes: 48 selection cases, exact four-word writes, original return/register setup and descriptor validation. Another 432 checks model request-length truncation, not the full control-transfer handler.
- Repository content audit excludes full firmware, bootloader dumps, recordings and personal paths.

CI runs synthetic tests and the content audit without firmware. Opcode models require locally reconstructed images. Neither is a substitute for hardware testing.

## Not established

No claim of ADC effective resolution, bit-perfect analog loopback, absence of every sample-level loss/concealment event, inaudible correction, high-frequency transparency, long-run endurance, or compatibility with other recorder models. Callback timestamps cannot detect every USB or device-side concealment event.
