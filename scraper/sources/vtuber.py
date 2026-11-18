"""VTuber 翻唱: songs ranked by how many times Taiwanese / HK / Macau VTubers covered them.

The covers come from a community playlist (about 3,000 videos), read with the YouTube Data
API v3 (`playlistItems.list`, 50 per page, 1 quota unit each; the key comes from the
YOUTUBE_API_KEY environment variable and is sent in a header, never in the URL).

1. Every playlist item is kept once per video id: the playlist has the same video more
   than once in places. Deleted and private videos are skipped.
2. Each title is cut into pieces by scraper/covers.py (song, original artist, performers),
   and the song is identified with the iTunes Search API using the first two pieces. The
   result, including "not found", is cached per search term in data/vtuber-songs.json, so
   only new titles are looked up; most popular terms first, within a time budget.
3. Covers are counted per song (identified songs group by iTunes title + artist; the rest by
   their guessed title) and ranked, ties sharing a rank.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time
import urllib.parse
from collections import defaultdict
from pathlib import Path

from .. import covers, enrich, match
from ..net import get_text

PLAYLIST_ID = "PLg42Bx1jWLfnUmAMCEEwsKE0yNUW5X6Jl"
PLAYLIST_URL = f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"
API = "https://www.googleapis.com/youtube/v3/playlistItems?"
FIELDS = ("nextPageToken,items(snippet(title,videoOwnerChannelTitle,publishedAt,resourceId/videoId),"
          "contentDetails/videoPublishedAt)")
ROOT = Path(__file__).resolve().parents[2]
VIDEOS = ROOT / "data" / "vtuber-covers.json"  # the playlist as last read: id -> title, channel, dates
SONGS = ROOT / "data" / "vtuber-songs.json"    # iTunes result per search term
TZ = dt.timezone(dt.timedelta(hours=8))
RECENT_DAYS = 90
MIN_COVERS = 3  # the all-time chart leaves off songs covered fewer times; the 90-day one lists every song
RETRY_DAYS = 30
LOOKUP_BUDGET = float(os.environ.get("VTUBER_LOOKUP_BUDGET", "600"))  # seconds of iTunes lookups per run
LOOKUP_MAX = int(os.environ.get("VTUBER_LOOKUP_MAX", "200"))

SOURCE = {
    "id": "vtuber",
    "name": {"zh": "VTuber 翻唱", "en": "VTuber Covers", "ja": "VTuber カバー"},
    "region": "tw",
    "kind": "cover",
    "site_url": PLAYLIST_URL,
}
CHART_TITLES = {
    "covers-all": {"zh": "累計翻唱次數", "en": "Most Covered · All Time", "ja": "累計カバー数"},
    "covers-90d": {"zh": f"近 {RECENT_DAYS} 天翻唱次數", "en": f"Most Covered · Last {RECENT_DAYS} Days",
                   "ja": f"直近 {RECENT_DAYS} 日のカバー数"},
}
SKIP_TITLES = {"Deleted video", "Private video"}


# ---------- YouTube ----------

def _read_once(key: str, playlist: str, videos: dict[str, dict]) -> int:
    """One pass over the playlist pages, adding videos not seen yet. Returns how many were new."""
    added, token = 0, None
    for _ in range(200):  # 10,000 videos at most; a loop guard, not a real limit
        params = {"part": "snippet,contentDetails", "playlistId": playlist, "maxResults": 50, "fields": FIELDS}
        if token:
            params["pageToken"] = token
        page = json.loads(get_text(API + urllib.parse.urlencode(params),
                                   {"Accept": "application/json", "X-Goog-Api-Key": key}))
        for item in page.get("items", []):
            snip = item.get("snippet") or {}
            vid = (snip.get("resourceId") or {}).get("videoId")
            title = snip.get("title") or ""
            if not vid or vid in videos or title in SKIP_TITLES or not snip.get("videoOwnerChannelTitle"):
                continue
            videos[vid] = {
                "t": title,
                "ch": snip["videoOwnerChannelTitle"],
                "pub": ((item.get("contentDetails") or {}).get("videoPublishedAt") or "")[:10] or None,
                "added": (snip.get("publishedAt") or "")[:10] or None,
            }
            added += 1
        token = page.get("nextPageToken")
        if not token:
            break
    return added


def fetch_playlist(key: str, playlist: str = PLAYLIST_ID, passes: int = 3) -> dict[str, dict]:
    """Every public video in the playlist, once per video id.

    On a playlist this long the API's pages can overlap, so one pass may skip some videos
    (one run missed 32 of 2,929). Passes are repeated, keeping the union, until one adds
    nothing new; at most `passes` times."""
    videos: dict[str, dict] = {}
    for i in range(passes):
        if not _read_once(key, playlist, videos) and i:
            break
    return videos


# ---------- identify ----------

def term_of(video: dict) -> tuple[list[str], str]:
    segs = covers.segments(video["t"], video.get("ch"))
    return segs, covers.query(segs)


def search(term: str, segs: list[str], country: str) -> dict | None:
    query = urllib.parse.urlencode({"term": term, "country": country, "media": "music", "entity": "song",
                                    "limit": 15, "lang": "en_us"})
    try:
        body = get_text(enrich.ITUNES + query, {"Accept": "application/json"})
    except RuntimeError as exc:
        if "403" in str(exc) or "429" in str(exc):
            raise enrich.RateLimited(str(exc)) from exc
        raise
    finally:
        time.sleep(enrich.ITUNES_DELAY)
    return covers.pick(json.loads(body).get("results", []), segs)


def identify(videos: dict[str, dict], songs: dict, itunes: dict, today: dt.date,
             budget: float = LOOKUP_BUDGET, max_terms: int = LOOKUP_MAX) -> dict:
    """Look up search terms not in the cache (or not found RETRY_DAYS ago), most covered first."""
    todo: dict[str, dict] = {}
    for video in videos.values():
        segs, term = term_of(video)
        key = match.norm(term)
        if not key:
            continue
        entry = songs.get(key)
        if entry and (entry.get("status") == "ok" or
                      (today - dt.date.fromisoformat(entry.get("checked", "1970-01-01"))).days < RETRY_DAYS):
            continue
        item = todo.setdefault(key, {"term": term, "segs": segs, "n": 0})
        item["n"] += 1
    order = sorted(todo.items(), key=lambda kv: (-kv[1]["n"], kv[0]))
    stats = {"todo": len(order), "looked_up": 0, "found": 0}
    start = time.monotonic()
    for key, item in order[:max_terms]:
        if time.monotonic() - start > budget:
            break
        first = "jp" if covers.looks_japanese(item["term"]) else "tw"
        try:
            hit, used = None, None
            for country in (first, enrich.OTHER[first]):
                hit = search(item["term"], item["segs"], country)
                if hit:
                    used = country
                    break
        except enrich.RateLimited as exc:
            print(f"::warning title=iTunes rate limited::{exc}", file=sys.stderr)
            break
        except Exception as exc:  # noqa: BLE001 - one bad title must not stop the batch
            print(f"iTunes lookup failed for {item['term']}: {exc}", file=sys.stderr)
            continue
        stats["looked_up"] += 1
        if hit:
            stats["found"] += 1
            entry = {"status": "ok", "id": hit.get("trackId"), "name": hit.get("trackName"),
                     "artist": hit.get("artistName"), "genre": hit.get("primaryGenreName"), "cc": used,
                     "checked": today.isoformat()}
            songs[key] = entry
            # Share the match with the genre / Apple Music step so it needs no lookup of its own.
            itunes.setdefault(match.song_key(entry["name"], entry["artist"]), {
                "status": "ok", "genre": entry["genre"], "id": entry["id"], "cc": used,
                "name": entry["name"], "artist": entry["artist"], "checked": today.isoformat()})
        else:
            songs[key] = {"status": "none", "checked": today.isoformat()}
    return stats


# ---------- rank ----------

def group_covers(videos: dict[str, dict], songs: dict) -> dict[str, dict]:
    """Song -> its title, artist and the cover videos.

    A match counts as confirmed when the matched artist is written in the cover title. A cover
    named by its title alone may have been matched to an older song of the same name (Mr. Big's
    "Jane Doe" for 米津玄師's), so unconfirmed and unidentified covers join the confirmed song with
    that title (the most covered one if there are several). With none, unconfirmed matches of one
    title fall together under the most common one, and unidentified covers join it or group by
    their guessed title."""
    known_artists: set[str] = set()
    for entry in songs.values():
        if entry.get("status") == "ok":
            known_artists.add(match.norm(match.first_artist(entry["artist"])))
    groups: dict[str, dict] = {}
    weak: dict[str, dict[str, list]] = defaultdict(dict)   # title -> song key -> [group, videos]
    pending = []
    for vid, video in videos.items():
        segs, term = term_of(video)
        if not segs:
            continue
        entry = songs.get(match.norm(term)) or {}
        if entry.get("status") != "ok":
            pending.append((vid, covers.guess(segs, known_artists)))
            continue
        key = covers.song_group(entry["name"], entry["artist"])
        # "有一種悲傷 (電影《…》主題曲)" shows as 有一種悲傷, as KTV charts list it
        group = {"title": covers.display_title(entry["name"]), "artist": entry["artist"], "videos": []}
        title = match.norm(group["title"])
        artist = match.norm(match.first_artist(entry["artist"]))
        if len(artist) >= 2 and artist in match.norm(" ".join(segs)).replace(title, "", 1):
            groups.setdefault(key, group)["videos"].append(vid)
        else:
            weak[title].setdefault(key, [group, []])[1].append(vid)
    confirmed: dict[str, list[str]] = defaultdict(list)
    for key, g in groups.items():
        confirmed[match.norm(g["title"])].append(key)
    by_title: dict[str, str] = {}
    for title, keys in confirmed.items():
        by_title[title] = max(keys, key=lambda k: len(groups[k]["videos"]))
    for title, cands in weak.items():
        if title not in by_title:
            by_title[title] = max(cands, key=lambda k: len(cands[k][1]))
            groups[by_title[title]] = cands[by_title[title]][0]
        groups[by_title[title]]["videos"].extend(v for _, vids in cands.values() for v in vids)
    for vid, (title, artist) in pending:
        t = match.norm(match.clean_title(title))
        if not t:
            continue
        key = by_title.get(t, "?" + t)
        g = groups.setdefault(key, {"title": match.clean_title(title), "artist": artist, "videos": []})
        g["videos"].append(vid)
    return groups


def performers(vids: list[str], videos: dict[str, dict]) -> list[list[str]]:
    """[name, video id] of each uploader, newest cover first; a channel that covered the song
    twice is listed once, with its newest video."""
    out, seen = [], set()
    for v in sorted(vids, key=lambda v: (videos[v].get("pub") or "", v), reverse=True):
        name = covers.performer_name(videos[v].get("ch"))
        if name and name not in seen:
            seen.add(name)
            out.append([name, v])
    return out


def rank_rows(groups: dict[str, dict], videos: dict[str, dict], since: str | None = None,
              min_covers: int = 1) -> list[dict]:
    """Rows by cover count (ties share a rank), newest cover first among equals; songs with
    fewer than `min_covers` covers are left off."""
    scored = []
    for g in groups.values():
        vids = [v for v in g["videos"] if since is None or (videos[v].get("pub") or "") >= since]
        if not vids or len(vids) < min_covers:
            continue
        latest = max(vids, key=lambda v: (videos[v].get("pub") or "", v))
        scored.append((len(vids), videos[latest].get("pub") or "", g, latest, vids))
    scored.sort(key=lambda s: (-s[0], "".join(chr(0x10FFFF - ord(c)) for c in s[1]), match.norm(s[2]["title"])))
    rows, prev, rank = [], None, 0
    for i, (n, _, g, latest, vids) in enumerate(scored):
        if n != prev:
            rank, prev = i + 1, n
        rows.append({"rank": rank, "title": g["title"], "artist": g["artist"], "covers": n, "cover_video": latest,
                     "performers": performers(vids, videos)})
    return rows


def build_charts(videos: dict[str, dict], songs: dict, today: dt.date) -> list[dict]:
    groups = group_covers(videos, songs)
    since = today - dt.timedelta(days=RECENT_DAYS - 1)
    out = []
    for cid, rows, period in [
        ("covers-all", rank_rows(groups, videos, min_covers=MIN_COVERS), f"{today:%Y/%m/%d}"),
        ("covers-90d", rank_rows(groups, videos, since.isoformat()), f"{since:%Y/%m/%d} ~ {today:%Y/%m/%d}"),
    ]:
        out.append({"id": cid, "title": CHART_TITLES[cid], "period": period, "source_url": PLAYLIST_URL,
                    "prev_from": "history", "videos": sum(r["covers"] for r in rows), "rows": rows})
    return out


def fetch() -> list[dict]:
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not key:
        raise RuntimeError("YOUTUBE_API_KEY is not set")
    today = dt.datetime.now(TZ).date()
    videos = fetch_playlist(key)
    if not videos:
        raise RuntimeError("vtuber: the playlist came back empty")
    enrich._save(VIDEOS, {"playlist": PLAYLIST_ID, "fetched": today.isoformat(), "videos": videos})  # a snapshot, replaced each run
    songs, itunes = enrich.load_cache(SONGS), enrich.load_cache(enrich.ITUNES_CACHE)
    stats = identify(videos, songs, itunes, today)
    enrich.save_cache(SONGS, songs)
    enrich.save_cache(enrich.ITUNES_CACHE, itunes)
    print(f"vtuber: {len(videos)} videos, {stats['todo']} new search terms, "
          f"looked up {stats['looked_up']}, found {stats['found']}")
    return build_charts(videos, songs, today)


JOBS = [{"name": "covers", "charts": list(CHART_TITLES), "fetch": fetch}]
