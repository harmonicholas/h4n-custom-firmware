# Contributing

Start with the architecture and testing notes. Keep changes small enough to compare with the known image and explain which behavior they change.

Run `python3 -m unittest discover -s tests -v` and `python3 tools/audit_public.py`. For firmware changes, record the source/target hashes, changed ranges, section/checksum checks, register/stack assumptions, and bounded-model results. Test through the SD loader before proposing installation. Clearly distinguish static checks from real hardware evidence.

A hardware report should name the recorder model, bootloader, firmware hash, sample rate, host OS/DAW, routing and precise reproduction steps. Summarize what worked and what remains unknown. Do not post proprietary firmware, dumps, private recordings or local session logs.

Patch manifests are the reproducible release artifact. Do not imply that generating a new delta validates its behavior. The entire firmware is not reconstructed source, and the current emulator models only the relevant instruction subset.

Contributions of original code and documentation are accepted under this project's MIT license. Third-party material retains its own rights and must be clearly identified. AI-assisted contributions should describe their verification, just like any other contribution.
