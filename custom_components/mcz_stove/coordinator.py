"""Central polling: one DATR0 per interval, INFR less often."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HottohClient, HottohError
from .const import DOMAIN, INFO_EVERY, MIN_FIELDS, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


@dataclass
class HottohData:
    fields: list[int]
    firmware: str | None
    rssi: int | None


class HottohCoordinator(DataUpdateCoordinator[HottohData]):
    """Polls the stove and hands the fields to all entities."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: HottohClient) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.client = client
        self._polls = 0
        self._firmware: str | None = None
        self._rssi: int | None = None

    async def _async_update_data(self) -> HottohData:
        try:
            fields = await self.client.read_fields()
        except HottohError as err:
            raise UpdateFailed(str(err)) from err
        if len(fields) < MIN_FIELDS:
            raise UpdateFailed(f"only {len(fields)} fields in the response")
        if self._polls % INFO_EVERY == 0:
            try:
                self._firmware, self._rssi = await self.client.read_info()
            except HottohError as err:
                _LOGGER.debug("INFR failed: %s", err)
        self._polls += 1
        return HottohData(fields, self._firmware, self._rssi)
