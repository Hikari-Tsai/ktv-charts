"""Add genre tags and listen links to the chart JSON.

    python -m scraper.enrich                       # look up new songs, then annotate
    python -m scraper.enrich --max 300 --budget 1200
    python -m scraper.enrich --no-network          # only re-annotate from the caches

Genre and the Apple Music link come from the iTunes Search API (no key needed, about
20 requests per minute). Each song is looked up once; results, including "not found",
are cached in data/itunes.json and not-found songs are retried after RETRY_DAYS.

KKBOX song ids come from the KKBOX charts and from Holiday's KKBOX preview links. They
are remembered in data/kkbox-ids.json and shared with every source by song key.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
import urllib.parse
from pathlib import Path

from . import match
from .net import get_text

ROOT = Path(__file__).resolve().parent.parent
SITE_DATA = ROOT / "site" / "data"
ITUNES_CACHE = ROOT / "data" / "itunes.json"
KKBOX_IDS = ROOT / "data" / "kkbox-ids.json"

SOURCES = ["holiday", "cashbox", "joysound", "dam", "kkbox"]
REGION = {"holiday": "tw", "cashbox": "tw", "kkbox": "tw", "joysound": "jp", "dam": "jp"}
OTHER = {"tw": "jp", "jp": "tw"}
ITUNES = "https://itunes.apple.com/search?"
ITUNES_DELAY = 3.2  # seconds between requests: Apple allows roughly 20 per minute
RETRY_DAYS = 30
TZ = dt.timezone(dt.timedelta(hours=8))


class RateLimited(RuntimeError):
    pass


# ---------- files ----------

def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _save(path: Path, data, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, sort_keys=True,
                      **({"separators": (",", ":")} if compact else {"indent": 1}))
    path.write_text(text + "\n", encoding="utf-8")


def load_sites(site_dir: Path = SITE_DATA) -> dict[str, dict]:
    out = {}
    for src in SOURCES:
        data = _load(site_dir / f"{src}.json", None)
        if data:
            out[src] = data
    return out


def iter_rows(sites: dict[str, dict]):
    for src, data in sites.items():
        for chart in data.get("charts", []):
            for row in chart.get("rows", []):
                yield src, chart, row


# ---------- KKBOX ids ----------

def collect_kkbox_ids(sites: dict[str, dict], known: dict[str, str]) -> int:
    added = 0
    for _, _, row in iter_rows(sites):
        kid = row.get("kkbox")
        if kid and not match.song_key(row.get("title"), row.get("artist")).startswith("|"):
            key = match.song_key(row.get("title"), row.get("artist"))
            if known.get(key) != kid:
                known[key] = kid
                added += 1
    return added


# ---------- iTunes ----------

def pick_best(results: list[dict], title: str, artist: str) -> dict | None:
    """Choose the result that is the same recording, or None."""
    q_title_raw = match.nfkc(title).casefold()
    q_title = match.norm(match.clean_title(title))
    q_artist = match.norm(match.first_artist(artist))
    q_artist_full = match.norm(match.clean_artist(artist))
    best, best_score = None, None
    for r in results:
        if r.get("kind") not in (None, "song"):
            continue
        name, singer = r.get("trackName", ""), r.get("artistName", "")
        t_sim = match.similarity(q_title, match.norm(match.clean_title(name)))
        a_res = match.norm(match.clean_artist(singer))
        a_sim = max(match.similarity(q_artist, a_res), match.similarity(q_artist_full, a_res))
        if t_sim < 0.85 or a_sim < 0.6:
            continue
        bad = match.is_bad_version(name, r.get("collectionName"))
        if bad and not match.is_bad_version(title):
            continue
        exact = match.nfkc(name).casefold() == q_title_raw
        score = (exact, round(t_sim, 3), round(a_sim, 3))
        if best_score is None or score > best_score:
            best, best_score = r, score
    return best


def search_itunes(title: str, artist: str, country: str) -> dict | None:
    term = f"{match.clean_title(title)} {match.first_artist(artist)}".strip()
    query = urllib.parse.urlencode({
        "term": term, "country": country, "media": "music", "entity": "song", "limit": 10, "lang": "en_us",
    })
    try:
        body = get_text(ITUNES + query, {"Accept": "application/json"})
    except RuntimeError as exc:
        if "403" in str(exc) or "429" in str(exc):
            raise RateLimited(str(exc)) from exc
        raise
    finally:
        time.sleep(ITUNES_DELAY)
    results = json.loads(body).get("results", [])
    return pick_best(results, title, artist)


def candidates(sites: dict[str, dict], cache: dict, today: dt.date) -> list[dict]:
    """Songs never looked up (or not found long enough ago), best-ranked first."""
    best: dict[str, dict] = {}
    for src, _, row in iter_rows(sites):
        key = match.song_key(row.get("title"), row.get("artist"))
        if key.startswith("|"):  # title normalizes to nothing: too ambiguous to match
            continue
        entry = cache.get(key)
        if entry:
            if entry.get("status") == "ok":
                continue
            checked = dt.date.fromisoformat(entry.get("checked", "1970-01-01"))
            if (today - checked).days < RETRY_DAYS:
                continue
        cur = best.get(key)
        if cur is None or row["rank"] < cur["rank"]:
            best[key] = {"key": key, "title": row.get("title"), "artist": row.get("artist"),
                         "region": REGION.get(src, "tw"), "rank": row["rank"]}
    return sorted(best.values(), key=lambda c: (c["rank"], c["key"]))


def lookup(todo: list[dict], cache: dict, max_songs: int, budget: float, save_every: int = 10) -> dict:
    stats = {"looked_up": 0, "found": 0, "rate_limited": False}
    start = time.monotonic()
    today = dt.datetime.now(TZ).date().isoformat()
    for item in todo[:max_songs]:
        if time.monotonic() - start > budget:
            break
        try:
            hit, used = None, None
            for country in (item["region"], OTHER[item["region"]]):
                hit = search_itunes(item["title"], item["artist"], country)
                if hit:
                    used = country
                    break
        except RateLimited as exc:
            print(f"::warning title=iTunes rate limited::{exc}", file=sys.stderr)
            stats["rate_limited"] = True
            break
        except Exception as exc:  # noqa: BLE001 - one bad song must not stop the batch
            print(f"iTunes lookup failed for {item['title']} / {item['artist']}: {exc}", file=sys.stderr)
            continue
        stats["looked_up"] += 1
        if hit:
            stats["found"] += 1
            cache[item["key"]] = {
                "status": "ok",
                "genre": hit.get("primaryGenreName"),
                "id": hit.get("trackId"),
                "cc": used,
                "name": hit.get("trackName"),
                "artist": hit.get("artistName"),
                "checked": today,
            }
        else:
            cache[item["key"]] = {"status": "none", "checked": today}
        if stats["looked_up"] % save_every == 0:
            _save(ITUNES_CACHE, cache)
            print(f"  ... {stats['looked_up']} looked up, {stats['found']} found", flush=True)
    return stats


# ---------- annotate ----------

def _prefix_index(kkbox_ids: dict) -> dict[str, list[tuple[str, str]]]:
    index: dict[str, list[tuple[str, str]]] = {}
    for key, kid in kkbox_ids.items():
        title, _, artist = key.partition("|")
        if title and artist:
            index.setdefault(artist, []).append((title, kid))
    return index


def fuzzy_kkbox(key: str, index: dict[str, list[tuple[str, str]]]) -> str | None:
    """Same artist, and one title starts with the other ("甲乙丙丁" vs "甲乙丙丁Strangers")."""
    title, _, artist = key.partition("|")
    if len(title) < 3:
        return None
    hits = {kid for t, kid in index.get(artist, ())
            if len(t) >= 3 and (t.startswith(title) or title.startswith(t))}
    return hits.pop() if len(hits) == 1 else None


def annotate(sites: dict[str, dict], cache: dict, kkbox_ids: dict) -> dict:
    counts = {"rows": 0, "genre": 0, "apple": 0, "kkbox": 0}
    prefix_index = _prefix_index(kkbox_ids)
    for _, _, row in iter_rows(sites):
        counts["rows"] += 1
        key = match.song_key(row.get("title"), row.get("artist"))
        for field in ("genre", "apple"):
            row.pop(field, None)
        entry = cache.get(key) if not key.startswith("|") else None
        if entry and entry.get("status") == "ok":
            if entry.get("genre"):
                row["genre"] = entry["genre"]
                counts["genre"] += 1
            if entry.get("id") and entry.get("cc"):
                row["apple"] = f"{entry['cc']}/{entry['id']}"
                counts["apple"] += 1
        if not row.get("kkbox") and not key.startswith("|"):
            kid = kkbox_ids.get(key) or fuzzy_kkbox(key, prefix_index)
            if kid:
                row["kkbox"] = kid
        if row.get("kkbox"):
            counts["kkbox"] += 1
        else:
            row.pop("kkbox", None)
    return counts


def write_sites(sites: dict[str, dict], site_dir: Path = SITE_DATA) -> None:
    for src, data in sites.items():
        (site_dir / f"{src}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def apply_files(site_dir: Path = SITE_DATA) -> dict:
    """No network: refresh KKBOX ids and annotate every row from the caches."""
    sites = load_sites(site_dir)
    kkbox_ids = _load(KKBOX_IDS, {})
    if collect_kkbox_ids(sites, kkbox_ids):
        _save(KKBOX_IDS, kkbox_ids)
    counts = annotate(sites, _load(ITUNES_CACHE, {}), kkbox_ids)
    write_sites(sites, site_dir)
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scraper.enrich")
    parser.add_argument("--max", type=int, default=300, help="max songs to look up this run")
    parser.add_argument("--budget", type=float, default=1200, help="max seconds to spend on lookups")
    parser.add_argument("--no-network", action="store_true", help="only annotate from caches")
    args = parser.parse_args(argv)

    if not args.no_network:
        sites = load_sites()
        cache = _load(ITUNES_CACHE, {})
        todo = candidates(sites, cache, dt.datetime.now(TZ).date())
        print(f"{len(todo)} songs need a lookup; doing up to {args.max}", flush=True)
        stats = lookup(todo, cache, args.max, args.budget)
        _save(ITUNES_CACHE, cache)
        print(f"looked up {stats['looked_up']}, found {stats['found']}"
              + (" (stopped: rate limited)" if stats["rate_limited"] else ""))
    counts = apply_files()
    print("annotated rows: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
