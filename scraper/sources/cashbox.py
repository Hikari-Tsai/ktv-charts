"""錢櫃: POST /ashx/ah_Song.ashx, needs a cashboxparty.com Referer, one row per song."""

from __future__ import annotations

import html

from ..net import post_json_array

ENDPOINT = "https://www.cashboxparty.com/ashx/ah_Song.ashx"
PAGE_URL = "https://www.cashboxparty.com/Music/KTVMusic.aspx"
HEADERS = {"Referer": PAGE_URL}

SOURCE = {
    "id": "cashbox",
    "name": {"zh": "錢櫃", "en": "Cashbox", "ja": "錢櫃 (Cashbox)"},
    "region": "tw",
    "site_url": "https://www.cashboxparty.com/",
}

LANG = {
    "01": {"zh": "國語", "en": "Mandarin", "ja": "中国語"},
    "02": {"zh": "台語", "en": "Taiwanese", "ja": "台湾語"},
    "03": {"zh": "粵語", "en": "Cantonese", "ja": "広東語"},
    "04": {"zh": "日語", "en": "Japanese", "ja": "日本語"},
    "05": {"zh": "英語", "en": "English", "ja": "英語"},
}
KIND = {
    "1": ("new", {"zh": "新歌", "en": " New Songs", "ja": "新曲"}),
    "2": ("hot", {"zh": "點播", "en": " Requests", "ja": "リクエスト"}),
}


def fetch_bill(t: str, langs: str) -> list[dict]:
    rows = post_json_array(ENDPOINT, {"m": "bl", "t": t, "lang": langs}, HEADERS)
    if not rows:
        raise RuntimeError(f"cashbox bl t={t}: empty response")
    if rows[0].get("Result") != "0":
        raise RuntimeError(f"cashbox bl t={t}: Result={rows[0].get('Result')} {rows[0].get('Msg')}")
    prefix, label = KIND[t]
    charts: dict[str, dict] = {}
    for item in rows:
        if not item.get("SongNo"):
            continue
        code = item["LangCode"]
        chart = charts.setdefault(code, {
            "id": f"{prefix}-{code}",
            "title": {k: LANG.get(code, {}).get(k, item.get("LangName", code)) + label[k] for k in label},
            "period": f"{item['StartDate']} ~ {item['EndDate']}",
            "source_url": PAGE_URL,
            "prev_from": "site",
            "rows": [],
        })
        last = int(item["LastWeekend"]) if str(item.get("LastWeekend", "")).isdigit() else 0
        chart["rows"].append({
            "rank": int(item["ThisWeekend"]),
            "title": html.unescape(item["SongName"]),
            "artist": html.unescape(item["Singer"]),
            "song_no": item["SongNo"],
            "last_rank": last or None,
            "is_new": last == 0,
        })
    if not charts:
        raise RuntimeError(f"cashbox bl t={t} lang={langs}: no songs")
    for c in charts.values():
        c["rows"].sort(key=lambda r: r["rank"])
    order = langs.split(",")
    return [charts[code] for code in order if code in charts]


JOBS = [
    {"name": "hot", "charts": ["hot-01", "hot-02"], "fetch": lambda: fetch_bill("2", "01,02")},
    {"name": "foreign", "charts": ["hot-03", "hot-04", "hot-05"], "fetch": lambda: fetch_bill("2", "03,04,05")},
    {"name": "new", "charts": ["new-01", "new-02"], "fetch": lambda: fetch_bill("1", "01,02")},
]
