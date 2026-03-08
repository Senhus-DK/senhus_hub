from __future__ import annotations

import logging

import aiohttp

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL_HUB1,
    GITHUB_API_RELEASES,
    FIRMWARE_ASSET_NAME,
)
from .coordinator import SenhusHubCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SenhusHubCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SenhusHubUpdateEntity(coordinator, entry)])


class SenhusHubUpdateEntity(UpdateEntity):
    """Represents the firmware update entity for a Senhus Hub device."""

    _attr_has_entity_name = True
    _attr_name = "Firmware"
    _attr_supported_features = (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
    )

    def __init__(self, coordinator: SenhusHubCoordinator, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_firmware"
        self._latest_version: str | None = None
        self._installed_version: str | None = None
        self._download_url: str | None = None
        self._attr_in_progress: bool = False

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL_HUB1,
        )

    @property
    def installed_version(self) -> str | None:
        return self._installed_version

    @property
    def latest_version(self) -> str | None:
        return self._latest_version

    async def async_update(self) -> None:
        """Check GitHub releases for a newer firmware version."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(GITHUB_API_RELEASES) as resp:
                if resp.status != 200:
                    _LOGGER.warning("GitHub API returned %s", resp.status)
                    return
                data = await resp.json()

            self._latest_version = data.get("tag_name", "").lstrip("v")
            self._download_url = next(
                (
                    asset["browser_download_url"]
                    for asset in data.get("assets", [])
                    if asset["name"] == FIRMWARE_ASSET_NAME
                ),
                None,
            )
        except aiohttp.ClientError as err:
            _LOGGER.warning("Failed to check for firmware updates: %s", err)

    async def async_install(self, version: str | None, backup: bool, **kwargs) -> None:
        """Download firmware from GitHub and OTA-flash the device via HTTP."""
        if not self._download_url:
            _LOGGER.error("No firmware download URL — run an update check first")
            return

        self._attr_in_progress = True
        self.async_write_ha_state()

        host = self._coordinator.entry.data["host"]
        ota_url = f"http://{host}/update"

        try:
            session = async_get_clientsession(self.hass)

            async with session.get(self._download_url) as resp:
                resp.raise_for_status()
                firmware = await resp.read()

            form = aiohttp.FormData()
            form.add_field("update", firmware, filename="firmware.bin", content_type="application/octet-stream")

            async with session.post(ota_url, data=form, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"OTA endpoint returned {resp.status}: {text}")

            _LOGGER.info("OTA firmware update completed successfully")
            self._installed_version = self._latest_version

        except Exception as err:
            _LOGGER.error("OTA update failed: %s", err)
        finally:
            self._attr_in_progress = False
            self.async_write_ha_state()
