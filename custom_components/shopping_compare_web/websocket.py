"""The card's websocket commands: one subscription, search, and small changes. Every field is bounded."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .api import SiteBusy, SiteError
from .const import CHAINS, DOMAIN, MAX_KEY, MAX_NAME, MAX_QUERY, SIGNAL_UPDATED

ENTRY = vol.All(str, vol.Length(min=1, max=64))
UID = vol.All(str, vol.Length(min=1, max=80))
KEY = vol.All(str, vol.Length(min=3, max=MAX_KEY))
QUERY = vol.All(str, vol.Length(min=1, max=MAX_QUERY))
CHAIN = vol.In(CHAINS)
QTY = vol.All(vol.Coerce(float), vol.Range(min=0, max=99))


def _item(value: Any) -> int | None:
    """A chain's item id (0: not sold there), or None to go back to the site's own match. Not a boolean."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2**53:
        raise vol.Invalid("not an item")
    return value


ITEM = _item
NAME = vol.All(str, vol.Length(max=MAX_NAME))
PRODUCT = vol.Schema({
    vol.Required("key"): KEY, vol.Required("name"): vol.All(str, vol.Length(min=1, max=MAX_NAME)),
    vol.Optional("name_en"): NAME, vol.Optional("name_ru"): NAME, vol.Optional("barcode"): vol.All(str, vol.Length(max=14)),
    vol.Optional("weighted"): bool, vol.Optional("chains"): vol.All([CHAIN], vol.Length(max=10)),
}, extra=vol.REMOVE_EXTRA)


def _coordinator(hass: HomeAssistant, entry_id: str | None):
    entries = [e for e in hass.config_entries.async_loaded_entries(DOMAIN)]
    if entry_id:
        entries = [e for e in entries if e.entry_id == entry_id]
    if not entries:
        raise HomeAssistantError("not set up")
    return entries[0].runtime_data


def _run(handler):
    """Answer the card, turning the site's and the list's errors into ones it can show."""
    async def run(hass, connection, msg):
        try:
            result = await handler(hass, connection, msg)
        except SiteBusy:
            connection.send_error(msg["id"], "busy", "the site is busy, try again in a minute")
            return
        except SiteError as err:
            connection.send_error(msg["id"], "site", str(err))
            return
        except HomeAssistantError as err:
            connection.send_error(msg["id"], "failed", str(err))
            return
        connection.send_result(msg["id"], result)
    return run


@callback
def async_register(hass: HomeAssistant) -> None:
    for command in (ws_subscribe, ws_search, ws_chain_search, ws_add, ws_qty, ws_remove, ws_choose, ws_compare):
        websocket_api.async_register_command(hass, command)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/subscribe", vol.Optional("entry_id"): ENTRY})
@websocket_api.async_response
async def ws_subscribe(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
    try:
        coordinator = _coordinator(hass, msg.get("entry_id"))
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "not_set_up", str(err))
        return

    @callback
    def push() -> None:
        connection.send_message(websocket_api.event_message(msg["id"], coordinator.snapshot()))

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, f"{SIGNAL_UPDATED}_{coordinator.entry.entry_id}", push)
    connection.send_result(msg["id"])
    push()


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/search", vol.Optional("entry_id"): ENTRY,
                                  vol.Required("query"): QUERY})
@websocket_api.async_response
@_run
async def ws_search(hass, connection, msg):
    return await _coordinator(hass, msg.get("entry_id")).search(msg["query"])


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/chain_search", vol.Optional("entry_id"): ENTRY,
                                  vol.Required("chain"): CHAIN, vol.Required("query"): QUERY})
@websocket_api.async_response
@_run
async def ws_chain_search(hass, connection, msg):
    return await _coordinator(hass, msg.get("entry_id")).chain_search(msg["chain"], msg["query"])


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/add", vol.Optional("entry_id"): ENTRY,
                                  vol.Required("product"): PRODUCT,
                                  vol.Optional("qty", default=1): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=99))})
@websocket_api.async_response
@_run
async def ws_add(hass, connection, msg):
    await _coordinator(hass, msg.get("entry_id")).async_add(msg["product"], msg["qty"])


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/qty", vol.Optional("entry_id"): ENTRY,
                                  vol.Required("uid"): UID, vol.Required("qty"): QTY})
@websocket_api.async_response
@_run
async def ws_qty(hass, connection, msg):
    await _coordinator(hass, msg.get("entry_id")).async_set_qty(msg["uid"], msg["qty"])


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/remove", vol.Optional("entry_id"): ENTRY,
                                  vol.Required("uid"): UID})
@websocket_api.async_response
@_run
async def ws_remove(hass, connection, msg):
    await _coordinator(hass, msg.get("entry_id")).async_remove(msg["uid"])


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/choose", vol.Optional("entry_id"): ENTRY,
                                  vol.Required("key"): KEY, vol.Required("chain"): CHAIN, vol.Required("item"): ITEM})
@websocket_api.async_response
@_run
async def ws_choose(hass, connection, msg):
    await _coordinator(hass, msg.get("entry_id")).async_choose(msg["key"], msg["chain"], msg["item"])


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/compare", vol.Optional("entry_id"): ENTRY})
@websocket_api.async_response
@_run
async def ws_compare(hass, connection, msg):
    await _coordinator(hass, msg.get("entry_id")).async_refresh()
