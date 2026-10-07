# Melty — lokale Veröffentlichungsnotizen, kein eingereichter Release

Abgefragt am 7. Oktober 2026: `list_my_mods` meldet keine bestehenden Projekte. `search_games` bestätigt `crusader-kings-3` und `minecraft-java`. Die Suche nach beiden Spielen hat keine CK3-Minecraft-Kombination geliefert. `game_info` liefert keinen automatisch installierten CK3-Loader. Die genannten Minecraft-Loader haben ebenfalls `autoInstall: false`; der geprüfte SkyCraft-Release erreicht den Ein-Klick-Start stattdessen mit einer portablen Prism-Instanz und einem ersten Minecraft-Setup. `mashup_info skycraft` bestätigt dieses Rezept und seinen Ein-Klick-Check. Seine konkreten Skyrim-Komponenten oder Spielerzahl werden nicht übernommen.

Geplante Spielrollen: CK3 `primary`, Minecraft `companion`; `recipe.together` erforderlich, weil beide gleichzeitig laufen. Spielordner müssen aus Meltys Launch-Übergabe stammen, keine im Code festgeschriebenen Benutzerpfade. Vanilla-Spieldateien, Saves und Authentifizierungsdaten gehören nicht ins Paket. Beide Katalogeinträge sind `tips-only`.

Kein `melty.json` ist als vermeintlich validiertes Rezept hinterlegt. Für eine tatsächliche Veröffentlichung fehlen noch:

- Live getestete CK3-Kommunikation, Rückgabe und automatischer Wechsel ohne manuelle Installation/Konsolenschritte.
- Mitgelieferte tragbare Laufzeiten und Prism-Instanz einschließlich Quellen-/Lizenzhinweisen erlaubter Fremdkomponenten; Minecraft-Anmeldung durch den Spieler, keine übernommenen Kontodaten.
- Abgestimmter Titel, Tagline, Beschreibung, Credits, Inhaltslizenz und Remix-Erlaubnis.
- Echtes Gameplay-Bild dieses Builds mit tatsächlicher CK3-Verbindung.
- `inspect_package`, `validate_recipe` und positiver `one_click_check` auf dem tatsächlichen Paket, anschließend ein echter Melty-Installationstest.
- Dein ausdrückliches Veröffentlichungs-Ja; erst danach Melty `publish` und bestätigter Serverstatus.

Der aktuelle Release darf keine Multiplayer-Funktion behaupten. Die optionale Multiplayer-Erweiterung wird erst mit getesteter Host-/Join-Funktion und passendem Melty-Rezept als Multiplayer veröffentlicht. Kein Clientlimit wird erfunden.
