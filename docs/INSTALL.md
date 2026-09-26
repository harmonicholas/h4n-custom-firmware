# Installation and recovery

This release is for the **original Zoom H4n**, developed with firmware 1.90 and bootloader 1.01. Other hardware revisions have not been established as compatible. Do not use it on an H4n Pro or H4essential.

The project supplies patches and tools, not firmware downloads. Reconstruct images from your own exact official 1.90 file as described in the README. Preserve that original image separately. Back up recordings before working with the card; the project does not format cards automatically.

## SD-loaded trial

1. Copy the generated `BOOT_DATA.BIN` to the root of the H4n's SD card and safely eject it.
2. With the H4n off, insert the card. Hold **MENU + REC** while powering on to use the observed SD application loader.
3. Open SYSTEM → VERSION. Expect **CUSTOM FIRMWARE**, version 1.9C and **DUPLEX 44.1/48k**.
4. Test menus, SD recording/playback, auto-mute and USB audio before considering installation. For USB loopback testing, connect the headphone/line output to the combo inputs, turn **MONITOR OFF**, start with a low output volume and check levels. Avoid a monitor feedback loop.
5. Power off and start normally without the shortcut to return to the installed application. Remove the trial file when it is no longer needed.

The SD loader was observed on bootloader 1.01. This does not establish compatibility with every bootloader. A trial may still hang or behave incorrectly; it is not a recovery guarantee.

## Flash installation

1. Use the generated **SYSTEM.BIN**, not BOOT_DATA.BIN. Put it in the SD card's root and safely eject the card.
2. Use reliable power and insert the card with the recorder off.
3. Hold **PLAY/PAUSE** while powering on and follow the firmware-update prompts.
4. Do not disconnect power or remove the card during the update.
5. After completion, start normally. Confirm CUSTOM FIRMWARE / DUPLEX 44.1/48k and test the normal recorder functions.

MENU + REC loads the SD trial; it does not install SYSTEM.BIN. Leaving an older BOOT_DATA.BIN on the card can make a later SD boot look like the installed release, so keep track of which image you are using.

## Returning to the official firmware

For an SD-only trial, a normal restart returns to the previously installed application. To replace an installed custom application, use your retained official SYSTEM.BIN through the normal updater if the updater remains accessible. The startup label 1.9C alone does not identify a particular custom build; use the output SHA256 and version-screen text.

The project does not guarantee recovery after an interrupted update or bootloader damage. A previous bootloader export is evidence for the development device, not a universal repair image. No bootloader patch or dump is distributed here.

## macOS sample rates

Select H4 4-IN/24 for capture and H4 2-OUT/16 for playback. Verify both are set to the same rate in Audio MIDI Setup. During development, selecting 44.1 kHz on the recorder left macOS at 48 kHz until both Core Audio devices were explicitly changed. A rate mismatch should be resolved before drawing conclusions about firmware failure.
