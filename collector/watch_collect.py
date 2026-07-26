#!/usr/bin/env python3
"""Collect ControllerRef transitions via kubectl get/watch into JSONL.

Requires kubectl context pointing at a live cluster. Emits normalized events
for Deployments, ReplicaSets, and Pods in a namespace.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RESOURCES = ("deployments", "replicasets", "pods")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def owners_from_obj(obj: dict[str, Any]) -> list[dict[str, Any]]:
    refs = (obj.get("metadata") or {}).get("ownerReferences") or []
    out = []
    for r in refs:
        out.append(
            {
                "uid": r.get("uid"),
                "name": r.get("name"),
                "controller": bool(r.get("controller")),
                "apiVersion": r.get("apiVersion"),
                "kind": r.get("kind"),
            }
        )
    return out


def normalize(resource: str, etype: str, obj: dict[str, Any], experiment_id: str) -> dict[str, Any]:
    md = obj.get("metadata") or {}
    return {
        "time": utc_now(),
        "resource": resource.rstrip("s") if resource.endswith("s") else resource,
        "namespace": md.get("namespace") or "default",
        "name": md.get("name") or "",
        "uid": md.get("uid") or "",
        "resourceVersion": str(md.get("resourceVersion") or ""),
        "event": etype.upper(),
        "owners": owners_from_obj(obj),
        "source": "watch",
        "experiment_id": experiment_id,
        "fault_state": "none",
    }


def watch_resource(
    resource: str,
    namespace: str,
    experiment_id: str,
    out_path: Path,
    stop: threading.Event,
    lock: threading.Lock,
) -> None:
    cmd = [
        "kubectl",
        "get",
        resource,
        "-n",
        namespace,
        "--watch",
        "-o",
        "json",
    ]
    # kubectl --watch -o json streams concatenated JSON objects; use watch-only via get --watch
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    buf = ""
    depth = 0
    in_str = False
    esc = False
    try:
        while not stop.is_set():
            ch = proc.stdout.read(1)
            if ch == "":
                if proc.poll() is not None:
                    break
                time.sleep(0.05)
                continue
            buf += ch
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and buf.strip():
                    try:
                        obj = json.loads(buf)
                    except json.JSONDecodeError:
                        buf = ""
                        continue
                    # kubectl --watch may emit full object; type is not always present
                    etype = "UPDATE"
                    if "type" in obj and "object" in obj:
                        etype = str(obj.get("type") or "UPDATE")
                        obj = obj.get("object") or {}
                    ev = normalize(resource, etype, obj, experiment_id)
                    with lock:
                        with out_path.open("a", encoding="utf-8") as f:
                            f.write(json.dumps(ev, separators=(",", ":")) + "\n")
                    buf = ""
    finally:
        proc.kill()


def snapshot(namespace: str, experiment_id: str, out_path: Path) -> int:
    """One-shot list of all target resources (reliable without streaming parser)."""
    n = 0
    with out_path.open("a", encoding="utf-8") as f:
        for resource in RESOURCES:
            cmd = ["kubectl", "get", resource, "-n", namespace, "-o", "json"]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                print(proc.stderr, file=sys.stderr)
                continue
            data = json.loads(proc.stdout or "{}")
            for obj in data.get("items") or []:
                ev = normalize(resource, "ADDED", obj, experiment_id)
                f.write(json.dumps(ev, separators=(",", ":")) + "\n")
                n += 1
    return n


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--namespace", default="kosv-smoke")
    p.add_argument("--experiment-id", default="KIND-COLLECT")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--mode", choices=["snapshot", "watch"], default="snapshot")
    p.add_argument("--duration-sec", type=float, default=30.0)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("", encoding="utf-8")

    if args.mode == "snapshot":
        n = snapshot(args.namespace, args.experiment_id, args.output)
        print(f"wrote {n} events to {args.output}")
        return 0

    stop = threading.Event()
    lock = threading.Lock()
    threads = []
    for resource in RESOURCES:
        t = threading.Thread(
            target=watch_resource,
            args=(resource, args.namespace, args.experiment_id, args.output, stop, lock),
            daemon=True,
        )
        t.start()
        threads.append(t)
    time.sleep(args.duration_sec)
    stop.set()
    time.sleep(0.5)
    lines = sum(1 for _ in args.output.open(encoding="utf-8") if _.strip())
    print(f"wrote {lines} events to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
