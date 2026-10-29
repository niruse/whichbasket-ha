"""Constants for the supermarket price comparison client (the website does the work; this talks to it)."""
from __future__ import annotations

DOMAIN = "shopping_compare_web"
VERSION = "0.2.0"
DEFAULT_SITE = "https://whichbasket.com"
# the site's old address, switched off later: saved entries move to DEFAULT_SITE
OLD_SITES = ("https://shopping-compare.onrender.com", "http://shopping-compare.onrender.com")

CONF_SITE = "site"
CONF_CITY = "city"                # {"code": int, "he": str, "en": str}
CONF_BRANCHES = "branches"        # [branch id, ...] as the site numbers them
CONF_BRANCH_INFO = "branch_info"  # {str(id): {"chain", "chain_name", "chain_name_en", "name", "online"}}
CONF_LIST = "list_source"         # OWN_LIST, or the entity id of another to-do list to follow
OWN_LIST = "own"

MAX_BRANCHES = 12                 # the site's limits (web/server/prices.py)
MAX_ITEMS = 100
MAX_NAME = 120
MAX_KEY = 200
MAX_QUERY = 60

STORAGE_VERSION = 1
SIGNAL_UPDATED = f"{DOMAIN}_updated"
CARD_URL = f"/{DOMAIN}/shopping-compare-web-card.js"

CHAINS = ("shufersal", "rami_levy", "carrefour", "victory", "mahsanei_hashuk")
CHAIN_NAMES = {"shufersal": ("שופרסל", "Shufersal"), "rami_levy": ("רמי לוי", "Rami Levy"),
               "carrefour": ("קרפור", "Carrefour"), "victory": ("ויקטורי", "Victory"),
               "mahsanei_hashuk": ("מחסני השוק", "Mahsanei HaShuk")}
