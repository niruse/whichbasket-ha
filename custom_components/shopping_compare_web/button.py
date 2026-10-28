"""Compare now (the list is compared by itself when it changes, and every morning)."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import ShoppingEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([CompareNow(entry.runtime_data)])


class CompareNow(ShoppingEntity, ButtonEntity):
    _attr_translation_key = "compare_now"
    _attr_icon = "mdi:scale-balance"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "compare_now", "button")

    @property
    def available(self) -> bool:
        return True

    async def async_press(self) -> None:
        await self.coordinator.async_refresh()
