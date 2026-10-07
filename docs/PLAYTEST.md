# Echte Spielprüfung auf Windows

Diese Schritte sind Entwicklungstests. Sie erfüllen noch nicht Meltys Ein-Klick-Anforderung. CK3 benötigt für den derzeitigen Log-/Konsolenweg den Debug-Modus; nutze eine neue, nicht-Ironman-Testkampagne. Keine bestehende Kampagne konvertieren. Der Nutzer hat unter CK3 Crozier **1.20.0.4** eine freie Reise mit passendem Charakternamen und CK3-ACK bestätigt (Stand `8329bfe`, historische ID im Konsolenbefehl manuell korrigiert). Der aktuelle Rückweg über eine gespeicherte Charakterreferenz muss noch separat live geprüft werden. Die öffentliche Engine-Referenz 1.10.2 belegt seine Funktionen, nicht den Erfolg dieses neuen Rückwegs.

## Voraussetzungen

Eigene installierte Kopien von CK3 und Minecraft Java, ein separates Fabric-Profil für **Minecraft 1.21.1**, Fabric Loader **0.16.10**, Fabric API **0.116.7+1.21.1**, Python **3.12+** für diesen Entwicklungsstand. Die geplante Veröffentlichung muss Python und Prism mitliefern; sie darf diese manuelle Installation nicht voraussetzen. Backups der persönlichen Spielstände und Profile erstellen. Die Cloud kann deinen Windows-PC nicht fernsteuern.

## CK3-Mod installieren

Im Projektordner mit dem tatsächlichen Windows-Dokumente-Pfad (gegebenenfalls OneDrive):

```powershell
python tools/install_ck3.py --documents "C:\Users\DEINNAME\Documents"
```

Das erzeugt ausschließlich `mod/ckcraft_dev` und `mod/ckcraft_dev.mod`. Der Installer lässt andere Mods und Saves unverändert und verweigert das Überschreiben eigener Änderungen. Im Paradox-Launcher einen separaten Test-Playset mit diesem Mod aktivieren. CK3 für den Test mit `-debug_mode` starten.

## Verbindung vor dem CK3-Ereignis starten

Die private Zustandsablage pro Kampagne getrennt halten. Keine Zustandsablage für andere Kampagnen oder ältere Save-Versionen wiederverwenden. Zunächst eine neue Kampagne benutzen.

```powershell
$env:PYTHONPATH = "$PWD\bridge"
python -m ckcraft --ck3-log "C:\Users\DEINNAME\Documents\Paradox Interactive\Crusader Kings III\logs\debug.log" --state "$env:LOCALAPPDATA\CKCraft\TestCampaign" --campaign "TestCampaign"
```

Das Terminal offen lassen. Es meldet den Pfad der privaten `bridge.json`; das Token selbst darf nicht veröffentlicht werden. Die Verbindung beginnt am aktuellen Log-Ende; vorhandene historische Ereignisse werden nicht erneut gestartet.

## Minecraft

Die gebaute JAR und die passende Fabric-API-JAR in die Mods der separaten Instanz legen. Für den Minecraft-Prozess die Variable `CKCRAFT_BRIDGE_CONFIG` auf die private `bridge.json` setzen (z.B. in den Umgebungsvariablen dieser Prism-Instanz). Eine neue Einzelspieler-Testwelt starten. `/ckcraft status` muss auf CK3 warten. Der Mod ist ohne diese Variable inaktiv; dedizierte Server werden derzeit nicht unterstützt.

## Prüfen und Belege festhalten

1. In CK3 **CKCraft einschalten** wählen. Eine Reise starten. Alternativ das Entwicklungsereignis mit `event ckcraft.1000 CHARAKTER_ID` auslösen, wenn eine Reise für deine Version noch nicht möglich ist. Die Kampagne beim Wechsel pausieren; der Mod pausiert den Reiseplan, nicht die gesamte Simulation. Es muss eine neue `CKCRAFT1|REQUEST|...`-Zeile im tatsächlichen Debug-Log erscheinen, mit aufgelösten Werten und einem anderen, erwachsenen Hofcharakter.
2. In Minecraft automatisch in die abgegrenzte Wegszene gelangen. Charaktername, Charakter-ID, Provinz und beide Kampfgeschickwerte mit CK3 vergleichen. Zum goldenen Wegende laufen, um das Duell zu beginnen. Ein vor Beginn unangreifbarer Gegner darf keinen vorzeitigen Sieg erlauben.
3. Sieg spielen, Niederlage spielen und eine neue Szene mit `/ckcraft return` abbrechen. Inventar, ursprüngliche Position, Spielmodus, Gesundheit, Hunger und Erfahrung jeweils vorher/nachher vergleichen. Die Wiederherstellung muss auch nach Disconnect/Neustart funktionieren. Die Szene darf keine normalen Weltblöcke ändern.
4. Die Verbindung legt nach jedem Ergebnis `return-command.json` in der privaten Zustandsablage an. Den darin enthaltenen `command` für diesen Entwicklungstest in der CK3-Konsole ausführen. Vor dem Einfügen das Eingabefeld vollständig leeren; kein neuer Befehl darf an einen alten Text angehängt werden. Der aktuelle Befehl verwendet `global_var:ckcraft_return_actor`, eine beim Request gespeicherte echte Charakterreferenz. Eine Laufzeit-ID aus `GetID` ist kein gültiger Ersatz für den historischen Schlüssel in `character:...`. Es muss **genau** die passende `CKCRAFT1|ACK|CHARAKTER|SEQUENZ|ERGEBNIS`-Zeile entstehen. Erst dann ist der Übergang abgeschlossen; das Ergebnis darf bei Wiederholung keine zweite Belohnung erzeugen.
5. **In Minecraft reisen** in CK3 wählen, frei umsehen, `/ckcraft return`. Das gültige Ergebnis ist `travelled`, ohne zusätzliche Belohnung. Einen hängenden CK3-Übergang kann die Entscheidung **Ausstehende Minecraft-Reise abbrechen** ohne Belohnung lösen; einen noch aktiven Minecraft-Durchlauf ebenfalls abbrechen.
6. Ein Bild oder einen Clip dieser tatsächlich laufenden Version aufnehmen. Ein Minecraft-Entwicklungstest mit synthetischen CK3-Zeilen ist kein Nachweis der vollständigen Verbindung und darf nicht als Melty-Veröffentlichungsbeleg dienen.

Aufzulösende Punkte vor Veröffentlichung: tatsächliche Skript-/Scope-Kompatibilität mit Crozier 1.20.0.4, automatische sichere Rückgabe statt manuellem Konsolenbefehl, zuverlässige Pause und Wechsel, Bereitstellung einer startbaren Minecraft-Welt, vollständige tragbare Laufzeiten, Ein-Klick-Installation, Lizenz/Credits/Remix-Entscheidung und echte Medien.

## Update bei leeren CK3-Exportfeldern

Der erste gemeldete Crozier-Test lieferte `CKCRAFT1|REQUEST|free_travel||||0|0|||none`. Das sind fehlende Kampagnendaten; die Verbindung lehnt sie ab. Die Entscheidung und der Logpfad können trotzdem korrekt eingerichtet sein. Der Einzelspieler-Export nutzt nun `GetPlayer`, und der echte ausgewählte Hofcharakter wird vor dem Duell in `ckcraft_opponent` gespeichert. Die Datenprüfung bleibt streng.

1. Testkampagne speichern und CK3 beenden. Die Verbindung im ersten PowerShell-Fenster mit **Strg+C** stoppen.
2. Den aktuellen Projekt-ZIP von GitHub herunterladen und in einen neuen Ordner entpacken. Im Explorer den Ordner öffnen, der `README.md` und `tools` enthält; in die Adressleiste `powershell` eingeben.
3. Den aktualisierten CK3-Mod installieren:

   ```powershell
   $documentsPath = [Environment]::GetFolderPath("MyDocuments")
   py -3.12 .\tools\install_ck3.py --documents "$documentsPath"
   ```

   Der Installer aktualisiert seine unveränderten eigenen Dateien anhand des bisherigen Installationsmanifests. Er ersetzt keine selbst bearbeiteten Mods. Das vorhandene Test-Playset kann weiterverwendet werden.
4. CK3 wieder im Debug-Modus starten und die Testkampagne laden. Im neuen Projektordner die Verbindung starten:

   ```powershell
   $env:PYTHONPATH = "$PWD\bridge"
   py -3.12 -m ckcraft --ck3-log "$documentsPath\Paradox Interactive\Crusader Kings III\logs\debug.log" --state "$env:LOCALAPPDATA\CKCraft\TestCampaign" --campaign "TestCampaign"
   ```

5. Falls sichtbar, zuerst **Ausstehende Minecraft-Reise abbrechen** ausführen; damit wird die abgelehnte alte Anfrage im CK3-Charakter freigegeben. Danach **In Minecraft reisen** erneut ausführen und zur laufenden Minecraft-Testwelt wechseln. Bei offenem Pausemenü mit Esc fortsetzen.
6. Erwartet werden echte ausgefüllte Felder in einer neuen `CKCRAFT1|REQUEST|...`-Zeile und `CK3 event accepted: free_travel` im Verbindungsterminal. Falls das weiter ausbleibt, die neueste Request-Zeile und die entsprechenden CKCraft-Meldungen in CK3s `logs/error.log` bereitstellen. `bridge.json` nicht weitergeben.

Minecraft verwendet dasselbe Protokoll; das bestehende Fabric-Profil und der gesetzte Verbindungspfad können für diesen Export-Test weiterverwendet werden. Ein erfolgreicher `/ckcraft status` allein bestätigt weder die CK3-Datenübertragung noch den Rücklauf.

## Rückgabe mit gespeichertem Charakter

Aktuelle Requests speichern `ckcraft_return_actor` als globale Charakterreferenz und verwenden einen kampagnenweiten Zähler. Dadurch kann der generierte Konsolenbefehl auch dynamisch erzeugte Herrscher erreichen und ein altes Ergebnis passt nicht zur nächsten Sequenz eines anderen Herrschers. Das Ergebnis entfernt die Referenz erst nach dem ACK-Log. Der Handler akzeptiert zum manuellen Abschließen alter Requests weiterhin ein ausstehendes Ereignis ohne diese Referenz; die neue generierte Befehlsvorlage benötigt jedoch einen **neuen Request nach Installation des aktualisierten CK3-Mods**.

Der bestätigte alte Test nutzte interne ID `11999`, historische ID `6878` und Sequenz `1`. Der ursprüngliche Befehl scheiterte am historischen Link `character:11999`; nach dem kontrollierten Ersatz durch `character:6878` kam `CK3 acknowledged the result`. Diese Nummern sind keine allgemeinen Vorgaben für andere Kampagnen.

Falls ein Mod-Update mit `Mod descriptor was edited` abbricht, war das Update nicht installiert. CK3 und Paradox-Launcher beenden, die Datei `mod/ckcraft_dev.mod` unter einem eindeutigen Namen sichern (z.B. `ckcraft_dev.mod.backup-<GUID>`) und den Installer erneut starten. Die übrigen installierten Dateien müssen weiterhin ihrem Eigentumsmanifest entsprechen; keine Prüfung abschalten und keine Dateien aus anderen Mods verschieben. Erst nach `Installed development mod:` mit dem nächsten Test fortfahren.
