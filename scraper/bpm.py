"""Detect BPM with the Beat This! ONNX model (aaatmy/beat-this-onnx) on iTunes 30-second previews.

    python -m scraper.bpm                        # analyze new songs, then annotate
    python -m scraper.bpm --max 300 --budget 1200

Needs ffmpeg plus numpy and onnxruntime (requirements-bpm.txt); the rest of the scraper
stays standard-library only. The pipeline is a port of the aaatmy/bpm-detector Space:
22,050 Hz mono, 128-bin log-mel (n_fft 1024, hop 441), 1,500-frame chunks with a 6-frame
border, max-pool peak picking, then a constant-grid tempo fit.

Each song is analyzed once. Results, including "no preview" and "too few beats", go into
the permanent append-only cache data/bpm.json; misses are retried after RETRY_DAYS.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path

from . import enrich, match
from .net import get_bytes, get_text

ROOT = Path(__file__).resolve().parent.parent
BPM_CACHE = ROOT / "data" / "bpm.json"
MODEL_DIR = Path(os.environ.get("BEAT_THIS_DIR", ROOT / ".cache" / "beat-this"))

MODEL_REPO = "aaatmy/beat-this-onnx"
MODEL_REV = "e2c0d4376fac8141905a8312c1b327849751d59c"
MODEL_FILE = "beat-this-final0.onnx"
MODEL_SHA256 = "e5e37b7d1802895e42559c5a1ced7619b1601d257a5c8e167c9d45de37c1b078"
MODEL_ID = "beat-this-final0"

SAMPLE_RATE = 22050
CHUNK = 1500
BORDER = 6
FPS = 50  # 22,050 / 441
RETRY_DAYS = 30
LOOKUP = "https://itunes.apple.com/lookup?"
LOOKUP_DELAY = 3.2  # shares Apple's ~20 requests/minute budget with the genre lookup
TZ = dt.timezone(dt.timedelta(hours=8))


# ---------- model ----------

def _hf_url(name: str) -> str:
    return f"https://huggingface.co/{MODEL_REPO}/resolve/{MODEL_REV}/{name}"


def ensure_model() -> tuple[Path, Path]:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model, frontend = MODEL_DIR / MODEL_FILE, MODEL_DIR / "frontend.json"
    if not frontend.exists():
        frontend.write_bytes(get_bytes(_hf_url("frontend.json")))
    if not model.exists() or _sha256(model) != MODEL_SHA256:
        tmp = model.with_suffix(".part")
        tmp.write_bytes(get_bytes(_hf_url(MODEL_FILE)))
        if _sha256(tmp) != MODEL_SHA256:
            tmp.unlink()
            raise RuntimeError("downloaded Beat This! model does not match the pinned SHA-256")
        tmp.replace(model)
    return model, frontend


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# ---------- audio and spectrogram ----------

def decode(data: bytes, suffix: str = ".m4a"):
    """Any ffmpeg-readable audio -> float32 mono at 22,050 Hz."""
    import numpy as np

    with tempfile.NamedTemporaryFile(suffix=suffix) as f:  # m4a needs a seekable input
        f.write(data)
        f.flush()
        out = subprocess.run(
            ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", f.name,
             "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "f32le", "pipe:1"],
            capture_output=True, check=True,
        ).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def log_mel(audio, window, filters):
    """Matches the Space's dsp.js: periodic Hann, reflect padding, |rfft| / sqrt(n_fft),
    Slaney mel filters from frontend.json, log1p(1000 * mel)."""
    import numpy as np

    n, hop = len(window), 441
    frames = len(audio) // hop + 1
    padded = np.pad(audio.astype(np.float64), (n // 2, n // 2), mode="reflect")
    windows = np.lib.stride_tricks.sliding_window_view(padded, n)[::hop][:frames]
    magnitude = np.abs(np.fft.rfft(windows * window, axis=1)) / np.sqrt(n)
    return np.log1p(1000.0 * (magnitude @ filters.T)).astype(np.float32)


def chunk_starts(frames: int) -> list[int]:
    starts = list(range(-BORDER, frames - BORDER, CHUNK - 2 * BORDER))
    if frames > CHUNK - 2 * BORDER:
        starts[-1] = frames - (CHUNK - BORDER)
    return starts


def predict(session, spect):
    """Chunked inference; later chunks are written first so earlier ones win (keep_first)."""
    import numpy as np

    frames = spect.shape[0]
    beat = np.full(frames, -1000.0, dtype=np.float32)
    downbeat = np.full(frames, -1000.0, dtype=np.float32)
    for start in reversed(chunk_starts(frames)):
        left = max(0, -start)
        right = max(0, min(BORDER, start + CHUNK - frames))
        lo, hi = max(0, start), min(start + CHUNK, frames)
        chunk = np.zeros((hi - lo + left + right, spect.shape[1]), dtype=np.float32)
        chunk[left:left + hi - lo] = spect[lo:hi]
        out = session.run(["beat", "downbeat"], {"spectrogram": chunk[None]})
        b, d = out[0][0], out[1][0]
        for i in range(BORDER, len(b) - BORDER):
            j = start + i
            if 0 <= j < frames:
                beat[j], downbeat[j] = b[i], d[i]
    return beat, downbeat


# ---------- beats and tempo (port of dsp.js / tempo.js) ----------

def peaks(values) -> list[float]:
    candidates = []
    n = len(values)
    for i in range(n):
        v = values[i]
        if v <= 0:
            continue
        if v == max(values[max(0, i - 3):min(n, i + 4)]):
            candidates.append(i)
    result, mean, count = [], None, 0
    for p in candidates:
        if mean is None:
            mean, count = float(p), 1
        elif p - mean <= 1:
            count += 1
            mean += (p - mean) / count
        else:
            result.append(mean / FPS)
            mean, count = float(p), 1
    if mean is not None:
        result.append(mean / FPS)
    return result


def postprocess(beat_logits, downbeat_logits) -> tuple[list[float], list[float]]:
    beats = peaks(beat_logits)
    raw = peaks(downbeat_logits)
    downbeats = []
    for t in raw:
        snapped = min(beats, key=lambda b: abs(b - t)) if beats else t
        if snapped not in downbeats:
            downbeats.append(snapped)
    return beats, downbeats


def _grid(beats):
    mid = (len(beats) - 1) / 2
    mean = sum(beats) / len(beats)
    num = sum((i - mid) * (t - mean) for i, t in enumerate(beats))
    den = sum((i - mid) ** 2 for i in range(len(beats)))
    period = num / den
    offset = mean - period * mid
    residual = max(abs(t - offset - period * i) for i, t in enumerate(beats))
    return period, residual


def _meter(beats, downbeats):
    if len(downbeats) < 3 or any(b <= a for a, b in zip(downbeats, downbeats[1:])):
        return None
    idx = []
    for d in downbeats:
        hit = next((i for i, b in enumerate(beats) if abs(b - d) <= 1e-6), -1)
        if hit < 0:
            return None
        idx.append(hit)
    n = idx[1] - idx[0]
    if n < 1 or n > 255 or any(b - a != n for a, b in zip(idx, idx[1:])):
        return None
    return n


def estimate_tempo(beats, downbeats) -> dict | None:
    if len(beats) < 2 or beats[0] < 0 or any(b <= a for a, b in zip(beats, beats[1:])):
        return None
    signature = _meter(beats, downbeats)
    period, residual = _grid(beats)
    constant = len(beats) >= 5 and signature is not None and residual <= 0.03
    variable = len(beats) >= 5 and residual > 0.03
    if not constant:
        period = (beats[-1] - beats[0]) / (len(beats) - 1)
    tempo_us = round(period * 1e6)  # Python rounds half to even, like the Space's roundEven
    if tempo_us < 1:
        return None
    return {
        "bpm": round(60e6 / tempo_us, 3),
        "avg_bpm": round(60 * (len(beats) - 1) / (beats[-1] - beats[0]), 3),
        "mode": "constant" if constant else "variable" if variable else "average",
        "signature": signature,
        "beats": len(beats),
    }


def analyze(session, frontend: dict, audio) -> dict | None:
    import numpy as np

    if not np.any(np.abs(audio) >= 1e-7):
        return None
    window = np.asarray(frontend["window"], dtype=np.float64)
    filters = np.asarray(frontend["mel_filters"], dtype=np.float64)
    beat, downbeat = predict(session, log_mel(audio, window, filters))
    beats, downbeats = postprocess(beat, downbeat)
    return estimate_tempo(beats, downbeats)


# ---------- candidates and previews ----------

def candidates(sites: dict, itunes: dict, cache: dict, today: dt.date) -> list[dict]:
    best: dict[str, dict] = {}
    for _, _, row in enrich.iter_rows(sites):
        key = match.song_key(row.get("title"), row.get("artist"))
        hit = itunes.get(key)
        if key.startswith("|") or not hit or hit.get("status") != "ok" or not hit.get("id"):
            continue
        entry = cache.get(key)
        track = f"{hit.get('cc', 'tw')}/{hit['id']}"
        if entry and entry.get("track") == track:  # a new iTunes match means re-analyze
            if entry.get("status") == "ok":
                continue
            if (today - dt.date.fromisoformat(entry.get("checked", "1970-01-01"))).days < RETRY_DAYS:
                continue
        if key not in best or row["rank"] < best[key]["rank"]:
            best[key] = {"key": key, "id": hit["id"], "cc": hit.get("cc", "tw"), "rank": row["rank"]}
    return sorted(best.values(), key=lambda c: (c["rank"], c["key"]))


def preview_urls(items: list[dict]) -> dict[int, str]:
    """Batch iTunes lookups (up to 100 ids per request) for 30-second preview URLs."""
    urls: dict[int, str] = {}
    by_cc: dict[str, list[int]] = {}
    for it in items:
        by_cc.setdefault(it["cc"], []).append(it["id"])
    for cc, ids in by_cc.items():
        for i in range(0, len(ids), 100):
            query = urllib.parse.urlencode({"id": ",".join(map(str, ids[i:i + 100])), "country": cc, "entity": "song"})
            try:
                body = get_text(LOOKUP + query, {"Accept": "application/json"})
            finally:
                time.sleep(LOOKUP_DELAY)
            for r in json.loads(body).get("results", []):
                if r.get("trackId") and r.get("previewUrl"):
                    urls[r["trackId"]] = r["previewUrl"]
    return urls


# ---------- main ----------

def run(max_songs: int, budget: float) -> dict:
    import onnxruntime as ort

    sites = enrich.load_sites()
    itunes = enrich.load_cache(enrich.ITUNES_CACHE)
    cache = enrich.load_cache(BPM_CACHE)
    today = dt.datetime.now(TZ).date()
    todo = candidates(sites, itunes, cache, today)[:max_songs]
    print(f"{len(todo)} songs to analyze this run", flush=True)
    stats = {"analyzed": 0, "ok": 0, "no_preview": 0, "few_beats": 0, "errors": 0}
    if not todo:
        return stats

    model, frontend_path = ensure_model()
    frontend = json.loads(frontend_path.read_text(encoding="utf-8"))
    opts = ort.SessionOptions()
    opts.log_severity_level = 3
    session = ort.InferenceSession(str(model), opts, providers=["CPUExecutionProvider"])
    urls = preview_urls(todo)

    start = time.monotonic()
    stamp = today.isoformat()
    for item in todo:
        if time.monotonic() - start > budget:
            break
        url = urls.get(item["id"])
        record = {"checked": stamp, "track": f"{item['cc']}/{item['id']}", "model": MODEL_ID}
        if not url:
            cache[item["key"]] = {**record, "status": "none", "reason": "no_preview"}
            stats["no_preview"] += 1
        else:
            try:
                result = analyze(session, frontend, decode(get_bytes(url)))
            except Exception as exc:  # noqa: BLE001 - one bad file must not stop the batch
                print(f"BPM failed for {item['key']}: {exc}", file=sys.stderr)
                stats["errors"] += 1
                continue
            if result:
                cache[item["key"]] = {**record, "status": "ok", **result}
                stats["ok"] += 1
            else:
                cache[item["key"]] = {**record, "status": "none", "reason": "few_beats"}
                stats["few_beats"] += 1
        stats["analyzed"] += 1
        if stats["analyzed"] % 10 == 0:
            enrich.save_cache(BPM_CACHE, cache)
            print(f"  ... {stats['analyzed']} analyzed, {stats['ok']} with BPM", flush=True)
    enrich.save_cache(BPM_CACHE, cache)
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scraper.bpm")
    parser.add_argument("--max", type=int, default=300, help="max songs to analyze this run")
    parser.add_argument("--budget", type=float, default=1200, help="max seconds to spend analyzing")
    args = parser.parse_args(argv)
    t0 = time.monotonic()
    stats = run(args.max, args.budget)
    print("bpm: " + ", ".join(f"{k}={v}" for k, v in stats.items()) + f" in {time.monotonic() - t0:.0f}s", flush=True)
    counts = enrich.apply_files()
    print("annotated rows: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
