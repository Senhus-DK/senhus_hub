# Senhus Hub — HACS Integration

## Project
Home Assistant custom integration for Senhus Hub e-paper display devices.
GitHub: `Senhus-DK/hacs-senhus-hub`
Integration domain: `senhus_hub`

## Structure
```
custom_components/senhus_hub/
├── __init__.py       — setup/teardown
├── manifest.json     — HACS metadata, zeroconf
├── const.py          — all constants
├── config_flow.py    — device discovery + options UI
├── coordinator.py    — ESPHome API connection, pushes values to device
├── update.py         — HA update entity, GitHub OTA
├── strings.json
└── translations/en.json
```

## Architecture
- Discovery: zeroconf `_esphomelib._tcp.local.` + manual IP fallback
- Device verified by `project_name.startswith("Senhus")` on connect
- Options flow: 3 slots x (entity_id, label, unit)
- Coordinator connects via `aioesphomeapi`, subscribes to configured HA entities,
  pushes values to device text entities (`slot1_value` etc.) on state change
- Update entity polls GitHub releases API, OTA-flashes via ESPHome API
- Each device = separate config entry (supports multiple devices)

## Display slots
- Slot 1 → left panel
- Slot 2 → right panel top
- Slot 3 → right panel bottom

## Card system
- `custom` card: user picks any sensor for each slot (implemented)
- Predefined cards (energy, weather etc.) planned for future — placeholder in const.py

## Notes
- The firmware repo may move to a separate GitHub repo in future
- `aioesphomeapi` is declared in manifest requirements (bundled with HA core)
