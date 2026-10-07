# Cloud-Entwicklung

Diese Cloud enthält keine CK3-Installation und hat keinen Zugriff auf den Windows-Spiele-PC. Der gespeicherte Umgebungsentwurf enthält das folgende geprüfte Setup und wiederverwendbare Startanweisungen. Cloud-Umgebung und Melty-Veröffentlichung sind getrennte Vorgänge.

## Installationsskript

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /workspace/CK3-Minecraft
python3 tools/design.py preflight
python3 tools/design.py check
python3 -m unittest discover -s tests -v
python3 tools/gradle.py --no-daemon build

```

## Startanweisungen

# CK3-Minecraft development environment

Use the existing checkout at /workspace/CK3-Minecraft. Cloud tasks are already isolated; do not create a Git worktree unless explicitly requested. Read AGENTS.md, README.md, MODLOG.md and artifacts/validation.json if present. This is a development prototype, not a verified live CK3 mashup or a published Melty release.

The retained .gradle/tools directory contains checksummed Gradle 8.10.2 and Temurin JDK 21. tools/gradle.py activates them and uses the cloud's existing proxy and system Java truststore without disabling TLS verification. No credentials are required for compilation or the bridge tests. From /workspace/CK3-Minecraft run python3 tools/design.py check, python3 -m unittest discover -s tests -v, and python3 tools/gradle.py --no-daemon build. Generated source is checked in the working folder: do not regenerate it during installation; change tables first only when doing a coding task.

Live processes must restart. To start the local bridge for an actual Windows CK3 test, follow docs/PLAYTEST.md with that player's actual debug.log and a private state directory dedicated to one disposable campaign. Command from the repository: PYTHONPATH=bridge python3 -m ckcraft --ck3-log <actual-debug.log> --state <private-state-directory> --campaign <unique-campaign-label>. It writes private bridge.json in that state directory; never print its token. Set CKCRAFT_BRIDGE_CONFIG to that file for the Minecraft process. Readiness: authenticated GET http://127.0.0.1:<generated-port>/v1/health must return protocol 1 and status running; /v1/session must initially be empty or identify an existing pending event. A running bridge or health response is not evidence of live gameplay. Return results remain pending until the matching actual CK3 ACK is read.

No CK3 installation or remote Windows access exists in this cloud. For Minecraft-only testing, use an explicitly named synthetic log fixture in an ignored private runtime folder, a fresh private campaign state directory and a disposable singleplayer world. Do not present synthetic requests or ACKs as a real CK3 roundtrip. On a desktop, launch the development client with python3 tools/gradle.py --no-daemon runClient after exporting its CKCRAFT_BRIDGE_CONFIG path. Never run Gradle build and runClient concurrently. Dedicated servers and multiplayer are not implemented.

The optional cloud graphical test tools were extracted from Debian's signature-verified repository into /workspace/.tools/ckcraft-x11; Xvfb is /workspace/.tools/ckcraft-x11/usr/bin/Xvfb. Start a free display with Xvfb :91 -screen 0 1280x720x24 -nolisten tcp after checking that display is unused and preparing /tmp/.X11-unix if absent. Use DISPLAY=:91 and LIBGL_ALWAYS_SOFTWARE=true only for the isolated development client. The toolkit checkout /tmp/ck3-universal-modder has bin/um for game recon; if absent, clone its official repository again outside the project. Do not drive a player's Windows input without explicit authorization, and use only their own game copies. Preserve their saves and original files.

Before distribution, require actual CK3 version/files, automated return and process switching, portable Prism and runtime packaging, a verified one-click recipe and installation, agreed listing/credits/license/remix choices and genuine live gameplay media. Do not upload the development archive or publish anything until those checks pass and the user authorizes publication.


