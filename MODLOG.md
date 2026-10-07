# MODLOG

## Anforderungen

CK3 als Hauptspiel und Minecraft Java parallel. Duelle, Belagerungen, Schlachten, einzelne Ereignisse und Reisen. Einzelspieler zuerst, später optional Multiplayer mit getrennten Reichen. Automatische situationsbedingte Übergänge, freies Wechseln zusätzlich. Plan am 7. Oktober 2026 zum Bauen freigegeben. Veröffentlichung noch nicht freigegeben.

## Quellen und Route

- universal-modder aus `https://github.com/rehan-remade/universal-modder`, lokaler Toolkit-Checkout `/tmp/ck3-universal-modder`; `mod-any-game` und `mashup-mods` gelesen, `um kb search` und `um scan --list` ausgeführt. Keine installierten Spiele in der Cloud gefunden. Keine bezahlten Assetdienste benutzt.
- Öffentliche CK3-Engine-Referenz: OldEnt/crusader-kings-3-triggers-modifiers-effects-event-scopes-targets-on-actions-code-revisions-list, Commit `e2d9b7b72168cbe2eaa56367f165b689666b9a09`, Dateien `1.10.2_effects.log`, `1.10.2_on_actions.log`, `1.10.2_event_targets.log`, `1.10.2_data_types_script.txt` und `1.10.2_data_types_uncategorized.txt`. Nur außerhalb dieses Projekts gelesen, keine Retail-Dateien kopiert. Diese Quelle belegt Syntax, nicht aktuelle Live-Kompatibilität.
- Geprüfte Befehle/Scopes: `debug_log` mit lokalisierbarem Text; `on_travel_plan_start` (character scope); `random_courtier_or_guest`; `current_travel_plan`; `pause_travel_plan` / `resume_travel_plan`; `set_variable` / `change_variable`; `add_character_flag` / `remove_character_flag`; `Character.GetID`, `GetProwess`, `GetCurrentLocation`; `SCOPE.sC`, `Scope.Var` und `Scope.GetValue`.
- Leichteste Route: nativer CK3-Skript-Mod + Fabric-Minecraft-Mod + lokale Python-Verbindung. Es ist keine Netzwerk-API im CK3-Skriptweg belegt. Die Rückgabe erfolgt aktuell über einen geschützten nativen Entwicklungs-Konsolenbefehl und gilt erst nach ACK als durchgeführt. Keine erfundenen Hooks oder Binäroffsets, keine Spielpatches.
- Minecraft 1.21.1, Yarn 1.21.1+build.3, Fabric Loader 0.16.10, Fabric API 0.116.7+1.21.1, Loom 1.8.13, Gradle 8.10.2, JDK 21. Windows als Ziel vom Benutzer bestätigt, genaue CK3-Version noch unbekannt.

## Umsetzung und Diagnose

- JSON-Tabellen generieren Java-Datensätze, CK3-Ereignisse, Lokalisierungen, additive Hooks und Entscheidungen. Preflight prüft alle aktiven Tabellenzellen und Bezüge; Live-Prüfungen sind separat zu belegen.
- Verbindung: nur Loopback, zufälliges lokales Token, eingeschränkte Körpergrößen, Origins/DNS-Rebinding abgewiesen, dauerhafte SQLite-Zustände, Besitzprüfung, Einzelsitzung und strenge Datenprüfung. Phase `RETURN_PENDING` ist ausdrücklich kein abgeschlossenes Spielereignis.
- Minecraft: eigene Dimension, Weg, gesperrter Gegner bis zum Wegende, aus wirklichem CK3-Prowess berechnete Kampfwerte, Inventar-/Positionswiederherstellung, Abbruch/Timeout/Disconnect. Kein Multiplayer.
- Erster Gradle-Start scheiterte an einem nicht beschreibbaren Standardcache. Caches ins ignorierte `.gradle/` verlegt. Java berücksichtigt den bestehenden Cloud-Proxy.
- Cloud hatte nur JRE 21. Offizielles Temurin JDK 21.0.12+8 mit offizieller SHA-256-Sidecar-Prüfung nachinstalliert. Gradle 8.10.2 ebenfalls mit festem offiziellen SHA-256 geprüft.
- Neues JDK kannte den verwalteten Cloud-Proxy-CA nicht. Vorhandenen System-Truststore `/etc/ssl/certs/java/cacerts` verwendet; TLS-Prüfung bleibt eingeschaltet.
- Python-Protokoll-/HTTP-/Zustands-/Generatortests erfolgreich; Minecraft-JAR und Java-Regeltests erfolgreich gebaut. Nächster Nachweis: Minecraft-Spielszene in isoliertem virtuellen Display; anschließend echte CK3-Integration auf dem Windows-PC. Die Cloud kann diesen PC nicht erreichen.

## Veröffentlichung

Melty funktioniert über die autorisierte HTTP-Verbindung; Zugangsdaten bleiben ausschließlich in der vom Benutzer hochgeladenen Datei außerhalb des Projekts. Keine Zugangsdaten in Code, Logs oder Paketen. Kein Listing, Upload oder Veröffentlichungsaufruf. Rechte und Remix-Wahl noch offen. Aktueller Stand ist nur ein Entwicklungsprototyp.

## Minecraft-Spieltest und Korrekturen

- Isolierter Fabric-Entwicklungsclient über Xvfb gestartet, ohne Spieleranmeldung oder Zugriff auf den Windows-PC. Die Daten Adelheid/Otto sind ausdrücklich synthetische Log-Fixtures, keine tatsächliche CK3-Kampagne. Vanilla-Welt und CKCraft-Dimension laden. Cloud besitzt 4 CPU-Anteile; Entwicklungsclient auf 4 Prozessoren und 2 GiB Heap begrenzt. Xvfb/xdotool aus signaturgeprüftem Debian-Repository lokal extrahiert.
- Erste Rückkehr durch 300-Sekunden-Timeout: sieben Test-Diamanten, ursprüngliche Position (7.5, 63, 25.5), 20 Lebenspunkte und Survival-Modus wiederhergestellt. Test-Eingaben hatten die Diamanten vor dem Szenenstart in die Nebenhand verschoben; die Wiederherstellung entspricht dem gespeicherten Szenenstart, nicht einem früheren UI-Bild.
- Tatsächlicher Gegner mit PersistenceRequired=1 hat bei Prowess 18 30 Lebenspunkte. Seine Waffe fügte ungewollt +5 Schaden hinzu (8 statt 3). Tabellen um explizite Waffen-/Attributfelder ergänzt; Attributmodifikatoren der visuellen Waffe entfernt.
- Chunk-Neuladen kann das Entity-Objekt austauschen. Die gespeicherte Referenz konnte daher einen bereits entladenen Gegner steuern (tatsächlich geladene Kopie blieb NoAI=1). Gegner nun über stabile UUID auflösen, Kampfzustand nach Neuladen erneut setzen und Tod anhand UUID erkennen. Getaggte alte Gegner werden entfernt; fremde Entities bleiben erhalten.
- Erste virtuelle Fenster-Schließung über xdotool verursachte einen X11-BadDrawable-Abbruch. Danach Minecraft regulär über Save and Quit / Quit Game beendet; Exit 0. Kein Quellcodeproblem oder behaupteter erfolgreicher Spieltest.

## Abschließender isolierter Durchlauf am 7. Oktober 2026

- Neue lokale Testwelt `CKCraft Final` und neue Verbindungsdaten, um vorherige Tests nicht zu vermischen. Echte Fabric-/Minecraft-Ausführung, weiterhin synthetische CK3-Frames. Die Cloud-Umgebung wurde während der Entwicklung aktualisiert; alte Laufzeitzustände wurden nicht als abschließender Nachweis verwendet.
- Gegner mit Kampfgeschick 18: 30 Lebenspunkte und tatsächlich 3 Angriffsschaden. Am Wegende startet der Kampf, der Gegner bewegt sich zum Spieler. Der Siegpfad wurde gezielt mit einem `/kill`-Testbefehl geprüft, nicht als natürlich erspielter Sieg ausgegeben: Rückkehr und `RETURN_PENDING/won`, erst nach synthetischem passenden ACK abgeschlossen.
- Freie Reise: automatische Szenenübernahme, `/ckcraft return`, `RETURN_PENDING/travelled`, danach synthetischer ACK. Nach regulärem Speichern wurden Position (-8.5, 63, 9.5), sieben Diamanten in Slot 0, Gesundheit 20 und Survival-Modus anhand der gespeicherten Spielerdaten geprüft.
- 25 Python-Tests erfolgreich; Java-Build mit 3 Regeltests erfolgreich. Preflight: 5 Tabellen, 112 belegte und typgeprüfte Zellen, Bezüge aufgelöst, generierte Dateien unverändert passend.
- `artifacts/validation.json` nennt Nachweise und Grenzen. Das Bild zeigt die echte Minecraft-Szene mit synthetischen Daten; es ist kein Nachweis eines echten CK3-Rundlaufs und keine Veröffentlichungsfreigabe.
- Wiederverwendbares Installationsskript, Startanweisungen und benötigte Netzwerkdomains als Cloud-Umgebungsentwurf gespeichert. Das ist keine Melty-Veröffentlichung. Lokales Entwicklerarchiv enthält Quellcode und gebaute JAR, aber keine Laufzeit-Token, Spielstände oder heruntergeladenen Spiele.
- Offen: aktuelles CK3 auf dem Windows-PC, echte Request-/ACK-Syntax und Spielauswirkungen, automatischer Rückweg, Windows-Ein-Klick-Installation, weitere Szenen und Multiplayer. Kein GitHub-Push, kein Melty-Upload und keine Veröffentlichung.

## Nutzer-Test Crozier 1.20.0.4 und Export-Korrektur

- Projektstand `3ba7fec` auf ausdrücklichen Wunsch unverändert auf GitHub `main` gepusht, einschließlich Quellcode, Datentabellen, bestehender JAR und Entwickler-ZIP. Kein Melty-Upload und kein Release.
- Nutzer hat CK3-Mod installiert, Test-Playset aktiviert, CKCraft-Entscheidungen gesehen und Python-Verbindung sowie Fabric-Profil gestartet. Minecraft meldet `Wartet auf CK3`; dies ist keine Bestätigung eines erfolgreichen HTTP- oder CK3-Rundlaufs.
- Tatsächliche vom Nutzer gelieferte CK3-Zeile: `CKCRAFT1|REQUEST|free_travel||||0|0|||none`, aus `ckcraft.1001:immediate`. Gemeldete Version Crozier 1.20.0.4. Die Exportfelder aus `ROOT.Char` sind sämtlich leer, die Literalwerte kommen an. Python lehnt den Frame ab; bislang keine bestätigte erfolgreiche Szenenübernahme aus CK3.
- Quelle erneut geprüft: öffentliche Engine-Referenz 1.10.2 dokumentiert `GetPlayer` als globalen Character-Getter, `Character.MakeScope`, `Scope.Var`, `Scope.Char`, `Character.GetID/GetProwess/GetCurrentLocation/GetFirstNameNoTooltip`, `Province.GetID`, `set_variable` mit Event-Target-Wert und `remove_variable`.
- Designvertrag zuerst aktualisiert; Request und ACK verwenden jetzt den globalen Einzelspieler-Getter `GetPlayer`. Der tatsächlich gewählte erwachsene Hofcharakter wird als Character-Variable vor dem Logexport gespeichert und nach dem ACK entfernt. Keine Ersatz-IDs oder erfundenen Namen; keine Lockerung der Datenprüfung. Der Ansatz ist anhand der Referenz implementiert, aber muss noch im aktuellen Spiel erfolgreich bestätigt werden.
- Leere Exportfelder werden in Python ausdrücklich mit ihren Feldnamen diagnostiziert. Regressionstest mit der tatsächlichen fehlerhaften Zeile, sowie Generatorprüfung auf kontextunabhängigen Player-Zugriff und Lebensdauer des echten Gegnerbezugs. 27 Python-Tests und Java-Build mit 3 Regeltests erfolgreich; Entwicklerpaket für diesen Stand aktualisiert. Minecraft-Spieltest aus dem früheren Abschnitt bleibt dem dortigen Build zugeordnet.
- Windows-Updateanleitung in `docs/PLAYTEST.md`: CK3 und Verbindung stoppen, aktuellen Projektstand separat entpacken, eigene unveränderte Moddateien über den Installer aktualisieren, Verbindung starten, altes ausstehendes CK3-Ereignis abbrechen und freie Reise erneut testen. Erfolgreicher Live-Request/ACK und automatischer Rückweg bleiben offen.

## Bestätigter freier Rundlauf und Korrektur der Rückgabe

- Das erste Update wurde beim Nutzer wegen einer geänderten externen Mod-Beschreibungsdatei verweigert; alte `ROOT.Char`-Exports blieben daher aktiv. Die unveränderte Nutzermod-Installation wurde nach Sicherungsumbenennung ausschließlich dieser Descriptor-Datei erfolgreich aktualisiert. Dieser Ablauf wurde zusätzlich mit einer isolierten Installation reproduziert; die gesicherte Datei blieb unverändert erhalten.
- Nutzer berichtet mit Stand `8329bfe`: Minecraft versetzt ihn auf den Weg, der tatsächliche Herrschername stimmt, `/ckcraft return` erzeugt die erwartete Rückkehrmeldung. Die Verbindung legt ein `travelled`-Rückgabeereignis für interne ID `11999`, Sequenz `1` bereit.
- Reale CK3-Logs belegen `Referencing non-existent character in script link character:11999`, sowie interne ID `11999` und historische ID `6878` desselben Herrschers. Der Konsolentext war außerdem versehentlich doppelt ineinander kopiert. Öffentliche Engine-Referenz `1.10.2_event_targets.log`: `character` ist ein globaler Link auf einen historischen, geskripteten Charakterschlüssel, nicht auf `Character.GetID`.
- Nutzer hat nach Leeren des Konsolenfelds den gleichen geschützten Befehl mit `character:6878` ausgeführt und ausdrücklich `CK3 acknowledged the result` bestätigt. Damit ist ein tatsächlicher freier CK3/Minecraft/CK3-Rundlauf unter Crozier 1.20.0.4 berichtet. Inventar-/Positionsgleichheit und natürliches Duell sind im aktuellen Nutzertest noch nicht vollständig dokumentiert. Kein Screenshot/Clip der echten Kampagne vorgelegt.
- Dauerhafte Befehlsvorlage korrigiert: beim Request gespeicherte globale Charakterreferenz statt historischer ID-Suche; kampagnenweit steigende Sequenz statt kollidierender Zähler auf unterschiedlichen Herrschern. Native Guards verhindern einen weiteren aktiven Request; Ergebnis bleibt an die Referenz gebunden und entfernt sie nach dem ACK. Historische/dynamische Charaktere werden identisch adressiert. Alte Requests können noch mit der bestätigten historischen ID abgeschlossen werden; die neue Vorlage benötigt den neuen CK3-Mod beim Request.
- JSON-Verträge zuerst geändert, Generator und Python-Befehlsvorlage aktualisiert. 28 Python-Tests einschließlich Referenz-Lebensdauer, globaler Sequenz, bestehender Replay-/Owner-/ACK-Tests erfolgreich; Java-Build und Entwicklerarchiv aktualisiert. Diese neue Vorlage ist noch nicht live bestätigt und keine automatische Konsolensteuerung.
