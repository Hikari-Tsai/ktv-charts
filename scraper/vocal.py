"""Estimate the sung range (lowest and highest note) from iTunes 30-second previews.

    python -m scraper.vocal                        # analyze new songs, then annotate
    python -m scraper.vocal --max 60 --budget 1200

Pipeline per song:
1. ffmpeg decodes the preview to 44,100 Hz stereo.
2. UVR MDX-Net Kim_Vocal_2 separates the vocals, so the bass, piano and guitar in the
   intro are not read as notes.
3. GAME Small (openvpi, Generative Adaptive MIDI Extractor) transcribes the vocals into
   notes with floating-point MIDI pitches.
4. filter_notes() removes ghost notes: blips, notes outside any human range, single-note
   spikes far from both neighbours (octave errors), notes cut off from the main body by
   an empty stretch, and extremes sung too briefly to count.
5. advise() turns the lowest and highest note into a suggestion for male and female
   voices, with a KTV key change when the original key does not fit.

Both models come from pinned Hugging Face mirrors (aaatmy/game-small-onnx and
aaatmy/uvr-mdx-net-onnx) and are checked against SHA-256. GAME's weights are
CC BY-NC-SA 4.0; the site is non-commercial and credits openvpi. Results, including
misses, go into the permanent append-only cache data/vocal-range.json.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import math
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from . import bpm, enrich
from .singrange import filter_notes, note_name
from .net import get_bytes

ROOT = Path(__file__).resolve().parent.parent
RANGE_CACHE = enrich.RANGE_CACHE
MODEL_DIR = Path(os.environ.get("VOCAL_MODEL_DIR", ROOT / ".cache" / "vocal"))
TZ = dt.timezone(dt.timedelta(hours=8))
RETRY_DAYS = 30
VERSION = 1  # bump to re-analyze every song after a pipeline change

GAME_REPO = "aaatmy/game-small-onnx"
GAME_REV = "da403f8b7740260d2833cad59a429439805fab53"
GAME_FILES = {
    "encoder.onnx": "a6868a702d9c88ccc06b19e54f49d88b7f8cba4a68517f20806bd81ef6f94e06",
    "segmenter.onnx": "7724db4ba59a388fff5aba2f08f0ac025d4ca59caef80e7f474053a1455c88e5",
    "estimator.onnx": "a84738b2504472a1f22773cc6b0eccad1353a8f36229ad490b8fea85388bb5e1",
    "dur2bd.onnx": "49d10d1ea186e43c51fd2c51cedb01a3852d363f1c7056ae77df50f7e8dd0996",
    "bd2dur.onnx": "6672d56b00f27a20e9bfaa92801c15e394bb520e49031d3ed2515b0a6cf27402",
}
UVR_REPO = "aaatmy/uvr-mdx-net-onnx"
UVR_REV = "1d1cf7c799e578a6ba1167c6ecbb010fe4c92649"
UVR_FILE = "Kim_Vocal_2.onnx"
UVR_SHA256 = "ce74ef3b6a6024ce44211a07be9cf8bc6d87728cc852a68ab34eb8e58cde9c8b"
MODEL_ID = "game-small-1.0.3+kim-vocal-2"

RATE = 44100
# UVR MDX-Net Kim_Vocal_2: STFT parameters from the mirror's manifest.json
N_FFT, HOP, DIM_F, DIM_T = 7680, 1024, 3072, 256
MDX_CHUNK = HOP * (DIM_T - 1)
MDX_TRIM = N_FFT // 2
MDX_GEN = MDX_CHUNK - 2 * MDX_TRIM
# GAME: 8-second windows with 1 second of context either side, 8 D3PM steps (t = i/8),
# universal language id 0, boundary and presence thresholds 0.2, radius 2 frames.
GAME_STEP, GAME_CONTEXT, GAME_STEPS, GAME_THRESHOLD, GAME_RADIUS = 8, 1, 8, 0.2, 2

# ---------- models ----------

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _fetch(repo: str, rev: str, name: str, sha: str) -> Path:
    path = MODEL_DIR / repo.split("/")[-1] / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or _sha256(path) != sha:
        tmp = path.with_suffix(".part")
        tmp.write_bytes(get_bytes(f"https://huggingface.co/{repo}/resolve/{rev}/{name}"))
        if _sha256(tmp) != sha:
            tmp.unlink()
            raise RuntimeError(f"downloaded {name} does not match the pinned SHA-256")
        tmp.replace(path)
    return path


class Models:
    def __init__(self):
        import onnxruntime as ort

        opts = ort.SessionOptions()
        opts.log_severity_level = 3

        def session(path):
            return ort.InferenceSession(str(path), opts, providers=["CPUExecutionProvider"])

        self.game = {name[:-5]: session(_fetch(GAME_REPO, GAME_REV, name, sha)) for name, sha in GAME_FILES.items()}
        self.mdx = session(_fetch(UVR_REPO, UVR_REV, UVR_FILE, UVR_SHA256))

    def run(self, name: str, feeds: dict) -> dict:
        s = self.game[name]
        return dict(zip([o.name for o in s.get_outputs()], s.run(None, feeds)))


# ---------- audio ----------

def decode_stereo(data: bytes, suffix: str = ".m4a"):
    """Any ffmpeg-readable audio -> float32 [2, samples] at 44,100 Hz."""
    import numpy as np

    with tempfile.NamedTemporaryFile(suffix=suffix) as f:
        f.write(data)
        f.flush()
        out = subprocess.run(
            ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", f.name,
             "-ac", "2", "-ar", str(RATE), "-f", "f32le", "pipe:1"],
            capture_output=True, check=True,
        ).stdout
    return np.frombuffer(out, dtype=np.float32).reshape(-1, 2).T.copy()


def _window():
    import numpy as np

    return np.hanning(N_FFT + 1)[:-1]  # periodic Hann, as torch.hann_window


def _stft(x, window):
    """[C, L] -> [C, N_FFT/2+1, frames] complex; centred with reflect padding like torch.stft."""
    import numpy as np

    p = np.pad(x, ((0, 0), (N_FFT // 2, N_FFT // 2)), mode="reflect")
    frames = 1 + (p.shape[1] - N_FFT) // HOP
    idx = np.arange(N_FFT)[None, :] + HOP * np.arange(frames)[:, None]
    return np.fft.rfft(p[:, idx] * window, axis=-1).transpose(0, 2, 1)


def _istft(spec, length: int, window):
    import numpy as np

    frames = np.fft.irfft(spec.transpose(0, 2, 1), n=N_FFT, axis=-1) * window
    count = frames.shape[1]
    out = np.zeros((spec.shape[0], N_FFT + HOP * (count - 1)))
    norm = np.zeros(out.shape[1])
    for t in range(count):
        out[:, t * HOP:t * HOP + N_FFT] += frames[:, t]
        norm[t * HOP:t * HOP + N_FFT] += window ** 2
    out /= np.maximum(norm, 1e-8)
    return out[:, N_FFT // 2:N_FFT // 2 + length]


def separate_vocals(models: Models, mix):
    """UVR MDX-Net: STFT chunks of 256 frames, 4 planes (L/R real/imag), predict the vocal stem."""
    import numpy as np

    window = _window()
    n = mix.shape[1]
    pad = MDX_GEN - n % MDX_GEN
    padded = np.concatenate([np.zeros((2, MDX_TRIM)), mix, np.zeros((2, pad + MDX_TRIM))], axis=1)
    name = models.mdx.get_inputs()[0].name
    parts = []
    for i in range(0, n + pad, MDX_GEN):
        spec = _stft(padded[:, i:i + MDX_CHUNK], window)[:, :DIM_F]
        x = np.stack([spec[0].real, spec[0].imag, spec[1].real, spec[1].imag])[None].astype(np.float32)
        y = models.mdx.run(None, {name: x})[0][0]
        full = np.zeros((2, N_FFT // 2 + 1, DIM_T), np.complex128)
        full[0, :DIM_F] = y[0] + 1j * y[1]
        full[1, :DIM_F] = y[2] + 1j * y[3]
        parts.append(_istft(full, MDX_CHUNK, window)[:, MDX_TRIM:-MDX_TRIM])
    return np.concatenate(parts, axis=1)[:, :n].astype(np.float32)


def _game_window(models: Models, samples, offset: float, own_start: float, own_end: float) -> list[tuple]:
    import numpy as np

    duration = len(samples) / RATE
    enc = models.run("encoder", {"waveform": samples.reshape(1, -1), "duration": np.array([duration], np.float32)})
    known = models.run("dur2bd", {"durations": np.array([[duration]], np.float32), "maskT": enc["maskT"]})["boundaries"]
    threshold = np.array(GAME_THRESHOLD, np.float32)
    bounds = known
    for i in range(GAME_STEPS):
        bounds = models.run("segmenter", {
            "x_seg": enc["x_seg"], "maskT": enc["maskT"], "language": np.array([0], np.int64),
            "known_boundaries": known, "prev_boundaries": bounds,
            "t": np.array([i / GAME_STEPS], np.float32), "threshold": threshold,
            "radius": np.array(GAME_RADIUS, np.int64),
        })["boundaries"]
    regions = models.run("bd2dur", {"boundaries": bounds, "maskT": enc["maskT"]})
    est = models.run("estimator", {"x_est": enc["x_est"], "boundaries": bounds, "maskT": enc["maskT"],
                                   "maskN": regions["maskN"], "threshold": threshold})
    notes, cursor = [], offset
    for dur, midi, voiced, valid in zip(regions["durations"][0], est["scores"][0],
                                        est["presence"][0], regions["maskN"][0]):
        start = max(cursor, own_start)
        cursor += float(dur)
        end = min(cursor, own_end)
        if valid and voiced and math.isfinite(float(midi)) and end > start:
            notes.append((round(start, 3), round(end - start, 3), round(float(midi), 2)))
    return notes


def transcribe(models: Models, mono) -> list[tuple]:
    """GAME over 8-second windows with 1 second of context; each window keeps only its own 8 seconds."""
    import numpy as np

    notes = []
    step, ctx = GAME_STEP * RATE, GAME_CONTEXT * RATE
    for s in range(0, len(mono), step):
        a, b = max(0, s - ctx), min(len(mono), s + step + ctx)
        chunk = np.ascontiguousarray(mono[a:b], dtype=np.float32)
        if np.abs(chunk).max(initial=0) < 1e-4:
            continue
        notes += _game_window(models, chunk, a / RATE, s / RATE, min(len(mono), s + step) / RATE)
    return notes


def analyze(models: Models, mix) -> dict | None:
    vocals = separate_vocals(models, mix).mean(axis=0)
    result = filter_notes(transcribe(models, vocals))
    if result:
        result["low_name"], result["high_name"] = note_name(result["low"]), note_name(result["high"])
    return result


# ---------- main ----------

def run(max_songs: int, budget: float) -> dict:
    sites = enrich.load_sites()
    itunes = enrich.load_cache(enrich.ITUNES_CACHE)
    cache = enrich.load_cache(RANGE_CACHE)
    today = dt.datetime.now(TZ).date()
    stale = {k for k, v in cache.items() if v.get("v", 0) < VERSION}
    todo = bpm.candidates(sites, itunes, {k: v for k, v in cache.items() if k not in stale}, today)[:max_songs]
    print(f"{len(todo)} songs to analyze this run", flush=True)
    stats = {"analyzed": 0, "ok": 0, "no_preview": 0, "few_notes": 0, "errors": 0}
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
        record = {"checked": stamp, "track": f"{item['cc']}/{item['id']}", "model": MODEL_ID, "v": VERSION}
        if not url:
            cache[item["key"]] = {**record, "status": "none", "reason": "no_preview"}
            stats["no_preview"] += 1
        else:
            try:
                result = analyze(models, decode_stereo(get_bytes(url)))
            except Exception as exc:  # noqa: BLE001 - one bad file must not stop the batch
                print(f"Range failed for {item['key']}: {exc}", file=sys.stderr)
                stats["errors"] += 1
                continue
            if result:
                cache[item["key"]] = {**record, "status": "ok", **result}
                stats["ok"] += 1
            else:
                cache[item["key"]] = {**record, "status": "none", "reason": "few_notes"}
                stats["few_notes"] += 1
        stats["analyzed"] += 1
        if stats["analyzed"] % 10 == 0:
            enrich.save_cache(RANGE_CACHE, cache)
            print(f"  ... {stats['analyzed']} analyzed, {stats['ok']} with a range", flush=True)
    enrich.save_cache(RANGE_CACHE, cache)
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scraper.vocal")
    parser.add_argument("--max", type=int, default=60, help="max songs to analyze this run")
    parser.add_argument("--budget", type=float, default=1200, help="max seconds to spend analyzing")
    args = parser.parse_args(argv)
    t0 = time.monotonic()
    stats = run(args.max, args.budget)
    print("vocal range: " + ", ".join(f"{k}={v}" for k, v in stats.items()) + f" in {time.monotonic() - t0:.0f}s",
          flush=True)
    counts = enrich.apply_files()
    print("annotated rows: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
