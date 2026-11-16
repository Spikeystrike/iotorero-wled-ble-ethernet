# IoTorero WLED + Bluetooth LE + Ethernet

**Status: Prototype / UNTESTED. Do not flash without checking the device's flash partitions and recovery path.**

This repository contains a reproducible build wrapper for **WLED 16.0.1** with [Boardsesh BLE JSON](https://github.com/boardsesh/wled-usermod-ble-json), specifically configured for an **IoTorero Addressable/DMX Ethernet/USB/Sound Reactive ESP32 controller**.

- **Ethernet:** stock WLED IoTorero type 6, LAN8720 on GPIO 23 (MDC), 18 (MDIO), 17 (clock output), PHY address 1.
- **Legacy migration:** vendor WLED 0.15.0 stores type 13 for IoTorero. This build attempts to migrate only matching PHY-pin configurations to stock type 6.
- **LED outputs:** DAT1 = GPIO 5 / 35 LEDs; DAT2 = GPIO 16 / 373 LEDs; DAT3 = GPIO 4 / 71 LEDs (479 total).
- **Audio:** optional build profile for the existing digital microphone (GPIO 32/15), currently unverified alongside Ethernet and BLE.
- **BLE:** opt-in after flashing; standard WLED app does not automatically support the custom BLE GATT protocol.
- **DMX is disabled** in the BLE candidate to conserve flash space.

For full instructions, version pins, backup procedure, partition verification and risk warnings, see [README_DE.md](README_DE.md).

Run GitHub Actions → **Build WLED IoTorero BLE Ethernet candidates** to build firmware candidates. Build success alone does **not** mean the images are safe to flash, and no hardware testing has been performed.

Personal configuration backups and private identifiers must not be committed.
