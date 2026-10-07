# Echte Spielprüfung auf Windows

Diese Schritte sind Entwicklungstests. Sie erfüllen noch nicht Meltys Ein-Klick-Anforderung. CK3 benötigt für den derzeitigen Log-/Konsolenweg den Debug-Modus; nutze eine neue, nicht-Ironman-Testkampagne. Keine bestehende Kampagne konvertieren. CK3-Version noch offen; verwendete Skriptbefehle sind anhand der öffentlichen Engine-Dokumentation 1.10.2 geprüft, nicht anhand deiner aktuellen Installation.

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
4. Die Verbindung legt nach jedem Ergebnis `return-command.json` in der privaten Zustandsablage an. Den darin enthaltenen `command` für diesen Entwicklungstest in der CK3-Konsole ausführen. Es muss **genau** die passende `CKCRAFT1|ACK|CHARAKTER|SEQUENZ|ERGEBNIS`-Zeile entstehen. Erst dann ist der Übergang abgeschlossen; das Ergebnis darf bei Wiederholung keine zweite Belohnung erzeugen.
5. **In Minecraft reisen** in CK3 wählen, frei umsehen, `/ckcraft return`. Das gültige Ergebnis ist `travelled`, ohne zusätzliche Belohnung. Einen hängenden CK3-Übergang kann die Entscheidung **Ausstehende Minecraft-Reise abbrechen** ohne Belohnung lösen; einen noch aktiven Minecraft-Durchlauf ebenfalls abbrechen.
6. Ein Bild oder einen Clip dieser tatsächlich laufenden Version aufnehmen. Ein Minecraft-Entwicklungstest mit synthetischen CK3-Zeilen ist kein Nachweis der vollständigen Verbindung und darf nicht als Melty-Veröffentlichungsbeleg dienen.

Aufzulösende Punkte vor Veröffentlichung: genaue CK3-Version und tatsächliche Skript-/Scope-Kompatibilität, automatische sichere Rückgabe statt manuellem Konsolenbefehl, zuverlässige Pause und Wechsel, Bereitstellung einer startbaren Minecraft-Welt, vollständige tragbare Laufzeiten, Ein-Klick-Installation, Lizenz/Credits/Remix-Entscheidung und echte Medien.
