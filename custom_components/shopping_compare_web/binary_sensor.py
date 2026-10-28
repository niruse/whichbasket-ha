"""Whether the last comparison reached the site (the sensors keep the last one meanwhile)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import ShoppingEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([SiteReachable(entry.runtime_data)])


class SiteReachable(ShoppingEntity, BinarySensorEntity):
    _attr_translation_key = "site"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "site", "binary_sensor")

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"site": self.coordinator.api.base, "error": self.coordinator.error,
                "last_compare": self.coordinator.last_compare}
