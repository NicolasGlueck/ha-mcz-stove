"""Diagnostics download: raw fields of the last poll (useful to map other MCZ models)."""
from __future__ import annotations

from typing import Any

from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant

from . import HottohConfigEntry


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: HottohConfigEntry) -> dict[str, Any]:
    data = entry.runtime_data.data
    return {
        "host": "**REDACTED**",
        "port": entry.data.get(CONF_PORT),
        "firmware": data.firmware,
        "rssi": data.rssi,
        "fields": dict(enumerate(data.fields)),
    }
