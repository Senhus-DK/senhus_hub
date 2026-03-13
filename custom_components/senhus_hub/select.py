from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL_HUB1, CONF_LAYOUT, ALL_LAYOUTS, LAYOUT_DEFAULT
from .coordinator import SenhusHubCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SenhusHubCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SenhusHubLayoutSelect(coordinator)])


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
        """Update the selected option, save to config entry, and trigger ESPHome update."""
        self._attr_current_option = option
        self.async_write_ha_state()

        new_options = dict(self.coordinator.entry.options)
        new_options[CONF_LAYOUT] = option

        # Updating the entry automatically triggers coordinator.async_options_updated
        self.coordinator.hass.config_entries.async_update_entry(
            self.coordinator.entry, options=new_options
        )
