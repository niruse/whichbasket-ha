"""The integration's own shopping list as a to-do list: Assist, the companion app and automations can add to it
("add milk to the supermarket list"), and the card adds products to it. Not created when the household follows a
to-do list of its own (the options)."""
from __future__ import annotations

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity, TodoListEntityFeature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SIGNAL_UPDATED
from .coordinator import summary
from .entity import ShoppingEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([ShoppingList(entry.runtime_data)])


class ShoppingList(ShoppingEntity, TodoListEntity):
    _attr_translation_key = "list"
    _attr_icon = "mdi:cart-variant"
    _attr_supported_features = (TodoListEntityFeature.CREATE_TODO_ITEM | TodoListEntityFeature.UPDATE_TODO_ITEM
                                | TodoListEntityFeature.DELETE_TODO_ITEM)

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "list", "todo")

    @property
    def available(self) -> bool:
        return True

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(async_dispatcher_connect(
            self.hass, f"{SIGNAL_UPDATED}_{self.coordinator.entry.entry_id}", self._changed))

    @callback
    def _changed(self) -> None:
        self.async_write_ha_state()

    @property
    def todo_items(self) -> list[TodoItem]:
        return [TodoItem(uid=i["uid"], summary=summary(i["name"], i["qty"]),
                         status=TodoItemStatus.COMPLETED if i["done"] else TodoItemStatus.NEEDS_ACTION)
                for i in self.coordinator.items]

    async def async_create_todo_item(self, item: TodoItem) -> None:
        await self.coordinator.async_todo_add(item.summary or "")
        if item.status == TodoItemStatus.COMPLETED:
            added = self.coordinator.items[-1]
            await self.coordinator.async_todo_update(added["uid"], None, True)

    async def async_update_todo_item(self, item: TodoItem) -> None:
        await self.coordinator.async_todo_update(item.uid or "", item.summary,
                                                 None if item.status is None else item.status == TodoItemStatus.COMPLETED)

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        await self.coordinator.async_todo_delete(uids)
