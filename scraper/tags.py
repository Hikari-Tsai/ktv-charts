"""Tag songs with Essentia's Discogs-EffNet models on iTunes 30-second previews.

    python -m scraper.tags                        # analyze new songs, then annotate
    python -m scraper.tags --max 1500 --budget 1200

One EffNet pass per song gives 400 Discogs style scores and a 1280-d embedding for each
~2 s patch; small heads map the same embeddings to instruments, moods and themes, voice,
gender and a few binary moods. Models come from essentia.upf.edu (MTG, CC BY-NC-SA 4.0),
pinned by SHA-256. Needs ffmpeg plus numpy and onnxruntime (requirements-bpm.txt).

The cache data/essentia.json keeps each song's top scores, not hashtags: scraper.hashtags
turns scores into hashtags when the site data is written, so its thresholds and Top-K can
be tuned later without re-analyzing anything.
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
from pathlib import Path

from . import bpm, enrich
from .net import get_bytes

ROOT = Path(__file__).resolve().parent.parent
TAGS_CACHE = enrich.TAGS_CACHE
MODEL_DIR = Path(os.environ.get("ESSENTIA_DIR", ROOT / ".cache" / "essentia"))
MODEL_BASE = "https://essentia.upf.edu/models"
MODEL_ID = "discogs-effnet-1"
TZ = dt.timezone(dt.timedelta(hours=8))

SR = 16000
FRAME, HOP, BANDS = 512, 256, 96
PATCH, PATCH_HOP = 128, 62  # ~2.05 s patches, Essentia's TensorflowPredictEffnetDiscogs defaults

EMBEDDER = ("feature-extractors/discogs-effnet/discogs-effnet-bsdynamic-1",
            "a280825b334797cf677939db8cd5762c0392aedd0ca6415dbc1cd083f045e43c")
HEADS = {
    "instrument": ("mtg_jamendo_instrument", "9ae2d9e763d66bd8eed654d1ac3aa171e6539cb8a0e11f3dcd53df1428980802"),
    "moodtheme": ("mtg_jamendo_moodtheme", "7d6270acaa5f4bba4b115a0d6849aca05ed6bd153dcb6d9da4f6ab9f99ef10ff"),
    "voice_instrumental": ("voice_instrumental", "20155e4c439714b0c45c08644b73c8e12d9dccb173bd4ab9934bf1e5aee837ca"),
    "gender": ("gender", "e3e865d4bf36d4817f32ddab9452b2729f9e33a4d068d1c44ea44972a7999e91"),
    "danceability": ("danceability", "9ce9b8c44f1dd5df5ffc124e5d41d67acf254232c1b90c7e057e079ab7cead73"),
    "mood_happy": ("mood_happy", "0ca322819ef137b4b87e9866bffe7370a630e6f1165184ec106326cef6f81e06"),
    "mood_sad": ("mood_sad", "1a50d11c23181bdfdeabc7d6032a2dad829dfc19c3776d2ee57ef1724cb08805"),
    "mood_relaxed": ("mood_relaxed", "8ba6515a1e5943a72b3b475e3a25fc7a2ff04142c3eaa6aa0716fca371efdfff"),
    "mood_aggressive": ("mood_aggressive", "de36550b5d1660791ad732ed6de6ebfdc3e65dcf50b928b2578ddf103dbfb400"),
    "mood_party": ("mood_party", "c50ac2106ec2f209dd04ad48756582df0e3f3512235310d1a4a3fcc453745f04"),
    "mood_acoustic": ("mood_acoustic", "56b02abf772b9c1cf528e4d6521d6e09515cedccce47895ee5de8de33fbdf848"),
    "mood_electronic": ("mood_electronic", "4cc09140d5b078cf39e55975a23cba813e6bd4014092b78e8c415fa32a382149"),
}
# Binary heads are stored as the probability of this class.
POSITIVE = {
    "voice_instrumental": "voice", "gender": "female", "danceability": "danceable",
    "mood_happy": "happy", "mood_sad": "sad", "mood_relaxed": "relaxed", "mood_aggressive": "aggressive",
    "mood_party": "party", "mood_acoustic": "acoustic", "mood_electronic": "electronic",
}
KEEP = {"style": 20, "instrument": 15, "moodtheme": 15}  # top scores stored per song

# ---------- models ----------

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _fetch(rel: str, sha: str) -> tuple[Path, list[str]]:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    name = rel.rsplit("/", 1)[-1]
    model, meta = MODEL_DIR / f"{name}.onnx", MODEL_DIR / f"{name}.json"
    if not model.exists() or _sha256(model) != sha:
        tmp = model.with_suffix(".part")
        tmp.write_bytes(get_bytes(f"{MODEL_BASE}/{rel}.onnx"))
        if _sha256(tmp) != sha:
            tmp.unlink()
            raise RuntimeError(f"downloaded {name}.onnx does not match the pinned SHA-256")
        tmp.replace(model)
    if not meta.exists():
        meta.write_bytes(get_bytes(f"{MODEL_BASE}/{rel}.json"))
    return model, json.loads(meta.read_text(encoding="utf-8"))["classes"]


class Models:
    def __init__(self):
        import onnxruntime as ort

        opts = ort.SessionOptions()
        opts.log_severity_level = 3

        def session(path):
            return ort.InferenceSession(str(path), opts, providers=["CPUExecutionProvider"])

        path, self.styles = _fetch(*EMBEDDER)
        self.embedder = session(path)
        self.heads = {}
        for name, (head, sha) in HEADS.items():
            path, classes = _fetch(f"classification-heads/{head}/{head}-discogs-effnet-1", sha)
            self.heads[name] = (session(path), classes)


# ---------- audio front end (matches Essentia's MonoLoader + TensorflowInputMusiCNN) ----------

def decode(data: bytes, suffix: str = ".m4a"):
    """Audio bytes -> 16 kHz mono float32. Channels are averaged like Essentia's MonoLoader
    (ffmpeg's -ac 1 weights them by 1/sqrt(2), which shifts the scores); soxr resampling
    lands closest to Essentia's own resampler."""
    import numpy as np

    with tempfile.NamedTemporaryFile(suffix=suffix) as f:
        f.write(data)
        f.flush()
        base = ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", f.name]
        tail = ["-ac", "2", "-ar", str(SR), "-f", "f32le", "pipe:1"]
        try:
            out = subprocess.run(base + ["-af", "aresample=resampler=soxr"] + tail,
                                 capture_output=True, check=True).stdout
        except subprocess.CalledProcessError:  # ffmpeg built without libsoxr
            out = subprocess.run(base + tail, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).reshape(-1, 2).mean(axis=1)


def _mel_filters():
    """Slaney mel, triangles linear in Hz with unit area: Essentia MelBands(normalize='unit_tri')."""
    import numpy as np

    def hz_to_mel(f):
        return np.where(f < 1000, f / (200 / 3), 15 + np.log(np.maximum(f, 1e-9) / 1000) / (np.log(6.4) / 27))

    def mel_to_hz(m):
        return np.where(m < 15, m * 200 / 3, 1000 * np.exp((m - 15) * np.log(6.4) / 27))

    edges = mel_to_hz(np.linspace(hz_to_mel(np.float64(0)), hz_to_mel(np.float64(SR / 2)), BANDS + 2))
    freqs = np.arange(FRAME // 2 + 1) * SR / FRAME
    lo, mid, hi = edges[:-2, None], edges[1:-1, None], edges[2:, None]
    tri = np.maximum(0, np.minimum((freqs - lo) / (mid - lo), (hi - freqs) / (hi - mid)))
    return (tri * (2 / (hi - lo))).astype(np.float32)


def log_mel(audio):
    """(frames, 96) log10(1 + 10000 * mel power); 512-point symmetric Hann, hop 256, full frames only."""
    import numpy as np

    if len(audio) < FRAME:
        audio = np.pad(audio, (0, FRAME - len(audio)))
    n = 1 + (len(audio) - FRAME) // HOP
    idx = np.arange(FRAME)[None, :] + HOP * np.arange(n)[:, None]
    power = np.abs(np.fft.rfft(audio[idx] * np.hanning(FRAME), axis=1)) ** 2
    return np.log10(1 + 10000 * (power.astype(np.float32) @ _mel_filters().T))


def patches(mel):
    import numpy as np

    if len(mel) < PATCH:
        mel = np.pad(mel, ((0, PATCH - len(mel)), (0, 0)))
    return np.stack([mel[s:s + PATCH] for s in range(0, len(mel) - PATCH + 1, PATCH_HOP)]).astype(np.float32)


def _top(names: list[str], values, k: int) -> dict[str, float]:
    order = sorted(range(len(names)), key=lambda i: -float(values[i]))[:k]
    return {names[i]: round(float(values[i]), 3) for i in order}


def analyze(models: Models, audio) -> dict:
    x = patches(log_mel(audio))
    acts, embs = models.embedder.run(["activations", "embeddings"], {"melspectrogram": x})
    result = {"style": _top(models.styles, acts.mean(0), KEEP["style"]), "binary": {}}
    for name, (session, classes) in models.heads.items():
        scores = session.run(None, {session.get_inputs()[0].name: embs})[0].mean(0)
        if name in POSITIVE:
            result["binary"][name] = round(float(scores[classes.index(POSITIVE[name])]), 3)
        else:
            result[name] = _top(classes, scores, KEEP[name])
    return result


# ---------- main ----------

def run(max_songs: int, budget: float) -> dict:
    sites = enrich.load_sites()
    itunes = enrich.load_cache(enrich.ITUNES_CACHE)
    cache = enrich.load_cache(TAGS_CACHE)
    today = dt.datetime.now(TZ).date()
    todo = bpm.candidates(sites, itunes, cache, today)[:max_songs]  # same rules as BPM
    print(f"{len(todo)} songs to tag this run", flush=True)
    stats = {"analyzed": 0, "ok": 0, "no_preview": 0, "errors": 0}
    if not todo:
        return stats

    models = Models()
    urls = bpm.preview_urls(todo)
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
                cache[item["key"]] = {**record, "status": "ok", **analyze(models, decode(get_bytes(url)))}
                stats["ok"] += 1
            except Exception as exc:  # noqa: BLE001 - one bad file must not stop the batch
                print(f"Tagging failed for {item['key']}: {exc}", file=sys.stderr)
                stats["errors"] += 1
                continue
        stats["analyzed"] += 1
        if stats["analyzed"] % 25 == 0:
            enrich.save_cache(TAGS_CACHE, cache)
            print(f"  ... {stats['analyzed']} analyzed", flush=True)
    enrich.save_cache(TAGS_CACHE, cache)
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scraper.tags")
    parser.add_argument("--max", type=int, default=1500, help="max songs to analyze this run")
    parser.add_argument("--budget", type=float, default=1200, help="max seconds to spend analyzing")
    args = parser.parse_args(argv)
    t0 = time.monotonic()
    stats = run(args.max, args.budget)
    print("tags: " + ", ".join(f"{k}={v}" for k, v in stats.items()) + f" in {time.monotonic() - t0:.0f}s", flush=True)
    counts = enrich.apply_files()
    print("annotated rows: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
