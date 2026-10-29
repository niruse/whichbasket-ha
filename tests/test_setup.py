"""The integration at work: the list, the comparison as sensors, the card's commands, a followed to-do list."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from conftest import HEALTH, JSON, OLD_SITE, SITE, comparison
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMockResponse

from custom_components.shopping_compare_web.config_flow import ShoppingCompareWebFlow
from custom_components.shopping_compare_web.const import CARD_URL, DEFAULT_SITE, DOMAIN, OLD_SITES, VERSION
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

DATA = {"site": SITE, "city": {"code": 3000, "he": "ירושלים", "en": "Jerusalem"}, "branches": [200005, 300128],
        "branch_info": {"200005": {"chain": "rami_levy", "chain_name": "רמי לוי", "chain_name_en": "Rami Levy",
                                   "name": "רב מכר", "online": False},
                        "300128": {"chain": "carrefour", "chain_name": "קרפור", "chain_name_en": "Carrefour",
                                   "name": "היפר", "online": False}},
        "list_source": "own"}


class Site:
    """The website, as far as the integration sees it: what it was asked, and its answers."""

    def __init__(self, aioclient_mock) -> None:
        self.compares: list[dict] = []
        self.votes: list[dict] = []
        self.down = False
        aioclient_mock.get(f"{SITE}/api/health", side_effect=self._health)
        aioclient_mock.post(f"{SITE}/api/compare", side_effect=self._compare)
        aioclient_mock.post(f"{SITE}/api/vote", side_effect=self._vote)
        aioclient_mock.get(f"{SITE}/api/search", headers=JSON, json=[
            {"key": "b:7290000000017", "name": "חלב 3% 1 ליטר", "name_en": "Milk 3% 1 l", "chains": ["rami_levy", "carrefour"],
             "prices": {"200005": 6.5}, "weighted": False, "size": {"total": 1000, "unit": "ml", "count": 1}}])
        aioclient_mock.get(f"{SITE}/api/chain_search", headers=JSON, json=[
            {"item": 30000099, "name": "חלב תנובה 3%", "prices": {"300128": 6.9}, "size": None}])

    async def _health(self, method, url, data):
        if self.down:
            return AiohttpClientMockResponse(method, url, status=503, json={"error": "busy"}, headers=JSON)
        return AiohttpClientMockResponse(method, url, json=HEALTH, headers=JSON)

    async def _compare(self, method, url, data):
        self.compares.append(data)
        return AiohttpClientMockResponse(method, url, json=comparison([i["key"] for i in data["items"]]), headers=JSON)

    async def _vote(self, method, url, data):
        self.votes.append(data)
        return AiohttpClientMockResponse(method, url, json={"ok": True, "decided": False, "review": True}, headers=JSON)


@pytest.fixture
async def site(hass: HomeAssistant, aioclient_mock):
    return Site(aioclient_mock)


@pytest.fixture
async def entry(hass: HomeAssistant, site):
    entry = MockConfigEntry(domain=DOMAIN, data=DATA, title="Jerusalem")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def compared(hass) -> None:
    """Let the debounced comparison run."""
    coordinator = hass.config_entries.async_entries(DOMAIN)[0].runtime_data
    await coordinator.async_refresh()
    await hass.async_block_till_done()


async def test_the_list_is_compared_and_the_sensors_say_where(hass, entry, site):
    await hass.services.async_call("todo", "add_item", {"entity_id": "todo.supermarket_list", "item": "חלב ×2"},
                                   blocking=True)
    await compared(hass)
    body = site.compares[-1]
    assert body["branches"] == [200005, 300128]
    assert body["items"] == [{"key": "t:חלב", "name": "חלב", "qty": 2.0, "choice": {}}]
    assert hass.states.get("sensor.supermarket_cheapest_branch").state == "Rami Levy · רב מכר"
    attrs = hass.states.get("sensor.supermarket_cheapest_branch").attributes
    assert attrs["total"] == 5.0 and attrs["cart_url"] == "https://www.rami-levy.co.il/he/basket?items=1"
    assert float(hass.states.get("sensor.supermarket_cheapest_total").state) == 5.0
    assert float(hass.states.get("sensor.supermarket_saving").state) == 1.0
    assert hass.states.get("sensor.supermarket_list_items").state == "1"
    carrefour = hass.states.get("sensor.supermarket_branch_300128")
    assert float(carrefour.state) == 6.0
    assert carrefour.attributes["branch"] == "Carrefour · היפר" and carrefour.attributes["cheapest"] is False
    assert hass.states.get("binary_sensor.supermarket_site").state == "on"
    assert hass.states.get("sensor.supermarket_prices_updated").state.startswith("2026-10-28T05:20:00")
    items = await hass.services.async_call("todo", "get_items", {"entity_id": "todo.supermarket_list"}, blocking=True,
                                           return_response=True)
    assert [i["summary"] for i in items["todo.supermarket_list"]["items"]] == ["חלב ×2"]


async def test_the_last_comparison_stays_while_the_site_is_away(hass, entry, site):
    await hass.services.async_call("todo", "add_item", {"entity_id": "todo.supermarket_list", "item": "במבה"}, blocking=True)
    await compared(hass)
    site.down = True
    await compared(hass)
    assert hass.states.get("binary_sensor.supermarket_site").state == "off"
    assert float(hass.states.get("sensor.supermarket_cheapest_total").state) == 5.0, "still the last comparison"


async def test_the_cards_commands(hass, entry, site, hass_ws_client):
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": f"{DOMAIN}/subscribe"})
    assert (await ws.receive_json())["success"]
    first = (await ws.receive_json())["event"]
    assert first["lines"] == [] and first["branches"][0]["chain"] == "rami_levy" and first["own"] is True

    await ws.send_json({"id": 2, "type": f"{DOMAIN}/search", "query": "חלב"})
    found = await ws.receive_json()
    while found.get("type") != "result":
        found = await ws.receive_json()
    product = found["result"][0]
    assert product["chains"] == ["rami_levy", "carrefour"]

    await ws.send_json({"id": 3, "type": f"{DOMAIN}/add", "product": {**product, "evil": "<x>"}, "qty": 1})
    reply = await ws.receive_json()
    while reply.get("id") != 3 or reply.get("type") != "result":
        reply = await ws.receive_json()
    assert reply["success"], reply
    await compared(hass)
    coordinator = entry.runtime_data
    assert [(i["key"], i["qty"], i["chains"]) for i in coordinator.items] == [("b:7290000000017", 1.0, ["rami_levy", "carrefour"])]
    assert "evil" not in coordinator.items[0]

    # the household picks the product at Carrefour: it applies at once and goes to the site as a suggestion
    await ws.send_json({"id": 4, "type": f"{DOMAIN}/choose", "key": "b:7290000000017", "chain": "carrefour", "item": 30000099})
    reply = await ws.receive_json()
    while reply.get("id") != 4 or reply.get("type") != "result":
        reply = await ws.receive_json()
    assert reply["success"], reply
    assert site.votes[-1] == {"key": "b:7290000000017", "chain": "carrefour", "item": 30000099}
    assert site.compares[-1]["items"][0]["choice"] == {"carrefour": 30000099}
    await ws.send_json({"id": 5, "type": f"{DOMAIN}/choose", "key": "b:7290000000017", "chain": "carrefour", "item": None})
    reply = await ws.receive_json()
    while reply.get("id") != 5 or reply.get("type") != "result":
        reply = await ws.receive_json()
    assert site.compares[-1]["items"][0]["choice"] == {} and len(site.votes) == 1, "going back sends nothing"

    uid = coordinator.items[0]["uid"]
    await ws.send_json({"id": 6, "type": f"{DOMAIN}/qty", "uid": uid, "qty": 3})
    reply = await ws.receive_json()
    while reply.get("id") != 6 or reply.get("type") != "result":
        reply = await ws.receive_json()
    assert coordinator.items[0]["qty"] == 3
    await ws.send_json({"id": 7, "type": f"{DOMAIN}/remove", "uid": uid})
    reply = await ws.receive_json()
    while reply.get("id") != 7 or reply.get("type") != "result":
        reply = await ws.receive_json()
    assert coordinator.items == []


@pytest.mark.parametrize("msg", [
    {"type": f"{DOMAIN}/choose", "key": "b:1234567", "chain": "evil", "item": 1},
    {"type": f"{DOMAIN}/choose", "key": "b:1234567", "chain": "carrefour", "item": True},
    {"type": f"{DOMAIN}/choose", "key": "b:1234567", "chain": "carrefour", "item": -1},
    {"type": f"{DOMAIN}/choose", "key": "x" * 201, "chain": "carrefour", "item": 1},
    {"type": f"{DOMAIN}/search", "query": "x" * 61},
    {"type": f"{DOMAIN}/add", "product": {"key": "z:1", "name": "x"}},
    {"type": f"{DOMAIN}/add", "product": {"key": "b:1234567", "name": "x"}, "qty": 1000},
    {"type": f"{DOMAIN}/qty", "uid": "u", "qty": -1},
])
async def test_the_commands_refuse_what_they_shouldnt_take(hass, entry, site, hass_ws_client, msg):
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, **msg})
    reply = await ws.receive_json()
    assert reply["success"] is False
    assert not site.votes


@pytest.fixture
def shopping_list_in_memory():
    """Home Assistant's own shopping list, without its file (the harness's config folder outlives a test)."""
    with patch("homeassistant.components.shopping_list.ShoppingData.save"), \
            patch("homeassistant.components.shopping_list.ShoppingData.async_load"):
        yield


async def test_following_a_list_the_household_already_has(hass, site, shopping_list_in_memory):
    shopping = MockConfigEntry(domain="shopping_list")
    shopping.add_to_hass(hass)
    assert await hass.config_entries.async_setup(shopping.entry_id)
    await hass.async_block_till_done()
    entry = MockConfigEntry(domain=DOMAIN, data={**DATA, "list_source": "todo.shopping_list"}, title="Jerusalem")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("todo.supermarket_list") is None, "no list of its own"
    await hass.services.async_call("todo", "add_item", {"entity_id": "todo.shopping_list", "item": "2 עגבניות"}, blocking=True)
    await hass.async_block_till_done()
    await compared(hass)
    assert site.compares[-1]["items"] == [{"key": "t:עגבניות", "name": "עגבניות", "qty": 2.0, "choice": {}}]
    # a product chosen in the card goes onto the household's list as its name, and is priced as that product
    coordinator = entry.runtime_data
    await coordinator.async_add({"key": "b:7290000000017", "name": "חלב 3% 1 ליטר", "chains": ["rami_levy"]}, 1)
    await hass.async_block_till_done()
    await compared(hass)
    items = await hass.services.async_call("todo", "get_items", {"entity_id": "todo.shopping_list"}, blocking=True,
                                           return_response=True)
    assert sorted(i["summary"] for i in items["todo.shopping_list"]["items"]) == ["2 עגבניות", "חלב 3% 1 ליטר"]
    assert {i["key"] for i in site.compares[-1]["items"]} == {"t:עגבניות", "b:7290000000017"}
    assert json.dumps(site.compares[-1], ensure_ascii=False).count("b:7290000000017") == 1


async def test_the_card_is_on_every_dashboard(hass, entry, frontend_ready, hass_client):
    frontend_ready.assert_called_once()
    url = frontend_ready.call_args.args[1]
    assert url.startswith(f"{CARD_URL}?v=")
    client = await hass_client()
    resp = await client.get(CARD_URL)
    assert resp.status == 200
    text = await resp.text()
    assert 'customElements.define("shopping-compare-web-card"' in text
    assert "innerHTML" not in text, "the card builds its page from nodes only"


# ---- the site's move to whichbasket.com --------------------------------------------------------------
@pytest.mark.parametrize("old", [OLD_SITE, f"{OLD_SITE}/", "http://shopping-compare.onrender.com"])
async def test_an_entry_on_the_old_address_moves_to_the_new_one(hass, site, old):
    entry = MockConfigEntry(domain=DOMAIN, data={**DATA, "site": old}, options={**DATA, "site": f"{old}/"},
                            title="Jerusalem", version=1, minor_version=1)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert (entry.version, entry.minor_version) == (1, 2)
    assert entry.data["site"] == SITE == DEFAULT_SITE
    assert entry.options["site"] == SITE
    assert entry.runtime_data.api.base == SITE
    assert {k: v for k, v in entry.data.items() if k != "site"} == {k: v for k, v in DATA.items() if k != "site"}


async def test_an_entry_on_a_site_of_its_own_stays(hass, aioclient_mock):
    own = "https://prices.example.co.il"
    aioclient_mock.get(f"{own}/api/health", json=HEALTH, headers=JSON)
    aioclient_mock.post(f"{own}/api/compare", json=comparison([]), headers=JSON)
    entry = MockConfigEntry(domain=DOMAIN, data={**DATA, "site": own}, title="Jerusalem", version=1, minor_version=1)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.minor_version == 2
    assert entry.data["site"] == own and not entry.options
    assert entry.runtime_data.api.base == own


async def test_an_entry_from_a_newer_version_is_not_touched(hass, site):
    entry = MockConfigEntry(domain=DOMAIN, data={**DATA, "site": OLD_SITE}, title="Jerusalem", version=2)
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.MIGRATION_ERROR
    assert entry.data["site"] == OLD_SITE


def test_the_version_is_bumped():
    manifest = json.loads((Path(__file__).parent.parent / "custom_components" / DOMAIN / "manifest.json").read_text())
    assert manifest["version"] == VERSION == "0.2.0"
    assert manifest["documentation"] == f"{DEFAULT_SITE}/home-assistant"
    assert ShoppingCompareWebFlow.VERSION == 1 and ShoppingCompareWebFlow.MINOR_VERSION == 2
    assert OLD_SITE in OLD_SITES and DEFAULT_SITE == "https://whichbasket.com"
