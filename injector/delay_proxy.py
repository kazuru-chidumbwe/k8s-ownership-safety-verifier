#!/usr/bin/env python3
"""TCP delay proxy with per-connection measured latency logging.

Listens on --listen, forwards to --upstream. Applies --delay-ms after accept
(before upstream connect) and optional --chunk-delay-ms per relay chunk.

Writes JSONL metrics to --metrics-log:
  {"kind":"conn","delay_ms_configured":500,"accept_to_upstream_ms":512.3,...}
"""
from __future__ import annotations

import argparse
import json
import select
import socket
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def relay(src: socket.socket, dst: socket.socket, chunk_delay_ms: float, stats: dict) -> None:
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            t0 = time.perf_counter()
            if chunk_delay_ms > 0:
                time.sleep(chunk_delay_ms / 1000.0)
            dst.sendall(data)
            stats["bytes"] = stats.get("bytes", 0) + len(data)
            stats["chunks"] = stats.get("chunks", 0) + 1
            stats.setdefault("chunk_latencies_ms", []).append(
                (time.perf_counter() - t0) * 1000.0
            )
    except OSError:
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def log_metric(path: Path | None, obj: dict) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, separators=(",", ":")) + "\n")


def handle(
    client: socket.socket,
    upstream_host: str,
    upstream_port: int,
    delay_ms: float,
    chunk_delay_ms: float,
    metrics: Path | None,
) -> None:
    t_accept = time.perf_counter()
    if delay_ms > 0:
        time.sleep(delay_ms / 1000.0)
    try:
        up = socket.create_connection((upstream_host, upstream_port), timeout=30)
    except OSError as e:
        log_metric(
            metrics,
            {
                "time": utc_now(),
                "kind": "conn_error",
                "delay_ms_configured": delay_ms,
                "error": str(e),
            },
        )
        client.close()
        return
    accept_to_up_ms = (time.perf_counter() - t_accept) * 1000.0
    s1: dict = {}
    s2: dict = {}
    t1 = threading.Thread(target=relay, args=(client, up, chunk_delay_ms, s1), daemon=True)
    t2 = threading.Thread(target=relay, args=(up, client, chunk_delay_ms, s2), daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    client.close()
    up.close()
    log_metric(
        metrics,
        {
            "time": utc_now(),
            "kind": "conn",
            "delay_ms_configured": delay_ms,
            "chunk_delay_ms_configured": chunk_delay_ms,
            "accept_to_upstream_ms": round(accept_to_up_ms, 3),
            "c2u_bytes": s1.get("bytes", 0),
            "u2c_bytes": s2.get("bytes", 0),
            "c2u_chunks": s1.get("chunks", 0),
            "u2c_chunks": s2.get("chunks", 0),
        },
    )


def main() -> int:
    p = argparse.ArgumentParser(description="KOSV TCP delay proxy")
    p.add_argument("--listen", default="127.0.0.1:18080")
    p.add_argument("--upstream", required=True, help="host:port")
    p.add_argument("--delay-ms", type=float, default=0)
    p.add_argument("--chunk-delay-ms", type=float, default=0)
    p.add_argument("--metrics-log", type=Path, default=None)
    args = p.parse_args()
    lh, lp = args.listen.rsplit(":", 1)
    uh, up = args.upstream.rsplit(":", 1)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((lh, int(lp)))
    srv.listen(128)
    print(
        f"delay_proxy listen={args.listen} upstream={args.upstream} "
        f"delay_ms={args.delay_ms} metrics={args.metrics_log}",
        flush=True,
    )
    while True:
        r, _, _ = select.select([srv], [], [], 1.0)
        if not r:
            continue
        c, _ = srv.accept()
        threading.Thread(
            target=handle,
            args=(c, uh, int(up), args.delay_ms, args.chunk_delay_ms, args.metrics_log),
            daemon=True,
        ).start()


if __name__ == "__main__":
    raise SystemExit(main())
