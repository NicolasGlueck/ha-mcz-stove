"""Main switch: stove on/off (DATW parameter 0)."""
from __future__ import annotations

import time
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HottohConfigEntry
from .api import HottohError
from .const import F_POWER, PENDING_TIMEOUT
from .entity import HottohEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: HottohConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([HottohPowerSwitch(entry.runtime_data)])


class HottohPowerSwitch(HottohEntity, SwitchEntity):
    _attr_name = None  # main feature: named after the device

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "power")
        self._assumed: bool | None = None
        self._assumed_since = 0.0

    @property
    def is_on(self) -> bool:
        if self._assumed is not None:
            return self._assumed
        return self.fields[F_POWER] != 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)

    async def _set(self, on: bool) -> None:
        try:
            await self.coordinator.client.set_power(on)
        except HottohError as err:
            raise HomeAssistantError(f"Could not switch the stove: {err}") from err
        # show the requested state until the stove reports it
        self._assumed, self._assumed_since = on, time.monotonic()
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        if self._assumed is not None and (
            (self.fields[F_POWER] != 0) == self._assumed
            or time.monotonic() - self._assumed_since > PENDING_TIMEOUT
        ):
            self._assumed = None
        super()._handle_coordinator_update()
