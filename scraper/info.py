"""Merge publishing details from the credit caches into the `info` field of a chart row.

Pure functions, no network: scraper.credits fills the caches, scraper.enrich calls
build_info() when it writes the site data.

Priority: Taiwan's National Central Library ISRC records (credits, label, ISRC), then
MusicBrainz (credits for songs NCL does not have, mostly Japanese and Western), then
Apple's album data (release date, album, copyright line) for everything iTunes matched.
The release year is the earliest date any source gives, since re-releases and digital
reissues carry later dates than the original.
"""

from __future__ import annotations

import re

ROLES = ("lyricist", "composer", "arranger", "producer", "mix", "recording", "mastering")
_COPYRIGHT = re.compile(r"^(?:this compilation\s*)?(?:℗|©|Ⓟ|\(p\)|\(c\)|\s)*\s*(\d{4})?[\s,.]*(.*)$", re.I)


def copyright_holder(text: str | None) -> tuple[str | None, str | None]:
    """'℗ 2018 Sony Music Labels Inc.' -> ('2018', 'Sony Music Labels Inc')."""
    if not text:
        return None, None
    m = _COPYRIGHT.match(text.strip())
    if not m:
        return None, None
    holder = re.split(r",?\s*(?:under (?:exclusive )?licen[cs]e|distributed by|marketed by|a division of)\b", m.group(2), flags=re.I)[0]
    holder = holder.strip(" .,;")
    return m.group(1), holder or None


def _year(date: str | None) -> str | None:
    return date[:4] if date and re.match(r"^\d{4}", date) and date[:4] != "0000" else None


def build_info(ncl: dict | None, mb: dict | None, apple: dict | None) -> dict:
    ncl = ncl if ncl and ncl.get("status") == "ok" else {}
    mb = mb if mb and mb.get("status") == "ok" else {}
    apple = apple if apple and apple.get("status") == "ok" else {}
    info: dict = {}
    used: set[str] = set()

    def put(field: str, *candidates: tuple) -> None:
        for value, source in candidates:
            if value:
                info[field] = value
                used.add(source)
                return

    nc, mc = ncl.get("credits") or {}, dict(mb.get("credits") or {})
    for role in ("lyricist", "composer"):  # MusicBrainz "writer" credits both words and music
        if not mc.get(role) and mc.get("writer"):
            mc[role] = mc["writer"]
    for role in ROLES:
        put(role, ((nc.get(role) or [])[:6], "ncl"), ((mc.get(role) or [])[:6], "mb"))

    # Earliest date wins (reissues carry later dates); within that year keep the most precise one.
    dates = [(d, s) for d, s in ((ncl.get("released"), "ncl"), (mb.get("released"), "mb"),
                                 (apple.get("released"), "apple")) if _year(d)]
    if dates:
        year = min(d[:4] for d, _ in dates)
        date, source = max((x for x in dates if x[0][:4] == year), key=lambda x: len(x[0]))
        info["year"], info["released"] = year, date
        used.add(source)

    _, holder = copyright_holder(apple.get("copyright"))
    put("label", (ncl.get("label"), "ncl"), (holder, "apple"))
    put("album", (ncl.get("album"), "ncl"), (apple.get("album"), "apple"), (mb.get("album"), "mb"))
    put("isrc", (ncl.get("isrc"), "ncl"), (mb.get("isrc"), "mb"))
    if ncl.get("maker") != info.get("label"):
        put("maker", (ncl.get("maker"), "ncl"))
    put("type", (ncl.get("type"), "ncl"))
    put("copyright", (apple.get("copyright"), "apple"))
    put("ncl", (ncl.get("item"), "ncl"))  # NCL track page id, for the source link
    put("mb", (mb.get("id"), "mb"))
    if not info:
        return {}
    info["src"] = [s for s in ("ncl", "mb", "apple") if s in used]
    return info
