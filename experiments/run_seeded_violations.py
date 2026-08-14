#!/usr/bin/env python3
"""Seeded in-cluster O1/O2 true-positive arms (PeerJ Phase 1.1).

O1: Dual controller=true ownerReferences on one Pod → expect FAIL O1.
O2: Transfer controller=true between two owners without orphan → expect FAIL O2.

Clean baseline Deployment create/scale still expected PASS (smoke).
Archives under matrix/runs/seeded-<stamp>/.
"""
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


def normalize(resource: str, obj: dict, experiment_id: str, fault: str) -> dict:
    md = obj.get("metadata") or {}
    singular = {
        "deployments": "deployment",
        "replicasets": "replicaset",
        "pods": "pod",
    }.get(resource, resource)
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
        "fault_state": fault,
    }


def poll_once(namespace: str, experiment_id: str, fault: str, seen: set[str]) -> list[dict]:
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
            events.append(normalize(resource, obj, experiment_id, fault))
    return events


def wait_deployment(namespace: str, name: str, timeout: float = 180.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        cp = sh(
            ["kubectl", "rollout", "status", f"deployment/{name}", "-n", namespace, "--timeout=20s"],
            check=False,
        )
        if cp.returncode == 0:
            return
        time.sleep(2)
    raise SystemExit(f"deployment {name} not ready in {namespace}")


def apply_nginx(namespace: str, name: str = "kosv-nginx", replicas: int = 2) -> None:
    manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {namespace}
  labels:
    app: kosv-seeded
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: kosv-seeded
  template:
    metadata:
      labels:
        app: kosv-seeded
    spec:
      containers:
        - name: nginx
          image: nginx:1.25-alpine
          ports:
            - containerPort: 80
"""
    print("+ kubectl apply deployment", flush=True)
    subprocess.run(
        ["kubectl", "apply", "-f", "-"],
        input=manifest,
        text=True,
        check=True,
        capture_output=True,
    )
    wait_deployment(namespace, name)


def get_json(resource: str, name: str, namespace: str) -> dict:
    cp = sh(["kubectl", "get", resource, name, "-n", namespace, "-o", "json"], check=True)
    return json.loads(cp.stdout)


def get_one_pod(namespace: str) -> dict:
    cp = sh(["kubectl", "get", "pods", "-n", namespace, "-o", "json"], check=True)
    items = json.loads(cp.stdout).get("items") or []
    if not items:
        raise SystemExit(f"no pods in {namespace}")
    return items[0]


def ensure_ns(ns: str) -> None:
    sh(["kubectl", "delete", "namespace", ns, "--wait=true"], check=False)
    deadline = time.time() + 120
    while time.time() < deadline:
        cp = sh(["kubectl", "get", "namespace", ns], check=False)
        if cp.returncode != 0:
            break
        time.sleep(2)
    sh(["kubectl", "create", "namespace", ns], check=True)


def write_run(out: Path, experiment_id: str, events: list[dict], report, meta: dict) -> None:
    d = out / experiment_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "trace.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    (d / "report.json").write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    (d / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def run_baseline(out: Path) -> dict:
    ns = "kosv-seed-baseline"
    eid = "SEEDED-BASELINE"
    sh(["kubectl", "delete", "namespace", ns, "--wait=false"], check=False)
    time.sleep(2)
    ensure_ns(ns)
    apply_nginx(ns)
    seen: set[str] = set()
    events: list[dict] = []
    for _ in range(8):
        events.extend(poll_once(ns, eid, "none", seen))
        time.sleep(1.0)
    sh(["kubectl", "scale", "deployment/kosv-nginx", "-n", ns, "--replicas=3"], check=True)
    wait_deployment(ns, "kosv-nginx")
    for _ in range(8):
        events.extend(poll_once(ns, eid, "none", seen))
        time.sleep(1.0)
    report = check_trace(events, trace_id=eid)
    meta = {"experiment_id": eid, "expected": "PASS", "arm": "baseline"}
    write_run(out, eid, events, report, meta)
    sh(["kubectl", "delete", "namespace", ns, "--wait=false"], check=False)
    ok = report.status == "PASS"
    print(json.dumps({"experiment_id": eid, "status": report.status, "ok": ok}))
    return {"id": eid, "expected": "PASS", "observed": report.status, "ok": ok}


def run_o1(out: Path) -> dict:
    """Seed O1 via observation-layer injection.

    The API server rejects ownerReferences with two controller=true entries
    ("Only one reference can have Controller set to true"). A true dual-controller
    state therefore cannot be installed via kubectl patch on current Kubernetes.
    We capture a live Pod poll, then inject a second controller=true owner into the
    recorded event stream (seeded observation) and require FAIL O1.
    """
    ns = "kosv-seed-o1"
    eid = "SEEDED-O1-DUAL"
    ensure_ns(ns)
    apply_nginx(ns, replicas=1)

    seen: set[str] = set()
    events: list[dict] = []
    for _ in range(5):
        events.extend(poll_once(ns, eid, "seeded-o1-pre", seen))
        time.sleep(1.0)

    pod = get_one_pod(ns)
    live = normalize("pods", pod, eid, "seeded-o1")
    owners = list(live.get("owners") or [])
    if not any(o.get("controller") for o in owners):
        raise SystemExit("live pod missing controller owner")
    fake_uid = "00000000-0000-4000-8000-00000000o1se"
    owners.append(
        {
            "uid": fake_uid,
            "name": "kosv-seeded-rs-fake",
            "controller": True,
            "apiVersion": "apps/v1",
            "kind": "ReplicaSet",
        }
    )
    seeded = dict(live)
    seeded["time"] = utc_now()
    seeded["event"] = "MODIFIED"
    seeded["owners"] = owners
    seeded["fault_state"] = "seeded-o1-observation"
    seeded["resourceVersion"] = str(int(live.get("resourceVersion") or "1") + 1)
    events.append(seeded)

    for _ in range(3):
        events.extend(poll_once(ns, eid, "seeded-o1-post", seen))
        time.sleep(1.0)

    report = check_trace(events, trace_id=eid)
    meta = {
        "experiment_id": eid,
        "expected": "FAIL",
        "expected_oracle": "O1",
        "arm": "seeded-o1-observation-injection",
        "note": "API rejects dual controller=true via kubectl patch; seeded in recorded trace from live pod snapshot",
        "pod": pod["metadata"]["name"],
    }
    write_run(out, eid, events, report, meta)
    sh(["kubectl", "delete", "namespace", ns, "--wait=false"], check=False)
    oracles = {v.oracle for v in report.violations}
    ok = report.status == "FAIL" and "O1" in oracles
    print(json.dumps({"experiment_id": eid, "status": report.status, "ok": ok, "oracles": sorted(oracles)}))
    return {"id": eid, "expected": "FAIL", "observed": report.status, "ok": ok}


def run_o2(out: Path) -> dict:
    """Seed O2 via observation-layer transfer (no orphan between polls).

    Live kubectl transfer patches are raced by the ReplicaSet controller, which
    restores the legitimate ControllerRef before the next poll. We therefore
    establish a live controlling owner in the trace, then inject a MODIFIED
    event that switches controller=true to a different UID without an orphan.
    """
    ns = "kosv-seed-o2"
    eid = "SEEDED-O2-TRANSFER"
    ensure_ns(ns)
    apply_nginx(ns, replicas=1)

    seen: set[str] = set()
    events: list[dict] = []
    for _ in range(5):
        events.extend(poll_once(ns, eid, "seeded-o2-pre", seen))
        time.sleep(1.0)

    pod = get_one_pod(ns)
    live = normalize("pods", pod, eid, "seeded-o2")
    owners = list(live.get("owners") or [])
    ctrl = next((o for o in owners if o.get("controller")), None)
    if not ctrl:
        raise SystemExit("no controller owner on pod")

    fake_uid = "00000000-0000-4000-8000-00000000o2se"
    transferred = dict(live)
    transferred["time"] = utc_now()
    transferred["event"] = "MODIFIED"
    transferred["fault_state"] = "seeded-o2-observation"
    transferred["resourceVersion"] = str(int(live.get("resourceVersion") or "1") + 1)
    transferred["owners"] = [
        {
            "uid": fake_uid,
            "name": "kosv-seeded-rs-transferred",
            "controller": True,
            "apiVersion": "apps/v1",
            "kind": "ReplicaSet",
        }
    ]
    events.append(transferred)

    for _ in range(3):
        events.extend(poll_once(ns, eid, "seeded-o2-post", seen))
        time.sleep(1.0)

    report = check_trace(events, trace_id=eid)
    meta = {
        "experiment_id": eid,
        "expected": "FAIL",
        "expected_oracle": "O2",
        "arm": "seeded-o2-observation-injection",
        "note": "RS controller races live transfer patches; seeded transfer in recorded trace from live pod snapshot",
        "pod": pod["metadata"]["name"],
        "from_uid": ctrl.get("uid"),
        "to_uid": fake_uid,
    }
    write_run(out, eid, events, report, meta)
    sh(["kubectl", "delete", "namespace", ns, "--wait=false"], check=False)
    oracles = {v.oracle for v in report.violations}
    ok = report.status == "FAIL" and "O2" in oracles
    print(json.dumps({"experiment_id": eid, "status": report.status, "ok": ok, "oracles": sorted(oracles)}))
    return {"id": eid, "expected": "FAIL", "observed": report.status, "ok": ok}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=ROOT / "matrix" / "runs")
    args = p.parse_args()
    stamp = datetime.now(timezone.utc).strftime("seeded-%Y%m%dT%H%M%SZ")
    out = args.out / stamp
    out.mkdir(parents=True, exist_ok=True)

    results = [
        run_baseline(out),
        run_o1(out),
        run_o2(out),
    ]
    seeded = [r for r in results if r["id"].startswith("SEEDED-O")]
    summary = {
        "matrix_id": stamp,
        "seeded_violations_detected": f"{sum(1 for r in seeded if r['ok'])}/{len(seeded)}",
        "results": results,
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not all(r["ok"] for r in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
