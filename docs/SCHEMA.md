# Trace schema (KOSV v0)

Normalized ownership events are newline-delimited JSON (**JSONL**). One object per line. The verifier (`verifier/check.py`) consumes this schema only.

## Event object

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `time` | string (ISO-8601 UTC) | yes | Observation time |
| `resource` | string | yes | Singular resource type: `deployment`, `replicaset`, `pod`, … |
| `namespace` | string | yes | Kubernetes namespace |
| `name` | string | yes | Object name |
| `uid` | string | yes | Kubernetes object UID (identity for O1/O2) |
| `resourceVersion` | string | yes | API `resourceVersion` at observation |
| `event` | string | yes | `ADDED` · `MODIFIED` · `DELETED` · `UPDATE` (poll) |
| `owners` | array of owner objects | yes | Normalized `ownerReferences` (may be empty) |
| `source` | string | yes | `poll` · `watch` · `fixture` |
| `experiment_id` | string | yes | Stable experiment / run id (e.g. `E0-r01`, `SMOKE-O1`) |
| `fault_state` | string | yes | Fault label at observation (e.g. `none`, `delay_500ms`, `delay_500ms+restart`) |

### Owner object

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `uid` | string | yes | Owner UID when known |
| `name` | string | yes | Owner name |
| `controller` | boolean | yes | `ownerReferences[].controller` |
| `apiVersion` | string | recommended | Owner API version |
| `kind` | string | recommended | Owner kind |

## Example

```json
{"time":"2026-07-26T21:02:57.123Z","resource":"pod","namespace":"kosv-demo","name":"kosv-nginx-x","uid":"…","resourceVersion":"12345","event":"UPDATE","owners":[{"uid":"…","name":"kosv-nginx-y","controller":true,"apiVersion":"apps/v1","kind":"ReplicaSet"}],"source":"poll","experiment_id":"E0-r01","fault_state":"none"}
```

## Object identity

Oracles key objects by **`(resource, uid)`**, not by name alone.

## Experiment metadata (alongside traces)

Per-run archive directories typically include:

| File | Role |
| --- | --- |
| `trace.jsonl` | Normalized events |
| `report.json` | Verifier output (`status`, `violations`, `suppressions`, `caveats`) |
| `meta.json` | Experiment parameters (delay, restart, Kind version, poll interval, …) |

Matrix calibration also records delay calibration summaries for `tc netem` targets (filenames may historically say `proxy-latency*.json`; the **in-cluster fault** for Kind matrix runs is **`tc netem`**).

## Report status

| Status | Meaning |
| --- | --- |
| `PASS` | No O1/O2 violation in the recorded trace |
| `FAIL` | ≥1 O1 or O2 violation |
| `INCONCLUSIVE` | Collector gap / continuity issue without O1/O2 FAIL |

`PASS` does **not** prove absence of short-lived dual-owner states shorter than the poll interval.
