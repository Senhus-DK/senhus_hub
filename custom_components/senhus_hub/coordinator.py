from __future__ import annotations

import logging
from typing import Any

from aioesphomeapi import APIClient, APIConnectionError, ReconnectLogic, TextInfo

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_PASSWORD, EVENT_STATE_CHANGED
from homeassistant.core import HomeAssistant, callback, Event

from .const import (
    ALL_SLOTS,
    CONF_ENTITY_ID,
    CONF_LABEL,
    CONF_LAYOUT,
    CONF_UNIT,
    ESP_ENTITY_LAYOUT,
    ESP_ENTITY_SLOT_VALUE,
    ESP_ENTITY_SLOT_LABEL,
    ESP_ENTITY_SLOT_UNIT,
    LAYOUT_DEFAULT,
)

_LOGGER = logging.getLogger(__name__)

# Map slot identifiers to their 1-based index on the device
_SLOT_INDEX = {slot: i + 1 for i, slot in enumerate(ALL_SLOTS)}


class SenhusHubCoordinator:
    """Manages the connection to a Senhus Hub device and keeps the display in sync."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._client: APIClient | None = None
        self._reconnect: ReconnectLogic | None = None
        self._text_keys: dict[str, int] = {}  # esp entity name -> api key
        self._unsub_ha: Any = None
        self.connected = False

    @property
    def options(self) -> dict:
        return self.entry.options

    # ── Lifecycle ────────────────────────────────────────────────────────────

    async def async_setup(self) -> None:
        host = self.entry.data[CONF_HOST]
        port = self.entry.data[CONF_PORT]
        password = self.entry.data.get(CONF_PASSWORD, "")

        self._client = APIClient(host, port, password)
        self._reconnect = ReconnectLogic(
            client=self._client,
            on_connect=self._on_connect,
            on_disconnect=self._on_disconnect,
        )
        await self._reconnect.start()

    async def async_teardown(self) -> None:
        self._unsub_ha_states()
        if self._reconnect:
            await self._reconnect.stop()
        if self._client:
            await self._client.disconnect()

    async def async_options_updated(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Called when user saves new options. Push updated config to device."""
        await self._push_layout()
        await self._push_labels_and_units()
        await self._push_all_current_values()
        self._subscribe_ha_states()

    # ── ESPHome connection callbacks ─────────────────────────────────────────

    async def _on_connect(self) -> None:
        self.connected = True
        _LOGGER.info("Connected to Senhus Hub at %s", self.entry.data[CONF_HOST])

        entities, _ = await self._client.list_entities_services()
        self._text_keys = {
            e.object_id: e.key for e in entities if isinstance(e, TextInfo)
        }
        self.version = getattr(info, "project_version", None)

        self._client.subscribe_states(lambda _state: None)  # keep connection alive

        await self._push_layout()
        await self._push_labels_and_units()
        await self._push_all_current_values()
        self._subscribe_ha_states()

    async def _on_disconnect(self, expected_disconnect: bool) -> None:
        self.connected = False
        self._unsub_ha_states()
        _LOGGER.debug(
            "Disconnected from Senhus Hub (expected=%s)", expected_disconnect
        )

    # ── HA state tracking ────────────────────────────────────────────────────

    def _subscribe_ha_states(self) -> None:
        self._unsub_ha_states()

        watched = {
            slot_cfg[CONF_ENTITY_ID]
            for slot in ALL_SLOTS
            if (slot_cfg := self.options.get(slot, {})).get(CONF_ENTITY_ID)
        }
        if not watched:
            return

        @callback
        def _on_state_change(event: Event) -> None:
            entity_id = event.data["entity_id"]
            new_state = event.data.get("new_state")
            if new_state is not None:
                self.hass.async_create_task(
                    self._push_sensor_value(entity_id, new_state.state)
                )

        self._unsub_ha = self.hass.bus.async_listen(
            EVENT_STATE_CHANGED,
            _on_state_change,
            event_filter=lambda e: e.data.get("entity_id") in watched,
        )

    def _unsub_ha_states(self) -> None:
        if self._unsub_ha:
            self._unsub_ha()
            self._unsub_ha = None

    # ── Push helpers ─────────────────────────────────────────────────────────

    async def _push_layout(self) -> None:
        layout = self.options.get(CONF_LAYOUT, LAYOUT_DEFAULT)
        await self._set_text(ESP_ENTITY_LAYOUT, layout)

    async def _push_labels_and_units(self) -> None:
        if not self.connected:
            return
        for slot, num in _SLOT_INDEX.items():
            cfg = self.options.get(slot, {})
            await self._set_text(ESP_ENTITY_SLOT_LABEL.format(n=num), cfg.get(CONF_LABEL, ""))
            await self._set_text(ESP_ENTITY_SLOT_UNIT.format(n=num), cfg.get(CONF_UNIT, ""))

    async def _push_all_current_values(self) -> None:
        for slot in ALL_SLOTS:
            cfg = self.options.get(slot, {})
            entity_id = cfg.get(CONF_ENTITY_ID)
            if entity_id:
                state = self.hass.states.get(entity_id)
                if state:
                    await self._push_sensor_value(entity_id, state.state)

    async def _push_sensor_value(self, entity_id: str, value: str) -> None:
        for slot, num in _SLOT_INDEX.items():
            if self.options.get(slot, {}).get(CONF_ENTITY_ID) == entity_id:
                await self._set_text(ESP_ENTITY_SLOT_VALUE.format(n=num), value)

    async def _set_text(self, object_id: str, value: str) -> None:
        if not self.connected:
            return
        key = self._text_keys.get(object_id)
        if key is None:
            _LOGGER.debug("ESP text entity '%s' not found on device", object_id)
            return
        try:
            await self._client.text_command(key, value)
        except APIConnectionError as err:
            _LOGGER.warning("Failed to write '%s' to device: %s", object_id, err)
