"""KKBOX 風雲榜: the JSON API behind kma.kkbox.com/charts. Gives this and last period ranks.

GET https://kma.kkbox.com/charts/api/v1/{daily|weekly}?terr=tw&lang=tc&type=song&category=<id>&limit=50
Weekly charts run Friday to Thursday; `date` in the response is the Thursday.
"""

from __future__ import annotations

import datetime as dt
import json

from ..net import get_text

API = "https://kma.kkbox.com/charts/api/v1/{period}?terr=tw&lang=tc&type={type}&category={category}&limit=50"
PAGE = "https://kma.kkbox.com/charts/{period}/{type}?terr=tw&lang=tc&cate={category}"

SOURCE = {
    "id": "kkbox",
    "name": {"zh": "KKBOX", "en": "KKBOX", "ja": "KKBOX"},
    "region": "tw",
    "kind": "streaming",
    "site_url": "https://kma.kkbox.com/charts/?terr=tw&lang=tc",
}

LANG = {
    297: {"zh": "華語", "en": "Mandopop", "ja": "中国語"},
    304: {"zh": "台語", "en": "Taiwanese", "ja": "台湾語"},
    390: {"zh": "西洋", "en": "Western", "ja": "洋楽"},
    308: {"zh": "日語", "en": "Japanese", "ja": "日本語"},
    314: {"zh": "韓語", "en": "Korean", "ja": "韓国語"},
    320: {"zh": "粵語", "en": "Cantonese", "ja": "広東語"},
}
PERIOD = {
    ("daily", "song"): {"zh": "單曲日榜", "en": " · Daily", "ja": " デイリー"},
    ("weekly", "song"): {"zh": "單曲週榜", "en": " · Weekly", "ja": " 週間"},
    ("weekly", "newrelease"): {"zh": "新歌週榜", "en": " · New Releases", "ja": " 新曲 週間"},
}
CHARTS = [  # (period, type, category), grouped by language
    *[(p, "song", c) for c in (297, 304, 390, 308, 314, 320) for p in ("daily", "weekly")],
    ("weekly", "newrelease", 297),
]


def chart_id(period: str, type_: str, category: int) -> str:
    return f"{type_}-{period}-{category}"


def chart_title(period: str, type_: str, category: int) -> dict:
    lang, suffix = LANG[category], PERIOD[(period, type_)]
    return {k: lang[k] + suffix[k] for k in ("zh", "en", "ja")}


def derive_period(period: str, date: str | None) -> str | None:
    if not date:
        return None
    end = dt.date.fromisoformat(date)
    if period == "weekly":
        return f"{(end - dt.timedelta(days=6)):%Y/%m/%d} ~ {end:%Y/%m/%d}"
    return f"{end:%Y/%m/%d}"


def parse(payload: dict, type_: str) -> tuple[str | None, list[dict]]:
    if payload.get("code") not in (0, "0"):
        raise RuntimeError(f"kkbox: code={payload.get('code')} {payload.get('message', '')}")
    data = payload.get("data") or {}
    items = (data.get("charts") or {}).get(type_) or []
    rows = []
    for item in items:
        ranks = item.get("rankings") or {}
        last = ranks.get("last_period")
        last = last if isinstance(last, int) and last > 0 else None
        rows.append({
            "rank": int(ranks["this_period"]),
            "title": item.get("song_name", ""),
            "artist": item.get("artist_name", ""),
            "song_url": item.get("song_url"),
            "last_rank": last,
            "is_new": last is None,
        })
    return data.get("date"), sorted(rows, key=lambda r: r["rank"])


def fetch_chart(period: str, type_: str, category: int) -> dict:
    url = API.format(period=period, type=type_, category=category)
    date, rows = parse(json.loads(get_text(url, {"Accept": "application/json"})), type_)
    if not rows:
        raise RuntimeError(f"kkbox {period}/{type_}/{category}: empty chart")
    return {
        "id": chart_id(period, type_, category),
        "title": chart_title(period, type_, category),
        "period": derive_period(period, date),
        "source_url": PAGE.format(period=period, type=type_, category=category),
        "prev_from": "site",
        "rows": rows,
    }


JOBS = [
    {
        "name": chart_id(p, t, c),
        "charts": [chart_id(p, t, c)],
        "fetch": (lambda p=p, t=t, c=c: [fetch_chart(p, t, c)]),
    }
    for p, t, c in CHARTS
]
