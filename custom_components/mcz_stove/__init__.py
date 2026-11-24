"""MCZ Pellet Stove (pre-Maestro): MCZ pellet stoves with the older (pre-Maestro) Wi-Fi module, controlled over the local network without cloud."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .api import HottohClient
from .const import DEFAULT_PORT
from .coordinator import HottohCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.NUMBER, Platform.SENSOR, Platform.SWITCH]

type HottohConfigEntry = ConfigEntry[HottohCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: HottohConfigEntry) -> bool:
    client = HottohClient(entry.data[CONF_HOST], entry.data.get(CONF_PORT, DEFAULT_PORT))
    coordinator = HottohCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HottohConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
