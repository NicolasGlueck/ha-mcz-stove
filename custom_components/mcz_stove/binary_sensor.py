"""Binary sensors: eco mode, timer program, fault."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HottohConfigEntry
from .const import F_ECO, F_STATE, F_TIMER, PROBLEM_CODES
from .entity import HottohEntity


@dataclass(frozen=True, kw_only=True)
class HottohBinaryDescription(BinarySensorEntityDescription):
    is_on_fn: Callable[[list[int]], bool]


BINARY_SENSORS: tuple[HottohBinaryDescription, ...] = (
    HottohBinaryDescription(key="eco", is_on_fn=lambda f: f[F_ECO] != 0),
    HottohBinaryDescription(key="timer", is_on_fn=lambda f: f[F_TIMER] != 0),
    HottohBinaryDescription(
        key="problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda f: f[F_STATE] in PROBLEM_CODES,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: HottohConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(HottohBinarySensor(entry.runtime_data, d) for d in BINARY_SENSORS)


class HottohBinarySensor(HottohEntity, BinarySensorEntity):
    entity_description: HottohBinaryDescription

    def __init__(self, coordinator, description: HottohBinaryDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        return self.entity_description.is_on_fn(self.fields)
