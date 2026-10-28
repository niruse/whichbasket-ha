"""Setting up: the town, the branches, the list."""
from __future__ import annotations

import pytest
from conftest import BRANCHES, CITIES, HEALTH, JSON, SITE

from custom_components.shopping_compare_web.const import DOMAIN
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType, InvalidData


def mock_site(aioclient_mock):
    aioclient_mock.get(f"{SITE}/api/health", json=HEALTH, headers=JSON)
    aioclient_mock.get(f"{SITE}/api/cities", params={"q": "ירוש"}, json=CITIES, headers=JSON)
    aioclient_mock.get(f"{SITE}/api/cities", params={"q": "zzz"}, json=[], headers=JSON)
    aioclient_mock.get(f"{SITE}/api/branches", params={"city": "3000"}, json=BRANCHES, headers=JSON)


async def test_town_branches_and_own_list(hass, aioclient_mock):
    mock_site(aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "user"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"city_name": "zzz"})
    assert result["errors"] == {"city_name": "no_city"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"city_name": "ירוש"})
    assert result["step_id"] == "city"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"city": "3000"})
    assert result["step_id"] == "branches"
    default = next(k for k in result["data_schema"].schema if str(k) == "branches").default()
    assert default == ["200005", "300128"], "one branch per chain, the biggest, and no online shop"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"branches": []})
    assert result["errors"] == {"branches": "no_branches"}
    with pytest.raises(InvalidData):
        await hass.config_entries.flow.async_configure(result["flow_id"], {"branches": ["200005", "999"]})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"branches": ["200005", "300128"]})
    assert result["step_id"] == "list"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"list_source": "own"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    data = result["data"]
    assert data["branches"] == [200005, 300128]
    assert data["site"] == SITE and data["city"]["code"] == 3000 and data["list_source"] == "own"
    assert data["branch_info"]["200005"]["chain"] == "rami_levy"


async def test_names_in_the_set_up_are_plain_text(hass, aioclient_mock):
    """The set-up's texts are markdown: a town's or a branch's name from the site shows, and is kept, as plain text
    (fourth review, 2026-10-28)."""
    evil = "![](https://attacker.example/t.gif)<b>x</b>[l](https://attacker.example)|"
    aioclient_mock.get(f"{SITE}/api/health", json=HEALTH, headers=JSON)
    aioclient_mock.get(f"{SITE}/api/cities", params={"q": "ירוש"}, headers=JSON,
                       json=[{**CITIES[0], "he": "ירושלים " + evil, "en": "Jerusalem " + evil}])
    aioclient_mock.get(f"{SITE}/api/branches", params={"city": "3000"}, headers=JSON,
                       json={g: [{**b, "name": f"{b['name']} {evil}"} for b in rows] for g, rows in BRANCHES.items()})
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"city_name": "ירוש"})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"city": "3000"})
    assert result["step_id"] == "branches"
    select = next(v for k, v in result["data_schema"].schema.items() if str(k) == "branches")
    shown = [result["description_placeholders"]["city"], *(o["label"] for o in select.config["options"])]
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"branches": ["200005", "300128"]})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"list_source": "own"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    shown += [result["title"], *(b["name"] for b in result["data"]["branch_info"].values())]
    assert all("attacker.example" in t for t in shown), shown
    assert not [t for t in shown if set(t) & set("<>[]|@") or "://" in t], shown


async def test_the_site_address_must_be_https(hass, aioclient_mock):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"city_name": "ירוש",
                                                                                 "site": "http://shopping-compare.onrender.com"})
    assert result["errors"] == {"site": "invalid_url"}
    assert not aioclient_mock.mock_calls, "nothing was sent to it"


async def test_following_a_list_needs_the_list(hass, aioclient_mock):
    mock_site(aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"city_name": "ירוש"})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"city": "3000"})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"branches": ["200005"]})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"list_source": "follow"})
    assert result["errors"] == {"todo_entity": "need_list"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"list_source": "follow",
                                                                                 "todo_entity": "todo.supermarket_list"})
    assert result["errors"] == {"todo_entity": "need_list"}, "not the integration's own list"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"list_source": "follow",
                                                                                 "todo_entity": "todo.shopping_list"})
    assert result["type"] is FlowResultType.CREATE_ENTRY and result["data"]["list_source"] == "todo.shopping_list"


async def test_a_site_that_is_down(hass, aioclient_mock):
    aioclient_mock.get(f"{SITE}/api/health", status=503, headers=JSON, json={"error": "busy"})
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"city_name": "ירוש"})
    assert result["errors"] == {"base": "cannot_connect"}
