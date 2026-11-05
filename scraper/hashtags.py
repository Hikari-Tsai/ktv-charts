"""Turn cached Essentia scores (data/essentia.json, written by scraper.tags) into hashtags.

Standard library only, so the chart scraper can annotate rows without numpy. The rules
keep tags sparse: a minimum score and a Top-K per group, a relative floor for a second
genre, no country/language styles, no generic parent next to a specific instrument, no
contradicting moods, and vocal gender only when the model is very sure.
"""

from __future__ import annotations

# Thresholds were set from the score distribution of 300 chart songs so a typical song
# gets zero to two tags per group; see README "Hashtag 標籤".

GENRE_MIN, GENRE_RELATIVE, GENRE_TOP = 0.15, 0.5, 2   # 2nd style needs half the 1st one's score
INSTRUMENT_MIN, INSTRUMENT_TOP = 0.35, 3
COMMON_INSTRUMENT_MIN = {"drums": 0.6, "bass": 0.6}  # in almost every pop song; tag only when prominent
MOOD_MIN, MOOD_TOP = 0.85, 2           # binary mood heads
THEME_MIN = 0.20                       # one MTG-Jamendo mood/theme, mood-like classes only
VOICE_MIN, INSTRUMENTAL_MAX = 0.6, 0.2
GENDER_MIN = 0.9                       # female >= 0.9, male <= 0.1, otherwise (duets, unsure) no tag

# Styles defined by country or language rather than sound. Discogs has no Mandopop class, so
# on chart songs these misfire badly (K-pop was right for 18 of 74 songs it topped); the
# iTunes genre tag already says where a song is from.
REGIONAL_STYLES = {
    "K-pop", "J-pop", "Kayōkyoku", "Bollywood", "Chanson", "Schlager",
    "Laïkó", "Éntekhno", "Canzone Napoletana", "Catalan Music", "Fado", "Flamenco", "Volksmusik",
    "Nordic", "Romani", "Séga", "Soukous", "Zouk", "Highlife", "Raï", "African", "Pacific",
    "Hindustani", "Indian Classical", "Celtic", "Polka", "Cajun", "Hillbilly",
}
STYLE_NAMES = {"Vocal": "Vocal Pop"}  # Discogs' "Pop---Vocal"; plain "Vocal" reads like the vocal group
# Generic classes that add nothing next to a more specific one.
INSTRUMENT_PARENTS = {
    "guitar": {"electricguitar", "acousticguitar", "classicalguitar"},
    "bass": {"acousticbassguitar", "doublebass"},
    "keyboard": {"piano", "electricpiano", "rhodes", "organ", "synthesizer"},
    "percussion": {"drums", "bongo"},
}
SKIP_INSTRUMENTS = {"voice", "beat", "computer", "sampler", "pad"}  # vocals have their own group; the rest are vague
THEMES = {  # mood-like MTG-Jamendo classes; context tags such as "advertising" or "film" are left out
    "calm", "dark", "dramatic", "dream", "emotional", "energetic", "epic", "groovy", "happy",
    "heavy", "hopeful", "love", "melancholic", "powerful", "romantic", "sad", "sexy", "soft",
    "uplifting",
}
MOOD_CONFLICTS = [{"happy", "sad"}, {"happy", "melancholic"}, {"relaxed", "aggressive"}, {"relaxed", "party"},
                  {"relaxed", "danceable"}, {"relaxed", "energetic"}, {"sad", "party"}, {"sad", "danceable"},
                  {"calm", "energetic"}, {"calm", "party"}, {"soft", "aggressive"}, {"soft", "heavy"}]
BINARY_MOODS = {"mood_happy": "happy", "mood_sad": "sad", "mood_relaxed": "relaxed",
                "mood_aggressive": "aggressive", "mood_party": "party", "danceability": "danceable"}


def _ranked(scores: dict) -> list[tuple[str, float]]:
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def select_tags(entry: dict) -> dict[str, list[str]]:
    """Cached scores -> {"genre": [...], "mood": [...], "instrument": [...], "vocal": [...]}."""
    if not entry or entry.get("status") != "ok":
        return {}
    tags: dict[str, list[str]] = {}

    styles = [(n, s) for n, s in _ranked(entry.get("style", {})) if n.split("---")[-1] not in REGIONAL_STYLES]
    if styles and styles[0][1] >= GENRE_MIN:
        floor = max(GENRE_MIN, styles[0][1] * GENRE_RELATIVE)
        names = [name.split("---")[-1] for name, s in styles[:GENRE_TOP] if s >= floor]
        tags["genre"] = [STYLE_NAMES.get(n, n) for n in names]

    binary = entry.get("binary", {})
    moods = _ranked({label: binary[head] for head, label in BINARY_MOODS.items() if head in binary})
    mood: list[str] = []

    def fits(m: str) -> bool:  # skip a mood that repeats or contradicts a stronger one
        return m not in mood and not any({m, k} in MOOD_CONFLICTS for k in mood)

    for m, s in moods:
        if s >= MOOD_MIN and len(mood) < MOOD_TOP and fits(m):
            mood.append(m)
    themes = [t for t, s in _ranked(entry.get("moodtheme", {})) if t in THEMES and s >= THEME_MIN]
    for t in themes:
        if fits(t):
            mood.append(t)
            break
    if mood:
        tags["mood"] = mood

    found = [(i, s) for i, s in _ranked(entry.get("instrument", {}))
             if s >= COMMON_INSTRUMENT_MIN.get(i, INSTRUMENT_MIN) and i not in SKIP_INSTRUMENTS]
    names = {i for i, _ in found}
    found = [(i, s) for i, s in found if not INSTRUMENT_PARENTS.get(i, set()) & names]
    if found:
        tags["instrument"] = [i for i, _ in found[:INSTRUMENT_TOP]]

    voice, female = binary.get("voice_instrumental"), binary.get("gender")
    if voice is not None and voice <= INSTRUMENTAL_MAX:
        tags["vocal"] = ["instrumental"]
    elif voice is not None and voice >= VOICE_MIN and female is not None:
        if female >= GENDER_MIN:
            tags["vocal"] = ["female"]
        elif female <= 1 - GENDER_MIN:
            tags["vocal"] = ["male"]
    return tags
