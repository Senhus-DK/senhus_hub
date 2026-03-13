from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from aioesphomeapi import APIClient, APIConnectionError, InvalidAuthAPIError

from homeassistant.components import zeroconf
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    DEFAULT_PORT,
    PROJECT_NAME_PREFIX,
    ALL_SLOTS,
    ALL_LAYOUTS,
    SLOT_LEFT,
    SLOT_RIGHT_TOP,
    SLOT_RIGHT_BOTTOM,
    CONF_ENTITY_ID,
    CONF_LABEL,
    CONF_UNIT,
    CONF_CARD_TYPE,
    CONF_LAYOUT,
    CARD_CUSTOM,
    LAYOUT_DEFAULT,
)

_LOGGER = logging.getLogger(__name__)

_SLOT_DEFAULTS = {
    SLOT_LEFT:         {CONF_LABEL: "Price", CONF_UNIT: ""},
    SLOT_RIGHT_TOP:    {CONF_LABEL: "Solar", CONF_UNIT: "W"},
    SLOT_RIGHT_BOTTOM: {CONF_LABEL: "Grid",  CONF_UNIT: "W"},
}


def _default_options() -> dict:
    return {
        CONF_CARD_TYPE: CARD_CUSTOM,
        CONF_LAYOUT: LAYOUT_DEFAULT,
        SLOT_LEFT:         {CONF_ENTITY_ID: "", **_SLOT_DEFAULTS[SLOT_LEFT]},
        SLOT_RIGHT_TOP:    {CONF_ENTITY_ID: "", **_SLOT_DEFAULTS[SLOT_RIGHT_TOP]},
        SLOT_RIGHT_BOTTOM: {CONF_ENTITY_ID: "", **_SLOT_DEFAULTS[SLOT_RIGHT_BOTTOM]},
    }


async def _try_connect(host: str, port: int, password: str) -> tuple[str | None, str | None]:
    """Attempt ESPHome API connection. Returns (error_key, device_name)."""
    client = APIClient(host, port, password)
    try:
        await client.connect(login=True)
        info = await client.device_info()
        await client.disconnect()
    except InvalidAuthAPIError:
        return "invalid_auth", None
    except APIConnectionError:
        return "cannot_connect", None
    except Exception:
        _LOGGER.exception("Unexpected error connecting to %s", host)
        return "unknown", None

    if not (info.project_name and info.project_name.startswith(PROJECT_NAME_PREFIX)):
        return "not_senhus_hub", None

    return None, info.name


class SenhusHubConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle config flow for Senhus Hub."""

    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._port: int = DEFAULT_PORT
        self._password: str = ""
        self._device_name: str | None = None
        self._zeroconf_props: dict = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port = user_input.get(CONF_PORT, DEFAULT_PORT)
            self._password = user_input.get(CONF_PASSWORD, "")

            error, name = await _try_connect(self._host, self._port, self._password)
            if error:
                errors["base"] = error
            else:
                self._device_name = name
                return self._create_entry()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): selector.TextSelector(),
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1, max=65535, mode=selector.NumberSelectorMode.BOX
                    )
                ),
                vol.Optional(CONF_PASSWORD, default=""): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
            }),
            errors=errors,
        )

    async def async_step_zeroconf(self, discovery_info: zeroconf.ZeroconfServiceInfo) -> FlowResult:
        self._host = discovery_info.host
        self._port = discovery_info.port or DEFAULT_PORT
        props = discovery_info.properties

        project_name = props.get("project_name") or props.get(b"project_name") or ""
        if isinstance(project_name, bytes):
            project_name = project_name.decode("utf-8", errors="ignore")
        if not project_name.startswith(PROJECT_NAME_PREFIX):
            return self.async_abort(reason="not_senhus_hub")

        await self.async_set_unique_id(props.get("mac", self._host))
        self._abort_if_unique_id_configured(updates={CONF_HOST: self._host})

        error, name = await _try_connect(self._host, self._port, "")
        if error:
            return self.async_abort(reason=error)

        self._device_name = name
        self._zeroconf_props = {"friendly_name": props.get("friendly_name", name)}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self._create_entry()

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={
                "name": self._zeroconf_props.get("friendly_name", self._device_name),
                "host": self._host,
            },
        )

    def _create_entry(self) -> FlowResult:
        return self.async_create_entry(
            title=self._device_name or self._host,
            data={
                CONF_HOST: self._host,
                CONF_PORT: self._port,
                CONF_PASSWORD: self._password,
            },
            options=_default_options(),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SenhusHubOptionsFlow(config_entry)


class SenhusHubOptionsFlow(OptionsFlow):
    """Handle options flow — configure display slots and layout."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        options = dict(self.config_entry.options)

        if user_input is not None:
            options[CONF_LAYOUT] = user_input[CONF_LAYOUT]
            for slot in ALL_SLOTS:
                options[slot] = {
                    CONF_ENTITY_ID: user_input.get(f"{slot}_entity") or "",
                    CONF_LABEL:     user_input.get(f"{slot}_label", _SLOT_DEFAULTS[slot][CONF_LABEL]),
                    CONF_UNIT:      user_input.get(f"{slot}_unit",  _SLOT_DEFAULTS[slot][CONF_UNIT]),
                }
            return self.async_create_entry(title="", data=options)

        def _slot_schema(slot: str) -> dict:
            cfg = options.get(slot, {})
            return {
                vol.Optional(
                    f"{slot}_entity",
                    description={"suggested_value": cfg.get(CONF_ENTITY_ID) or None},
                ): selector.EntitySelector(),
                vol.Optional(
                    f"{slot}_label",
                    default=cfg.get(CONF_LABEL, _SLOT_DEFAULTS[slot][CONF_LABEL]),
                ): selector.TextSelector(),
                vol.Optional(
                    f"{slot}_unit",
                    default=cfg.get(CONF_UNIT, _SLOT_DEFAULTS[slot][CONF_UNIT]),
                ): selector.TextSelector(),
            }

        schema: dict = {
            vol.Required(
                CONF_LAYOUT,
                default=options.get(CONF_LAYOUT, LAYOUT_DEFAULT),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=ALL_LAYOUTS,
                    translation_key="layout",
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
        }
        for slot in ALL_SLOTS:
            schema.update(_slot_schema(slot))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )
