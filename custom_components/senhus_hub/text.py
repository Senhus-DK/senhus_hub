from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN, MANUFACTURER, MODEL_HUB1, ALL_SLOTS,
    CONF_LABEL, CONF_UNIT
)
from .coordinator import SenhusHubCoordinator

_SLOT_NAMES = {
    "slot_left": "Left panel",
    "slot_right_top": "Right top",
    "slot_right_bottom": "Right bottom",
}

_SLOT_DEFAULTS = {
    "slot_left":         {CONF_LABEL: "Price", CONF_UNIT: ""},
    "slot_right_top":    {CONF_LABEL: "Solar", CONF_UNIT: "W"},
    "slot_right_bottom": {CONF_LABEL: "Grid",  CONF_UNIT: "W"},
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SenhusHubCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    
    for slot in ALL_SLOTS:
        entities.append(SenhusHubTextEntity(coordinator, slot, CONF_LABEL, f"{_SLOT_NAMES[slot]} — Label", _SLOT_DEFAULTS[slot][CONF_LABEL]))
        entities.append(SenhusHubTextEntity(coordinator, slot, CONF_UNIT, f"{_SLOT_NAMES[slot]} — Unit", _SLOT_DEFAULTS[slot][CONF_UNIT]))

    async_add_entities(entities)


class SenhusHubTextEntity(TextEntity):
    """Text entity that updates the Senhus Hub configuration and pushes to ESPHome."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SenhusHubCoordinator, slot: str, conf_key: str, name: str, default_val: str) -> None:
        self.coordinator = coordinator
        self.slot = slot
        self.conf_key = conf_key
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{slot}_{conf_key}"
        self._attr_native_value = coordinator.options.get(slot, {}).get(conf_key, default_val)
        self._attr_icon = "mdi:form-textbox"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=self.coordinator.entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL_HUB1,
        )

    async def async_set_value(self, value: str) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()

        new_options = dict(self.coordinator.entry.options)
        slot_cfg = dict(new_options.get(self.slot, {}))
        slot_cfg[self.conf_key] = value
        new_options[self.slot] = slot_cfg

        self.coordinator.hass.config_entries.async_update_entry(self.coordinator.entry, options=new_options)
