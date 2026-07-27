# Matrix analysis — `20260726T210257Z` (one page)

**Verdict:** 20/20 runs **PASS** O1/O2. No FAIL. No INCONCLUSIVE. Instrument detects synthetic violations (fixtures) and does not fire on E0–E3 benign Deployment create/scale under Kind v1.31.6.

**No findings claims.** This is instrument validity under fault load only.

## Design notes

| Point | Response |
| --- | --- |
| O1 resource-type keying | O1 evaluates **per event**; identity is `resource/namespace/name` + `uid`. No cross-type RV merge. |
| O1 incompleteness | Explicit caveat on every report + below: PASS ≠ proof of absence. |
| Event order | Events sorted by `time` (stable); O1 runs before any ownership-state update; collector dedup is by `(resource,uid,RV)` **after** emit, not inside checker. |
| O2 handoff | Timeline uses prior `last_ctrl`; orphan then adopt is suppression, not FAIL. No Deployment whitelist (not required). |
| Delay measurement | `delay_proxy` calibrated per run (`proxy-latency.json`); Kind in-cluster path uses matching `tc netem` (proxy cannot sit between static-pod controller-manager and apiserver without control-plane surgery). |
| Suppressions | Logged in each `report.json` (`suppressions[]`). |

## Results table

| Exp | Fault | Runs | Status | Events (min–max) | Proxy mean (ms) | Within ±10% target |
| --- | --- | --- | --- | --- | --- | --- |
| E0 | 0ms baseline | 5 | PASS | 14–16 | ~1.8 | yes (target 0) |
| E1 | 500ms delay | 5 | PASS | 7–8 | ~503.3 | **yes** |
| E2 | 2000ms delay | 5 | PASS | 7–7 | ~2003.4 | **yes** |
| E3 | controller-manager restart | 5 | PASS | 12–12 | ~1.8 | yes |

Matrix id: `matrix/runs/20260726T210257Z/` — each run has `trace.jsonl`, `report.json`, `meta.json`, `proxy-latency.json`.

## Proxy delay distribution (self-test through `delay_proxy`)

- E1 (500ms): means ≈ 502.9–503.5 ms; variance ≪ 10%.  
- E2 (2000ms): means ≈ 2003.3–2003.5 ms; variance ≪ 10%.  

## Event completeness note

Under E1/E2, poll yields **fewer** ownership events (cluster slowed by `tc`). That is a **coverage reduction**, not an O1/O2 FAIL. PASS under reduced coverage still does not prove absence of missed dual-owner flashes. E0 retains higher event counts (deployment/replicaset/pod transitions present).

## False-positive / suppression log

Across all 20 matrix runs: **0** O1/O2 violations; **0** continuity INCONCLUSIVE marks. Fixture orphan path still records `orphan_observed` / `intended_orphan_then_adopt` suppressions when exercised offline.

## Scope note

This matrix is a calibration artifact for the KOSV instrument. It is not a vulnerability finding report.
