"""Base class of all entities: one device per stove."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HottohCoordinator


class HottohEntity(CoordinatorEntity[HottohCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: HottohCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="MCZ",
            model="Pellet stove (pre-Maestro Wi-Fi module)",
            sw_version=coordinator.data.firmware,
        )

    @property
    def fields(self) -> list[int]:
        return self.coordinator.data.fields
