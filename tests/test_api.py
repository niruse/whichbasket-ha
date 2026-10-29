"""The site client: only https, no redirects, bounded answers, every field checked."""
from __future__ import annotations

import re

import pytest
from conftest import HEALTH, JSON, SITE

from custom_components.shopping_compare_web.api import (
    MAX_BYTES,
    SiteAPI,
    SiteBusy,
    SiteError,
    clean_chain_item,
    clean_compare,
    clean_product,
    plain,
    site_url,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession


@pytest.mark.parametrize("text, expected", [
    ("https://whichbasket.com", "https://whichbasket.com"),
    ("https://whichbasket.com/", "https://whichbasket.com"),
    (" https://prices.example.co.il ", "https://prices.example.co.il"),
])
def test_site_url_takes_an_https_origin(text, expected):
    assert site_url(text) == expected


@pytest.mark.parametrize("text", ["http://whichbasket.com", "https://user:pw@host.example",
                                  "https://host.example/api", "https://host.example/?x=1", "https://host.example/#a",
                                  "ftp://host.example", "javascript:alert(1)", "", "https://"])
def test_site_url_refuses_anything_else(text):
    with pytest.raises(ValueError):
        site_url(text)


def test_answers_are_checked_field_by_field():
    assert clean_product({"key": "x:1", "name": "a"}) is None, "an unknown kind of key"
    assert clean_product({"key": "b:1", "name": 5}) is None
    p = clean_product({"key": "b:7290000000017", "name": "חלב" * 200, "chains": ["rami_levy", "../x", 5], "prices": {
        "200005": 6.5, "x": 1, "300128": "7", "1" * 12: 3, "200001": float("nan")}, "weighted": "yes", "size": {
        "total": 1000, "unit": "ml", "count": 1, "each": -3, "evil": "<script>"}})
    assert len(p["name"]) == 120 and p["chains"] == ["rami_levy"] and p["prices"] == {"200005": 6.5}
    assert p["weighted"] is False and p["size"] == {"total": 1000.0, "unit": "ml", "count": 1}
    with pytest.raises(SiteError):
        clean_compare({"branches": "x", "lines": []})
    res = clean_compare({"branches": [{"id": 200005, "chain": "rami_levy", "total": 10, "fair": 10, "cheapest": True,
                                       "cart": {"kind": "link", "url": "https://evil.example/he/basket"}},
                                      {"id": "200001"}, "junk"],
                         "lines": [{"key": "t:חלב", "per_branch": {"200005": {"item": 1, "cost": 6.5, "price": 6.5},
                                                                    "999": {"item": 2, "cost": 1}}}, {"key": 5}]})
    assert [b["id"] for b in res["branches"]] == [200005] and res["branches"][0]["cart_url"] is None, \
        "a cart link only to the chains' own shops"
    assert list(res["lines"][0]["per_branch"]) == ["200005"], "only the branches the answer names"


# ---- names are plain text (fourth review, 2026-10-28) --------------------------------------------------------------
HOSTILE = ["![](https://attacker.example/t.gif)", "[קנו כאן](https://attacker.example/login)",
           '<ha-alert alert-type="error" title="x">קנו כאן</ha-alert>', "רמי לוי | מרכז",
           "\u202eלוי\u202c\x00\nרמי\u200f", "xhttps://attacker.example/login", "אwww.attacker.example/login",
           "mailto:a@attacker.example", "<https://attacker.example>"]
HIDDEN = re.compile("[\x00-\x1f\x7f-\x9f\u061c\u200b-\u200f\u202a-\u202e\u2060-\u2069\ufeff]")
LINK = re.compile(r"(?i)(https?|ftp)://|www\.|@")      # what markdown makes a link of, even after a letter


@pytest.mark.parametrize("name", HOSTILE)
def test_names_from_the_site_are_plain_text(name):
    """Names come from the chains' files through the site. Markdown cards, notifications and the set-up render
    markdown, so a name brings no tag, image, link, table cell or hidden character."""
    shown = plain(name)
    assert not set(shown) & set("<>[]|`\\") and not HIDDEN.search(shown) and shown == shown.strip()
    assert not LINK.search(shown), shown
    p = clean_product({"key": "b:1", "name": name, "name_en": name, "name_ru": name})
    item = clean_chain_item({"item": 1, "name": name, "name_en": name, "name_ru": name})
    res = clean_compare({"branches": [{"id": 200005, "chain": "rami_levy", "chain_name": name, "chain_name_en": name,
                                       "name": name}],
                         "lines": [{"key": "b:1", "name": name, "per_branch": {"200005": {
                             "item": 1, "cost": 6.5, "price": 6.5, "name": name}}}]})
    b, line = res["branches"][0], res["lines"][0]
    assert {p["name"], p["name_en"], p["name_ru"], item["name"], item["name_en"], b["name"], line["name"],
            line["per_branch"]["200005"]["name"]} == {shown}
    assert b["chain_name"] == b["chain_name_en"] == plain(name, 40)


def test_plain_text_keeps_the_words():
    assert plain("![](https://attacker.example/t.gif)") == "!()(https：//attacker.example/t.gif)"
    assert plain("www.attacker.example a@b.example") == "www．attacker.example a＠b.example"
    assert plain("רמי לוי  [קניון]  | מרכז\n") == "רמי לוי (קניון) / מרכז"
    assert plain("חלב 3% 1 ליטר") == "חלב 3% 1 ליטר" and plain("⁨Fairy⁩") == "Fairy"
    assert plain(5) == plain(None) == "" and plain("א" * 300, 80) == "א" * 80
    assert plain(plain(HOSTILE[2])) == plain(HOSTILE[2]), "cleaning twice changes nothing"


def test_a_cart_host_that_isnt_punycode_is_no_cart():
    """yarl raises (UnicodeDecodeError) reading such a host: the comparison still comes through."""
    res = clean_compare({"branches": [{"id": 200005, "chain": "rami_levy", "cart": {
        "kind": "link", "url": "https://xn--a.com/he/basket"}}], "lines": []})
    assert res["branches"][0]["cart_url"] is None


async def test_towns_and_branches_are_plain_text(hass, aioclient_mock):
    api = SiteAPI(async_get_clientsession(hass), SITE)
    aioclient_mock.get(f"{SITE}/api/cities", headers=JSON, json=[
        {"code": 3000, "he": "<b>ירושלים</b>", "en": "[J](https://attacker.example)", "ru": "|И|", "branches": 3}])
    aioclient_mock.get(f"{SITE}/api/branches", headers=JSON, json={"local": [
        {"id": 200005, "chain": "rami_levy", "chain_name": "רמי לוי<img src=x>", "chain_name_en": "Rami ![](x)",
         "name": "![](https://attacker.example/t.gif)"}], "nearby": [], "online": []})
    (city,) = await api.cities("ירוש")
    assert (city["he"], city["en"], city["ru"]) == ("bירושלים/b", "(J)(https：//attacker.example)", "/И/")
    (branch,) = await api.branches(3000)
    assert (branch["chain_name"], branch["chain_name_en"], branch["name"]) == (
        "רמי לויimg src=x", "Rami !()(x)", "!()(https：//attacker.example/t.gif)")


async def test_the_client_refuses_redirects_errors_and_huge_answers(hass, aioclient_mock):
    api = SiteAPI(async_get_clientsession(hass), SITE)
    aioclient_mock.get(f"{SITE}/api/health", status=302, headers={"location": "https://evil.example/"})
    with pytest.raises(SiteError):
        await api.health()
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{SITE}/api/health", status=429, headers=JSON, json={"error": "too many"})
    with pytest.raises(SiteBusy):
        await api.health()
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{SITE}/api/health", text="<html>", headers={"content-type": "text/html"})
    with pytest.raises(SiteError):
        await api.health()
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{SITE}/api/health", content=b"[" + b"1," * MAX_BYTES + b"1]", headers=JSON)
    with pytest.raises(SiteError, match="too large"):
        await api.health()
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{SITE}/api/health", json={"ok": False}, headers=JSON)
    with pytest.raises(SiteError):
        await api.health()
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{SITE}/api/health", json=HEALTH, headers=JSON)
    assert (await api.health())["matches"] == "admin"
    method, url, _, headers = aioclient_mock.mock_calls[-1]
    assert headers["User-Agent"].startswith("ShoppingCompareHA/")


async def test_compare_sends_only_bounded_known_fields(hass, aioclient_mock):
    api = SiteAPI(async_get_clientsession(hass), SITE)
    aioclient_mock.post(f"{SITE}/api/compare", json={"branches": [], "lines": [], "partial": False}, headers=JSON)
    await api.compare([200005] * 20, [{"key": "t:" + "x" * 500, "name": "y" * 500, "qty": 1000,
                                        "choice": {"rami_levy": 5, "evil": 1, "carrefour": True, "victory": -1}}] * 150)
    _, _, body, _ = aioclient_mock.mock_calls[-1]
    assert len(body["branches"]) == 12 and len(body["items"]) == 100
    item = body["items"][0]
    assert len(item["key"]) == 200 and len(item["name"]) == 120 and item["qty"] == 99.0
    assert item["choice"] == {"rami_levy": 5}
