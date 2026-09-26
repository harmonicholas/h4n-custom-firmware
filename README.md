# H4n Custom Firmware

More useful USB audio and monitoring controls for the **original Zoom H4n**, built as a patch to firmware 1.90.

This project grew out of a working recorder, patient testing, and a question: what else can this hardware do? The result keeps the familiar recorder workflow while adding four-channel USB capture, automatic monitor muting, and controls that make the interface easier to use.

## Features

- **Four USB inputs at 24-bit depth**, with simultaneous stereo 16-bit playback at 44.1 or 48 kHz. Channels 1/2 are the built-in left/right microphones; channels 3/4 are the two combo inputs.
- **AUTO MUTE** in REC settings: silences the headphone/line output during recording standby and recording, with a persistent ON/OFF choice. Turn it off to monitor through headphones.
- **REC shortcut** from the initial USB selection screen to 48 kHz audio-interface mode.
- **Independent USB input levels**, four-channel meters, a sample-rate/depth badge, and all three input LEDs illuminated.
- **Smoother USB clock correction**, spreading occasional sample insertions/removals across a short interpolation window.
- A **CUSTOM FIRMWARE** version screen, with `DUPLEX 44.1/48k` and a summary of the custom functions. Startup version remains `1.9C`.

## Compatibility and status

| Item | Status |
| --- | --- |
| Original H4n, firmware 1.90, bootloader 1.01 | Development hardware |
| H4n Pro / H4essential / other models | Unsupported; do not install |
| Four-input capture + stereo output,48 kHz | 60-second capture including 28-second duplex playback passed |
| Same test at 44.1 kHz | Passed |
| Screen and controls during 48 kHz duplex | User confirmed responsive |
| Windows / Linux hosts | Not validated by this project |
| Final release packaging | Exact images reconstructed; maintainer confirmed installation, normal boot and final version screen |

USB24 refers to 24 significant sample bits carried in 32-bit USB slots. It is not a claim of 24 effective ADC bits. These are short functional tests, not a guarantee of endurance or perceptual transparency. See [test evidence](docs/TESTING.md).

On macOS, capture and playback appear as separate devices: **H4 4-IN/24** and **H4 2-OUT/16**. Select them separately in your DAW, or configure an Aggregate Device if your application requires one. The firmware does not merge them into a single macOS device. macOS can retain the previous rate: set both devices to the same 44.1 or 48 kHz rate in Audio MIDI Setup.

## Build your own image

Python 3.10 or newer is sufficient; no pip packages, compiler or radare2 are required to apply the patch.

1. Obtain the original **H4n System Version 1.90** from [Zoom's H4n support page](https://zoomcorp.com/en/us/handheld-recorders/handheld-recorders/h4n/h4n-support/). Extract its `SYSTEM.BIN`. Do not use H4n Pro firmware.
2. Keep that original file outside the repository, or in the ignored `private/` directory.
3. Generate an SD trial first:

```sh
python3 tools/patch_firmware.py /path/to/original/SYSTEM.BIN --variant sd --output build/BOOT_DATA.BIN
python3 tools/verify_clock.py build/BOOT_DATA.BIN
```

The tool requires this exact original image:

```text
Size:   1835264 bytes
SHA256: f0999c20d92441e61763d13314aaa1a8f181cdd62b10b743adec0ec23fc2ab66
```

It refuses a wrong input, verifies the output checksum and SHA256, and refuses to overwrite existing files. A same-name image from another version will not work. The supplied patch is not a from-source build of Zoom's firmware.

For the installable image:

```sh
python3 tools/patch_firmware.py /path/to/original/SYSTEM.BIN --variant system --output build/SYSTEM.BIN
```

**Read [installation and recovery](docs/INSTALL.md) before copying either file to a card.** Firmware changes can leave a device unable to start. An SD trial avoids installing the modified application in flash, but is not a guarantee of safe behavior. Back up your recordings and keep the official firmware available.

## Verification and development

```sh
python3 -m unittest discover -s tests -v
python3 tools/audit_public.py
```

CI runs synthetic patch tests and a repository-content audit without downloading proprietary firmware. `verify_clock.py` additionally executes the actual released clock-correction opcodes in a bounded model when a locally reconstructed image is supplied. It is not a full DSP or peripheral emulator.

- [Architecture and patch format](docs/ARCHITECTURE.md)
- [Hardware test evidence and limits](docs/TESTING.md)
- [Contributing](CONTRIBUTING.md)
- [Release notes](CHANGELOG.md)
- [Publishing checklist](docs/PUBLISHING.md)

## License and acknowledgments

Original project contributions are released under the [MIT license](LICENSE). Zoom's firmware is not included and is not relicensed; see [NOTICE](NOTICE.md). This is an independent project with no Zoom endorsement.

Built through hands-on testing and AI-assisted reverse engineering with OpenAI Codex. Contributions with clear, reproducible evidence are welcome.
