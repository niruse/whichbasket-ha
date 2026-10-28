"""The website's public API, the same one its own pages use, and nothing else.

Every answer is checked field by field before it is used: types, lengths, numbers that are numbers. The site's
address must be https (TLS is verified by Home Assistant's shared session), redirects are not followed, and an
answer larger than MAX_BYTES is refused.
"""
from __future__ import annotations

import asyncio
import json
import math
import re
from typing import Any

import aiohttp
from yarl import URL

from .const import CHAINS, MAX_BRANCHES, MAX_ITEMS, MAX_KEY, MAX_NAME, MAX_QUERY, VERSION

MAX_BYTES = 3 * 1024 * 1024
TIMEOUT = aiohttp.ClientTimeout(total=45, connect=15)
USER_AGENT = f"ShoppingCompareHA/{VERSION} (Home Assistant)"
# the chains' own shops a "fill the cart" link may open (the site's own list: web/static/app.js CART_HOSTS)
CART_HOSTS = {"www.rami-levy.co.il": "/he/basket", "www.carrefour.co.il": "/", "www.victoryonline.co.il": "/",
              "www.mck.co.il": "/"}
UNITS = ("g", "ml", "pcs", "m")
_CHAIN_KEY = re.compile(r"[a-z_]{1,40}")


class SiteError(Exception):
    """The site answered with an error, or something that isn't an answer."""


class SiteBusy(SiteError):
    """Too many requests, or the site is busy or loading prices: try again later."""


def site_url(text: str) -> str:
    """The site's origin from what the user typed: https only, no user, path, query or fragment."""
    try:
        url = URL(str(text).strip())
    except (ValueError, TypeError):
        raise ValueError("invalid_url") from None
    if url.scheme != "https" or not url.host or url.user or url.password:
        raise ValueError("invalid_url")
    if url.path not in ("", "/") or url.query_string or url.fragment:
        raise ValueError("invalid_url")
    return str(url.origin())


# ---- checking answers ----------------------------------------------------------------------------------
def _str(value: Any, limit: int = MAX_NAME) -> str:
    return value[:limit] if isinstance(value, str) else ""


_CONTROLS = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_INVISIBLE = re.compile("[\u061c\u200b-\u200f\u202a-\u202e\u2060-\u2069\ufeff]")
# what turns text into markup where Home Assistant renders markdown (markdown cards, notifications, set-up texts):
# tags, images, links and a table's cells. Square brackets become round ones.
_MARKUP = str.maketrans({"<": None, ">": None, "[": "(", "]": ")", "|": "/", "`": "'", "\\": "/", "@": "＠"})
# markdown also links bare addresses (https://…, www.…, a@b.c): their colon, dot and @ become full-width look-alikes
_SCHEME = re.compile(r"(?i)(https?|ftp):(?=//)")     # marked links these after any character, a letter too
_WWW = re.compile(r"(?i)(www)\.")


def plain(value: Any, limit: int = MAX_NAME) -> str:
    """A name as plain text. Names come from the chains' files through the site: hostile text that ends up in
    states, attributes, to-do items and notifications, so it may carry no markup, no link and no hidden character."""
    if not isinstance(value, str):
        return ""
    text = " ".join(_INVISIBLE.sub("", _CONTROLS.sub(" ", value)).translate(_MARKUP).split())
    return _WWW.sub(r"\1．", _SCHEME.sub(r"\1：", text))[:limit]


def _num(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) and abs(value) < 1e9 else None


def _int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and 0 <= value < 2**53 else None


def _chain(value: Any) -> str:
    return value if isinstance(value, str) and _CHAIN_KEY.fullmatch(value) else ""


def clean_size(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    out: dict[str, Any] = {}
    for k in ("total", "each"):
        n = _num(value.get(k))
        if n is not None and n > 0:
            out[k] = n
    count = _int(value.get("count"))
    if count:
        out["count"] = count
    if value.get("unit") in UNITS:
        out["unit"] = value["unit"]
    return out or None


def _prices(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    out = {}
    for k, v in list(value.items())[:MAX_BRANCHES]:
        n = _num(v)
        if isinstance(k, str) and k.isdigit() and len(k) <= 9 and n is not None:
            out[k] = n
    return out


def clean_product(p: Any) -> dict[str, Any] | None:
    """A product from search: what the card shows and what a list line needs."""
    if not isinstance(p, dict) or not isinstance(p.get("key"), str) or not isinstance(p.get("name"), str):
        return None
    key = p["key"][:MAX_KEY]
    if key[:2] not in ("b:", "w:", "c:", "t:"):
        return None
    return {"key": key, "name": plain(p["name"]), "name_en": plain(p.get("name_en")), "name_ru": plain(p.get("name_ru")),
            "barcode": _str(p.get("barcode"), 14), "weighted": p.get("weighted") is True,
            "chains": [c for c in (p.get("chains") or [])[:10] if _chain(c)] if isinstance(p.get("chains"), list) else [],
            "prices": _prices(p.get("prices")), "size": clean_size(p.get("size"))}


def clean_chain_item(p: Any) -> dict[str, Any] | None:
    """One chain's product from the in-chain search (choosing the right one in that chain)."""
    if not isinstance(p, dict) or _int(p.get("item")) is None or not isinstance(p.get("name"), str):
        return None
    return {"item": p["item"], "name": plain(p["name"]), "name_en": plain(p.get("name_en")),
            "name_ru": plain(p.get("name_ru")), "size": clean_size(p.get("size")), "prices": _prices(p.get("prices")),
            "weighted": p.get("weighted") is True}


def _cart_url(cart: Any) -> str | None:
    if not isinstance(cart, dict) or cart.get("kind") != "link" or not isinstance(cart.get("url"), str):
        return None
    try:
        url = URL(cart["url"][:4000])
        if url.scheme != "https" or CART_HOSTS.get(url.host or "") != url.path or url.user or url.port != 443:
            return None
        return str(url)
    except ValueError:          # also a host that isn't valid punycode (UnicodeError is a ValueError)
        return None


def clean_compare(res: Any) -> dict[str, Any]:
    """The comparison as the card and the sensors use it."""
    if not isinstance(res, dict) or not isinstance(res.get("branches"), list) or not isinstance(res.get("lines"), list):
        raise SiteError("not a comparison")
    branches = []
    for b in res["branches"][:MAX_BRANCHES]:
        if not isinstance(b, dict) or _int(b.get("id")) is None:
            continue
        branches.append({
            "id": b["id"], "chain": _chain(b.get("chain")), "chain_name": plain(b.get("chain_name"), 40),
            "chain_name_en": plain(b.get("chain_name_en"), 40), "name": plain(b.get("name"), 80),
            "online": b.get("online") is True, "cheapest": b.get("cheapest") is True,
            **{k: _num(b.get(k)) or 0.0 for k in ("total", "fair", "fill_elsewhere", "shared_total")},
            **{k: _int(b.get(k)) or 0 for k in ("found", "missing", "pending", "other_size", "unsure")},
            "cart_url": _cart_url(b.get("cart")),
        })
    ids = {str(b["id"]) for b in branches}
    lines = []
    for ln in res["lines"][:MAX_ITEMS]:
        if not isinstance(ln, dict) or not isinstance(ln.get("key"), str):
            continue
        per = {}
        for bid, c in (ln.get("per_branch") or {}).items() if isinstance(ln.get("per_branch"), dict) else ():
            if bid not in ids:
                continue
            if not isinstance(c, dict) or _num(c.get("cost")) is None or _int(c.get("item")) is None:
                per[bid] = None
                continue
            per[bid] = {"item": c["item"], "name": plain(c.get("name")), "price": _num(c.get("price")) or 0.0,
                        "cost": _num(c.get("cost")), "source": _str(c.get("source"), 20),
                        "exact": c.get("exact") is True, "unsure": c.get("unsure") is True,
                        "weighted": c.get("weighted") is True, "size": clean_size(c.get("size")),
                        "size_mismatch": c.get("size_mismatch") is True, "counted": c.get("counted") is not False}
        alts = {}
        if isinstance(ln.get("alternatives"), dict):
            for chain, rows in list(ln["alternatives"].items())[:10]:
                if _chain(chain) and isinstance(rows, list):
                    alts[chain] = [r for r in (clean_chain_item(x) for x in rows[:6]) if r]
        sources = {c: _str(s, 20) for c, s in (ln.get("sources") or {}).items() if _chain(c)} \
            if isinstance(ln.get("sources"), dict) else {}
        lines.append({"key": ln["key"][:MAX_KEY], "name": plain(ln.get("name")), "qty": _num(ln.get("qty")) or 1.0,
                      "per_branch": per, "alternatives": alts, "sources": sources,
                      "pending": [c for c in (ln.get("pending") or []) if _chain(c)]
                      if isinstance(ln.get("pending"), list) else [],
                      "votable": ln.get("votable") is not False, "size": clean_size(ln.get("size")),
                      "sizes_differ": ln.get("sizes_differ") is True})
    return {"branches": branches, "lines": lines, "partial": res.get("partial") is True,
            "shared_count": _int(res.get("shared_count")) or 0}


# ---- the client ----------------------------------------------------------------------------------------
class SiteAPI:
    def __init__(self, session: aiohttp.ClientSession, base: str) -> None:
        self._session = session
        self.base = site_url(base)

    async def _call(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> Any:
        url = f"{self.base}{path}"
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        try:
            async with self._session.request(method, url, params=params, json=body, headers=headers, timeout=TIMEOUT,
                                             allow_redirects=False) as resp:
                if resp.status in (429, 503):
                    raise SiteBusy(f"busy ({resp.status})")
                if resp.status >= 300:
                    raise SiteError(f"HTTP {resp.status}")
                if resp.content_type != "application/json":
                    raise SiteError("not JSON")
                data = bytearray()
                async for chunk in resp.content.iter_chunked(65536):
                    data += chunk
                    if len(data) > MAX_BYTES:
                        raise SiteError("answer too large")
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise SiteError(f"can't reach the site: {type(err).__name__}") from None
        try:
            return json.loads(bytes(data))
        except ValueError:
            raise SiteError("broken JSON") from None

    async def health(self) -> dict[str, Any]:
        data = await self._call("GET", "/api/health")
        if not isinstance(data, dict) or data.get("ok") is not True:
            raise SiteError("not the price comparison site")
        return {"built_at": _str(data.get("built_at"), 40) or None, "importing": data.get("importing") is True,
                "matches": "crowd" if data.get("matches") == "crowd" else "admin"}

    async def cities(self, query: str) -> list[dict[str, Any]]:
        data = await self._call("GET", "/api/cities", {"q": str(query)[:40], "limit": "30"})
        out = []
        for c in data if isinstance(data, list) else []:
            if isinstance(c, dict) and _int(c.get("code")) and isinstance(c.get("he"), str):
                out.append({"code": c["code"], "he": plain(c["he"], 80), "en": plain(c.get("en"), 80),
                            "ru": plain(c.get("ru"), 80), "branches": _int(c.get("branches")) or 0})
        return out

    async def branches(self, city: int) -> list[dict[str, Any]]:
        """The town's branches (biggest first in each chain), those within 15 km, then the online shops."""
        data = await self._call("GET", "/api/branches", {"city": str(int(city))})
        if not isinstance(data, dict):
            raise SiteError("not a list of branches")
        out = []
        for group in ("local", "nearby", "online"):
            for b in data.get(group) if isinstance(data.get(group), list) else []:
                if not isinstance(b, dict) or _int(b.get("id")) is None or not _chain(b.get("chain")):
                    continue
                out.append({"id": b["id"], "chain": b["chain"], "chain_name": plain(b.get("chain_name"), 40),
                            "chain_name_en": plain(b.get("chain_name_en"), 40), "name": plain(b.get("name"), 80),
                            "online": b.get("online") is True, "group": group, "km": _num(b.get("km")),
                            "items": _int(b.get("items")) or 0})
        return out

    async def search(self, query: str, branches: list[int], limit: int = 24) -> list[dict[str, Any]]:
        data = await self._call("GET", "/api/search", {"q": str(query)[:MAX_QUERY], "limit": str(min(max(limit, 1), 60)),
                                                       "branches": ",".join(str(int(b)) for b in branches[:MAX_BRANCHES])})
        return [p for p in (clean_product(x) for x in (data if isinstance(data, list) else [])) if p]

    async def chain_search(self, chain: str, query: str, branches: list[int], limit: int = 20) -> list[dict[str, Any]]:
        if not _chain(chain):
            raise SiteError("unknown chain")
        data = await self._call("GET", "/api/chain_search", {
            "chain": chain, "q": str(query)[:MAX_QUERY], "limit": str(min(max(limit, 1), 30)),
            "branches": ",".join(str(int(b)) for b in branches[:MAX_BRANCHES])})
        return [p for p in (clean_chain_item(x) for x in (data if isinstance(data, list) else [])) if p]

    async def compare(self, branches: list[int], items: list[dict[str, Any]]) -> dict[str, Any]:
        body = {"branches": [int(b) for b in branches[:MAX_BRANCHES]],
                "items": [{"key": str(i["key"])[:MAX_KEY], "name": str(i.get("name") or "")[:MAX_NAME],
                           "qty": min(max(float(i.get("qty") or 1), 0.05), 99.0),
                           "choice": {c: int(v) for c, v in (i.get("choice") or {}).items()
                                      if c in CHAINS and isinstance(v, int) and not isinstance(v, bool) and 0 <= v < 2**53}}
                          for i in items[:MAX_ITEMS]]}
        return clean_compare(await self._call("POST", "/api/compare", body=body))

    async def suggest_match(self, key: str, chain: str, item: int) -> None:
        """The household's pick for a line in one chain, as a suggestion for the site's admin (it applies to the
        household at once anyway: every comparison carries it)."""
        if chain not in CHAINS or not isinstance(item, int) or item < 0:
            raise SiteError("invalid suggestion")
        await self._call("POST", "/api/vote", body={"key": str(key)[:MAX_KEY], "chain": chain, "item": item})
