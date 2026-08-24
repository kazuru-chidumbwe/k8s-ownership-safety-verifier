#!/usr/bin/env python3
"""Instrument-validation matrix: E0/E1/E2/E3 × N runs (default N=5; use --runs for 40-pack).

E0: 0ms baseline
E1: 500ms collector-to-API delay (delay_proxy self-test + tc netem on Kind eth0)
E2: 2000ms same
E3: controller-manager restart during scale (no delay)

Each run archives trace, verifier report, fault metadata, proxy latency summary.
Supports --path deployment|statefulset.
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
sys.path.insert(0, str(ROOT / "experiments"))
from verifier.check import check_trace  # noqa: E402
from cluster_env import KIND_NODE, capture_cluster_env  # noqa: E402
from workload_paths import WorkloadPath, get_path  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def sh(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def sh_retry(
    cmd: list[str],
    *,
    attempts: int = 5,
    sleep_s: float = 3.0,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Retry kubectl under collector-path netem (transient API/timeout failures)."""
    last: subprocess.CompletedProcess[str] | None = None
    for i in range(1, attempts + 1):
        last = sh(cmd, check=False)
        if last.returncode == 0:
            return last
        err = (last.stderr or last.stdout or "").strip()
        print(f"! attempt {i}/{attempts} failed rc={last.returncode}: {err[-400:]}", flush=True)
        if i < attempts:
            time.sleep(sleep_s * i)
    if check and last is not None and last.returncode != 0:
        raise subprocess.CalledProcessError(
            last.returncode, cmd, output=last.stdout, stderr=last.stderr
        )
    assert last is not None
    return last


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


def normalize(
    resource: str, obj: dict, experiment_id: str, fault_state: str, path: WorkloadPath
) -> dict:
    md = obj.get("metadata") or {}
    singular = path.singular_map.get(resource, resource)
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


def poll_once(
    namespace: str,
    experiment_id: str,
    fault_state: str,
    seen: set[str],
    path: WorkloadPath,
) -> list[dict]:
    events: list[dict] = []
    for resource in path.poll_resources:
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
            events.append(normalize(resource, obj, experiment_id, fault_state, path))
    return events


def wait_rollout(namespace: str, name: str, path: WorkloadPath, timeout: float = 300.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        cp = sh(
            [
                "kubectl",
                "rollout",
                "status",
                f"{path.rollout_kind}/{name}",
                "-n",
                namespace,
                "--timeout=20s",
            ],
            check=False,
        )
        if cp.returncode == 0:
            return True
        time.sleep(2)
    return False


def workload_manifest(path: WorkloadPath, ns: str, name: str) -> str:
    if path.name == "deployment":
        return f"""apiVersion: apps/v1
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
    if path.name == "statefulset":
        return f"""apiVersion: v1
kind: Service
metadata:
  name: {name}
  namespace: {ns}
spec:
  clusterIP: None
  selector:
    app: kosv-matrix
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {name}
  namespace: {ns}
  labels:
    app: kosv-matrix
spec:
  serviceName: {name}
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
    raise ValueError(f"no manifest for path {path.name}")


def apply_tc_delay(delay_ms: int) -> None:
    # Collector-to-API delay on single-node Kind: eth0 netem shapes host/kubectl
    # traffic. Controller-manager→API is local (own eth0 IP via lo) and is NOT
    # delayed by this qdisc. See docs/THREAT-MODEL.md.
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
    poll_interval: float = 1.0,
    cluster: dict | None = None,
    path: WorkloadPath | None = None,
) -> dict:
    path = path or get_path("deployment")
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
        "poll_interval_s": poll_interval,
        "poll_seconds": poll_seconds,
        "started": utc_now(),
        "namespace": ns,
        "ownership_path": path.name,
    }
    if cluster:
        meta["kind_node_image"] = cluster.get("kind_node_image")
        meta["kubelet_version"] = cluster.get("kubelet_version")
        meta["cluster"] = cluster

    cal_path = run_dir / "proxy-latency.json"
    meta["proxy_latency"] = calibrate_proxy(delay_ms if experiment != "E3" else 0, cal_path)

    sh(["kubectl", "delete", "namespace", ns, "--wait=false"], check=False)
    time.sleep(1)
    sh(["kubectl", "create", "namespace", ns], check=False)

    apply_tc_delay(delay_ms if experiment in ("E1", "E2") else 0)
    fault_window: dict = {"configured_delay_ms": delay_ms, "tc_applied": experiment in ("E1", "E2")}

    manifest = workload_manifest(path, ns, name)
    apply = subprocess.run(
        ["kubectl", "apply", "-f", "-"],
        input=manifest,
        text=True,
        capture_output=True,
        check=False,
    )
    if apply.returncode != 0:
        time.sleep(3)
        apply = subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=manifest,
            text=True,
            capture_output=True,
            check=True,
        )
    print((apply.stdout or "").strip() or (apply.stderr or "").strip(), flush=True)

    seen: set[str] = set()
    events: list[dict] = []
    t0 = time.time()
    while time.time() - t0 < poll_seconds / 2:
        events.extend(poll_once(ns, experiment_id, fault_state, seen, path))
        time.sleep(poll_interval)

    ready_timeout = 420.0 if delay_ms >= 500 else 300.0
    ready1 = wait_rollout(ns, name, path, timeout=ready_timeout)
    events.extend(poll_once(ns, experiment_id, fault_state, seen, path))

    if do_restart:
        fault_window["restart"] = restart_controller_manager()
        time.sleep(3)

    sh_retry(
        ["kubectl", "-n", ns, "scale", f"{path.rollout_kind}/{name}", "--replicas=3"],
        attempts=6,
        sleep_s=4.0,
        check=True,
    )
    t1 = time.time()
    while time.time() - t1 < poll_seconds / 2:
        events.extend(poll_once(ns, experiment_id, fault_state, seen, path))
        time.sleep(poll_interval)
    ready2 = wait_rollout(ns, name, path, timeout=ready_timeout)
    events.extend(poll_once(ns, experiment_id, fault_state, seen, path))

    clear_tc_delay()
    fault_window["ended"] = utc_now()
    fault_window["rollout_ready_pre_scale"] = ready1
    fault_window["rollout_ready_post_scale"] = ready2

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

    sh(["kubectl", "delete", "namespace", ns, "--wait=false"], check=False)
    print(json.dumps({"experiment_id": experiment_id, "status": report.status, "events": len(events)}))
    return meta


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=ROOT / "matrix" / "runs")
    p.add_argument("--poll-seconds", type=float, default=30.0)
    p.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="Sleep seconds between poll sweeps (default 1.0; use 0.2 for denser sensitivity)",
    )
    p.add_argument("--only", default="", help="Comma experiments e.g. E0,E1")
    p.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Runs per experiment cell (default 5 → 20 total; use 10 → 40 total)",
    )
    p.add_argument(
        "--path",
        default="deployment",
        choices=sorted({"deployment", "statefulset"}),
        help="Ownership path under test (default deployment)",
    )
    args = p.parse_args()
    path = get_path(args.path)

    if args.runs < 1:
        raise SystemExit("--runs must be >= 1")
    if args.poll_interval <= 0:
        raise SystemExit("--poll-interval must be > 0")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = args.out / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    cluster = capture_cluster_env()
    (out_dir / "cluster.json").write_text(json.dumps(cluster, indent=2) + "\n", encoding="utf-8")

    n = args.runs
    plan = [
        ("E0", 0, False, n),
        ("E1", 500, False, n),
        ("E2", 2000, False, n),
        ("E3", 0, True, n),
    ]
    if args.only:
        want = {x.strip().upper() for x in args.only.split(",") if x.strip()}
        plan = [row for row in plan if row[0] in want]

    results = []
    for experiment, delay, restart, n_runs in plan:
        for i in range(1, n_runs + 1):
            results.append(
                run_one(
                    experiment,
                    i,
                    delay,
                    restart,
                    out_dir,
                    args.poll_seconds,
                    poll_interval=args.poll_interval,
                    cluster=cluster,
                    path=path,
                )
            )

    summary = {
        "matrix_id": stamp,
        "ownership_path": path.name,
        "kind_node_image": cluster.get("kind_node_image"),
        "kubelet_version": cluster.get("kubelet_version"),
        "cluster": cluster,
        "poll_interval_s": args.poll_interval,
        "poll_seconds": args.poll_seconds,
        "runs": len(results),
        "runs_per_cell": n,
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
    fails = [r for r in results if r["status"] == "FAIL"]
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
