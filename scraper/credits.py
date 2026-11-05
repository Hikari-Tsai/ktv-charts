"""Look up publishing details: songwriters, producers, label, release date and ISRC.

    python -m scraper.credits                      # all three lookups, then annotate
    python -m scraper.credits --ncl-max 200 --mb-max 300 --budget 1200

Three sources, each with its own permanent cache keyed by song key:

* Apple (data/apple-albums.json): album, release date and the ℗/© line for every song
  iTunes matched, via the iTunes Lookup API, 100 tracks per request.
* National Central Library ISRC center (data/ncl-isrc.json): Taiwan's ISRC agency.
  Labels that release in Taiwan register every recording with performer, lyricist,
  composer, arranger, producer and label, so this is the source for Taiwanese songs.
  Searched by title AND performer through the public query site isrc-web.ncl.edu.tw;
  the same records are published as open data (data.gov.tw dataset 36940, Open
  Government Data License v1). Taiwan-region charts only.
* MusicBrainz (data/musicbrainz.json): community credits (CC0), good for Japanese and
  Western songs that NCL does not have. 1 request per second, as MusicBrainz asks.

Not-found songs are retried after RETRY_DAYS. scraper.info merges the three into the
`info` field of each chart row.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from . import enrich, match

ROOT = enrich.ROOT
APPLE_CACHE = enrich.APPLE_ALBUM_CACHE
NCL_CACHE = enrich.NCL_CACHE
MB_CACHE = enrich.MB_CACHE
TZ = dt.timezone(dt.timedelta(hours=8))
RETRY_DAYS = 60
PROJECT_UA = "ktv-charts/1.0 ( https://github.com/Hikari-Tsai/ktv-charts )"

ITUNES_LOOKUP = "https://itunes.apple.com/lookup?"
APPLE_BATCH = 100

NCL_URL = "https://isrc-web.ncl.edu.tw/C200/C20004"
NCL_DELAY = 1.5
NCL_VERSION = 1

MB_URL = "https://musicbrainz.org/ws/2/"
MB_DELAY = 1.1
MB_VERSION = 1

# NCL registers karaoke and instrumental tracks too; never take those for the song.
_NCL_BAD = re.compile(r"kala|ktv|伴奏|伴唱|導唱|純音樂|演奏|\binst|demo|accompaniment|off\s*vocal|\bmv\b", re.I)
_NCL_ROLE = {
    "表演者": "performer", "樂團名稱": "performer", "主唱": "performer", "演唱者": "performer",
    "演唱": "performer", "歌手": "performer", "作詞者": "lyricist", "作詞": "lyricist",
    "作曲者": "composer", "作曲": "composer", "編曲者": "arranger", "編曲": "arranger",
    "製作人": "producer",
}
_NAME_SPLIT = re.compile(r"\s*(?:、|,|，|/|／|\+|＋|;|；)\s*")
_REGISTRANT = re.compile(r"^\s*(?=[A-Z0-9]{0,2}\d)[A-Z0-9]{3}(?=\s|[^\x00-\x7f])\s*")
_CJK = re.compile(r"[぀-ヿ㐀-鿿가-힯]")
_HAN = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
_MB_ROLES = {"lyricist", "composer", "writer", "arranger", "producer"}


def _today() -> dt.date:
    return dt.datetime.now(TZ).date()


def _due(entry: dict | None, today: dt.date, version: int = 1) -> bool:
    if not entry:
        return True
    if entry.get("status") == "ok":
        return False
    if entry.get("v", 1) < version:
        return True
    checked = dt.date.fromisoformat(entry.get("checked", "1970-01-01"))
    return (today - checked).days >= RETRY_DAYS


def songs(sites: dict, region: str | None = None) -> list[dict]:
    """One item per song key, best rank first."""
    best: dict[str, dict] = {}
    for src, _, row in enrich.iter_rows(sites):
        key = match.song_key(row.get("title"), row.get("artist"))
        reg = enrich.REGION.get(src, "tw")
        if key.startswith("|") or (region and reg != region):
            continue
        if key not in best or row["rank"] < best[key]["rank"]:
            best[key] = {"key": key, "title": row.get("title"), "artist": row.get("artist"),
                         "region": reg, "rank": row["rank"]}
    return sorted(best.values(), key=lambda c: (c["rank"], c["key"]))


def _date(value: str | None) -> str | None:
    m = re.match(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", value or "")
    if not m:
        return None
    return "-".join(p for p in m.groups() if p)


# ---------- Apple ----------

def apple_todo(sites: dict, itunes: dict, cache: dict) -> list[dict]:
    todo = []
    for item in songs(sites):
        hit = itunes.get(item["key"])
        if not hit or hit.get("status") != "ok" or not hit.get("id"):
            continue
        have = cache.get(item["key"])
        if have and have.get("track") == f"{hit['cc']}/{hit['id']}":
            continue
        todo.append({**item, "cc": hit["cc"], "id": hit["id"]})
    return todo


def apple_lookup(todo: list[dict], cache: dict, budget: float) -> dict:
    stats = {"looked_up": 0, "found": 0}
    start, stamp = time.monotonic(), _today().isoformat()
    by_cc: dict[str, list[dict]] = {}
    for item in todo:
        by_cc.setdefault(item["cc"], []).append(item)
    for cc, items in by_cc.items():
        for i in range(0, len(items), APPLE_BATCH):
            if time.monotonic() - start > budget:
                return stats
            batch = items[i:i + APPLE_BATCH]
            query = urllib.parse.urlencode({"id": ",".join(str(x["id"]) for x in batch), "country": cc,
                                            "entity": "album", "lang": "en_us"})
            try:
                body = enrich.get_text(ITUNES_LOOKUP + query, {"Accept": "application/json"})
            except RuntimeError as exc:
                print(f"::warning title=Apple lookup failed::{exc}", file=sys.stderr)
                return stats
            finally:
                time.sleep(enrich.ITUNES_DELAY)
            results = json.loads(body).get("results", [])
            tracks = {r["trackId"]: r for r in results if r.get("wrapperType") == "track" and r.get("trackId")}
            albums = {r["collectionId"]: r for r in results if r.get("wrapperType") == "collection"}
            for item in batch:
                stats["looked_up"] += 1
                record = {"track": f"{cc}/{item['id']}", "checked": stamp}
                tr = tracks.get(item["id"])
                if not tr:
                    cache[item["key"]] = {**record, "status": "none"}
                    continue
                al = albums.get(tr.get("collectionId"), {})
                cache[item["key"]] = {**record, "status": "ok", "album": tr.get("collectionName"),
                                      "released": _date(tr.get("releaseDate") or al.get("releaseDate")),
                                      "copyright": (al.get("copyright") or "").strip() or None}
                stats["found"] += 1
    return stats


# ---------- National Central Library ----------

def _ncl_names(text: str) -> list[str]:
    out = []
    for name in _NAME_SPLIT.split(text.strip()):
        name = re.sub(r"\s*等$", "", name).strip()
        if name and name not in out:
            out.append(name)
    return out


def ncl_roles(action: str | None) -> dict[str, list[str]]:
    """'表演者:田馥甄<br />作詞者:徐世珍, 吳輝福<br />' -> {'performer': [...], 'lyricist': [...]}"""
    roles: dict[str, list[str]] = {}
    for part in re.split(r"<br\s*/?>", action or "", flags=re.I):
        if ":" not in part and "：" not in part:
            continue
        role, _, names = part.replace("：", ":").partition(":")
        key = _NCL_ROLE.get(role.strip())
        if key:
            for name in _ncl_names(names):
                if name not in roles.setdefault(key, []):
                    roles[key].append(name)
    return roles


def ncl_company(text: str | None) -> str | None:
    name = _REGISTRANT.sub("", (text or "").strip()).strip()
    return name or None


def ncl_title(text: str | None) -> str:
    """'曲目名稱:小幸運<br />' -> '小幸運'"""
    for part in re.split(r"<br\s*/?>", text or "", flags=re.I):
        if part.strip():
            return part.split(":", 1)[-1].strip()
    return ""


def artist_keyword(artist: str | None) -> str:
    """The search keyword for a performer: its first CJK word if it has one ('芒果醬 Mango Jump')."""
    first = match.first_artist(artist)
    for word in first.split():
        if _CJK.search(word):
            return word
    return first


def ncl_search(title: str, artist: str | None) -> list[dict]:
    params = {"field1": "NAME", "keyword1": title, "operator1": "AND",
              "field2": "ACTION", "keyword2": artist or "", "operator2": "AND",
              "field3": "aNAME", "keyword3": "", "start": "", "end": ""}
    data = json.dumps({"FunctionId": "C20004", "ObjParams": params}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(NCL_URL, data=data, method="POST", headers={
        "User-Agent": PROJECT_UA, "Content-Type": "application/json; charset=utf-8", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            body = json.loads(res.read().decode("utf-8"))
    finally:
        time.sleep(NCL_DELAY)
    if str(body.get("Result")) != "1":
        raise RuntimeError(f"NCL search failed: {body.get('Message') or body.get('Result')}")
    return json.loads(body.get("Data") or "[]")


def ncl_pick(records: list[dict], title: str, artist: str) -> list[dict]:
    """Records of the same recording, earliest release first."""
    q_title = match.norm(match.clean_title(title))
    q_artists = {match.norm(match.first_artist(artist)), match.norm(match.clean_artist(artist)),
                 match.norm(artist_keyword(artist))} - {""}
    wants_bad = match.is_bad_version(title) or bool(_NCL_BAD.search(title or ""))
    out = []
    for r in records:
        name = ncl_title(r.get("NAME"))
        if match.similarity(q_title, match.norm(match.clean_title(name))) < 0.85:
            continue
        if not wants_bad and (match.is_bad_version(name) or _NCL_BAD.search(name)):
            continue
        roles = ncl_roles(r.get("ACTION"))
        performers = roles.get("performer", [])
        cands = [match.norm(match.clean_artist(p)) for p in performers] + [match.norm("".join(performers))]
        if max((match.similarity(q, c) for q in q_artists for c in cands if c), default=0) < 0.6:
            continue
        out.append({**r, "_roles": roles, "_name": name})
    return sorted(out, key=lambda r: (r.get("aSENT_TIME") or "9999", r.get("TOPIC") or ""))


def _richness(r: dict) -> int:
    return sum(1 for k in ("lyricist", "composer", "arranger", "producer") if r["_roles"].get(k))


def ncl_entry(matches: list[dict], stamp: str) -> dict:
    first = matches[0]
    same = [r for r in matches if r.get("TOPIC") == first.get("TOPIC")]
    rich = max(same, key=_richness)
    if _richness(rich) < 2:
        rich = max(matches, key=_richness)
    credits = {k: v for k, v in rich["_roles"].items() if k != "performer"}
    entry = {"status": "ok", "isrc": first.get("TOPIC"), "item": first.get("ITEM"), "title": first["_name"],
             "performer": first["_roles"].get("performer", []), "album": (first.get("aNAME") or "").strip() or None,
             "released": _date(first.get("aSENT_TIME")), "label": ncl_company(first.get("aSENT_COM")),
             "maker": ncl_company(first.get("PRODUCER")), "type": (first.get("apubtype") or "").strip() or None,
             "credits": credits, "checked": stamp, "v": NCL_VERSION}
    return {k: v for k, v in entry.items() if v not in (None, [], {})}


def ncl_lookup(todo: list[dict], cache: dict, budget: float) -> dict:
    stats = {"looked_up": 0, "found": 0, "errors": 0}
    start, stamp = time.monotonic(), _today().isoformat()
    for item in todo:
        if time.monotonic() - start > budget:
            break
        title = match.clean_title(item["title"])
        try:
            matches = ncl_pick(ncl_search(title, artist_keyword(item["artist"])), item["title"], item["artist"])
            if not matches and len(title) >= 2:
                # The performer may be written differently ("A-Lin 黃麗玲"); search the title alone.
                matches = ncl_pick(ncl_search(title, None), item["title"], item["artist"])
        except Exception as exc:  # noqa: BLE001 - one bad song must not stop the batch
            print(f"NCL lookup failed for {item['title']} / {item['artist']}: {exc}", file=sys.stderr)
            stats["errors"] += 1
            if stats["errors"] >= 5 and stats["found"] == 0:
                print("::warning title=NCL ISRC unreachable::stopping NCL lookups for this run", file=sys.stderr)
                break
            continue
        stats["looked_up"] += 1
        if matches:
            cache[item["key"]] = ncl_entry(matches, stamp)
            stats["found"] += 1
        else:
            cache[item["key"]] = {"status": "none", "checked": stamp, "v": NCL_VERSION}
        if stats["looked_up"] % 25 == 0:
            enrich.save_cache(NCL_CACHE, cache)
            print(f"  ... NCL {stats['looked_up']} looked up, {stats['found']} found", flush=True)
    enrich.save_cache(NCL_CACHE, cache)
    return stats


# ---------- MusicBrainz ----------

def _mb_get(path: str, params: dict) -> dict:
    url = MB_URL + path + "?" + urllib.parse.urlencode({**params, "fmt": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": PROJECT_UA, "Accept": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                return json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503) and attempt < 2:  # over the rate limit: back off
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f"MusicBrainz {path} failed: HTTP {exc.code}") from None
        finally:
            time.sleep(MB_DELAY)
    raise RuntimeError(f"MusicBrainz {path} kept rate limiting")


def _lucene(text: str) -> str:
    return re.sub(r'([+\-&|!(){}\[\]^"~*?:\\/])', r"\\\1", text)


def mb_shape(recordings: list[dict]) -> list[dict]:
    """MusicBrainz recordings in the shape enrich.pick_best expects."""
    out = []
    for rec in recordings:
        credit = "".join(c.get("name", "") + c.get("joinphrase", "") for c in rec.get("artist-credit", []))
        releases = rec.get("releases") or [{}]
        out.append({"kind": "song", "trackName": rec.get("title", ""), "artistName": credit,
                    "collectionName": releases[0].get("title"), "_rec": rec})
    return out


def mb_credits(detail: dict) -> dict[str, list[str]]:
    credits: dict[str, list[str]] = {}

    def add(rel: dict) -> None:
        role, name = rel.get("type"), (rel.get("artist") or {}).get("name")
        if role in _MB_ROLES and name and name not in credits.setdefault(role, []):
            credits[role].append(name)

    for rel in detail.get("relations", []):
        if rel.get("artist"):
            add(rel)
        for wrel in (rel.get("work") or {}).get("relations", []):
            if wrel.get("artist"):
                add(wrel)
    return {k: v for k, v in credits.items() if v}


def mb_find(title: str, artist: str) -> dict | None:
    query = f'recording:"{_lucene(match.clean_title(title))}" AND artist:"{_lucene(match.first_artist(artist))}"'
    shaped = mb_shape(_mb_get("recording", {"query": query, "limit": 15}).get("recordings", []))
    fallback = None
    for _ in range(3):  # the best match may be a recording nobody linked to its work yet
        hit = enrich.pick_best(shaped, title, artist)
        if not hit:
            break
        shaped.remove(hit)
        rec = hit["_rec"]
        detail = _mb_get(f"recording/{rec['id']}", {"inc": "artist-rels+work-rels+work-level-rels+isrcs"})
        releases = rec.get("releases") or [{}]
        entry = {"status": "ok", "id": rec["id"], "title": rec.get("title"), "artist": hit["artistName"],
                 "released": _date(rec.get("first-release-date")), "album": releases[0].get("title"),
                 "isrc": (detail.get("isrcs") or [None])[0], "credits": mb_credits(detail)}
        entry = {k: v for k, v in entry.items() if v not in (None, [], {})}
        if entry.get("credits"):
            return entry
        fallback = fallback or entry
    return fallback


def mb_lookup(todo: list[dict], cache: dict, budget: float) -> dict:
    stats = {"looked_up": 0, "found": 0, "with_credits": 0, "errors": 0}
    start, stamp = time.monotonic(), _today().isoformat()
    for item in todo:
        if time.monotonic() - start > budget:
            break
        try:
            hit = mb_find(item["title"], item["artist"])
        except Exception as exc:  # noqa: BLE001
            print(f"MusicBrainz lookup failed for {item['title']} / {item['artist']}: {exc}", file=sys.stderr)
            stats["errors"] += 1
            if stats["errors"] >= 5 and stats["found"] == 0:
                break
            continue
        stats["looked_up"] += 1
        if hit:
            cache[item["key"]] = {**hit, "checked": stamp, "v": MB_VERSION}
            stats["found"] += 1
            stats["with_credits"] += bool(hit.get("credits"))
        else:
            cache[item["key"]] = {"status": "none", "checked": stamp, "v": MB_VERSION}
        if stats["looked_up"] % 25 == 0:
            enrich.save_cache(MB_CACHE, cache)
            print(f"  ... MusicBrainz {stats['looked_up']} looked up, {stats['found']} found", flush=True)
    enrich.save_cache(MB_CACHE, cache)
    return stats


# ---------- main ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scraper.credits")
    parser.add_argument("--ncl-max", type=int, default=200, help="max songs to look up at NCL this run")
    parser.add_argument("--mb-max", type=int, default=300, help="max songs to look up at MusicBrainz this run")
    parser.add_argument("--budget", type=float, default=1200, help="max seconds for all lookups")
    parser.add_argument("--only", choices=["apple", "ncl", "mb"], help="run one lookup only")
    args = parser.parse_args(argv)
    t0 = time.monotonic()
    left = lambda: args.budget - (time.monotonic() - t0)  # noqa: E731
    sites = enrich.load_sites()
    today = _today()

    if args.only in (None, "apple"):
        cache = enrich.load_cache(APPLE_CACHE)
        todo = apple_todo(sites, enrich.load_cache(enrich.ITUNES_CACHE), cache)
        print(f"{len(todo)} songs need Apple album details", flush=True)
        stats = apple_lookup(todo, cache, min(left(), 300))
        enrich.save_cache(APPLE_CACHE, cache)
        print("apple: " + ", ".join(f"{k}={v}" for k, v in stats.items()), flush=True)

    ncl = enrich.load_cache(NCL_CACHE)
    if args.only in (None, "ncl"):
        # Songs with no Han or kana in title or artist (K-pop, Western) are not registered in Taiwan.
        todo = [s for s in songs(sites, "tw") if _HAN.search(f"{s['title']}{s['artist']}")
                and _due(ncl.get(s["key"]), today, NCL_VERSION)][:args.ncl_max]
        print(f"{len(todo)} songs to look up at NCL ISRC", flush=True)
        # NCL first: it is the better source for the Taiwanese songs, and MusicBrainz skips what it found.
        stats = ncl_lookup(todo, ncl, left() * (0.6 if args.only is None else 1))
        print("ncl: " + ", ".join(f"{k}={v}" for k, v in stats.items()), flush=True)

    if args.only in (None, "mb"):
        cache = enrich.load_cache(MB_CACHE)
        todo = [s for s in songs(sites) if not (ncl.get(s["key"], {}).get("credits"))
                and _due(cache.get(s["key"]), today, MB_VERSION)][:args.mb_max]
        print(f"{len(todo)} songs to look up at MusicBrainz", flush=True)
        stats = mb_lookup(todo, cache, left())
        print("musicbrainz: " + ", ".join(f"{k}={v}" for k, v in stats.items()), flush=True)

    counts = enrich.apply_files()
    print("annotated rows: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
