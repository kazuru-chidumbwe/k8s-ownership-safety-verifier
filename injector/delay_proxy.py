#!/usr/bin/env python3
"""Minimal TCP delay proxy for deterministic observation-path delay.

Listens on --listen, forwards to --upstream, sleeping --delay-ms on each
direction after accept (per-connection startup delay) and optionally on each
relay chunk (--chunk-delay-ms).

This is the v0 fault injector surface. It does not claim to capture controller
belief (O3). It only delays bytes on a chosen TCP path.
"""
from __future__ import annotations

import argparse
import select
import socket
import threading
import time


def relay(src: socket.socket, dst: socket.socket, chunk_delay_ms: float) -> None:
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            if chunk_delay_ms > 0:
                time.sleep(chunk_delay_ms / 1000.0)
            dst.sendall(data)
    except OSError:
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def handle(
    client: socket.socket,
    upstream_host: str,
    upstream_port: int,
    delay_ms: float,
    chunk_delay_ms: float,
) -> None:
    if delay_ms > 0:
        time.sleep(delay_ms / 1000.0)
    try:
        up = socket.create_connection((upstream_host, upstream_port), timeout=30)
    except OSError:
        client.close()
        return
    t1 = threading.Thread(target=relay, args=(client, up, chunk_delay_ms), daemon=True)
    t2 = threading.Thread(target=relay, args=(up, client, chunk_delay_ms), daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    client.close()
    up.close()


def main() -> int:
    p = argparse.ArgumentParser(description="KOSV TCP delay proxy")
    p.add_argument("--listen", default="127.0.0.1:18080")
    p.add_argument("--upstream", required=True, help="host:port")
    p.add_argument("--delay-ms", type=float, default=0)
    p.add_argument("--chunk-delay-ms", type=float, default=0)
    args = p.parse_args()
    lh, lp = args.listen.rsplit(":", 1)
    uh, up = args.upstream.rsplit(":", 1)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((lh, int(lp)))
    srv.listen(128)
    print(
        f"delay_proxy listen={args.listen} upstream={args.upstream} "
        f"delay_ms={args.delay_ms} chunk_delay_ms={args.chunk_delay_ms}",
        flush=True,
    )
    while True:
        r, _, _ = select.select([srv], [], [], 1.0)
        if not r:
            continue
        c, _ = srv.accept()
        threading.Thread(
            target=handle,
            args=(c, uh, int(up), args.delay_ms, args.chunk_delay_ms),
            daemon=True,
        ).start()


if __name__ == "__main__":
    raise SystemExit(main())
