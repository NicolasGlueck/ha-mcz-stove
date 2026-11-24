"""UI setup: enter the IP address of the stove's Wi-Fi module."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT

from .api import HottohClient, HottohError
from .const import DEFAULT_NAME, DEFAULT_NAME_DE, DEFAULT_PORT, DOMAIN


class HottohConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()
            try:
                await HottohClient(host, port).read_fields()
            except HottohError:
                errors["base"] = "cannot_connect"
            else:
                name = user_input.get(CONF_NAME, "").strip() or DEFAULT_NAME
                return self.async_create_entry(title=name, data={CONF_HOST: host, CONF_PORT: port})
        name = DEFAULT_NAME_DE if self.hass.config.language == "de" else DEFAULT_NAME
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=(user_input or {}).get(CONF_NAME, name)): str,
                vol.Required(CONF_HOST, default=(user_input or {}).get(CONF_HOST, "")): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
