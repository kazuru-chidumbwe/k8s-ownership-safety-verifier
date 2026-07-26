#!/usr/bin/env python3
"""20-run matrix: E0/E1/E2/E3 × 5.

E0: 0ms baseline
E1: 500ms observation delay (delay_proxy calibrated + tc netem in Kind node)
E2: 2000ms same
E3: controller-manager restart during scale (no delay)

Each run archives trace, verifier report, fault metadata, proxy latency summary.
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

KIND_NODE = "kosv-control-plane"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def sh(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


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


def normalize(resource: str, obj: dict, experiment_id: str, fault_state: str) -> dict:
    md = obj.get("metadata") or {}
    singular = {"deployments": "deployment", "replicasets": "replicaset", "pods": "pod"}.get(
        resource, resource
    )
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
        "fault_state": fault_state,
    }


def poll_once(namespace: str, experiment_id: str, fault_state: str, seen: set[str]) -> list[dict]:
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
            events.append(normalize(resource, obj, experiment_id, fault_state))
    return events


def wait_deployment(namespace: str, name: str, timeout: float = 180.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        cp = sh(
            ["kubectl", "rollout", "status", f"deployment/{name}", "-n", namespace, "--timeout=15s"],
            check=False,
        )
        if cp.returncode == 0:
            return True
        time.sleep(2)
    return False


def apply_tc_delay(delay_ms: int) -> None:
    # Kind control-plane observation-path approximation (in-cluster API path).
    if delay_ms <= 0:
        clear_tc_delay()
        return
    sh(
        [
            "docker",
            "exec",
            KIND_NODE,
            "bash",
            "-lc",
            f"tc qdisc replace dev eth0 root netem delay {delay_ms}ms",
        ],
        check=False,
    )


def clear_tc_delay() -> None:
    sh(
        ["docker", "exec", KIND_NODE, "bash", "-lc", "tc qdisc del dev eth0 root 2>/dev/null || true"],
        check=False,
    )


def restart_controller_manager() -> dict:
    t0 = utc_now()
    # Static pod: kill process; kubelet restarts it.
    cp = sh(
        [
            "docker",
            "exec",
            KIND_NODE,
            "bash",
            "-lc",
            "pidof kube-controller-manager | xargs -r kill -TERM; sleep 2; pidof kube-controller-manager || true",
        ],
        check=False,
    )
    t1 = utc_now()
    return {
        "fault": "controller_restart",
        "start": t0,
        "end": t1,
        "stdout": (cp.stdout or "")[-500:],
        "returncode": cp.returncode,
    }


def calibrate_proxy(delay_ms: int, out: Path) -> dict:
    cp = sh(
        [
            sys.executable,
            str(ROOT / "injector" / "measure_proxy_latency.py"),
            "--self-test",
            "--delay-ms",
            str(delay_ms),
            "--n",
            "30",
            "-o",
            str(out),
        ],
        check=False,
    )
    if out.exists():
        return json.loads(out.read_text(encoding="utf-8"))
    return {"error": cp.stderr or cp.stdout, "returncode": cp.returncode}


def run_one(
    experiment: str,
    run_idx: int,
    delay_ms: int,
    do_restart: bool,
    out_dir: Path,
    poll_seconds: float,
) -> dict:
    experiment_id = f"{experiment}-r{run_idx:02d}"
    run_dir = out_dir / experiment_id
    run_dir.mkdir(parents=True, exist_ok=True)
    ns = f"kosv-{experiment.lower()}-r{run_idx:02d}"
    name = "kosv-nginx"
    fault_state = f"delay_{delay_ms}ms" if delay_ms else "none"
    if do_restart:
        fault_state = "controller_restart"

    meta: dict = {
        "experiment_id": experiment_id,
        "experiment": experiment,
        "run": run_idx,
        "delay_ms_configured": delay_ms,
        "controller_restart": do_restart,
        "started": utc_now(),
        "namespace": ns,
    }

    # Proxy calibration (always for E0–E2; E3 records zero-delay proxy sanity)
    cal_path = run_dir / "proxy-latency.json"
    meta["proxy_latency"] = calibrate_proxy(delay_ms if experiment != "E3" else 0, cal_path)

    sh(["kubectl", "delete", "namespace", ns, "--wait=false"], check=False)
    time.sleep(1)
    sh(["kubectl", "create", "namespace", ns], check=False)

    apply_tc_delay(delay_ms if experiment in ("E1", "E2") else 0)
    fault_window: dict = {"configured_delay_ms": delay_ms, "tc_applied": experiment in ("E1", "E2")}

    manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {ns}
  labels:
    app: kosv-matrix
spec:
  replicas: 2
  selector:
    matchLabels:
      app: kosv-matrix
  template:
    metadata:
      labels:
        app: kosv-matrix
    spec:
      containers:
      - name: nginx
        image: nginx:1.27-alpine
        ports:
        - containerPort: 80
"""
    subprocess.run(["kubectl", "apply", "-f", "-"], input=manifest, text=True, check=True)

    seen: set[str] = set()
    events: list[dict] = []
    t0 = time.time()
    while time.time() - t0 < poll_seconds / 2:
        events.extend(poll_once(ns, experiment_id, fault_state, seen))
        time.sleep(1.0)

    ready1 = wait_deployment(ns, name)
    events.extend(poll_once(ns, experiment_id, fault_state, seen))

    if do_restart:
        fault_window["restart"] = restart_controller_manager()
        time.sleep(3)

    sh(["kubectl", "-n", ns, "scale", f"deployment/{name}", "--replicas=3"], check=True)
    t1 = time.time()
    while time.time() - t1 < poll_seconds / 2:
        events.extend(poll_once(ns, experiment_id, fault_state, seen))
        time.sleep(1.0)
    ready2 = wait_deployment(ns, name)
    events.extend(poll_once(ns, experiment_id, fault_state, seen))

    clear_tc_delay()
    fault_window["ended"] = utc_now()
    fault_window["deployment_ready_pre_scale"] = ready1
    fault_window["deployment_ready_post_scale"] = ready2

    trace_path = run_dir / "trace.jsonl"
    with trace_path.open("w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev, separators=(",", ":")) + "\n")

    report = check_trace(events, trace_id=experiment_id)
    report_path = run_dir / "report.json"
    report_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")

    meta["ended"] = utc_now()
    meta["fault_window"] = fault_window
    meta["events"] = len(events)
    meta["status"] = report.status
    meta["violations"] = len(report.violations)
    meta["suppressions"] = len(report.suppressions)
    meta["resource_counts"] = report.resource_counts
    meta["event_type_counts"] = report.event_type_counts
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    # cleanup ns to save cluster load
    sh(["kubectl", "delete", "namespace", ns, "--wait=false"], check=False)
    print(json.dumps({"experiment_id": experiment_id, "status": report.status, "events": len(events)}))
    return meta


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=ROOT / "matrix" / "runs")
    p.add_argument("--poll-seconds", type=float, default=30.0)
    p.add_argument("--only", default="", help="Comma experiments e.g. E0,E1")
    args = p.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = args.out / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    plan = [
        ("E0", 0, False, 5),
        ("E1", 500, False, 5),
        ("E2", 2000, False, 5),
        ("E3", 0, True, 5),
    ]
    if args.only:
        want = {x.strip().upper() for x in args.only.split(",") if x.strip()}
        plan = [row for row in plan if row[0] in want]

    results = []
    for experiment, delay, restart, n in plan:
        for i in range(1, n + 1):
            results.append(run_one(experiment, i, delay, restart, out_dir, args.poll_seconds))

    summary = {
        "matrix_id": stamp,
        "runs": len(results),
        "by_status": {},
        "by_experiment": {},
        "results": results,
    }
    for r in results:
        summary["by_status"][r["status"]] = summary["by_status"].get(r["status"], 0) + 1
        summary["by_experiment"].setdefault(r["experiment"], []).append(
            {"id": r["experiment_id"], "status": r["status"], "events": r["events"]}
        )

    (out_dir / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"matrix_id": stamp, "by_status": summary["by_status"]}, indent=2))
    # Gate: no unexpected FAIL
    fails = [r for r in results if r["status"] == "FAIL"]
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
