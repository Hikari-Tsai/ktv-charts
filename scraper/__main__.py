"""Fetch every source and write site/data/<source>.json.

    python -m scraper                # all sources
    python -m scraper holiday dam    # only some

A job that fails keeps the charts from the previous run (marked stale), so one broken
site never blanks the page. Exit code is 1 only when every job of every source failed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import traceback
from pathlib import Path

from . import enrich
from .history import History, period_key
from .sources import ALL

ROOT = Path(__file__).resolve().parent.parent
SITE_DATA = ROOT / "site" / "data"
HISTORY = ROOT / "data" / "history"
TZ = dt.timezone(dt.timedelta(hours=8))  # display times in Taiwan time


def now_iso() -> str:
    return dt.datetime.now(TZ).isoformat(timespec="seconds")


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def run_source(module, history: History) -> tuple[dict, int, int]:
    src = module.SOURCE
    label = src["name"]["zh"] if isinstance(src["name"], dict) else src["name"]
    out_path = SITE_DATA / f"{src['id']}.json"
    previous = {c["id"]: c for c in load_json(out_path).get("charts", [])}
    today = dt.datetime.now(TZ).date().isoformat()

    charts: list[dict] = []
    errors: list[str] = []
    ok_jobs = 0
    for job in module.JOBS:
        try:
            fresh = job["fetch"]()
        except Exception as exc:  # noqa: BLE001 - any failure falls back to old data
            msg = f"{job['name']}: {exc}"
            errors.append(msg)
            print(f"::warning title={label} {job['name']} failed::{exc}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            for cid in job["charts"]:
                if cid in previous:
                    old = dict(previous[cid])
                    old["stale"] = True
                    charts.append(old)
            continue
        ok_jobs += 1
        stamp = now_iso()
        for chart in fresh:
            chart["period_key"] = period_key(chart.get("period") or chart.get("updated"), today)
            chart["rank_change"] = chart.pop("prev_from")  # "site" or "history"
            if chart["rank_change"] == "history":
                history.fill_previous_ranks(src["id"], chart)
            history.save(src["id"], chart)
            chart["fetched_at"] = stamp
            chart["stale"] = False
            charts.append(chart)
        print(f"{label} {job['name']}: " + ", ".join(f"{c['id']}={len(c['rows'])}" for c in fresh))

    data = {
        "source": src["id"],
        "name": src["name"],
        "region": src["region"],
        "kind": src.get("kind", "ktv"),
        "site_url": src["site_url"],
        "checked_at": now_iso(),
        "errors": errors,
        "charts": charts,
    }
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return data, ok_jobs, len(module.JOBS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scraper")
    parser.add_argument("sources", nargs="*", help="source ids to run (default: all)")
    args = parser.parse_args(argv)
    modules = [m for m in ALL if not args.sources or m.SOURCE["id"] in args.sources]
    if not modules:
        parser.error(f"unknown source; choose from {[m.SOURCE['id'] for m in ALL]}")

    history = History(HISTORY)
    total_ok = total_jobs = 0
    for module in modules:
        _, ok, jobs = run_source(module, history)
        total_ok += ok
        total_jobs += jobs

    index = {
        "updated_at": now_iso(),
        "sources": [
            {**{k: m.SOURCE[k] for k in ("id", "name", "region", "site_url")}, "kind": m.SOURCE.get("kind", "ktv")}
            for m in ALL
        ],
    }
    (SITE_DATA / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    try:
        counts = enrich.apply_files(SITE_DATA)  # genres and links from caches; no network
        print("annotated rows: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    except Exception as exc:  # noqa: BLE001 - tags are optional; rankings must still publish
        print(f"::warning title=Genre tags skipped::{exc}", file=sys.stderr)
    print(f"done: {total_ok}/{total_jobs} jobs succeeded")
    return 0 if total_ok else 1


if __name__ == "__main__":
    sys.exit(main())
