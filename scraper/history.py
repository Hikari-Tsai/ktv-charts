"""Per-chart history snapshots, used to derive previous ranks where a site gives none."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path


def period_key(period: str | None, fallback: str) -> str:
    """Turn '2026/10/26 ~ 2026/11/01' into '2026-10-26_2026-11-01' (sortable file name)."""
    dates = re.findall(r"\d{4}/\d{1,2}(?:/\d{1,2})?", period or "")
    if not dates:
        return fallback
    parts = []
    for d in dates:
        nums = [int(x) for x in d.split("/")]
        parts.append("-".join(f"{n:02d}" if i else str(n) for i, n in enumerate(nums)))
    return "_".join(parts)


def normalize(text: str | None) -> str:
    text = unicodedata.normalize("NFKC", text or "").casefold()
    return re.sub(r"\s+", "", text)


def song_key(row: dict) -> str:
    """Stable identity for a song within one source."""
    if row.get("song_no"):
        return "no:" + row["song_no"]
    if row.get("song_url"):
        return "url:" + row["song_url"]
    return "ta:" + normalize(row.get("title")) + "|" + normalize(row.get("artist"))


class History:
    def __init__(self, root: Path):
        self.root = root

    def _dir(self, source: str, chart: str) -> Path:
        return self.root / source / chart

    def save(self, source: str, chart: dict) -> None:
        d = self._dir(source, chart["id"])
        d.mkdir(parents=True, exist_ok=True)
        rows = [
            {k: r.get(k) for k in ("rank", "title", "artist", "song_no", "song_url") if r.get(k) is not None}
            for r in chart["rows"]
        ]
        payload = {"period": chart.get("period"), "rows": rows}
        (d / f"{chart['period_key']}.json").write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
        )

    def previous(self, source: str, chart_id: str, key: str) -> dict | None:
        """Latest snapshot strictly older than `key`."""
        d = self._dir(source, chart_id)
        if not d.is_dir():
            return None
        older = sorted(p for p in d.glob("*.json") if p.stem < key)
        if not older:
            return None
        return json.loads(older[-1].read_text(encoding="utf-8"))

    def fill_previous_ranks(self, source: str, chart: dict) -> None:
        """Set last_rank / is_new from the previous snapshot. Leaves None when there is none."""
        prev = self.previous(source, chart["id"], chart["period_key"])
        if prev is None:
            for r in chart["rows"]:
                r["last_rank"] = None
                r["is_new"] = None
            return
        ranks = {song_key(r): r["rank"] for r in prev["rows"]}
        for r in chart["rows"]:
            last = ranks.get(song_key(r))
            r["last_rank"] = last
            r["is_new"] = last is None
