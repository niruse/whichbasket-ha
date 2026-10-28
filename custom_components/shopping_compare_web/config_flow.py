"""Set up: the town, the branches to compare, and which to-do list is the shopping list."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .api import SiteAPI, SiteError, plain, site_url
from .const import (
    CONF_BRANCH_INFO,
    CONF_BRANCHES,
    CONF_CITY,
    CONF_LIST,
    CONF_SITE,
    DEFAULT_SITE,
    DOMAIN,
    MAX_BRANCHES,
    OWN_LIST,
)

FOLLOW = "follow"


def _he(hass: HomeAssistant) -> bool:
    return (hass.config.language or "he").startswith("he")


def city_label(hass: HomeAssistant, c: dict[str, Any]) -> str:
    # the set-up's texts are markdown: a name stays plain text
    return plain(c["he"] if _he(hass) or not c.get("en") else c["en"], 80)


def branch_label(hass: HomeAssistant, b: dict[str, Any]) -> str:
    chain = b.get("chain_name") if _he(hass) else (b.get("chain_name_en") or b.get("chain_name"))
    return plain(f"{chain} · {b.get('name') or ''}", 160).strip(" ·")


class _Steps:
    """The steps the first set-up and the options share: town, branches, list."""

    hass: HomeAssistant

    def _init_state(self) -> None:
        self._site = DEFAULT_SITE
        self._cities: list[dict[str, Any]] = []
        self._city: dict[str, Any] | None = None
        self._branches: list[dict[str, Any]] = []
        self._chosen: list[int] = []

    def _api(self) -> SiteAPI:
        return SiteAPI(async_get_clientsession(self.hass), self._site)

    async def _find_cities(self, query: str) -> str | None:
        """None when found; else an error key."""
        try:
            self._cities = await self._api().cities(query)
        except SiteError:
            return "cannot_connect"
        return None if self._cities else "no_city"

    def _city_schema(self) -> vol.Schema:
        options = [SelectOptionDict(value=str(c["code"]), label=f"{city_label(self.hass, c)} ({c['branches']})")
                   for c in self._cities]
        return vol.Schema({vol.Required(CONF_CITY): SelectSelector(SelectSelectorConfig(
            options=options, mode=SelectSelectorMode.LIST))})

    async def _load_branches(self) -> str | None:
        try:
            self._branches = await self._api().branches(self._city["code"])
        except SiteError:
            return "cannot_connect"
        return None if self._branches else "no_branches"

    def _branches_schema(self, current: list[int] | None = None) -> vol.Schema:
        def label(b: dict[str, Any]) -> str:
            extra = ""
            if b["group"] == "online":
                extra = " (online)"
            elif b["group"] == "nearby" and b.get("km") is not None:
                extra = f" ({b['km']:g} km)"
            return branch_label(self.hass, b) + extra

        if current:
            default = [str(b) for b in current if any(x["id"] == b for x in self._branches)]
        else:
            # one branch per chain, as the site picks: the town's biggest, else the nearest
            seen, default = set(), []
            for b in self._branches:
                if b["group"] != "online" and b["chain"] not in seen and len(default) < MAX_BRANCHES:
                    seen.add(b["chain"])
                    default.append(str(b["id"]))
        options = [SelectOptionDict(value=str(b["id"]), label=label(b)) for b in self._branches]
        return vol.Schema({vol.Required(CONF_BRANCHES, default=default): SelectSelector(SelectSelectorConfig(
            options=options, multiple=True, mode=SelectSelectorMode.LIST))})

    def _pick_branches(self, picked: list[str]) -> str | None:
        ids = [int(x) for x in picked if str(x).isdigit()]
        known = {b["id"] for b in self._branches}
        ids = [i for i in ids if i in known]
        if not ids:
            return "no_branches"
        if len(ids) > MAX_BRANCHES:
            return "too_many"
        self._chosen = ids
        return None

    def _list_schema(self, current: str = OWN_LIST) -> vol.Schema:
        follow = current != OWN_LIST
        fields: dict[Any, Any] = {
            vol.Required(CONF_LIST, default=FOLLOW if follow else OWN_LIST): SelectSelector(SelectSelectorConfig(
                options=[OWN_LIST, FOLLOW], translation_key="list_source", mode=SelectSelectorMode.LIST)),
        }
        entity = vol.Optional("todo_entity", description={"suggested_value": current} if follow else None)
        fields[entity] = EntitySelector(EntitySelectorConfig(domain="todo"))
        return vol.Schema(fields)

    def _list_value(self, user_input: dict[str, Any]) -> str | None:
        if user_input.get(CONF_LIST) != FOLLOW:
            return OWN_LIST
        entity = user_input.get("todo_entity") or ""
        if not entity.startswith("todo.") or entity.startswith(f"todo.{DOMAIN}") or entity == "todo.supermarket_list":
            return None
        return entity

    def _result(self, list_source: str) -> dict[str, Any]:
        info = {str(b["id"]): {k: b.get(k) for k in ("chain", "chain_name", "chain_name_en", "name", "online")}
                for b in self._branches if b["id"] in self._chosen}
        return {CONF_SITE: self._site, CONF_CITY: {k: self._city.get(k) for k in ("code", "he", "en", "ru")},
                CONF_BRANCHES: self._chosen, CONF_BRANCH_INFO: info, CONF_LIST: list_source}


class ShoppingCompareWebFlow(_Steps, ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._init_state()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ShoppingCompareWebOptions()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self._site = site_url(user_input.get(CONF_SITE) or DEFAULT_SITE)
            except ValueError:
                errors[CONF_SITE] = "invalid_url"
            if not errors:
                try:
                    await self._api().health()
                except SiteError:
                    errors["base"] = "cannot_connect"
            if not errors:
                error = await self._find_cities(user_input.get("city_name", ""))
                if error:
                    errors["base" if error == "cannot_connect" else "city_name"] = error
                else:
                    return await self.async_step_city()
        schema = vol.Schema({
            vol.Required("city_name"): TextSelector(),
            vol.Optional(CONF_SITE, default=self._site): TextSelector(),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_city(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._city = next((c for c in self._cities if str(c["code"]) == user_input.get(CONF_CITY)), None)
            if self._city is None:
                errors[CONF_CITY] = "no_city"
            else:
                error = await self._load_branches()
                if error:
                    errors["base"] = error
                else:
                    return await self.async_step_branches()
        return self.async_show_form(step_id="city", data_schema=self._city_schema(), errors=errors)

    async def async_step_branches(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            error = self._pick_branches(user_input.get(CONF_BRANCHES) or [])
            if error:
                errors[CONF_BRANCHES] = error
            else:
                return await self.async_step_list()
        return self.async_show_form(step_id="branches", data_schema=self._branches_schema(), errors=errors,
                                    description_placeholders={"city": city_label(self.hass, self._city)})

    async def async_step_list(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            source = self._list_value(user_input)
            if source is None:
                errors["todo_entity"] = "need_list"
            else:
                return self.async_create_entry(title=city_label(self.hass, self._city), data=self._result(source))
        return self.async_show_form(step_id="list", data_schema=self._list_schema(), errors=errors)


class ShoppingCompareWebOptions(_Steps, OptionsFlow):
    """Another town, other branches, or another list."""

    def __init__(self) -> None:
        self._init_state()

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}
        self._site = current.get(CONF_SITE) or DEFAULT_SITE
        errors: dict[str, str] = {}
        if user_input is not None:
            error = await self._find_cities(user_input.get("city_name", ""))
            if error:
                errors["base" if error == "cannot_connect" else "city_name"] = error
            else:
                return await self.async_step_city()
        city = current.get(CONF_CITY) or {}
        schema = vol.Schema({vol.Required("city_name", default=city_label(self.hass, city) if city else ""): TextSelector()})
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)

    async def async_step_city(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._city = next((c for c in self._cities if str(c["code"]) == user_input.get(CONF_CITY)), None)
            if self._city is None:
                errors[CONF_CITY] = "no_city"
            else:
                error = await self._load_branches()
                if error:
                    errors["base"] = error
                else:
                    return await self.async_step_branches()
        return self.async_show_form(step_id="city", data_schema=self._city_schema(), errors=errors)

    async def async_step_branches(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}
        if user_input is not None:
            error = self._pick_branches(user_input.get(CONF_BRANCHES) or [])
            if error:
                errors[CONF_BRANCHES] = error
            else:
                return await self.async_step_list()
        same_town = (current.get(CONF_CITY) or {}).get("code") == self._city["code"]
        return self.async_show_form(step_id="branches", errors=errors,
                                    data_schema=self._branches_schema(current.get(CONF_BRANCHES) if same_town else None),
                                    description_placeholders={"city": city_label(self.hass, self._city)})

    async def async_step_list(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}
        if user_input is not None:
            source = self._list_value(user_input)
            if source is None:
                errors["todo_entity"] = "need_list"
            else:
                self.hass.config_entries.async_update_entry(self.config_entry, title=city_label(self.hass, self._city))
                return self.async_create_entry(title="", data=self._result(source))
        return self.async_show_form(step_id="list", data_schema=self._list_schema(current.get(CONF_LIST) or OWN_LIST),
                                    errors=errors)
