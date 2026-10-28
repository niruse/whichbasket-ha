"""Supermarket price comparison for Home Assistant, through the website (https://shopping-compare.onrender.com).

The website imports the chains' price files every night and works out the comparison; this integration only talks
to the website's public API, the same one its pages use. It keeps the household's list (or follows a to-do list
the household already has), compares it in the chosen branches, and offers sensors, a card and ready dashboards.
"""
from __future__ import annotations

import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import CARD_URL, CONF_LIST, DOMAIN, OWN_LIST, VERSION
from .coordinator import ShoppingCoordinator
from .websocket import async_register

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR, Platform.TODO]

type ShoppingEntry = ConfigEntry[ShoppingCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """The websocket commands and the card (loaded on every dashboard: no resource to add by hand)."""
    from homeassistant.components.frontend import add_extra_js_url
    from homeassistant.components.http import StaticPathConfig

    async_register(hass)
    path = os.path.join(os.path.dirname(__file__), "www", "shopping-compare-web-card.js")
    await hass.http.async_register_static_paths([StaticPathConfig(CARD_URL, path, False)])
    stamp = int(await hass.async_add_executor_job(os.path.getmtime, path))
    add_extra_js_url(hass, f"{CARD_URL}?v={VERSION}-{stamp}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ShoppingEntry) -> bool:
    coordinator = ShoppingCoordinator(hass, entry)
    await coordinator.async_load()
    entry.runtime_data = coordinator
    platforms = PLATFORMS if ({**entry.data, **entry.options}.get(CONF_LIST) or OWN_LIST) == OWN_LIST \
        else [p for p in PLATFORMS if p != Platform.TODO]
    await hass.config_entries.async_forward_entry_setups(entry, platforms)
    coordinator.start()
    # the list works without the site; the first comparison comes in the background
    entry.async_create_background_task(hass, coordinator.async_refresh(), f"{DOMAIN} first comparison")
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


async def _reload(hass: HomeAssistant, entry: ShoppingEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ShoppingEntry) -> bool:
    platforms = PLATFORMS if ({**entry.data, **entry.options}.get(CONF_LIST) or OWN_LIST) == OWN_LIST \
        else [p for p in PLATFORMS if p != Platform.TODO]
    return await hass.config_entries.async_unload_platforms(entry, platforms)
