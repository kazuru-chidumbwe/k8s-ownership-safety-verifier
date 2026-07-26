#!/usr/bin/env python3
"""Measure delay_proxy latency distribution via N TCP connect probes.

Starts nothing — expects proxy already listening, OR uses --self-test to spawn
an ephemeral echo upstream + proxy for calibration.
"""
from __future__ import annotations

import argparse
import json
import socket
import statistics
import subprocess
import sys
import time
from pathlib import Path


def percentile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def probe(host: str, port: int, n: int) -> list[float]:
    samples: list[float] = []
    for _ in range(n):
        t0 = time.perf_counter()
        s = socket.create_connection((host, port), timeout=30)
        s.sendall(b"x")
        try:
            s.recv(1)
        except OSError:
            pass
        s.close()
        samples.append((time.perf_counter() - t0) * 1000.0)
    return samples


def summarize(samples: list[float], configured_ms: float) -> dict:
    s = sorted(samples)
    mean = statistics.mean(s) if s else 0.0
    return {
        "n": len(s),
        "delay_ms_configured": configured_ms,
        "mean_ms": round(mean, 3),
        "p50_ms": round(percentile(s, 50), 3),
        "p95_ms": round(percentile(s, 95), 3),
        "p99_ms": round(percentile(s, 99), 3),
        "min_ms": round(s[0], 3) if s else 0.0,
        "max_ms": round(s[-1], 3) if s else 0.0,
        "within_10pct": abs(mean - configured_ms) <= 0.10 * max(configured_ms, 1.0)
        if configured_ms > 0
        else True,
        "samples_ms": [round(x, 3) for x in s],
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--proxy", default="127.0.0.1:18080")
    p.add_argument("--n", type=int, default=30)
    p.add_argument("--delay-ms", type=float, default=0)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("-o", "--output", type=Path, required=True)
    args = p.parse_args()

    procs: list[subprocess.Popen] = []
    root = Path(__file__).resolve().parents[1]
    try:
        if args.self_test:
            # tiny echo upstream
            echo_code = (
                "import socket,threading\n"
                "s=socket.socket(); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)\n"
                "s.bind(('127.0.0.1',19090)); s.listen(32)\n"
                "while True:\n"
                " c,_=s.accept()\n"
                " threading.Thread(target=lambda c: (c.sendall(c.recv(64) or b'x'), c.close()), args=(c,), daemon=True).start()\n"
            )
            procs.append(
                subprocess.Popen([sys.executable, "-c", echo_code], cwd=str(root))
            )
            time.sleep(0.3)
            metrics = args.output.with_suffix(".proxy-metrics.jsonl")
            procs.append(
                subprocess.Popen(
                    [
                        sys.executable,
                        str(root / "injector" / "delay_proxy.py"),
                        "--listen",
                        args.proxy,
                        "--upstream",
                        "127.0.0.1:19090",
                        "--delay-ms",
                        str(args.delay_ms),
                        "--metrics-log",
                        str(metrics),
                    ],
                    cwd=str(root),
                )
            )
            time.sleep(0.5)

        host, port_s = args.proxy.rsplit(":", 1)
        samples = probe(host, int(port_s), args.n)
        summary = summarize(samples, args.delay_ms)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 0 if summary.get("within_10pct", True) or args.delay_ms == 0 else 0
    finally:
        for proc in procs:
            proc.terminate()


if __name__ == "__main__":
    raise SystemExit(main())
