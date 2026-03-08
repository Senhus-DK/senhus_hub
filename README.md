# Senhus Hub

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

Home Assistant integration for the **Senhus Hub1** — a Waveshare 2.9" e-paper display powered by an ESP32-S3, built to show your Home Assistant sensor data at a glance.

![Senhus Hub1 display layout](docs/display-layout.png)

---

## Features

- **Auto-discovery** via zeroconf — no manual IP configuration needed
- **3 display slots** — assign any HA sensor to the left panel, top-right, and bottom-right
- **Custom labels and units** — override the sensor name and unit shown on the display
- **OTA firmware updates** — update the device directly from the HA UI via the update entity
- **Multi-device** — each Hub is a separate config entry

## Display Layout

```
┌──────────────────────────────────────────────┐
│ 12:34                        Sat 07 Mar      │  ← time & date (on device)
├─────────────────┬────────────────────────────┤
│                 │  [Slot 2 value] [unit]      │
│  [Slot 1 value] │  [Slot 2 label]             │
│  [Slot 1 unit]  ├────────────────────────────┤
│  [Slot 1 label] │  [Slot 3 value] [unit]      │
│                 │  [Slot 3 label]             │
└─────────────────┴────────────────────────────┘
```

- **Slot 1** — left panel (large font, ideal for a primary value like energy price)
- **Slot 2** — right panel top row
- **Slot 3** — right panel bottom row

## Requirements

- Home Assistant 2024.1 or newer
- Senhus Hub1 device running the matching ESPHome firmware
- [HACS](https://hacs.xyz) installed

## Installation

### Via HACS (recommended)

1. In HACS, go to **Integrations** → three-dot menu → **Custom repositories**
2. Add `https://github.com/Senhus-DK/senhus_hub` as category **Integration**
3. Find **Senhus Hub** in HACS and install it
4. Restart Home Assistant

### Manual

Copy the `custom_components/senhus_hub` folder into your HA `config/custom_components/` directory and restart.

## Setup

1. Power on your Senhus Hub1 — it will be auto-discovered by HA
2. Go to **Settings → Devices & Services** and confirm the discovered device
3. Open the integration options to assign sensors to each display slot

## Configuration

Each slot can be configured with:

| Field | Description |
|-------|-------------|
| Entity | Any `sensor` or `input_number` entity from HA |
| Label | Text shown below the value on the display |
| Unit | Unit shown next to the value (overrides entity unit) |

## Firmware

The ESPHome firmware for the Hub1 is available in the [development repository](https://github.com/Senhus-DK/development).

## License

[CC BY-NC 4.0](LICENSE) — free for personal use, attribution required, no commercial use.
