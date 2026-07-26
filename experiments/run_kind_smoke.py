#!/usr/bin/env python3
"""Kind smoke: Deployment create/scale, poll ownership events, verify O1/O2 PASS."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.check import check_trace  # noqa: E402


def sh(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def owners_from_obj(obj: dict) -> list[dict]:
    refs = (obj.get("metadata") or {}).get("ownerReferences") or []
    return [
        {
            "uid": r.get("uid"),
            "name": r.get("name"),
            "controller": bool(r.get("controller")),
            "apiVersion": r.get("apiVersion"),
            "kind": r.get("kind"),
        }
        for r in refs
    ]


def normalize(resource: str, obj: dict, experiment_id: str) -> dict:
    md = obj.get("metadata") or {}
    singular = {"deployments": "deployment", "replicasets": "replicaset", "pods": "pod"}.get(resource, resource)
    return {
        "time": utc_now(),
        "resource": singular,
        "namespace": md.get("namespace") or "default",
        "name": md.get("name") or "",
        "uid": md.get("uid") or "",
        "resourceVersion": str(md.get("resourceVersion") or ""),
        "event": "UPDATE",
        "owners": owners_from_obj(obj),
        "source": "poll",
        "experiment_id": experiment_id,
        "fault_state": "none",
    }


def poll_once(namespace: str, experiment_id: str, seen: set[str]) -> list[dict]:
    events: list[dict] = []
    for resource in ("deployments", "replicasets", "pods"):
        cp = sh(["kubectl", "get", resource, "-n", namespace, "-o", "json"], check=False)
        if cp.returncode != 0:
            continue
        data = json.loads(cp.stdout or "{}")
        for obj in data.get("items") or []:
            md = obj.get("metadata") or {}
            key = f"{resource}:{md.get('uid')}:{md.get('resourceVersion')}"
            if key in seen:
                continue
            seen.add(key)
            events.append(normalize(resource, obj, experiment_id))
    return events


def wait_deployment(namespace: str, name: str, timeout: float = 180.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        cp = sh(["kubectl", "rollout", "status", f"deployment/{name}", "-n", namespace, "--timeout=20s"], check=False)
        if cp.returncode == 0:
            return
        time.sleep(2)
    raise RuntimeError("deployment did not become ready")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--namespace", default="kosv-smoke")
    p.add_argument("--name", default="kosv-nginx")
    p.add_argument("--experiment-id", default="SMOKE-KIND-CLEAN")
    p.add_argument("--out-trace", type=Path, default=ROOT / "traces" / "kind-clean.jsonl")
    p.add_argument("--out-report", type=Path, default=ROOT / "results" / "kind-clean.json")
    p.add_argument("--poll-seconds", type=float, default=40.0)
    args = p.parse_args()

    args.out_trace.parent.mkdir(parents=True, exist_ok=True)
    args.out_report.parent.mkdir(parents=True, exist_ok=True)

    sh(["kubectl", "create", "namespace", args.namespace], check=False)
    sh(["kubectl", "-n", args.namespace, "delete", "deployment", args.name, "--ignore-not-found"], check=False)

    manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {args.name}
  namespace: {args.namespace}
  labels:
    app: kosv-smoke
spec:
  replicas: 2
  selector:
    matchLabels:
      app: kosv-smoke
  template:
    metadata:
      labels:
        app: kosv-smoke
    spec:
      containers:
      - name: nginx
        image: nginx:1.27-alpine
        ports:
        - containerPort: 80
"""
    subprocess.run(["kubectl", "apply", "-f", "-"], input=manifest, text=True, check=True)

    seen: set[str] = set()
    all_events: list[dict] = []
    t0 = time.time()
    while time.time() - t0 < args.poll_seconds / 2:
        all_events.extend(poll_once(args.namespace, args.experiment_id, seen))
        time.sleep(1.0)

    wait_deployment(args.namespace, args.name)
    all_events.extend(poll_once(args.namespace, args.experiment_id, seen))

    sh(["kubectl", "-n", args.namespace, "scale", f"deployment/{args.name}", "--replicas=3"], check=True)
    t1 = time.time()
    while time.time() - t1 < args.poll_seconds / 2:
        all_events.extend(poll_once(args.namespace, args.experiment_id, seen))
        time.sleep(1.0)
    wait_deployment(args.namespace, args.name)
    all_events.extend(poll_once(args.namespace, args.experiment_id, seen))

    with args.out_trace.open("w", encoding="utf-8") as f:
        for ev in all_events:
            f.write(json.dumps(ev, separators=(",", ":")) + "\n")

    report = check_trace(all_events, trace_id=args.experiment_id)
    args.out_report.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report.to_dict(), indent=2))
    print(f"trace={args.out_trace} events={len(all_events)} status={report.status}")
    return 0 if report.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
