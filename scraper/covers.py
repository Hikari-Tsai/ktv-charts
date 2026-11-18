"""Turn a cover video's title into the song it covers. Standard library only.

VTuber cover titles mix many styles:

    numb numb - TAK｜白月心宿 × 埃穆亞 (cover)
    【Cover】要不然我們就這樣一萬年／黃霄雲｜ Cover by 阿絲塔Aasta
    【歌ってみた】唱(Show) - Ado | Covered by 可可伊丹CocoEden
    蕭敬騰 - 皮囊 ／ 昴 Pleiades【Cover】

`segments` strips the cover noise (【Cover】, "covered by ...", hashtags, the uploader's own
name) and splits what is left into pieces; the song title and the original artist are
usually the first two. Which one is which is settled by the iTunes lookup in
scraper/sources/vtuber.py, so this module never has to guess the order.
"""

from __future__ import annotations

import re
import unicodedata

from . import match

# Bracketed text that only describes the video, not the song.
_NOISE = re.compile(
    r"cover|covered|coverd|カバー|歌ってみた|歌って|翻唱|唱了|中文字幕|字幕|\bcc\b|\bpv\b|\bmv\b|music\s*video|動畫|"
    r"vtuber|台v|新人|紀念|纪念|周年|週年|生日|誕生|投稿|pick\s*up|所屬|合唱|阿卡貝拉|a\s*cappella|"
    r"\bver\b|version|full|mashup|remix|arrange|填詞|中文版|日本語|配信|企劃|計畫|计划|特別|節目|official",
    re.I,
)
_BRACKET = re.compile(r"[\[【〔〖《『「(（<＜{｛]([^\]】〕〗》』」)）>＞}｝]*)[\]】〕〗》』」)）>＞}｝]")
_COVERED_BY = re.compile(r"\b(?:covered|cover|coverd|cv)\.?\s*(?:by|ft\.?|feat\.?)\b.*$", re.I)
_LEADING_BY = re.compile(r"^\s*by[\s.]", re.I)
_WORDS = re.compile(r"\b(?:covered|cover|coverd)\b|歌ってみた|翻唱|中文翻唱|唱了", re.I)
_TAGS = re.compile(r"[#＃@][^\s#＃@【】\[\]|｜/／]+")
_SEPARATORS = re.compile(
    r"\s*(?:/|／|\||｜|│|丨|‣|✧|✦|ꕤ|❆|✿|⌇|┊|⊹|⋄|⟣|•|⁝|－|–|\s[-‐—~〜]\s?|[-‐—]\s)\s*"
)
_PERFORMERS = re.compile(r"\s*(?:×|⨯|&|＆|、|,|，)\s*|\s+x\s+", re.I)
_CH_WORDS = re.compile(r"\b(?:ch|channel|official|vtuber|music)\b\.?", re.I)
_KANA = re.compile(r"[぀-ヿ]")
_BY = re.compile(r"\s+by(?:[.\s]+|(?=[^\x00-\x7f]))", re.I)  # "可愛くてごめん by HoneyWorks", "残響散歌 by凡笙弦語"
_BRACKET_AFTER_BY = re.compile(
    r"(?:covered|cover|coverd)\s*by\.?\s*[\[【〔〖《『「(（][^\]】〕〗》』」)）]*[\]】〕〗》』」)）]", re.I)
_FEAT_ONLY = re.compile(r"^(?:feat|ft)(?:\.|\s)", re.I)
_SMALL_CAPS = str.maketrans("ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘʀꜱᴛᴜᴠᴡʏᴢ", "abcdefghijklmnoprstuvwyz")
_DECOR = set("୨୧⠸⁂")


def _clean_chars(text: str) -> str:
    """NFKC (turns 𝑺𝒊𝒔 into Sis); emoji and symbols become piece boundaries, zero-width characters go."""
    text = text.replace("－", " / ")  # a full-width dash separates; NFKC would make it a plain hyphen
    text = unicodedata.normalize("NFKC", text).translate(_SMALL_CAPS)
    keep = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat == "So" or ch in "♪♫☆★♡♥":
            keep.append(" / ")  # ❆ ✿ 🎵: decorations that sit between the song and the singer
        elif cat in ("Sk", "Cf", "Co", "Cn") or ch in _DECOR:
            keep.append(" ")
        else:
            keep.append(ch)
    return re.sub(r"\s+", " ", "".join(keep)).strip()


_PAIRS = {"(": ")", "（": "）", "「": "」", "『": "』", "【": "】", "[": "]", "〈": "〉", "《": "》"}


def _unbalanced(seg: str) -> str:
    """Drop a bracket left without its partner after splitting: "可愛くてごめん)" -> "可愛くてごめん"."""
    for o, c in _PAIRS.items():
        if seg.count(o) != seg.count(c):
            seg = seg.replace(o, " ").replace(c, " ")
    return re.sub(r"\s+", " ", seg).strip()


def channel_names(channel: str | None) -> list[str]:
    """Normalized pieces of the uploader's channel name, e.g. '緹露 Tilu Ch.' -> ['緹露tilu', '緹露', 'tilu']."""
    text = _CH_WORDS.sub(" ", _BRACKET.sub(" ", _clean_chars(channel or "")))
    parts = [text] + re.split(r"[\s/／|｜·・.．、,，和]+", text)
    out = []
    for p in parts:
        n = match.norm(p)
        if len(n) >= 2 and n not in out:
            out.append(n)
    return out


def _is_performer(seg: str, names: list[str]) -> bool:
    """The piece is the uploader's name (or most of it is)."""
    n = match.norm(seg)
    if not n:
        return True
    for name in names:
        if n == name or (len(n) >= 2 and n in name) or (len(name) >= 3 and name in n and len(name) * 10 >= len(n) * 7):
            return True
    return False


def _drop_performer_words(seg: str, names: list[str]) -> str:
    """"春日影 瓦西瓦瓦" -> "春日影" when 瓦西瓦瓦 uploaded it."""
    words = seg.split(" ")
    kept = [w for w in words if not (match.norm(w) and _is_performer(w, names))]
    return " ".join(kept) if kept else ""


def segments(title: str, channel: str | None = None, keep_tags: bool = False) -> list[str]:
    """The pieces of a cover title that can be the song or its original artist, in order."""
    text = _clean_chars(title)
    text = re.sub(r"[#＃]", " ", text) if keep_tags else _TAGS.sub(" ", text)
    text = _BRACKET_AFTER_BY.sub(" ", text)  # "Cover by 【奎爾·玫蘭莎】": the performer
    pieces: list[str] = []
    weak: list[str] = []

    def keep_bracket(m: re.Match) -> str:
        inner = m.group(1).strip()
        if inner and not _NOISE.search(inner):
            pieces.append(inner)  # 【メメントモリ】 or 「僕は...」: may be the song itself
            return " / "
        if inner:  # 【天ノ弱 Piano Ver.】: what is left after the noise words, as a last resort
            rest = _NOISE.sub(" ", _COVERED_BY.sub("", inner))
            rest = re.sub(r"\b(?:piano|guitar|acoustic|electro|swing|with|and)\b", " ", rest, flags=re.I)
            if len(match.norm(rest)) >= 2:
                weak.append(rest)
        return " / "

    text = _BRACKET.sub(keep_bracket, text)
    names = channel_names(channel)
    out: list[str] = []
    split = lambda t: [x for part in _SEPARATORS.split(t) for x in _BY.split(_COVERED_BY.sub("", part))]
    in_brackets = [x for p in pieces for x in split(p.replace("-", " - "))]
    for seg in split(text) + in_brackets + ["\0"] + [x for p in weak for x in split(p)]:
        if seg == "\0":  # leftovers of 【...周年紀念...】 only when nothing else is left
            if out:
                break
            continue
        seg = _COVERED_BY.sub("", seg)
        if _LEADING_BY.match(seg):  # "by HoneyWorks" after "cover"
            seg = _LEADING_BY.sub("", seg)
        seg = _WORDS.sub(" ", seg)
        seg = re.sub(r"\s+", " ", seg).strip(" .:：-_~!！?？,，")
        seg = _unbalanced(seg)
        seg = re.sub(r"\s+l$", "", seg)  # "biz×ZERA l Covered by": a lowercase L used as a bar
        if not seg or not match.norm(seg) or _FEAT_ONLY.match(seg) or match.norm(seg) in ("feat", "ft"):
            continue
        if len(match.norm(_NOISE.sub("", seg))) < 2 and len(match.norm(seg)) > 1:
            continue  # "中文字幕", "mashup ver": only describes the video
        if _is_performer(seg, names):
            continue
        # "白月心宿 × 埃穆亞": several performers joined, one of them the uploader
        parts = [p for p in _PERFORMERS.split(seg) if p]
        if len(parts) > 1 and any(_is_performer(p, names) for p in parts):
            continue
        seg = _drop_performer_words(seg, names)
        if not match.norm(seg):
            continue
        if seg not in out:
            out.append(seg)
    if not out and _TAGS.search(title) and not keep_tags:
        return segments(title, channel, keep_tags=True)  # "#超絶かわいい // covered by ...": the tag is the song
    return out


_CJK = re.compile(r"[぀-ヿ㐀-鿿豈-﫿]")


def performer_name(channel: str | None) -> str:
    """Short display name of the uploader: "森森鈴蘭 / Lily Linglan【箱箱The Box所屬】" -> "森森鈴蘭",
    "Nemesis ch. 涅默" -> "Nemesis 涅默", "浠Mizuki Channel" -> "浠Mizuki"."""
    text = _BRACKET.sub(" ", unicodedata.normalize("NFKC", channel or ""))
    text = "".join(" " if unicodedata.category(ch) == "So" else ch for ch in text)
    text = re.sub(r"(?:\b|_)(?:channel|ch|official|vtuber)\b\.?", " ", text, flags=re.I)
    parts = [p.strip(" -_.・･∅") for p in re.split(r"\s*(?:/|／|⁄|\s-\s)\s*", text)]
    parts = [p for p in parts if p]
    if not parts:
        return (channel or "").strip()
    name = next((p for p in parts if _CJK.search(p)), parts[0]) if len(parts) > 1 else parts[0]
    return re.sub(r"\s+", " ", name).strip()


def looks_japanese(text: str) -> bool:
    return bool(_KANA.search(text))


_CJK_THEN_LATIN = re.compile(r"^([぀-ヿ㐀-鿿豈-﫿]+)\s*[A-Za-z][A-Za-z .'-]*$")


def _search_form(text: str) -> str:
    """"徐佳瑩Lala Tsu" -> "徐佳瑩": iTunes finds nothing when both spellings are in the term."""
    m = _CJK_THEN_LATIN.match(text.strip())
    return m.group(1) if m else text.strip()


def query(segs: list[str]) -> str:
    """iTunes search term: the first two pieces, which are the song and its artist in either order."""
    out = []
    for i, seg in enumerate(segs[:2]):
        # The title keeps "with" (Die With A Smile); the artist is cut to its first name.
        seg = (re.split(r"\s*[×⨯]\s*", match._BRACKETS.sub("", match.nfkc(seg)).strip())[0] or seg) if i == 0 \
            else _PERFORMERS.split(match.first_artist(seg))[0]
        out.append(_search_form(seg))
    return " ".join(out).strip()


def pick(results: list[dict], segs: list[str]) -> dict | None:
    """The iTunes result whose title is one piece of the cover title and whose artist is another
    piece or appears elsewhere in it. With no artist in the title, only an exact title match counts."""
    keys = [match.norm(match.clean_title(s)) for s in segs[:5]]
    whole = match.norm(" ".join(segs))
    best, best_score = None, None
    for order, r in enumerate(results):
        if r.get("kind") not in (None, "song"):
            continue
        name, artist = r.get("trackName", ""), r.get("artistName", "")
        if match.is_bad_version(name, r.get("collectionName")) and not match.is_bad_version(*segs):
            continue
        n_name = match.norm(match.clean_title(name))
        a_full, a_first = match.norm(match.clean_artist(artist)), match.norm(match.first_artist(artist))
        if not n_name:
            continue
        sims = [match.similarity(k, n_name) for k in keys]
        t_sim = max(sims, default=0.0)
        others = [k for i, k in enumerate(keys) if i != sims.index(t_sim)]
        a_sim = max([match.similarity(o, a) for o in others for a in (a_full, a_first)] or [0.0])
        # The artist written anywhere else in the title also counts ("一生懸命 米津玄師 IRIS OUT").
        rest = whole.replace(n_name, "", 1)
        a_in = len(a_first) >= 2 and a_first in rest
        if a_in:
            a_sim = max(a_sim, 0.9)
        if t_sim >= 0.85:
            ok = a_sim >= 0.6 if others else (t_sim == 1.0 or a_in)
        else:  # title and artist run together in one piece
            ok = len(n_name) >= 3 and n_name in whole and a_in
        if not ok:
            continue
        # With no artist in the title, the earliest release is most likely the original,
        # not one of the many covers on iTunes.
        released = "" if others else (r.get("releaseDate") or "9999")[:10]
        score = (round(a_sim, 2), t_sim == 1.0, [-ord(c) for c in released], -order)
        if best_score is None or score > best_score:
            best, best_score = r, score
    return best


def display_title(name: str) -> str:
    """Song title as the chart shows it: 「可愛くてごめん (feat. ちゅーたん(CV:早見沙織))」 -> 可愛くてごめん."""
    return _unbalanced(match.clean_title(name))


def song_group(name: str, artist: str) -> str:
    """Grouping key for an identified song: clean title plus first artist, so single and album
    releases of the same song fall together."""
    return match.norm(match.clean_title(name)) + "|" + match.norm(match.first_artist(artist))


def guess(segs: list[str], known_artists: set[str]) -> tuple[str, str]:
    """Title and artist for a video iTunes could not identify: the first piece that is not a
    known artist is the title; the other one, if any, the artist."""
    if not segs:
        return "", ""
    if len(segs) > 1 and match.norm(match.first_artist(segs[0])) in known_artists:
        return segs[1], segs[0]
    return segs[0], (segs[1] if len(segs) > 1 else "")
