"""Find Spotify track ids for chart songs, for the Spotify listen button.

    python -m scraper.spotify                       # look up new songs, then annotate
    python -m scraper.spotify --max 1500 --budget 900

Needs SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET (a Spotify for Developers app, client
credentials flow). Without them the lookup is skipped and the site keeps any ids already
cached. Spotify only serves Development Mode apps while the app owner has Premium, so
ids are cached permanently in data/spotify.json: the embed player needs no API key, and
songs found while the subscription was active keep their button after it lapses.

Matching reuses the iTunes rules (scraper.enrich.pick_best): title similarity >= 0.85,
artist >= 0.6, and no live/karaoke/remix versions unless the chart title says so.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from . import enrich, match
from .net import USER_AGENT

SPOTIFY_CACHE = enrich.SPOTIFY_CACHE
TOKEN_URL = "https://accounts.spotify.com/api/token"
SEARCH_URL = "https://api.spotify.com/v1/search?"
MARKET = {"tw": "TW", "jp": "JP"}
DELAY = 0.5           # seconds between searches
MAX_RETRY_AFTER = 60  # a longer 429 back-off ends the run; the rest waits for tomorrow
RETRY_DAYS = 30
TZ = dt.timezone(dt.timedelta(hours=8))


class Stop(RuntimeError):
    """Auth failure or long rate limit: stop this run, keep what was found."""


def _request(req: urllib.request.Request) -> dict:
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def get_token(client_id: str, client_secret: str) -> str:
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=b"grant_type=client_credentials",
        method="POST",
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded",
                 "User-Agent": USER_AGENT},
    )
    try:
        return _request(req)["access_token"]
    except urllib.error.HTTPError as exc:  # never echo the credentials, only the status
        raise Stop(f"Spotify token request failed: HTTP {exc.code}") from None


def search(token: str, title: str, artist: str, market: str) -> list[dict]:
    q = f"{match.clean_title(title)} {match.first_artist(artist)}".strip()
    url = SEARCH_URL + urllib.parse.urlencode({"q": q, "type": "track", "limit": 10, "market": market})
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT})
    for _ in range(3):
        try:
            return _request(req).get("tracks", {}).get("items", [])
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                wait = int(exc.headers.get("Retry-After", "5") or 5)
                if wait > MAX_RETRY_AFTER:
                    raise Stop(f"Spotify rate limit: retry after {wait}s") from None
                time.sleep(wait + 1)
                continue
            if exc.code in (401, 403):
                raise Stop(f"Spotify search refused: HTTP {exc.code} (Premium lapsed or app disabled?)") from None
            raise RuntimeError(f"Spotify search failed: HTTP {exc.code}") from None
        finally:
            time.sleep(DELAY)
    raise Stop("Spotify kept rate limiting")


def pick_best(items: list[dict], title: str, artist: str) -> dict | None:
    """Spotify tracks in the shape enrich.pick_best expects, so both use the same rules."""
    shaped = []
    for it in items:
        if not it or not it.get("id"):
            continue
        shaped.append({
            "kind": "song",
            "trackName": it.get("name", ""),
            "artistName": ", ".join(a.get("name", "") for a in it.get("artists", [])),
            "collectionName": (it.get("album") or {}).get("name"),
            "_id": it["id"],
        })
    return enrich.pick_best(shaped, title, artist)


def candidates(sites: dict, cache: dict, today: dt.date) -> list[dict]:
    """Songs never looked up, or not found RETRY_DAYS ago, best-ranked first."""
    best: dict[str, dict] = {}
    for src, _, row in enrich.iter_rows(sites):
        key = match.song_key(row.get("title"), row.get("artist"))
        if key.startswith("|"):
            continue
        entry = cache.get(key)
        if entry and (entry.get("status") == "ok" or
                      (today - dt.date.fromisoformat(entry.get("checked", "1970-01-01"))).days < RETRY_DAYS):
            continue
        if key not in best or row["rank"] < best[key]["rank"]:
            best[key] = {"key": key, "title": row.get("title"), "artist": row.get("artist"),
                         "region": enrich.REGION.get(src, "tw"), "rank": row["rank"]}
    return sorted(best.values(), key=lambda c: (c["rank"], c["key"]))


def lookup(todo: list[dict], cache: dict, token: str, budget: float) -> dict:
    stats = {"looked_up": 0, "found": 0, "stopped": None}
    start = time.monotonic()
    stamp = dt.datetime.now(TZ).date().isoformat()
    for item in todo:
        if time.monotonic() - start > budget:
            break
        hit, market = None, None
        try:
            for region in (item["region"], enrich.OTHER[item["region"]]):
                hit = pick_best(search(token, item["title"], item["artist"], MARKET[region]), item["title"], item["artist"])
                if hit:
                    market = MARKET[region]
                    break
        except Stop as exc:
            stats["stopped"] = str(exc)
            break
        except Exception as exc:  # noqa: BLE001 - one bad song must not stop the batch
            print(f"Spotify lookup failed for {item['title']} / {item['artist']}: {exc}", file=sys.stderr)
            continue
        stats["looked_up"] += 1
        if hit:
            stats["found"] += 1
            cache[item["key"]] = {"status": "ok", "id": hit["_id"], "name": hit["trackName"],
                                  "artist": hit["artistName"], "market": market, "checked": stamp}
        else:
            cache[item["key"]] = {"status": "none", "checked": stamp}
        if stats["looked_up"] % 25 == 0:
            enrich.save_cache(SPOTIFY_CACHE, cache)
            print(f"  ... {stats['looked_up']} looked up, {stats['found']} found", flush=True)
    enrich.save_cache(SPOTIFY_CACHE, cache)
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scraper.spotify")
    parser.add_argument("--max", type=int, default=1500, help="max songs to look up this run")
    parser.add_argument("--budget", type=float, default=900, help="max seconds to spend on lookups")
    args = parser.parse_args(argv)

    client_id, secret = os.environ.get("SPOTIFY_CLIENT_ID"), os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not secret:
        print("SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET not set; skipping Spotify lookups.")
    else:
        sites = enrich.load_sites()
        cache = enrich.load_cache(SPOTIFY_CACHE)
        todo = candidates(sites, cache, dt.datetime.now(TZ).date())[:args.max]
        print(f"{len(todo)} songs need a Spotify lookup", flush=True)
        if todo:
            try:
                token = get_token(client_id, secret)
            except Stop as exc:
                print(f"::warning title=Spotify skipped::{exc}", file=sys.stderr)
            else:
                stats = lookup(todo, cache, token, args.budget)
                print(f"looked up {stats['looked_up']}, found {stats['found']}")
                if stats["stopped"]:
                    print(f"::warning title=Spotify stopped early::{stats['stopped']}", file=sys.stderr)
    counts = enrich.apply_files()
    print("annotated rows: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
