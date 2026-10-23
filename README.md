# ESP32 Wi-Fi Telemetry Monitor

A small hardware + Python prototype that scans nearby Wi-Fi access points with an ESP32 and displays summary telemetry in a live terminal dashboard. It includes simple rule-based alerts for notable changes in access-point count and strongest received signal strength (RSSI).

> **Scope and safety:** This project observes publicly broadcast Wi-Fi beacon information (network count, signal strength, and channel usage). It does not connect to access points, capture traffic, identify users, or prove that an attack is occurring. Alerts are heuristics for unusual changes, not confirmed intrusion detections. Detection is rule-based; this version does not use machine learning.

## Features

- ESP32 scans nearby Wi-Fi access points using the Arduino Wi-Fi library.
- Collects visible network count, strongest and average RSSI, and count of observed 2.4 GHz channels.
- Sends newline-delimited JSON telemetry over USB serial.
- Python terminal dashboard displays live metrics, recent scan history, and activity events.
- Baseline-based rules flag large changes in access-point count or strongest RSSI.

## Architecture

```text
Nearby Wi-Fi beacons
        |
        v
ESP32 firmware (Arduino IDE)
        |
        | USB serial, 115200 baud, JSON lines
        v
Python dashboard (pyserial + Rich)
        |
        v
Live terminal metrics + rule-based anomaly alerts
```

## Hardware and software

- ESP32 development board (for example, ESP32-WROOM-32 / ESP32 Dev Module)
- USB data cable
- Arduino IDE with an ESP32 board package installed
- Python 3.10+ recommended
- Windows, Linux, or macOS (adjust the serial port for your OS)

## Setup

### 1. Flash the ESP32

1. Open `firmware/esp32_wifi_monitor.ino` in Arduino IDE.
2. Select the appropriate ESP32 board (often **ESP32 Dev Module**) and the correct serial port.
3. Upload the sketch.
4. Close Arduino Serial Monitor and Serial Plotter before running the Python dashboard, because only one application can generally open the serial port at a time.

### 2. Install Python dependencies

From this repository folder, run:

```bash
python -m pip install -r requirements.txt
```

### 3. Configure the serial port

Open `dashboard.py` and change `PORT = "COM4"` to match your device.

- Windows example: `COM4`
- Linux example: `/dev/ttyUSB0` or `/dev/ttyACM0`
- macOS example: `/dev/cu.usbserial-XXXX` or the device name shown by your system

### 4. Run the dashboard

```bash
python dashboard.py
```

Use **Ctrl+C** to stop monitoring. If you get a serial access error, close Arduino Serial Monitor/Plotter and any other process that is using the port.

## What the alerts mean

The dashboard collects an initial baseline of 10 scans. After that, it reports a warning when:

- the visible access-point count differs from the baseline average by at least 3; or
- the strongest observed RSSI differs from its baseline average by at least 15 dB.

Wi-Fi environments naturally change. Interference, movement, walls, devices appearing/disappearing, and scan variability can all trigger these rules. A warning is **not evidence of an attack**.

## Limitations and next steps

- Current implementation uses fixed-threshold rules, not machine learning.
- The dashboard is a prototype intended for learning and demonstration.
- Channel counting covers channels 1–14, so it summarizes the common 2.4 GHz band rather than all possible Wi-Fi bands.
- No historical database, packet capture, authentication, or attack attribution is implemented.

Potential future improvements: save timestamped CSV/SQLite data, tune thresholds using collected samples, improve charting, and evaluate a trained anomaly detector against a labeled dataset.

## Repository structure

```text
esp32-wifi-telemetry-monitor/
├── firmware/
│   └── esp32_wifi_monitor.ino
├── dashboard.py
├── requirements.txt
├── .gitignore
└── README.md
```

