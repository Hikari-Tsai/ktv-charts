"""site/data/range.json: every charted song with a chorus range, for the range finder tab.

Built from the annotated chart files with no network, each time scraper.enrich.apply_files
runs (so after the BPM, hashtag and vocal range steps too). A song on several charts is
listed once, keyed like the rest of the site by clean title + artist; the page filters it
by the visitor's own range.
"""

from __future__ import annotations

from . import match

# Per-chart details the page does not need in this list (rank movement belongs to one chart).
_DROP = ("rank", "last_rank", "is_new", "covers", "cover_video", "performers")


def build(sites: dict[str, dict], updated_at: str | None = None) -> dict:
    """{"updated_at", "titles": {"src/chart": title}, "rows": [...]}, most charted songs first.

    Each row keeps the fields of the song's best-ranked chart row (filled in from its other
    rows) plus "seen": [[source, chart, rank], ...], best rank first."""
    songs: dict[str, dict] = {}
    titles: dict[str, object] = {}
    for src, data in sites.items():
        for chart in data.get("charts", []):
            for row in chart.get("rows", []):
                r = row.get("range")
                if not (isinstance(r, dict) and isinstance(r.get("low"), int) and isinstance(r.get("high"), int)):
                    continue
                if not row.get("artist"):
                    continue  # VTuber covers whose original artist is unknown ("--")
                key = match.song_key(row.get("title"), row.get("artist"))
                if key.startswith("|") or key.endswith("|"):
                    continue
                titles[f"{src}/{chart['id']}"] = chart.get("title")
                song = songs.setdefault(key, {"best": None, "fields": {}, "seen": []})
                song["seen"].append([src, chart["id"], row.get("rank") or 0])
                if song["best"] is None or (row.get("rank") or 10**6) < song["best"]:
                    song["best"] = row.get("rank") or 10**6
                    song["fields"] = {**song["fields"], **row}
                else:
                    song["fields"] = {**row, **song["fields"]}
    rows = []
    for song in songs.values():
        fields = {k: v for k, v in song["fields"].items() if k not in _DROP}
        seen = sorted(song["seen"], key=lambda s: (s[2], s[0], s[1]))
        rows.append({**fields, "seen": seen})
    # Songs on more charts first, then by their best rank: a rough popularity order.
    rows.sort(key=lambda r: (-len(r["seen"]), r["seen"][0][2], match.norm(r.get("title"))))
    return {"updated_at": updated_at, "titles": titles, "rows": rows}
