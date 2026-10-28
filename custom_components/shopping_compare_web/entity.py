"""What every entity of the integration shares: its device, and showing the last comparison while the site is away."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import plain
from .const import CHAIN_NAMES, DOMAIN, VERSION
from .coordinator import ShoppingCoordinator


def hebrew(hass) -> bool:
    return (hass.config.language or "he").startswith("he")


def branch_label(hass, b: dict[str, Any]) -> str:
    names = CHAIN_NAMES.get(b.get("chain") or "")
    he = hebrew(hass)
    chain = (names[0] if he else names[1]) if names else (b.get("chain_name") if he else b.get("chain_name_en")) or ""
    # plain text also for what an older version kept in the set-up (the names are the chains')
    return plain(f"{chain} · {b.get('name') or ''}", 160).strip(" ·")


class ShoppingEntity(CoordinatorEntity[ShoppingCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: ShoppingCoordinator, key: str, platform: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.entry
        city = coordinator.city or {}
        he = hebrew(coordinator.hass)
        town = plain((city.get("he") if he else city.get("en")) or city.get("he") or "", 80)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        # stable ids for the ready dashboards and automations (a second set-up gets _2)
        self.entity_id = f"{platform}.supermarket_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)}, entry_type=DeviceEntryType.SERVICE,
            name=f"{'מחירי סופר' if he else 'Supermarket prices'} · {town}".strip(" ·"),
            manufacturer="shopping-compare", model="Supermarket price comparison", sw_version=VERSION,
            configuration_url=coordinator.api.base)

    @property
    def available(self) -> bool:
        # the last comparison stays on show while the site can't be reached (binary_sensor.supermarket_site says so)
        return self.coordinator.data is not None

    @property
    def result(self) -> dict[str, Any] | None:
        return (self.coordinator.data or {}).get("result")
