"""The comparison as sensors: the cheapest branch, its total, the saving, each chosen branch, the list's size and
when the site's prices were last updated."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import ShoppingEntity, branch_label

CURRENCY = "₪"


def _cheapest(result: dict[str, Any] | None) -> dict[str, Any] | None:
    if not result:
        return None
    return next((b for b in result["branches"] if b["cheapest"]), None)


def _figures(b: dict[str, Any]) -> dict[str, Any]:
    return {"total": b["total"], "whole_list": b["fair"], "found": b["found"], "missing": b["missing"],
            "other_size": b["other_size"], "unsure": b["unsure"], "chain": b["chain"], "branch_id": b["id"],
            "online": b["online"], "cart_url": b["cart_url"]}


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [CheapestBranch(coordinator), CheapestTotal(coordinator), Saving(coordinator),
                                    ListItems(coordinator), PricesUpdated(coordinator)]
    entities += [BranchTotal(coordinator, b) for b in coordinator.branches]
    async_add_entities(entities)


class CheapestBranch(ShoppingEntity, SensorEntity):
    """Where the whole list costs least (what a branch lacks counted at the cheapest other chosen branch)."""
    _attr_translation_key = "cheapest_branch"
    _attr_icon = "mdi:trophy-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "cheapest_branch", "sensor")

    @property
    def native_value(self) -> str | None:
        best = _cheapest(self.result)
        return branch_label(self.hass, best)[:255] if best else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        best = _cheapest(self.result)
        out: dict[str, Any] = {"lines": len(self.coordinator.lines()), "partial": bool(self.result and self.result["partial"])}
        if best:
            out.update(_figures(best))
        return out


class CheapestTotal(ShoppingEntity, SensorEntity):
    _attr_translation_key = "cheapest_total"
    _attr_icon = "mdi:cash"
    _attr_native_unit_of_measurement = CURRENCY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "cheapest_total", "sensor")

    @property
    def native_value(self) -> float | None:
        best = _cheapest(self.result)
        return round(best["fair"], 2) if best else None


class Saving(ShoppingEntity, SensorEntity):
    """How much the cheapest branch saves against the dearest, for the whole list."""
    _attr_translation_key = "saving"
    _attr_icon = "mdi:piggy-bank-outline"
    _attr_native_unit_of_measurement = CURRENCY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "saving", "sensor")

    @property
    def native_value(self) -> float | None:
        result = self.result
        if not result or result["partial"] or len(result["branches"]) < 2:
            return None
        fair = [b["fair"] for b in result["branches"]]
        return round(max(fair) - min(fair), 2)


class ListItems(ShoppingEntity, SensorEntity):
    _attr_translation_key = "list_items"
    _attr_icon = "mdi:format-list-checks"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "list_items", "sensor")

    @property
    def available(self) -> bool:
        return True                              # the list is the household's own: no site needed

    @property
    def native_value(self) -> int:
        return len(self.coordinator.lines())

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        from homeassistant.helpers.dispatcher import async_dispatcher_connect

        from .const import SIGNAL_UPDATED
        self.async_on_remove(async_dispatcher_connect(
            self.hass, f"{SIGNAL_UPDATED}_{self.coordinator.entry.entry_id}", self.async_write_ha_state))


class PricesUpdated(ShoppingEntity, SensorEntity):
    """When the site last imported the chains' prices."""
    _attr_translation_key = "prices_updated"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "prices_updated", "sensor")

    @property
    def native_value(self) -> datetime | None:
        built = self.coordinator.health.get("built_at")
        return dt_util.parse_datetime(built) if built else None


class BranchTotal(ShoppingEntity, SensorEntity):
    """What the list costs in one chosen branch (what it has; the rest is in the attributes)."""
    _attr_translation_key = "branch_total"
    _attr_icon = "mdi:store"
    _attr_native_unit_of_measurement = CURRENCY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator, branch_id: int) -> None:
        super().__init__(coordinator, f"branch_{branch_id}", "sensor")
        self._branch = branch_id
        info = coordinator.branch_info.get(str(branch_id)) or {}
        self._attr_translation_placeholders = {"branch": branch_label(coordinator.hass, info) or str(branch_id)}

    def _mine(self) -> dict[str, Any] | None:
        result = self.result
        return next((b for b in result["branches"] if b["id"] == self._branch), None) if result else None

    @property
    def native_value(self) -> float | None:
        mine = self._mine()
        return round(mine["total"], 2) if mine else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        # the branch's own name too, for dashboards that list the branches (the entity's name carries the device's)
        mine = self._mine()
        label = {"branch": self._attr_translation_placeholders["branch"]}
        return {**label, **_figures(mine), "cheapest": mine["cheapest"]} if mine else label
