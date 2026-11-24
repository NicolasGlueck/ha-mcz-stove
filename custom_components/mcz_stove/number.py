"""Numbers: power level and fan speeds.

Quick successive changes are collected: the entity shows the requested value immediately,
the command is sent only after DEBOUNCE_SECONDS without further changes, and only with the last value.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
import time

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_call_later

from . import HottohConfigEntry
from .api import HottohClient, HottohError
from .const import (
    DEBOUNCE_SECONDS,
    F_LEVEL_MAX,
    F_LEVEL_MIN,
    F_LEVEL_SET,
    PENDING_TIMEOUT,
    fan_fields,
    has_fan,
)
from .entity import HottohEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class HottohNumberDescription(NumberEntityDescription):
    value_idx: int
    min_fn: Callable[[list[int]], int]
    max_fn: Callable[[list[int]], int]
    write_fn: Callable[[HottohClient, int, list[int]], Awaitable[None]]
    fan: int | None = None


def _fan(nr: int) -> HottohNumberDescription:
    _, setpoint, maximum = fan_fields(nr)
    return HottohNumberDescription(
        key=f"fan_{nr}_set",
        fan=nr,
        value_idx=setpoint,
        min_fn=lambda f: 0,
        max_fn=lambda f, i=maximum: f[i],
        write_fn=lambda c, v, f, nr=nr: c.set_fan(nr, v, f),
    )


NUMBERS: tuple[HottohNumberDescription, ...] = (
    HottohNumberDescription(
        key="level",
        value_idx=F_LEVEL_SET,
        min_fn=lambda f: f[F_LEVEL_MIN],
        max_fn=lambda f: f[F_LEVEL_MAX],
        write_fn=lambda c, v, f: c.set_level(v, f),
    ),
    _fan(1),
    _fan(2),
    _fan(3),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: HottohConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    fields = coordinator.data.fields
    async_add_entities(
        HottohNumber(coordinator, d) for d in NUMBERS if d.fan is None or has_fan(fields, d.fan)
    )


class HottohNumber(HottohEntity, NumberEntity):
    entity_description: HottohNumberDescription
    _attr_native_step = 1
    _attr_mode = NumberMode.AUTO

    def __init__(self, coordinator, description: HottohNumberDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._pending: int | None = None
        self._pending_since = 0.0
        self._timer: CALLBACK_TYPE | None = None
        self._sending = False

    @property
    def native_value(self) -> float:
        if self._pending is not None:
            return self._pending
        return self.fields[self.entity_description.value_idx]

    @property
    def native_min_value(self) -> float:
        return self.entity_description.min_fn(self.fields)

    @property
    def native_max_value(self) -> float:
        return self.entity_description.max_fn(self.fields)

    async def async_set_native_value(self, value: float) -> None:
        self._pending, self._pending_since = int(value), time.monotonic()
        self.async_write_ha_state()
        if self._timer:
            self._timer()
        self._timer = async_call_later(self.hass, DEBOUNCE_SECONDS, self._send)

    async def _send(self, _now=None) -> None:
        self._timer = None
        target = self._pending
        if target is None:
            return
        self._sending = True
        try:
            await self.entity_description.write_fn(self.coordinator.client, target, self.fields)
        except HottohError as err:
            _LOGGER.warning("%s: could not set %s: %s", self.entity_id, target, err)
            if self._pending == target:
                self._pending = None
            self.async_write_ha_state()
            return
        finally:
            self._sending = False
        await asyncio.sleep(1.5)  # the stove does not report the new value in DATR0 right away
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        if (
            self._pending is not None
            and self._timer is None
            and not self._sending
            and (
                self.fields[self.entity_description.value_idx] == self._pending
                or time.monotonic() - self._pending_since > PENDING_TIMEOUT
            )
        ):
            self._pending = None
        super()._handle_coordinator_update()

    async def async_will_remove_from_hass(self) -> None:
        if self._timer:
            self._timer()
            self._timer = None
