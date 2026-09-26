# Evidence and limits

Development used one original H4n with bootloader 1.01 and a Mac. No broad hardware-revision or host-OS compatibility claim is made.

| Test | 48 kHz | 44.1 kHz |
| --- | --- | --- |
| Captured duration | 60 seconds | 60 seconds |
| Four-channel frames | 2,880,000 | 2,646,000 |
| Simultaneous stereo playback | 28 seconds | 28 seconds |
| Left 997 Hz / right 1301 Hz / both returned on correct combo channels | Pass | Pass |
| Clipped samples | 0 | 0 |
| Callback timestamp discontinuities | 0 | 0 |
| Device route lost | No | No |
| Adjacent identical four-channel frames | 0 | 0 |

Numerical results are in [test-results.json](test-results.json). No personal recordings are distributed. The waveform sequence used four seconds of left tone, four seconds of right tone, then twelve seconds of both, with intervening gaps. Input 3 carried the left output loop and input 4 the right. The built-in microphones remained active. All playback was explicitly routed to the H4n output.

The user confirmed responsive screen and controls after the 48 kHz test. The 44.1 kHz test succeeded after correcting both macOS device rates from their retained 48 kHz setting. Previous feature trials confirmed auto-mute, playback restoration, persistent settings, LEDs, meter layout and independent levels.

An earlier unsmoothed 40-second capture had 94 adjacent identical four-channel frames. Their absence in the later captures is consistent with the new correction scheme, but it is not a matched A/B proof or an exact count of correction events.

## Software checks

- Exact input/output hashes, container checksum, size and section layout.
- Synthetic tests for patch reconstruction, wrong inputs, malformed runs, corruption and overwrite refusal.
- Bounded execution of actual smoothing opcodes: 576 producer cases, one disabled-producer case and 16 worker-status cases. Fixtures cover extrema, low-bit values, random blocks, channel ramps, impulses and ring wrap.
- Final version-screen rendering was checked in a bounded display model. The final two text changes were packaged after audio testing; audio/control instructions remain byte-identical.

GitHub CI can run the synthetic tests without firmware. The opcode model requires a locally reconstructed image. Neither is a substitute for hardware testing.

## Not established

No claim of ADC effective resolution, bit-perfect analog loopback, absence of every sample-level loss/concealment event, inaudible correction, high-frequency transparency, long-run endurance, or compatibility with other recorder models. Callback timestamps cannot detect every USB or device-side concealment event. The maintainer confirmed installation of the final SYSTEM.BIN, normal boot, and the DUPLEX 44.1/48k version screen on 27 September 2026.
