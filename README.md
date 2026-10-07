# CK3-Minecraft — Arbeitstitel CKCraft

Ein echtes Mashup von **Crusader Kings III** und **Minecraft: Java Edition**. CK3 bleibt das Hauptspiel. Duelle, Belagerungen, Schlachten, einzelne Ereignisse und Reisen sollen in Minecraft stattfinden und zurück auf die CK3-Kampagne wirken. Passende Situationen wechseln automatisch; freies Wechseln ist zusätzlich vorgesehen. Zuerst Einzelspieler, später optional Multiplayer mit getrennten Reichen.

**Status: Entwicklungsprototyp, kein fertiger Melty-Release.** Die erste Umsetzung enthält einen nativen CK3-Skript-Mod, einen Fabric-Mod für Minecraft 1.21.1 und eine lokale Verbindung. Die CK3-Seite und der vollständige automatische Wechsel sind noch nicht im laufenden CK3 geprüft. Die Rückgabe liegt zunächst als geschützter Konsolenbefehl bereit; sie gilt erst nach der tatsächlichen Bestätigung im CK3-Log als übernommen. Eine manuelle Rückgabe ist kein Ein-Klick-Release.

## Erster Durchlauf

Nach Aktivierung über die CK3-Entscheidung erzeugt der Reisestart ein Wegduell mit einem tatsächlichen erwachsenen Charakter deines Hofes. Namen, Charakter-IDs, Provinz und Kampfgeschick werden aus der laufenden Kampagne übertragen. Minecraft erzeugt eine abgegrenzte Wegszene in einer eigenen Dimension. Der Gegner verwendet seinen tatsächlichen CK3-Kampfgeschickwert für Lebenspunkte und Schaden. Seine Minecraft-Darstellung ist vorläufig ein beschrifteter, ausgerüsteter Zombie, kein übernommenes CK3-Modell.

Du läufst zum Gegner und kämpfst. Sieg, Niederlage oder Abbruch erzeugen unterschiedliche CK3-Rückgabeereignisse. Inventar, Position, Spielmodus, Lebenspunkte, Hunger und Erfahrung werden vor der Szene gespeichert und anschließend wiederhergestellt. Eine zweite CK3-Entscheidung erlaubt eine freie Reise mit `/ckcraft return` zur Rückkehr. Fehlt ein geeigneter Hofcharakter, startet kein Wegduell.

Belagerungen, größere Schlachten, zusätzliche Ereignisse und Multiplayer sind im [weiteren Plan](docs/ROADMAP.md) festgehalten und noch nicht implementiert. Die erste Szene ist keine Rekonstruktion der vollständigen CK3-Welt.

## Entwickeln

Python **3.12+** und JDK **21**. Java und Gradle werden bei Bedarf aus offiziellen Quellen heruntergeladen und mit ihren offiziellen SHA-256-Prüfsummen geprüft. Kein bezahlter Dienst und keine API-Schlüssel sind nötig.

```sh
python tools/design.py preflight
python tools/design.py check
python -m unittest discover -s tests -v
python tools/gradle.py --no-daemon build
```

Der gebaute Minecraft-Mod liegt in `minecraft/build/libs/ckcraft-0.1.0-dev.jar`. Designänderungen zuerst in `design/sheets/`, danach `python tools/design.py generate`. Jeder Tabellenzeile entspricht ein generierter Java-Datensatz; daraus entstehen auch CK3-Ereignisse, Entscheidungen, Hooks und Lokalisierung. Der Preflight prüft jede Zelle auf Belegung und Typ sowie alle Referenzen. Er ist keine Behauptung, dass diese Zelle bereits im Spiel geprüft wurde.

Gradle-Caches und Tools bleiben unter `.gradle/`. TLS-, Paket- und Prüfsummenprüfung bleiben eingeschaltet. Die Cloud verwendet den vorhandenen Netzwerkproxy und den System-Java-Truststore, damit auch das nachinstallierte JDK dessen Zertifikate prüft.

## Auf deinem Windows-Spiele-PC testen

Die Testkampagne und eine separate Minecraft-Instanz vorbereiten; persönliche Spielstände vorher sichern. [PLAYTEST.md](docs/PLAYTEST.md) beschreibt die Installation und jede notwendige echte Spielprüfung. Die Cloud hat keinen Zugriff auf deinen Spiele-PC oder dessen CK3-Dateien.

Die Verbindung bindet ausschließlich an `127.0.0.1`. Ein lokales, zufällig generiertes Zugriffstoken befindet sich nur in der privaten Laufzeitkonfiguration. Keine Spielinhalte, Melty-Zugangsdaten oder Spielstände gehören in Git oder in ein Release.

## Melty und Rechte

CK3 ist als `primary`, Minecraft als `companion` vorgesehen; beide müssen gleichzeitig laufen. Für Minecraft orientieren wir uns an SkyCrafts portablem Prism-Paket. [MELTY.md](docs/MELTY.md) beschreibt die noch offenen Veröffentlichungsprüfungen. Titel, öffentliche Beschreibung, Credits, Lizenz und Remix-Erlaubnis sind noch nicht mit dir festgelegt. Es wurde kein Listing erstellt, kein Paket hochgeladen und nichts veröffentlicht. Eine Inhaltslizenz wurde noch nicht vergeben.
