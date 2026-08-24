#!/usr/bin/env python3
"""Compute same-object and inter-sweep poll gaps from matrix trace.jsonl archives.

Definitions (must match PeerJ CS §4.3(B)):

  Same-object gap: elapsed time between two consecutive normalized events for
  the same (resource, uid) pair, irrespective of intervening sweeps.

  Inter-sweep gap: elapsed time from the last event of one poll sweep to the
  first event of the next sweep. A sweep is a contiguous block of events with
  successive inter-event gaps strictly below SWEEP_GAP_MS.

Default SWEEP_GAP_MS=200 matches the PeerJ CS §4.3(B) table computation.
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path


SWEEP_GAP_MS = 200.0


def parse_t(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def pct(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    if f == c:
        return xs[f]
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def analyze_run(trace: Path, sweep_gap_ms: float) -> tuple[list[float], list[float], int]:
    events: list[dict] = []
    with trace.open(encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            if e.get("source") == "poll":
                events.append(e)
    if not events:
        return [], [], 0

    # Same-object gaps
    by_obj: dict[tuple[str, str], list[datetime]] = defaultdict(list)
    for e in events:
        by_obj[(e["resource"], e["uid"])].append(parse_t(e["time"]))
    same_obj: list[float] = []
    for times in by_obj.values():
        times.sort()
        for a, b in zip(times, times[1:]):
            same_obj.append((b - a).total_seconds() * 1000.0)

    # Inter-sweep gaps: contiguous blocks with successive gaps < sweep_gap_ms
    times_all = sorted(parse_t(e["time"]) for e in events)
    inter_sweep: list[float] = []
    for a, b in zip(times_all, times_all[1:]):
        d = (b - a).total_seconds() * 1000.0
        if d >= sweep_gap_ms:
            inter_sweep.append(d)

    return same_obj, inter_sweep, len(events)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "matrix_stamp",
        type=Path,
        help="Path to matrix stamp dir (e.g. matrix/runs/20260726T210257Z)",
    )
    p.add_argument(
        "--sweep-gap-ms",
        type=float,
        default=SWEEP_GAP_MS,
        help=f"Inter-event threshold defining a sweep boundary (default {SWEEP_GAP_MS})",
    )
    p.add_argument("--levels", default="E0,E1,E2", help="Comma-separated experiment prefixes")
    args = p.parse_args()

    print(f"stamp={args.matrix_stamp}")
    print(f"sweep_gap_ms={args.sweep_gap_ms}")
    print("level,poll_events,same_obj_n,same_obj_p50_ms,inter_sweep_n,inter_sweep_p50_ms")
    for level in [x.strip() for x in args.levels.split(",") if x.strip()]:
        same: list[float] = []
        inter: list[float] = []
        n_events = 0
        for run in sorted(args.matrix_stamp.glob(f"{level}-r*")):
            trace = run / "trace.jsonl"
            if not trace.exists():
                continue
            s, i, n = analyze_run(trace, args.sweep_gap_ms)
            same.extend(s)
            inter.extend(i)
            n_events += n
        print(
            f"{level},{n_events},{len(same)},{pct(same, 50):.0f},{len(inter)},{pct(inter, 50):.0f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
