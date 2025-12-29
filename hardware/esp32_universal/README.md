# ESP32 Universal Node

## Overview

This is the ESP32 version with automatic hardware detection. It replaces the ESP8266 nodes with a more powerful, flexible solution.

## Features

- **Automatic Hardware Detection**: Detects RFID, PIR, BLE at boot
- **Modular**: Only enables modules for detected hardware
- **MQTT Communication**: Pub/sub instead of HTTP polling
- **Lower Power**: Deep sleep support for battery operation
- **OTA Updates**: Update firmware over-the-air
- **Better Performance**: ESP32 dual-core, more memory

## Hardware Support

| Module | Detection | Auto-Enable |
|--------|-----------|-------------|
| RFID (MFRC522) | SPI bus scan | Yes |
| PIR Sensor | GPIO configured | Yes |
| BLE Beacon | Config flag | Optional |

## Pin Configuration

### ESP32 DevKit Default Pins

```
RFID Reader (SPI):
- RST: GPIO 22
- SS:  GPIO 21
- MOSI: GPIO 23 (default SPI)
- MISO: GPIO 19 (default SPI)
- SCK:  GPIO 18 (default SPI)
- VCC:  3.3V
- GND:  GND

PIR Sensor:
- OUT: GPIO 4
- VCC: 5V
- GND: GND

LED:
- Built-in: GPIO 2
```

## Dependencies

Install via Arduino Library Manager:

1. **WiFi** (built-in ESP32)
2. **PubSubClient** (MQTT client)
3. **ArduinoJson** (JSON serialization)
4. **MFRC522** (RFID reader)

## Setup

1. Copy `config.h.example` to `config.h`
2. Edit `config.h` with your WiFi and MQTT settings
3. Select **ESP32 Dev Module** in Arduino IDE
4. Upload to your ESP32

## Modes of Operation

### Mode 1: RFID + PIR (Most Common)
- Entry: PIR detects → RFID scans → Publishes to MQTT
- Both modules auto-detected and enabled

### Mode 2: PIR Only
- Entry: PIR detects → Publishes motion event
- RFID not connected, auto-disabled

### Mode 3: RFID + PIR + BLE Beacon
- Same as Mode 1 + broadcasts BLE UUID
- Enable by uncommenting `#define ENABLE_BLE` in config.h

## Boot Sequence

```
1. Power on
2. Serial output: "Detecting hardware..."
3. Checks SPI bus for RFID (version register)
4. Checks GPIO for PIR
5. Checks config for BLE flag
6. Connects to WiFi
7. Connects to MQTT broker
8. Publishes device status with capabilities
9. Ready!
```

## MQTT Topics

### Publish (Device → Server)

**Sensor Events**:
```
Topic: zias/devices/{device_name}/sensor
Payload: {
  "device_id": "room1_node1",
  "cluster_id": 1,
  "event_type": "activated",
  "rfid": "04 AB CD EF",
  "sensor": true,
  "timestamp": 12345
}
```

**Device Status**:
```
Topic: zias/devices/{device_name}/status
Payload: {
  "device_id": "room1_node1",
  "status": "online",
  "has_rfid": true,
  "has_pir": true,
  "has_ble": false,
  "ip": "192.168.1.100",
  "rssi": -65
}
```

### Subscribe (Server → Device)

**Commands**:
```
Topic: zias/devices/{device_name}/cmd
Payload: {
  "command": "restart|update|config"
}
```

## Power Consumption

**Active Mode**:
- WiFi active: ~160mA
- RFID idle: ~15mA
- PIR: ~50µA
- Total: ~175mA @ 3.3V

**Deep Sleep Mode** (future):
- Wake on PIR: ~10µA
- Battery operation: 6+ months on 18650

## Advantages Over ESP8266

| Feature | ESP8266 | ESP32 |
|---------|---------|-------|
| CPU | 80MHz single | 240MHz dual-core |
| RAM | 80KB | 520KB |
| Flash | 4MB | 4MB+ |
| WiFi | 2.4GHz only | 2.4GHz + BLE |
| GPIO | 11 usable | 34 usable |
| Auto-detect | No | Yes |
| OTA | Limited | Full support |
| Deep sleep | Basic | Advanced |
| Cost | ~Rs. 150 | ~Rs. 250 |

## Troubleshooting

**RFID not detected**:
- Check SPI wiring
- Verify 3.3V power
- Swap MOSI/MISO if needed

**MQTT not connecting**:
- Check broker IP in config.h
- Verify firewall allows port 1883
- Check WiFi signal strength

**PIR false triggers**:
- Adjust sensitivity pot on sensor
- Increase DEBOUNCE_DELAY
- Shield from air currents

## Migration from ESP8266

1. Replace NodeMCU with ESP32 DevKit
2. Update pin numbers in config.h
3. Re-upload code
4. Verify auto-detection in serial monitor
5. Update device name in MQTT broker

Cost difference: ~Rs. 100 more per node, worth it for reliability.
