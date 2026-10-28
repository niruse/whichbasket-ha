"""The ready dashboards and the blueprint: valid, only the integration's own entities and cards, and templates that
render with and without a comparison."""
from __future__ import annotations

import glob
import os
import re

import pytest
import yaml
from conftest import HEALTH, JSON, SITE, comparison
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMockResponse

from custom_components.shopping_compare_web.const import DOMAIN
from homeassistant.components.automation.config import AUTOMATION_BLUEPRINT_SCHEMA
from homeassistant.components.blueprint import models
from homeassistant.helpers.template import Template
from homeassistant.util.yaml import load_yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHBOARDS = sorted(glob.glob(os.path.join(ROOT, "dashboards", "*.yaml")))
BLUEPRINT = os.path.join(ROOT, "blueprints", "automation", "shopping_compare_web", "cheapest_notify.yaml")
CARD_TYPES = {"sections", "panel", "grid", "heading", "conditional", "markdown", "tile", "statistics-graph", "todo-list",
              "custom:shopping-compare-web-card"}
ENTITY = re.compile(r"\b(?:sensor|binary_sensor|button|todo)\.supermarket_[a-z0-9_]+")
DATA = {"site": SITE, "city": {"code": 3000, "he": "ירושלים", "en": "Jerusalem"}, "branches": [200005, 300128],
        "branch_info": {"200005": {"chain": "rami_levy", "chain_name": "רמי לוי", "chain_name_en": "Rami Levy",
                                   "name": "רב מכר", "online": False},
                        "300128": {"chain": "carrefour", "chain_name": "קרפור", "chain_name_en": "Carrefour",
                                   "name": "היפר", "online": False}},
        "list_source": "own"}


def nodes(tree):
    if isinstance(tree, dict):
        yield tree
        for v in tree.values():
            yield from nodes(v)
    elif isinstance(tree, list):
        for v in tree:
            yield from nodes(v)


def markdown(tree) -> list[str]:
    return [n["content"] for n in nodes(tree) if n.get("type") == "markdown"]


def read(path: str):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture
async def entry(hass, aioclient_mock):
    async def compare(method, url, data):
        return AiohttpClientMockResponse(method, url, json=comparison([i["key"] for i in data["items"]]), headers=JSON)
    aioclient_mock.get(f"{SITE}/api/health", json=HEALTH, headers=JSON)
    aioclient_mock.post(f"{SITE}/api/compare", side_effect=compare)
    entry = MockConfigEntry(domain=DOMAIN, data=DATA, title="Jerusalem")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.mark.parametrize("path", DASHBOARDS, ids=os.path.basename)
async def test_a_dashboard_uses_only_known_cards_and_our_entities(hass, entry, path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    tree = yaml.safe_load(text)
    types = {n["type"] for n in nodes(tree) if isinstance(n.get("type"), str)}
    assert types <= CARD_TYPES, types - CARD_TYPES
    for card in nodes(tree):
        if card.get("type") == "custom:shopping-compare-web-card":
            assert card.get("view", "full") in ("full", "list", "compare", "summary")
    for entity_id in set(ENTITY.findall(text)) - {"sensor.supermarket_branch_"}:     # (that one is a pattern)
        assert hass.states.get(entity_id) is not None, f"{entity_id} in {os.path.basename(path)}"


@pytest.mark.parametrize("path", [p for p in DASHBOARDS if markdown(read(p))],
                         ids=os.path.basename)
async def test_the_markdown_renders_before_and_after_a_comparison(hass, entry, path):
    contents = markdown(read(path))
    before = [Template(c, hass).async_render(parse_result=False) for c in contents]
    assert all("ההשוואה תופיע כאן" in t or "עוד אין השוואה" in t or "⚠️" in t for t in before), before
    await hass.services.async_call("todo", "add_item", {"entity_id": "todo.supermarket_list", "item": "חלב ×2"}, blocking=True)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    after = "\n".join(Template(c, hass).async_render(parse_result=False) for c in contents)
    if "| סניף |" in after:
        rows = [line for line in after.splitlines() if line.startswith("| ")]
        assert rows[1].startswith("| 🏆 Rami Levy · רב מכר | ₪5.00"), rows       # (rows[0] is the heading)
        assert rows[2].startswith("| Carrefour · היפר | ₪6.00"), rows
    if "🏆 Rami Levy · רב מכר" in after and "###" in after:
        assert "**₪5.00**" in after and "**₪1.00**" in after


EVIL = ('![](https://attacker.example/t.gif) <ha-alert alert-type="error">x</ha-alert> [קנו](https://attacker.example/l) | '
        'www.attacker.example/w a@attacker.example')
MARKUP = re.compile(r"[<>]|!\[|\]\(|(?i:https?|ftp)://|(?i:www)\.|@")


async def test_a_hostile_branch_name_is_only_text(hass, aioclient_mock):
    """Branch names come from the chains' files. A markdown card renders images, links and some tags (and so do
    notifications), so a name reaches them as plain text: from the site's answer, and from what an older version
    kept in the set-up (fourth review, 2026-10-28)."""
    async def compare(method, url, data):
        res = comparison([i["key"] for i in data["items"]])
        for b in res["branches"]:
            b["name"] = EVIL
        return AiohttpClientMockResponse(method, url, json=res, headers=JSON)
    aioclient_mock.get(f"{SITE}/api/health", json=HEALTH, headers=JSON)
    aioclient_mock.post(f"{SITE}/api/compare", side_effect=compare)
    data = {**DATA, "city": {"code": 3000, "he": EVIL, "en": EVIL},
            "branch_info": {k: {**v, "name": EVIL} for k, v in DATA["branch_info"].items()}}
    entry = MockConfigEntry(domain=DOMAIN, data=data, title="Jerusalem")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await hass.services.async_call("todo", "add_item", {"entity_id": "todo.supermarket_list", "item": "חלב"}, blocking=True)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    states = [s for s in hass.states.async_all("sensor") if s.entity_id.startswith("sensor.supermarket_")]
    texts = [str(s.state) for s in states] + [str(v) for s in states for k, v in s.attributes.items() if k != "cart_url"]
    texts += [Template(c, hass).async_render(parse_result=False) for path in DASHBOARDS for c in markdown(read(path))]
    texts.append(Template(load_yaml(BLUEPRINT)["variables"]["title"].replace("best", "states('sensor.supermarket_"
                                                                                       "cheapest_branch')"),
                          hass).async_render(parse_result=False))
    shown = "\n".join(texts)
    assert "attacker.example/t.gif" in shown, "the name is there, as text"
    assert not MARKUP.search(shown), [t for t in texts if MARKUP.search(t)]


def test_the_blueprint_is_valid_and_needs_its_inputs():
    blueprint = models.Blueprint(load_yaml(BLUEPRINT), expected_domain="automation", schema=AUTOMATION_BLUEPRINT_SCHEMA)
    assert set(blueprint.inputs) == {"notify_device", "at", "days", "min_items", "min_saving"}
    with open(BLUEPRINT, encoding="utf-8") as fh:
        text = fh.read()
    assert set(ENTITY.findall(text)) <= {"sensor.supermarket_cheapest_branch", "sensor.supermarket_cheapest_total",
                                        "sensor.supermarket_saving", "sensor.supermarket_list_items"}


async def test_the_blueprints_message_renders(hass, entry):
    await hass.services.async_call("todo", "add_item", {"entity_id": "todo.supermarket_list", "item": "במבה"}, blocking=True)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    data = load_yaml(BLUEPRINT)
    variables = {k: v for k, v in data["variables"].items() if isinstance(v, str)}
    values = {}
    for name in ("best", "total", "saving", "items", "cart"):
        values[name] = Template(variables[name], hass).async_render()
    assert values["best"] == "Rami Levy · רב מכר" and values["total"] == 5.0 and values["items"] == 1
    assert values["cart"] == "https://www.rami-levy.co.il/he/basket?items=1"
    message = Template(variables["message"], hass).async_render(values, parse_result=False)
    assert message == "1 פריטים · ₪5.00 · חיסכון ₪1.00", message
