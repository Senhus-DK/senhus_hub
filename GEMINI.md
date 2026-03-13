# Senhus Hub Development Notes

## Architecture Constraints
- **Configuration Approach:** The user strongly prefers configuration entities directly on the device page (using `text` and `select` entities) rather than hiding settings behind an `OptionsFlow` configuration menu.
- **Entity Types:**
  - Use `SelectEntity` populated with `hass.states.async_all()` to provide dropdown lists of HA sensors directly on the device page.
  - Use `TextEntity` for arbitrary string inputs (labels, units).
- **State Management:** All configuration changes from these entities must save back to `config_entry.options` via `hass.config_entries.async_update_entry` to ensure the coordinator picks up the changes and pushes them to the ESPHome device.
- **Discovery:** Device discovery requires checking for the exact prefix `Senhus.Hub` to avoid false positives with other Senhus series devices.

## Release Process
1. Bump version in `manifest.json`.
2. Commit changes.
3. Push to `main`.
4. Create a git tag.
5. Push tag.
6. Use `gh release create` to trigger HACS visibility.
