"""Title/artist normalization shared by cross-source matching and the iTunes lookup."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

_BRACKETS = re.compile(r"\s*[\(\[（【〔｛{＜<].*?[\)\]）】〕｝}＞>]")
_SUBTITLE = re.compile(r"\s+[-‐–—~〜]\s*.*$")   # "曲名 - 影集主題曲", "怪獣の花唄 - replica -"
_FEAT = re.compile(r"\s+(feat\.?|ft\.?|featuring|with)\s+.*$", re.I)
_ARTIST_SPLIT = re.compile(r"\s*(?:、|,|，|&|＆|/|／|×|\+|;|\s(?:feat\.?|ft\.?)\s)\s*", re.I)
_NON_WORD = re.compile(r"[\W_]+")
_BAD_VERSION = re.compile(
    r"\b(live|instrumental|inst\.?|karaoke|off\s*vocal|backing\s*track|remix|acoustic ver|tv\s*size|cover)\b"
    r"|カラオケ|オフボーカル|伴奏|純音樂|演奏|ライブ|現場",
    re.I,
)


def nfkc(text: str | None) -> str:
    return unicodedata.normalize("NFKC", text or "").strip()


def clean_title(title: str | None) -> str:
    t = nfkc(title)
    t = _BRACKETS.sub("", t)
    t = _FEAT.sub("", t)
    t = _SUBTITLE.sub("", t)
    return t.strip() or nfkc(title)


def clean_artist(artist: str | None) -> str:
    a = _BRACKETS.sub("", nfkc(artist))
    return a.strip() or nfkc(artist)


def first_artist(artist: str | None) -> str:
    parts = [p for p in _ARTIST_SPLIT.split(clean_artist(artist)) if p and p.strip()]
    return parts[0].strip() if parts else clean_artist(artist)


def norm(text: str | None) -> str:
    return _NON_WORD.sub("", nfkc(text).casefold())


def song_key(title: str | None, artist: str | None) -> str:
    """Identity of a song across sources: normalized clean title + full clean artist."""
    return norm(clean_title(title)) + "|" + norm(clean_artist(artist))


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if len(min(a, b, key=len)) >= 2 and (a in b or b in a):
        return 0.9
    return SequenceMatcher(None, a, b).ratio()


def is_bad_version(*texts: str | None) -> bool:
    return any(_BAD_VERSION.search(nfkc(t)) for t in texts if t)
