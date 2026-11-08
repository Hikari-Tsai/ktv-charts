"""Pure helpers for the vocal range: the ghost-note filter and the male/female advice.

scraper.vocal runs the models and calls filter_notes(); scraper.enrich calls advise() when
it writes the site data, so the thresholds can change without re-analyzing any audio.
Standard library only.
"""

from __future__ import annotations

import math
from collections import defaultdict

# ---------- outlier filter ----------
MIN_DUR = 0.1           # shorter notes are consonants, breaths or segmentation blips
LOWEST, HIGHEST = 36, 96  # C2..C7: no pop lead vocal goes outside this
SPIKE_JUMP = 7          # a short note this many semitones from both neighbours ...
SPIKE_DUR = 0.3         # ... and shorter than this is a spike (octave error)
NEIGHBOUR_GAP = 1.0     # notes further apart in time than this are not neighbours
BODY_GAP = 4            # more empty semitones than this split off the main body
SUPPORT_DUR = 0.25      # an extreme note needs this many seconds in total ...
SUPPORT_COUNT = 2       # ... or this many separate notes
MIN_VOICED = 4.0        # seconds of singing needed for a result
MIN_NOTES = 12

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def note_name(midi: int) -> str:
    return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def _semi(midi: float) -> int:
    return math.floor(midi + 0.5)


def drop_spikes(notes: list[tuple]) -> list[tuple]:
    """Drop short notes that jump far from every neighbour, like an octave error inside a phrase."""
    keep = []
    for i, (start, dur, midi) in enumerate(notes):
        near = []
        if i and start - (notes[i - 1][0] + notes[i - 1][1]) <= NEIGHBOUR_GAP:
            near.append(notes[i - 1][2])
        if i + 1 < len(notes) and notes[i + 1][0] - (start + dur) <= NEIGHBOUR_GAP:
            near.append(notes[i + 1][2])
        if dur < SPIKE_DUR and near and all(abs(midi - x) >= SPIKE_JUMP for x in near):
            continue
        keep.append((start, dur, midi))
    return keep


def main_body(notes: list[tuple]) -> list[tuple]:
    """Keep the notes connected to the duration-weighted median pitch without a wide empty gap."""
    weight: dict[int, float] = defaultdict(float)
    for _, dur, midi in notes:
        weight[_semi(midi)] += dur
    half, acc, median = sum(weight.values()) / 2, 0.0, None
    for k in sorted(weight):
        acc += weight[k]
        if acc >= half:
            median = k
            break
    lo = hi = median
    for k in sorted((k for k in weight if k < median), reverse=True):
        if lo - k > BODY_GAP:
            break
        lo = k
    for k in sorted(k for k in weight if k > median):
        if k - hi > BODY_GAP:
            break
        hi = k
    return [n for n in notes if lo <= _semi(n[2]) <= hi]


def supported_extremes(notes: list[tuple]) -> tuple[int, int] | None:
    """Lowest and highest semitone held long enough, or sung often enough, to trust."""
    dur: dict[int, float] = defaultdict(float)
    count: dict[int, int] = defaultdict(int)
    for _, d, midi in notes:
        dur[_semi(midi)] += d
        count[_semi(midi)] += 1
    ok = [k for k in sorted(dur) if dur[k] >= SUPPORT_DUR or count[k] >= SUPPORT_COUNT]
    return (ok[0], ok[-1]) if ok else None


def filter_notes(notes: list[tuple]) -> dict | None:
    """notes: (start, duration, midi) in time order -> {low, high, notes, dropped, voiced} or None."""
    kept = [n for n in notes if n[1] >= MIN_DUR and LOWEST <= n[2] <= HIGHEST]
    kept = drop_spikes(kept)
    kept = main_body(kept) if kept else []
    voiced = sum(n[1] for n in kept)
    extremes = supported_extremes(kept)
    if len(kept) < MIN_NOTES or voiced < MIN_VOICED or not extremes:
        return None
    return {"low": extremes[0], "high": extremes[1], "notes": len(kept),
            "dropped": len(notes) - len(kept), "voiced": round(voiced, 1)}


# ---------- advice ----------
# Comfortable chest-voice ranges for untrained KTV singers (the site footer explains them).
# (comfortable low, comfortable high, hard high): above "comfortable high" is "high",
# above "hard high" is "very high".
ZONES = {"m": (45, 66, 69), "f": (53, 72, 76)}  # male A2-F#4 (to A4), female F3-C5 (to E5)
MAX_KEY = 7


def verdict(low: int, high: int, zone: tuple[int, int, int]) -> str:
    lo, hi, hard = zone
    too_low, too_high = low < lo, high > hi
    if too_low and too_high:
        return "wide"
    if too_high:
        return "vhigh" if high > hard else "high"
    return "low" if too_low else "ok"


def best_key(low: int, high: int, zone: tuple[int, int, int]) -> tuple[int, int] | None:
    """Smallest KTV key change (and octave the singer moves to) that fits the comfortable range."""
    lo, hi, _ = zone
    options = [(abs(k), abs(octave), k, octave)
               for octave in (0, -12, 12) for k in range(-MAX_KEY, MAX_KEY + 1)
               if lo <= low + k + octave and high + k + octave <= hi]
    if not options:
        return None
    _, _, k, octave = min(options)
    return k, octave


def advise(low: int, high: int) -> dict:
    """Who the original key suits, and per voice the verdict plus a key change if needed."""
    out: dict = {}
    for g, zone in ZONES.items():
        v = verdict(low, high, zone)
        item = {"v": v}
        if v != "ok":
            key = best_key(low, high, zone)
            if key:
                item["key"], item["oct"] = key
        out[g] = item
    m, f = out["m"]["v"] == "ok", out["f"]["v"] == "ok"
    if m and f:
        fit = "both"
    elif m or f:
        fit = "m" if m else "f"
    else:  # neither fits as is: name the voice whose comfortable range is nearer
        centre = (low + high) / 2
        fit = min(ZONES, key=lambda g: abs(centre - (ZONES[g][0] + ZONES[g][1]) / 2))
    out["fit"] = fit
    return out
