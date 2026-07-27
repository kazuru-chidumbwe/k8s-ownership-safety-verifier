# Architecture (KOSV v0)

KOSV is a **research instrument** for measuring Kubernetes ownership safety. It is not an operator control plane.

## Component diagram

```text
┌────────────────────┐     ┌─────────────────────┐
│ Workload Generator │     │   Fault Injector    │
│ (Deployment create │     │  • tc netem delay   │
│  / scale scripts)  │     │  • controller-mgr   │
└─────────┬──────────┘     │    restart          │
          │                └──────────┬──────────┘
          ▼                           │
   ┌──────────────────────────────────┴──────────┐
   │         Kind laboratory cluster (v1.31.x)   │
   └──────────────────────┬──────────────────────┘
                          │ ownerReferences
                          ▼
                 ┌─────────────────┐
                 │ Trace Collector │  (kubectl poll / watch)
                 └────────┬────────┘
                          ▼
                 ┌─────────────────┐
                 │ Event Normalizer│  → JSONL (docs/SCHEMA.md)
                 └────────┬────────┘
                          ▼
                 ┌─────────────────┐
                 │    Verifier     │  O1 / O2 (O3/O4 extension points)
                 └────────┬────────┘
                          ▼
                      report JSON

   Synthetic fixtures ──────────────────────────► Verifier (smoke)
```

## Roles

| Component | Responsibility |
| --- | --- |
| **Workload generator** | Creates/scales Deployment→ReplicaSet→Pod workloads with stable `experiment_id`s |
| **Fault injector** | Applies reproducible **collector-to-API** delay (`tc netem` on Kind node `eth0`) and/or restarts `kube-controller-manager` |
| **Trace collector** | Observes API objects and `ownerReferences` |
| **Event normalizer** | Emits schema-stable JSONL events |
| **Verifier** | Evaluates O1/O2; reserved hooks for O3/O4 when belief-state traces exist |

## Fault injection notes

An earlier prototype considered a transparent TCP **proxy** between controller-manager and the API server. In Kind, `kube-controller-manager` runs as a **static control-plane pod**, so transparent interception requires control-plane surgery. v0 instead applies **Linux `tc netem` on `eth0`**, preserving a stock Kind topology.

**Scope lock:** on single-node Kind, controller-manager→API is local (`lo` delivery to the node’s own IP). `eth0` netem therefore delays the **external collector (`kubectl`) ↔ API** path, not API↔controller informer traffic. That matches KOSV’s poll-based architecture; see [THREAT-MODEL.md](THREAT-MODEL.md) and [SCOPE-ISOLATION.md](SCOPE-ISOLATION.md). True controller↔API delay is deferred (`lo` netem / interception).

Optional host-side `injector/delay_proxy.py` remains for calibration self-tests; it is **not** the Kind matrix collector-delay fault.

## Determinism and replay

- Every event carries `experiment_id` and `fault_state`.
- Runs archive `trace.jsonl` + `report.json` + `meta.json` under a stamp directory.
- Synthetic fixtures in `fixtures/` replay known PASS/FAIL cases without a cluster.
- Cite a **git tag**, not `main`, when reproducing published artifacts.

## Oracle extension points

| Oracle | Status | Needs |
| --- | --- | --- |
| O1 Snapshot SCOI (Single Controller Ownership Invariant) | Implemented | API/trace events |
| O2 Unintended transfer | Implemented | API/trace events + intended-transfer rules |
| O3 Observation mismatch | **Defined, not implemented** | Controller belief/informer view at reconcile time |
| O4 Behavioral thrash | **Defined, not implemented** | Thresholded adopt/orphan / recreate patterns + belief or dense traces |

See [`EXTENDING.md`](EXTENDING.md).
