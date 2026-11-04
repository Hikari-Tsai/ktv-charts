"""DAM: static HTML, one <div class="c-section" id="ranking-..."> per chart. No previous rank."""

from __future__ import annotations

import datetime as dt
import html
import re

from ..net import get_text

BASE = "https://www.clubdam.com"

SOURCE = {
    "id": "dam",
    "name": {"zh": "DAM", "en": "DAM", "ja": "DAM"},
    "region": "jp",
    "site_url": "https://www.clubdam.com/",
}


def _t(zh: str, en: str, ja: str) -> dict:
    return {"zh": zh, "en": en, "ja": ja}

# (job name, page path, [(section id on page, chart id, title, period kind)])
PAGES = [
    ("ranking", "/ranking/", [
        ("ranking-daily", "all-daily", _t("綜合日榜", "Overall · Daily", "総合 デイリー"), "daily"),
        ("ranking-weekly", "all-weekly", _t("綜合週榜", "Overall · Weekly", "総合 週間"), "weekly"),
        ("ranking-monthly", "all-monthly", _t("綜合月榜", "Overall · Monthly", "総合 月間"), "monthly"),
    ]),
    ("burst", "/ranking/burst/", [("ranking-weekly", "burst-weekly", _t("急上昇週榜", "Rising · Weekly", "急上昇 週間"), "weekly")]),
    ("anison", "/genre/anison/", [("ranking-weekly", "anime-weekly", _t("動畫週榜", "Anime · Weekly", "アニメ 週間"), "weekly")]),
    ("vocaloid", "/genre/vocaloid/", [("ranking-weekly", "vocaloid-weekly", _t("VOCALOID週榜", "VOCALOID · Weekly", "ボーカロイド 週間"), "weekly")]),
    ("vtuber", "/genre/vtuber/", [("ranking-weekly", "vtuber-weekly", _t("VTuber週榜", "VTuber · Weekly", "VTuber 週間"), "weekly")]),
    ("enka", "/genre/enka/", [("ranking-weekly", "enka-weekly", _t("演歌週榜", "Enka · Weekly", "演歌・歌謡 週間"), "weekly")]),
    ("foreign", "/genre/foreign/", [("ranking-weekly", "foreign-weekly", _t("外國曲週榜", "Foreign · Weekly", "外国曲 週間"), "weekly")]),
    ("duet", "/ranking/duet/", [("ranking-weekly", "duet-weekly", _t("對唱週榜", "Duet · Weekly", "デュエット 週間"), "weekly")]),
]

_SECTION = re.compile(r'<div class="c-section" id="([^"]+)">(.*?)(?=<div class="c-section" id="|\Z)', re.S)
_DATE = re.compile(r'p-section-header__date">\s*(\d{4}/\d{1,2}/\d{1,2})')
_ROW = re.compile(
    r'href="(/karaokesearch/songleaf\.html\?requestNo=([\d-]+))"[^>]*>\s*'
    r'<div class="p-ranking__num[^"]*">\s*(\d+)\s*</div>'
    r'.*?p-song__title">(.*?)</h4>\s*<div class="p-song__artist">(.*?)</div>',
    re.S,
)


def derive_period(updated: str | None, kind: str) -> str | None:
    """DAM only shows the update date; the FAQ defines the window it covers."""
    if not updated:
        return None
    day = dt.datetime.strptime(updated, "%Y/%m/%d").date()
    fmt = lambda d: d.strftime("%Y/%m/%d")
    if kind == "daily":
        return fmt(day - dt.timedelta(days=1))
    if kind == "weekly":
        end = day - dt.timedelta(days=1)
        return f"{fmt(end - dt.timedelta(days=6))} ~ {fmt(end)}"
    if kind == "monthly":
        end = day.replace(day=1) - dt.timedelta(days=1)
        return f"{fmt(end.replace(day=1))} ~ {fmt(end)}"
    return None


def parse_sections(page: str) -> dict[str, dict]:
    out = {}
    for sid, body in _SECTION.findall(page):
        date = _DATE.search(body)
        rows, seen = [], set()
        for href, req_no, rank, title, artist in _ROW.findall(body):
            if req_no in seen:  # PC and mobile markup repeat each row
                continue
            seen.add(req_no)
            rows.append({
                "rank": int(rank),
                "title": html.unescape(re.sub(r"<[^>]+>", "", title)).strip(),
                "artist": html.unescape(re.sub(r"<[^>]+>", "", artist)).strip(),
                "song_no": req_no,
                "song_url": BASE + href,
            })
        out[sid] = {"updated": date.group(1) if date else None, "rows": rows}
    return out


def fetch_page(path: str, wanted: list[tuple[str, str, dict, str]]) -> list[dict]:
    url = BASE + path
    sections = parse_sections(get_text(url))
    charts = []
    for sid, cid, title, kind in wanted:
        sec = sections.get(sid)
        if not sec or not sec["rows"]:
            raise RuntimeError(f"dam {path}: section #{sid} missing or empty")
        charts.append({
            "id": cid,
            "title": title,
            "period": derive_period(sec["updated"], kind),
            "updated": sec["updated"],
            "source_url": url,
            "prev_from": "history",
            "rows": sorted(sec["rows"], key=lambda r: r["rank"]),
        })
    return charts


JOBS = [
    {"name": name, "charts": [w[1] for w in wanted], "fetch": (lambda p=path, w=wanted: fetch_page(p, w))}
    for name, path, wanted in PAGES
]
