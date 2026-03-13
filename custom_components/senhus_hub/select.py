from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL_HUB1, CONF_LAYOUT, ALL_LAYOUTS, LAYOUT_DEFAULT, ALL_SLOTS, CONF_ENTITY_ID
from .coordinator import SenhusHubCoordinator

_SLOT_NAMES = {
    "slot_left": "Left panel",
    "slot_right_top": "Right top",
    "slot_right_bottom": "Right bottom",
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SenhusHubCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [SenhusHubLayoutSelect(coordinator)]
    
    # Generate a list of available sensors for the dropdown
    sensor_entities = [""] + [
        state.entity_id 
        for state in hass.states.async_all() 
        if state.domain in ["sensor", "input_number", "number"]
    ]
    # Ensure currently selected entities are in the list even if they are currently unavailable
    for slot in ALL_SLOTS:
        current_entity = coordinator.options.get(slot, {}).get(CONF_ENTITY_ID, "")
        if current_entity and current_entity not in sensor_entities:
            sensor_entities.append(current_entity)
            
    sensor_entities.sort()

    for slot in ALL_SLOTS:
        entities.append(SenhusHubEntitySelect(coordinator, slot, sensor_entities))

    async_add_entities(entities)


class SenhusHubLayoutSelect(SelectEntity):
    """Select entity that updates the Senhus Hub layout and pushes to ESPHome."""

    _attr_has_entity_name = True
    _attr_name = "Display Layout"
    _attr_options = ALL_LAYOUTS
    _attr_icon = "mdi:view-dashboard"

    def __init__(self, coordinator: SenhusHubCoordinator) -> None:
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.entry.entry_id}_layout"
        self._attr_current_option = coordinator.options.get(CONF_LAYOUT, LAYOUT_DEFAULT)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=self.coordinator.entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL_HUB1,
        )

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self.async_write_ha_state()

        new_options = dict(self.coordinator.entry.options)
        new_options[CONF_LAYOUT] = option
        self.coordinator.hass.config_entries.async_update_entry(self.coordinator.entry, options=new_options)


class SenhusHubEntitySelect(SelectEntity):
    """Select entity to choose a Home Assistant sensor for a slot."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SenhusHubCoordinator, slot: str, options: list[str]) -> None:
        self.coordinator = coordinator
        self.slot = slot
        self._attr_name = f"{_SLOT_NAMES[slot]} — Sensor"
        self._attr_options = options
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{slot}_entity_id"
        self._attr_current_option = coordinator.options.get(slot, {}).get(CONF_ENTITY_ID, "")
        self._attr_icon = "mdi:identifier"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=self.coordinator.entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL_HUB1,
        )

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self.async_write_ha_state()

        new_options = dict(self.coordinator.entry.options)
        slot_cfg = dict(new_options.get(self.slot, {}))
        slot_cfg[CONF_ENTITY_ID] = option
        new_options[self.slot] = slot_cfg

        self.coordinator.hass.config_entries.async_update_entry(self.coordinator.entry, options=new_options)
