"""JOYSOUND: server-rendered pages with a schema.org ItemList in JSON-LD. No previous rank."""

from __future__ import annotations

import html
import json
import re

from ..net import get_text

BASE = "https://www.joysound.com/web/karaoke/ranking/"

SOURCE = {
    "id": "joysound",
    "name": {"zh": "JOYSOUND", "en": "JOYSOUND", "ja": "JOYSOUND"},
    "region": "jp",
    "site_url": "https://www.joysound.com/",
}

CHARTS = [
    ("all-daily", "all", {"zh": "綜合日榜", "en": "Overall · Daily", "ja": "総合 デイリー"}),
    ("all-weekly", "all/weekly", {"zh": "綜合週榜", "en": "Overall · Weekly", "ja": "総合 週間"}),
    ("all-monthly", "all/monthly", {"zh": "綜合月榜", "en": "Overall · Monthly", "ja": "総合 月間"}),
    ("anime-weekly", "anime/weekly", {"zh": "動畫週榜", "en": "Anime · Weekly", "ja": "アニメ 週間"}),
    ("vocaloid-weekly", "vocaloid/weekly", {"zh": "VOCALOID週榜", "en": "VOCALOID · Weekly", "ja": "ボカロ 週間"}),
    ("enka-weekly", "enka/weekly", {"zh": "演歌週榜", "en": "Enka · Weekly", "ja": "演歌 週間"}),
    ("foreign-weekly", "foreign/weekly", {"zh": "西洋週榜", "en": "Western · Weekly", "ja": "洋楽 週間"}),
]

_LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
_PERIOD = re.compile(r"集計期間\s*[:：]\s*(?:<[^>]+>\s*)*(\d{4}/\d{1,2}(?:/\d{1,2})?(?:\s*[-~〜]\s*\d{4}/\d{1,2}(?:/\d{1,2})?)?)")


def parse_page(page: str) -> tuple[str | None, list[dict]]:
    m = _PERIOD.search(page)
    period = re.sub(r"\s*[-~〜]\s*", " ~ ", m.group(1).strip()) if m else None
    rows: list[dict] = []
    for block in _LD.findall(page):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        nodes = data.get("@graph", [data]) if isinstance(data, dict) else data
        for node in nodes:
            lst = node.get("mainEntity") if isinstance(node, dict) else None
            if not (isinstance(lst, dict) and lst.get("@type") == "ItemList"):
                continue
            for el in lst.get("itemListElement", []):
                song = el.get("item") or {}
                artist = song.get("byArtist") or {}
                rows.append({
                    "rank": int(el["position"]),
                    "title": html.unescape(song.get("name", "")),
                    "artist": html.unescape(artist.get("name", "")),
                    "song_url": song.get("url"),
                })
    return period, rows


def fetch_chart(chart_id: str, path: str, title: dict) -> dict:
    url = BASE + path
    period, rows = parse_page(get_text(url))
    if not rows:
        raise RuntimeError(f"joysound {path}: no JSON-LD ItemList found")
    return {
        "id": chart_id,
        "title": title,
        "period": period,
        "source_url": url,
        "prev_from": "history",
        "rows": sorted(rows, key=lambda r: r["rank"]),
    }


JOBS = [
    {"name": cid, "charts": [cid], "fetch": (lambda c=cid, p=path, t=title: [fetch_chart(c, p, t)])}
    for cid, path, title in CHARTS
]
