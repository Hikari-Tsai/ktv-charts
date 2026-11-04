"""好樂迪: POST /Ashx/SongInfo.ashx, URL-encoded string fields, 20 rows per page."""

from __future__ import annotations

import re
import urllib.parse

from ..net import post_json_array

ENDPOINT = "https://www.holiday.com.tw/Ashx/SongInfo.ashx"
PAGE_URL = "https://www.holiday.com.tw/SongInfo/SongList.aspx?st=top&lt={ltype}"

SOURCE = {
    "id": "holiday",
    "name": {"zh": "好樂迪", "en": "Holiday", "ja": "好樂迪 (Holiday)"},
    "region": "tw",
    "site_url": "https://www.holiday.com.tw/",
}

CHARTS = [
    ("tc", {"zh": "國語點播", "en": "Mandarin Requests", "ja": "中国語リクエスト"}),
    ("tt", {"zh": "台語點播", "en": "Taiwanese Requests", "ja": "台湾語リクエスト"}),
    ("ct", {"zh": "粵語點播", "en": "Cantonese Requests", "ja": "広東語リクエスト"}),
    ("et", {"zh": "英語點播", "en": "English Requests", "ja": "英語リクエスト"}),
    ("jt", {"zh": "日語點播", "en": "Japanese Requests", "ja": "日本語リクエスト"}),
    ("kt", {"zh": "韓語點播", "en": "Korean Requests", "ja": "韓国語リクエスト"}),
    ("vt", {"zh": "越南語點播", "en": "Vietnamese Requests", "ja": "ベトナム語リクエスト"}),
    ("nc", {"zh": "國語新歌", "en": "Mandarin New Songs", "ja": "中国語新曲"}),
    ("nt", {"zh": "台語新歌", "en": "Taiwanese New Songs", "ja": "台湾語新曲"}),
]


def _dec(value):
    return urllib.parse.unquote(value) if isinstance(value, str) else value


def _call(ltype: str, page: int) -> dict:
    data = post_json_array(ENDPOINT, {"m": "top", "ltype": ltype, "page": page})[0]
    if data.get("Ok") != "1":
        raise RuntimeError(f"holiday {ltype}: Ok={data.get('Ok')} {_dec(data.get('Msg'))}")
    return data


def _int_or_none(value: str):
    value = (value or "").strip()
    return int(value) if value.isdigit() and int(value) > 0 else None


def fetch_chart(ltype: str, title: dict) -> dict:
    first = _call(ltype, 1)
    raw = list(first.get("DataList") or [])
    for page in range(2, int(first["Page"][0]["MaxPage"]) + 1):
        raw += _call(ltype, page).get("DataList") or []
    rows = []
    for item in raw:
        item = {k: _dec(v) for k, v in item.items()}
        if not item.get("id"):
            continue
        last = _int_or_none(item.get("lastweek"))
        kk = re.search(r"[?&]id=([A-Za-z0-9_-]+)", item.get("songurl") or "")
        rows.append({
            "rank": int(item["thisweek"]),
            "title": item["songname"],
            "artist": item["singer"],
            "song_no": item["id"],
            "kkbox": kk.group(1) if kk else None,  # KKBOX song id from the preview widget link
            "last_rank": last,
            "is_new": last is None,
        })
    if not rows:
        raise RuntimeError(f"holiday {ltype}: empty chart")
    sdate, edate = _dec(first.get("sdate")), _dec(first.get("edate"))
    return {
        "id": ltype,
        "title": title,
        "period": f"{sdate} ~ {edate}" if sdate and edate else None,
        "source_url": PAGE_URL.format(ltype=ltype),
        "prev_from": "site",
        "rows": sorted(rows, key=lambda r: r["rank"]),
    }


JOBS = [
    {"name": ltype, "charts": [ltype], "fetch": (lambda lt=ltype, t=title: [fetch_chart(lt, t)])}
    for ltype, title in CHARTS
]
