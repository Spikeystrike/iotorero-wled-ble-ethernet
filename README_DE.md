# IoTorero WLED + BLE JSON + Ethernet (Deutsch)

**Experimenteller Build-Kandidat – NICHT vor einer Prüfung der Flash-Partitionen und eines USB-Recovery-Wegs flashen!**

Dieses Projekt richtet sich an den fotografierten **IoTorero Addressable/DMX Ethernet/USB/Sound Reactive ESP32-Controller**. Die Daten stammen aus der gesicherten WLED-Konfiguration; persönliche Netzwerkdaten, Passwörter und Gerätekennungen werden nicht veröffentlicht.

## Hardwareprofil

| Anschluss | GPIO | LEDs |
| --- | ---: | ---: |
| DAT1 | 5 | 35 |
| DAT2 | 16 | 373 |
| DAT3 | 4 | 71 |

Insgesamt 479 LEDs, Typ 22 (WS281x RGB), Farbreihenfolge RGB, Grenze 7000 mA, 42 FPS. Taste GPIO 0, Relais GPIO 2, digitales Mikrofon Typ 5 auf GPIO 32/15.

Ethernet verwendet den LAN8720-PHY (Adresse 1), MDC GPIO 23, MDIO GPIO 18 und ETH_CLOCK_GPIO17_OUT. **Achtung:** Die Hersteller-Firmware WLED 0.15.0 speichert Ethernet-Typ **13**. Im offiziellen WLED **16.0.1** lautet das IoTorero-Profil **6**. Das Build-Skript ergänzt eine Migration, die nur für die erwartete gespeicherte Pinliste greift.

## Bauen

Das Skript lädt angepinnte Versionen: WLED Commit `29b389df1c1aaec6ff53aea742d17063b985906c`, Boardsesh BLE JSON Commit `a47f0e894d6d71302b25f3e97a8ba201811a3cf3`.

**GitHub Actions:** Reiter Actions → Workflow „Build WLED IoTorero BLE Ethernet candidates“ → Run workflow. Der Workflow versucht zwei Varianten zu bauen (mit und ohne AudioReactive), führt Tests aus und legt nur bei erfolgreichem Build ein Artefakt mit dem Namen `iotorero-ble-ethernet-untested` an.

**Lokal (mit Internet, Python 3.11+, Git):**
1. `python -m pip install platformio==6.1.18`
2. `python build_iotorero.py --self-test`
3. `python build_iotorero.py --profile both`

Das Skript flasht nicht. Es versucht, Images zu erzeugen und prüft die Größe gegen einen **angenommenen** Slot von 0x180000 Bytes. Dies beweist **keine** OTA-Kompatibilität.

## Unbedingt vor dem Flashen

1. Bestehende `cfg.json` und `presets.json` sichern und privat aufbewahren.
2. Originalen ESP32-Flash über USB vollständig sichern und Recovery testen.
3. Partitionstabelle lesen (nur lesend), z. B. `python -m esptool --chip esp32 --port COM3 read_flash 0x8000 0x1000 partition.bin` (Port/Befehl und Flashgröße vorher prüfen).
4. `python inspect_partition.py partition.bin` ausführen. Slots und Offsets mit der für den Build verwendeten WLED-Partitionstabelle abgleichen.
5. **Kein OTA-Flash**, wenn die Partitionen inkompatibel sind.
6. Erst die Ethernet-Verbindung und die LED-Ausgänge prüfen, dann BLE in den WLED-Usermod-Einstellungen aktivieren und LAN und BLE gleichzeitig testen.

BLE nutzt ein eigenes GATT-Protokoll ohne verpflichtende Kopplung bzw. Zugriffskontrolle. Andere Clients in Funkreichweite könnten die LEDs steuern. Eine normale WLED-App unterstützt das BLE-GATT-Protokoll nicht automatisch. Im BLE-Kandidaten sind einige Funktionen einschließlich DMX zur Platzersparnis deaktiviert. AudioReactive + Ethernet + BLE wurde noch nicht an diesem Gerät verifiziert.

**Status:** Projektdateien und Offline-Selbsttest erstellt; GitHub-Actions-Ergebnis, tatsächliche Funktion, Sicherheit der Partitionen und Gerätetests müssen getrennt bestätigt werden.