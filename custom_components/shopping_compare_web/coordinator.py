"""The household's list, its own picks per chain, and the comparison the website works out for them.

The list is either this integration's own to-do list or another to-do list in Home Assistant that the household
already uses (the shopping list Assist adds to, say), followed as it is. Each line goes to the website as a product
key (a product chosen from the search) or as its text ("t:חלב"), and the site matches it in each chain. A pick the
household makes for a line in one chain applies to it at once (it goes with every comparison) and is also sent to
the site as a suggestion for its admin.
"""
from __future__ import annotations

import logging
import random
import re
import uuid
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_state_change_event, async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import SiteAPI, SiteBusy, SiteError, clean_product, plain
from .const import (
    CHAINS,
    CONF_BRANCH_INFO,
    CONF_BRANCHES,
    CONF_CITY,
    CONF_LIST,
    CONF_SITE,
    DEFAULT_SITE,
    DOMAIN,
    MAX_BRANCHES,
    MAX_ITEMS,
    MAX_KEY,
    MAX_NAME,
    OWN_LIST,
    SIGNAL_UPDATED,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)
PARTIAL_RETRIES = 5            # a big list is matched over a few comparisons (the site's budget per request)
PARTIAL_WAIT = 20
_QTY_AFTER = re.compile(r"^(.*?)\s*[×xX*]\s*(\d+(?:\.\d+)?)\s*$")       # "חלב ×2", "milk x2"
_QTY_BEFORE = re.compile(r"^(\d+(?:\.\d+)?)\s+(\S.*)$")                 # "2 חלב" (not "2 ליטר חלב")
_SIZE_WORDS = {"ליטר", "ליטרים", "גרם", "גר", "קג", 'ק"ג', "קילו", "מל", 'מ"ל', "l", "kg", "g", "ml", "liter", "litre"}


def _qty(value: Any) -> float:
    try:
        return round(min(max(float(value), 0.05), 99.0), 3)
    except (TypeError, ValueError):
        return 1.0


def parse_summary(text: str) -> tuple[str, float]:
    """A to-do item's text as (name, how many): "חלב ×2" and "2 חלב" are two of חלב."""
    t = " ".join(str(text or "").split())[:MAX_NAME]
    m = _QTY_AFTER.match(t)
    if m and m.group(1):
        return m.group(1), _qty(m.group(2))
    m = _QTY_BEFORE.match(t)
    if m and m.group(2).split()[0].lower() not in _SIZE_WORDS:
        return m.group(2), _qty(m.group(1))
    return t, 1.0


def summary(name: str, qty: float) -> str:
    return name if qty == 1 else f"{name} ×{qty:g}"


def _norm(text: str) -> str:
    return " ".join(str(text or "").split()).casefold()


def _clean_item(x: Any) -> dict[str, Any] | None:
    """A stored list line, field by field."""
    if not isinstance(x, dict) or not isinstance(x.get("key"), str) or not isinstance(x.get("name"), str):
        return None
    if x["key"][:2] not in ("b:", "w:", "c:", "t:"):
        return None
    return {"uid": str(x.get("uid") or uuid.uuid4().hex)[:40], "key": x["key"][:MAX_KEY], "name": plain(x["name"]),
            "name_en": plain(x.get("name_en")), "name_ru": plain(x.get("name_ru")),
            "qty": _qty(x.get("qty", 1)), "weighted": x.get("weighted") is True, "done": x.get("done") is True,
            "chains": [c for c in x.get("chains") or [] if c in CHAINS] if isinstance(x.get("chains"), list) else []}


class ShoppingCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """``data`` = {"result": the site's last comparison (checked) or None}."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=timedelta(hours=6),
                         request_refresh_debouncer=Debouncer(hass, _LOGGER, cooldown=4, immediate=False))
        opts = {**entry.data, **entry.options}
        self.entry = entry
        self.api = SiteAPI(async_get_clientsession(hass), opts.get(CONF_SITE) or DEFAULT_SITE)
        self.branches: list[int] = [int(b) for b in opts.get(CONF_BRANCHES, [])][:MAX_BRANCHES]
        self.branch_info: dict[str, dict[str, Any]] = dict(opts.get(CONF_BRANCH_INFO) or {})
        self.city: dict[str, Any] = dict(opts.get(CONF_CITY) or {})
        self.list_source: str = opts.get(CONF_LIST) or OWN_LIST
        self._store: Store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        self.items: list[dict[str, Any]] = []             # this integration's own list
        self.choices: dict[str, dict[str, int]] = {}      # list key -> chain -> item (0: not sold there)
        self.products: dict[str, dict[str, Any]] = {}     # a followed list's item text -> the product meant by it
        self.followed: list[dict[str, Any]] = []          # the followed list's open items, as last read
        self.health: dict[str, Any] = {}
        self.error: str | None = None
        self.last_compare: str | None = None
        self._tries = 0

    # ---- storage -------------------------------------------------------------------------------------
    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.items = [i for i in (_clean_item(x) for x in data.get("items") or []) if i][:MAX_ITEMS * 2]
        self.choices = {k[:MAX_KEY]: {c: v for c, v in picks.items() if c in CHAINS and isinstance(v, int) and v >= 0}
                        for k, picks in (data.get("choices") or {}).items() if isinstance(picks, dict)}
        self.products = {k: p for k, p in ((t, clean_product(p)) for t, p in (data.get("products") or {}).items()) if p}

    async def _save(self) -> None:
        await self._store.async_save({"items": self.items, "choices": self.choices, "products": self.products})

    @callback
    def changed(self) -> None:
        """The card's subscription redraws (the list, a pick, a new comparison)."""
        async_dispatcher_send(self.hass, f"{SIGNAL_UPDATED}_{self.entry.entry_id}")

    @callback
    def async_update_listeners(self) -> None:
        super().async_update_listeners()
        self.changed()

    # ---- start and stop ------------------------------------------------------------------------------
    @callback
    def start(self) -> None:
        """Compare again each morning, after the site's nightly import (a random minute, so homes spread out), and
        whenever a followed list changes."""
        minute, second = random.randint(30, 59), random.randint(0, 59)
        self.entry.async_on_unload(async_track_time_change(self.hass, self._morning, hour=7, minute=minute,
                                                           second=second))
        if self.list_source != OWN_LIST:
            self.entry.async_on_unload(async_track_state_change_event(self.hass, [self.list_source], self._followed_changed))

    async def _morning(self, _now=None) -> None:
        await self.async_request_refresh()

    @callback
    def _followed_changed(self, _event: Event) -> None:
        self.hass.async_create_task(self._reread_and_compare())

    async def _reread_and_compare(self) -> None:
        try:
            await self._read_followed()
        except HomeAssistantError as err:
            self.error = f"list: {err}"
        self.changed()
        await self.async_request_refresh()

    # ---- the list ------------------------------------------------------------------------------------
    @property
    def own(self) -> bool:
        return self.list_source == OWN_LIST

    async def _read_followed(self) -> None:
        """The followed list's open items. Its text is the line; a product the household chose for that text (from
        the card) stands in for it."""
        try:
            resp = await self.hass.services.async_call("todo", "get_items", {"entity_id": self.list_source,
                                                                             "status": ["needs_action"]},
                                                       blocking=True, return_response=True)
        except Exception as err:  # noqa: BLE001 - the list was removed, or can't be read
            raise HomeAssistantError(f"can't read {self.list_source}: {type(err).__name__}") from None
        items = ((resp or {}).get(self.list_source) or {}).get("items") or []
        out = []
        for it in items[:MAX_ITEMS]:
            if not isinstance(it, dict) or not isinstance(it.get("summary"), str):
                continue
            name, qty = parse_summary(it["summary"])
            if not name:
                continue
            prod = self.products.get(_norm(name))
            out.append({"uid": str(it.get("uid") or "")[:80], "key": prod["key"] if prod else f"t:{name}"[:MAX_KEY],
                        "name": prod["name"] if prod else name, "name_en": prod["name_en"] if prod else "",
                        "name_ru": prod["name_ru"] if prod else "", "qty": qty,
                        "weighted": bool(prod and prod["weighted"]), "chains": prod["chains"] if prod else [],
                        "text": name, "done": False})
        self.followed = out

    def lines(self) -> list[dict[str, Any]]:
        """The open lines, one per product (the same product twice adds up)."""
        source = [i for i in self.items if not i["done"]] if self.own else self.followed
        merged: dict[str, dict[str, Any]] = {}
        for line in source:
            if line["key"] in merged:
                merged[line["key"]]["qty"] = _qty(merged[line["key"]]["qty"] + line["qty"])
            else:
                merged[line["key"]] = dict(line)
        return list(merged.values())[:MAX_ITEMS]

    async def async_add(self, product: dict[str, Any], qty: float = 1) -> None:
        """A product from the search (or free text: key t:<text>), added to the list."""
        product = clean_product(product)
        if product is None:
            raise HomeAssistantError("not a product")
        qty = _qty(qty)
        if self.own:
            line = next((i for i in self.items if i["key"] == product["key"] and not i["done"]), None)
            if line:
                line["qty"] = _qty(line["qty"] + qty)
            else:
                if len([i for i in self.items if not i["done"]]) >= MAX_ITEMS:
                    raise HomeAssistantError("the list is full")
                self.items.append({"uid": uuid.uuid4().hex, "key": product["key"], "name": product["name"],
                                   "name_en": product["name_en"], "name_ru": product["name_ru"], "qty": qty,
                                   "weighted": product["weighted"], "done": False, "chains": product["chains"]})
            await self._save()
            self.changed()
        else:
            if not product["key"].startswith("t:"):
                self.products[_norm(product["name"])] = product
                await self._save()
            await self.hass.services.async_call("todo", "add_item", {"entity_id": self.list_source,
                                                                     "item": summary(product["name"], qty)},
                                                blocking=True)
            await self._read_followed()
            self.changed()
        await self.async_request_refresh()

    async def async_set_qty(self, uid: str, qty: float) -> None:
        if self.own:
            line = next((i for i in self.items if i["uid"] == uid), None)
            if line is None:
                raise HomeAssistantError("not on the list")
            if qty <= 0:
                self.items.remove(line)
            else:
                line["qty"] = _qty(qty)
            await self._save()
            self.changed()
        else:
            line = next((i for i in self.followed if i["uid"] == uid), None)
            if line is None:
                raise HomeAssistantError("not on the list")
            if qty <= 0:
                await self.hass.services.async_call("todo", "remove_item", {"entity_id": self.list_source,
                                                                            "item": uid}, blocking=True)
            else:
                await self.hass.services.async_call("todo", "update_item", {
                    "entity_id": self.list_source, "item": uid, "rename": summary(line["text"], _qty(qty))},
                    blocking=True)
            await self._read_followed()
            self.changed()
        await self.async_request_refresh()

    async def async_remove(self, uid: str) -> None:
        await self.async_set_qty(uid, 0)

    # the own list as a to-do entity (todo.py)
    async def async_todo_add(self, text: str) -> None:
        name, qty = parse_summary(text)
        if not name:
            raise HomeAssistantError("nothing to add")
        await self.async_add({"key": f"t:{name}"[:MAX_KEY], "name": name}, qty)

    async def async_todo_update(self, uid: str, text: str | None, done: bool | None) -> None:
        line = next((i for i in self.items if i["uid"] == uid), None)
        if line is None:
            raise HomeAssistantError("not on the list")
        if text is not None:
            name, qty = parse_summary(text)
            if name and _norm(name) != _norm(line["name"]):
                # renamed by hand: now the text is the line (the site matches it by name)
                line.update({"key": f"t:{name}"[:MAX_KEY], "name": name, "name_en": "", "name_ru": "", "chains": [],
                             "weighted": False})
            line["qty"] = qty
        if done is not None:
            line["done"] = done
        await self._save()
        self.changed()
        await self.async_request_refresh()

    async def async_todo_delete(self, uids: list[str]) -> None:
        self.items = [i for i in self.items if i["uid"] not in set(uids)]
        await self._save()
        self.changed()
        await self.async_request_refresh()

    # ---- picks per chain -----------------------------------------------------------------------------
    async def async_choose(self, key: str, chain: str, item: int | None) -> None:
        """The household's own pick for a line in one chain (0: not sold there; None: back to the site's own
        match). It applies at once; a pick is also suggested to the site, where the site knows the line."""
        if chain not in CHAINS or not isinstance(key, str) or not key:
            raise HomeAssistantError("invalid choice")
        picks = self.choices.setdefault(key[:MAX_KEY], {})
        if item is None:
            picks.pop(chain, None)
            if not picks:
                self.choices.pop(key[:MAX_KEY], None)
        else:
            picks[chain] = int(item)
        await self._save()
        self.changed()
        result = (self.data or {}).get("result") or {}
        line = next((ln for ln in result.get("lines", []) if ln["key"] == key), None)
        if item is not None and (line is None or line["votable"]):
            try:
                await self.api.suggest_match(key, chain, int(item))
            except SiteError as err:            # the household's own pick still applies
                _LOGGER.debug("suggestion not sent: %s", err)
        await self.async_refresh()

    # ---- the site ------------------------------------------------------------------------------------
    def chain_branches(self, chain: str) -> list[int]:
        return [b for b in self.branches if (self.branch_info.get(str(b)) or {}).get("chain") == chain]

    async def search(self, query: str) -> list[dict[str, Any]]:
        return await self.api.search(query, self.branches)

    async def chain_search(self, chain: str, query: str) -> list[dict[str, Any]]:
        return await self.api.chain_search(chain, query, self.chain_branches(chain))

    async def _async_update_data(self) -> dict[str, Any]:
        if not self.own:
            try:
                await self._read_followed()
            except HomeAssistantError as err:
                self.error = str(err)
                raise UpdateFailed(str(err)) from None
        lines = self.lines()
        try:
            self.health = await self.api.health()
            result = None
            if lines and self.branches:
                result = await self.api.compare(self.branches, [
                    {"key": ln["key"], "name": ln["name"], "qty": ln["qty"], "choice": self.choices.get(ln["key"], {})}
                    for ln in lines])
        except SiteBusy as err:
            self.error = "busy"
            raise UpdateFailed(f"the site is busy: {err}") from None
        except SiteError as err:
            self.error = "site"
            raise UpdateFailed(str(err)) from None
        self.error = None
        self.last_compare = dt_util.utcnow().isoformat()
        # lines over the site's matching budget come back pending: compare again shortly for the rest
        if result and result["partial"] and self._tries < PARTIAL_RETRIES:
            self._tries += 1
            self.entry.async_on_unload(async_call_later(self.hass, PARTIAL_WAIT, self._again))
        else:
            self._tries = 0
        return {"result": result}

    async def _again(self, _now=None) -> None:
        await self.async_request_refresh()

    # ---- what the card draws ---------------------------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        result = (self.data or {}).get("result")
        return {
            "title": self.entry.title, "city": self.city, "site": self.api.base,
            "branches": [{"id": b, **{k: (self.branch_info.get(str(b)) or {}).get(k)
                                      for k in ("chain", "chain_name", "chain_name_en", "name", "online")}}
                         for b in self.branches],
            "own": self.own, "list_source": self.list_source,
            "lines": [{k: ln.get(k) for k in ("uid", "key", "name", "name_en", "name_ru", "qty", "weighted", "chains")}
                      for ln in self.lines()],
            "choices": self.choices, "result": result,
            "updated": self.health.get("built_at"), "matches": self.health.get("matches", "admin"),
            "last_compare": self.last_compare, "error": self.error,
        }
