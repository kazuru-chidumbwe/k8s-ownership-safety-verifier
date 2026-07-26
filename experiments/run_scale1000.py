#!/usr/bin/env python3
"""KOSV scale-1000 campaign (pre-registered design in PRE-ANALYSIS-PLAN.md).

10 cells: delay in {0,100,500,1000,2000} x restart in {no,yes}, 100 reps each.
Fast poll, proxy calibrated once per delay level, checkpoint SUMMARY every run.
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
DELAYS = [0, 100, 500, 1000, 2000]
REPS = 100


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def sh(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
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
        cp = sh(["kubectl", "get", resource, "-n", namespace, "-o", "json"])
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


def wait_ready(namespace: str, name: str, timeout: float = 90.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        cp = sh(
            ["kubectl", "rollout", "status", f"deployment/{name}", "-n", namespace, "--timeout=10s"]
        )
        if cp.returncode == 0:
            return True
        time.sleep(1)
    return False


def apply_tc(delay_ms: int) -> None:
    if delay_ms <= 0:
        sh(["docker", "exec", KIND_NODE, "bash", "-lc", "tc qdisc del dev eth0 root 2>/dev/null || true"])
        return
    sh(
        [
            "docker",
            "exec",
            KIND_NODE,
            "bash",
            "-lc",
            f"tc qdisc replace dev eth0 root netem delay {delay_ms}ms",
        ]
    )


def restart_cm() -> dict:
    t0 = utc_now()
    cp = sh(
        [
            "docker",
            "exec",
            KIND_NODE,
            "bash",
            "-lc",
            "pidof kube-controller-manager | xargs -r kill -TERM; sleep 1; pidof kube-controller-manager || true",
        ]
    )
    return {"start": t0, "end": utc_now(), "rc": cp.returncode, "out": (cp.stdout or "")[-200:]}


def calibrate_proxy(delay_ms: int, out: Path) -> dict:
    if out.exists():
        return json.loads(out.read_text(encoding="utf-8"))
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
        ]
    )
    if out.exists():
        return json.loads(out.read_text(encoding="utf-8"))
    return {"error": (cp.stderr or cp.stdout or "")[-300:], "rc": cp.returncode}


def cell_id(delay_ms: int, restart: bool) -> str:
    return f"D{delay_ms}-R{'Y' if restart else 'N'}"


def run_one(
    out_dir: Path,
    delay_ms: int,
    restart: bool,
    rep: int,
    poll_seconds: float,
    proxy_cache: dict[int, dict],
) -> dict:
    cid = cell_id(delay_ms, restart)
    experiment_id = f"{cid}-r{rep:03d}"
    run_dir = out_dir / experiment_id
    if (run_dir / "meta.json").exists():
        return json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))

    run_dir.mkdir(parents=True, exist_ok=True)
    ns = f"k{delay_ms}{'r' if restart else 'n'}{rep:03d}"[:63]
    name = "kosv-nginx"
    fault_state = f"delay_{delay_ms}ms" + ("+restart" if restart else "")

    meta: dict = {
        "experiment_id": experiment_id,
        "cell": cid,
        "delay_ms": delay_ms,
        "restart": restart,
        "rep": rep,
        "started": utc_now(),
        "namespace": ns,
        "proxy_latency": proxy_cache[delay_ms],
    }

    sh(["kubectl", "delete", "namespace", ns, "--wait=false", "--ignore-not-found=true"])
    time.sleep(0.3)
    sh(["kubectl", "create", "namespace", ns], check=True)

    apply_tc(delay_ms)
    manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {ns}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: kosv
  template:
    metadata:
      labels:
        app: kosv
    spec:
      containers:
      - name: nginx
        image: nginx:1.27-alpine
"""
    subprocess.run(["kubectl", "apply", "-f", "-"], input=manifest, text=True, check=True)

    seen: set[str] = set()
    events: list[dict] = []
    t0 = time.time()
    while time.time() - t0 < poll_seconds / 2:
        events.extend(poll_once(ns, experiment_id, fault_state, seen))
        time.sleep(0.7)

    ready1 = wait_ready(ns, name, timeout=60 if delay_ms < 1000 else 120)
    events.extend(poll_once(ns, experiment_id, fault_state, seen))

    restart_meta = None
    if restart:
        restart_meta = restart_cm()
        time.sleep(1.5)

    sh(["kubectl", "-n", ns, "scale", f"deployment/{name}", "--replicas=3"], check=True)
    t1 = time.time()
    while time.time() - t1 < poll_seconds / 2:
        events.extend(poll_once(ns, experiment_id, fault_state, seen))
        time.sleep(0.7)
    ready2 = wait_ready(ns, name, timeout=60 if delay_ms < 1000 else 120)
    events.extend(poll_once(ns, experiment_id, fault_state, seen))

    apply_tc(0)

    trace_path = run_dir / "trace.jsonl"
    with trace_path.open("w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev, separators=(",", ":")) + "\n")

    report = check_trace(events, trace_id=experiment_id)
    (run_dir / "report.json").write_text(
        json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8"
    )

    meta.update(
        {
            "ended": utc_now(),
            "events": len(events),
            "status": report.status,
            "violations": len(report.violations),
            "suppressions": len(report.suppressions),
            "resource_counts": report.resource_counts,
            "ready_pre": ready1,
            "ready_post": ready2,
            "restart_meta": restart_meta,
        }
    )
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    sh(["kubectl", "delete", "namespace", ns, "--wait=false", "--ignore-not-found=true"])
    print(
        json.dumps(
            {
                "id": experiment_id,
                "status": report.status,
                "events": len(events),
                "t": utc_now(),
            }
        ),
        flush=True,
    )
    return meta


def write_summary(out_dir: Path, results: list[dict]) -> None:
    by_status: dict[str, int] = {}
    by_cell: dict[str, dict] = {}
    for r in results:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        cell = r["cell"]
        slot = by_cell.setdefault(cell, {"n": 0, "PASS": 0, "FAIL": 0, "INCONCLUSIVE": 0, "events_sum": 0})
        slot["n"] += 1
        slot[r["status"]] = slot.get(r["status"], 0) + 1
        slot["events_sum"] += r.get("events", 0)
    summary = {
        "campaign": "scale-1000",
        "pre_analysis_plan": "PRE-ANALYSIS-PLAN.md",
        "completed": len(results),
        "by_status": by_status,
        "by_cell": by_cell,
        "updated": utc_now(),
    }
    (out_dir / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--poll-seconds", type=float, default=14.0)
    p.add_argument("--reps", type=int, default=REPS)
    p.add_argument("--delays", default="0,100,500,1000,2000")
    args = p.parse_args()

    delays = [int(x) for x in args.delays.split(",") if x.strip()]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = args.out or (ROOT / "matrix" / "scale1000" / stamp)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "PLAN_REF.txt").write_text(
        "PRE-ANALYSIS-PLAN.md locked before campaign\n", encoding="utf-8"
    )

    proxy_cache: dict[int, dict] = {}
    for d in delays:
        cal = out_dir / f"proxy-latency-D{d}.json"
        print(f"calibrating proxy delay={d}ms", flush=True)
        proxy_cache[d] = calibrate_proxy(d, cal)
        print(json.dumps({"delay": d, "mean_ms": proxy_cache[d].get("mean_ms")}), flush=True)

    results: list[dict] = []
    # resume: load existing metas
    for meta_path in sorted(out_dir.glob("*/meta.json")):
        results.append(json.loads(meta_path.read_text(encoding="utf-8")))
    done_ids = {r["experiment_id"] for r in results}
    print(f"resuming with {len(done_ids)} completed", flush=True)

    total = len(delays) * 2 * args.reps
    for delay_ms in delays:
        for restart in (False, True):
            for rep in range(1, args.reps + 1):
                eid = f"{cell_id(delay_ms, restart)}-r{rep:03d}"
                if eid in done_ids:
                    continue
                meta = run_one(out_dir, delay_ms, restart, rep, args.poll_seconds, proxy_cache)
                results.append(meta)
                done_ids.add(eid)
                write_summary(out_dir, results)
                if len(results) % 25 == 0:
                    print(f"progress {len(results)}/{total}", flush=True)

    write_summary(out_dir, results)
    print(json.dumps({"done": len(results), "target": total}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
