# CK3-Minecraft

Use the existing checkout; cloud tasks are already isolated. Do not create worktrees unless requested.

Read README.md and MODLOG.md first. Design tables in `design/sheets/` are the source of truth. Change a table before its generated code. Run `python tools/design.py preflight` before every build, then `python tools/design.py generate`. Do not edit generated files directly. `python tools/design.py check` detects drift.

Keep game installations, saves, extracted content, account credentials and the Melty token outside this repository. Use only the player's own game copies. No paid asset generation without permission. Protect original saves; use a disposable campaign and a separate Minecraft instance for playtests.

The bridge tests are not a live CK3 test. Do not describe queued return commands, compiled Minecraft code or synthetic log tests as verified in-game integration. Read `docs/PLAYTEST.md` for the required evidence. Multiplayer is planned, not implemented. Do not submit or publish a release before both games, return acknowledgement, installation and real screenshots have been tested.
