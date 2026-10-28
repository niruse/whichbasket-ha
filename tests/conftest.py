"""Home Assistant's own test harness (pytest-homeassistant-custom-component) for the client integration.

    pip install pytest-homeassistant-custom-component
    cd ha-client && python -m pytest -q tests
"""
from __future__ import annotations

import os
import sys

from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SITE = "https://shopping-compare.onrender.com"
JSON = {"content-type": "application/json"}
HEALTH = {"ok": True, "importing": False, "matches": "admin", "built_at": "2026-10-28T05:20:00+00:00", "chains": []}
CITIES = [{"code": 3000, "he": "ירושלים", "en": "Jerusalem", "ru": "Иерусалим", "branches": 40}]
BRANCHES = {
    "local": [
        {"id": 200005, "chain": "rami_levy", "chain_name": "רמי לוי", "chain_name_en": "Rami Levy", "name": "רב מכר",
         "address": "", "city": 3000, "online": False, "items": 9000},
        {"id": 200001, "chain": "rami_levy", "chain_name": "רמי לוי", "chain_name_en": "Rami Levy", "name": "תלפיות",
         "address": "", "city": 3000, "online": False, "items": 7000},
        {"id": 300128, "chain": "carrefour", "chain_name": "קרפור", "chain_name_en": "Carrefour", "name": "היפר",
         "address": "", "city": 3000, "online": False, "items": 8000},
    ],
    "nearby": [],
    "online": [{"id": 100413, "chain": "shufersal", "chain_name": "שופרסל", "chain_name_en": "Shufersal",
                "name": "שופרסל אונליין", "address": "", "city": None, "online": True, "items": 20000}],
}


def cell(item, name, price, **extra):
    return {"item": item, "name": name, "price": price, "cost": price, "source": "exact", "exact": True, "unsure": False,
            "weighted": False, "size": None, "size_mismatch": False, "counted": True, **extra}


def comparison(lines):
    """A site answer for a list of keys: Rami Levy cheaper than Carrefour."""
    out = []
    for i, key in enumerate(lines):
        out.append({"key": key, "name": key[2:], "qty": 1,
                    "per_branch": {"200005": cell(20000000 + i, f"{key[2:]} רמי", 5.0),
                                   "300128": cell(30000000 + i, f"{key[2:]} קרפור", 6.0, source="auto", exact=False)},
                    "alternatives": {}, "sources": {}, "pending": [], "votable": True, "size": None,
                    "sizes_differ": False})
    total_r, total_c = 5.0 * len(lines), 6.0 * len(lines)
    branch = lambda bid, chain, name, name_en, here, total, cheapest: {  # noqa: E731
        "id": bid, "chain": chain, "chain_name": name, "chain_name_en": name_en, "name": here, "total": total,
        "fill_elsewhere": 0, "fair": total, "found": len(lines), "missing": 0, "pending": 0, "other_size": 0,
        "shared_total": total, "unsure": 0, "cheapest": cheapest,
        "cart": {"kind": "link", "url": "https://www.rami-levy.co.il/he/basket?items=1", "count": 1}}
    return {"branches": [branch(200005, "rami_levy", "רמי לוי", "Rami Levy", "רב מכר", total_r, True),
                         branch(300128, "carrefour", "קרפור", "Carrefour", "היפר", total_c, False)],
            "lines": out, "shared_count": len(lines), "partial": False}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def frontend_ready(hass):
    """The dashboards' frontend isn't installed in the test harness: the card's script registration is not under
    test, so the frontend counts as set up."""
    hass.config.components.add("frontend")
    with patch("homeassistant.components.frontend.add_extra_js_url") as js:
        yield js
