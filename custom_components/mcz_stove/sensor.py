"""Sensors: state, temperatures, power level, fans, Wi-Fi signal."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    REVOLUTIONS_PER_MINUTE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import HottohConfigEntry
from .const import (
    F_EXHAUST_FAN,
    F_EXHAUST_TEMP,
    F_POWER_PERCENT,
    F_ROOM_TEMP,
    F_STATE,
    F_TARGET_TEMP,
    STATE_UNKNOWN,
    STATES,
    fan_fields,
    has_fan,
)
from .coordinator import HottohData
from .entity import HottohEntity


def _level(percent: int) -> float | int:
    """Actual power in % -> level (20 % = level 1)."""
    v = percent / 20
    return int(v) if v.is_integer() else round(v, 1)


@dataclass(frozen=True, kw_only=True)
class HottohSensorDescription(SensorEntityDescription):
    value_fn: Callable[[HottohData], StateType]
    fan: int | None = None  # only created if the stove reports this fan


TEMP = {
    "device_class": SensorDeviceClass.TEMPERATURE,
    "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
    "state_class": SensorStateClass.MEASUREMENT,
    "suggested_display_precision": 1,
}

SENSORS: tuple[HottohSensorDescription, ...] = (
    HottohSensorDescription(
        key="status",
        device_class=SensorDeviceClass.ENUM,
        options=[*STATES.values(), STATE_UNKNOWN],
        value_fn=lambda d: STATES.get(d.fields[F_STATE], STATE_UNKNOWN),
    ),
    HottohSensorDescription(key="room_temperature", value_fn=lambda d: d.fields[F_ROOM_TEMP] / 10, **TEMP),
    HottohSensorDescription(key="exhaust_temperature", value_fn=lambda d: d.fields[F_EXHAUST_TEMP] / 10, **TEMP),
    HottohSensorDescription(
        key="target_temperature",
        value_fn=lambda d: d.fields[F_TARGET_TEMP] / 10,
        entity_registry_enabled_default=False,
        **TEMP,
    ),
    HottohSensorDescription(
        key="power_level",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _level(d.fields[F_POWER_PERCENT]),
    ),
    HottohSensorDescription(
        key="exhaust_fan_speed",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        value_fn=lambda d: d.fields[F_EXHAUST_FAN],
    ),
    *(
        HottohSensorDescription(
            key=f"fan_{nr}",
            state_class=SensorStateClass.MEASUREMENT,
            fan=nr,
            value_fn=lambda d, nr=nr: d.fields[fan_fields(nr)[0]],
        )
        for nr in (1, 2, 3)
    ),
    HottohSensorDescription(
        key="wifi_signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.rssi,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: HottohConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    fields = coordinator.data.fields
    async_add_entities(
        HottohSensor(coordinator, d) for d in SENSORS if d.fan is None or has_fan(fields, d.fan)
    )


class HottohSensor(HottohEntity, SensorEntity):
    entity_description: HottohSensorDescription

    def __init__(self, coordinator, description: HottohSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key == "status":
            return {"code": self.fields[F_STATE]}
        return None
