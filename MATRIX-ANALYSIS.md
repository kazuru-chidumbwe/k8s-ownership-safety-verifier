# Matrix analysis — `20260814T083135Z` (primary, one page)

**Verdict:** 20/20 runs **PASS** O1/O2. No FAIL. No INCONCLUSIVE. Instrument detects synthetic violations (fixtures) and seeded in-cluster violations (2/2). Matrix run on Kind **`kindest/node:v1.34.0`**.

**No findings claims.** This is instrument validity under stated lab faults only.

## Design notes

| Point | Response |
| --- | --- |
| O1 resource-type keying | O1 evaluates **per event**; identity is `resource/namespace/name` + `uid`. No cross-type RV merge. |
| O1 incompleteness | Explicit caveat on every report + below: PASS ≠ proof of absence. |
| Event order | Events sorted by `time` (stable); O1 runs before any ownership-state update; collector dedup is by `(resource,uid,RV)` **after** emit, not inside checker. |
| O2 handoff | Timeline uses prior `last_ctrl`; orphan then adopt is suppression, not FAIL. No Deployment whitelist (not required). |
| Delay measurement | Host `delay_proxy` self-test per run (`proxy-latency.json`); Kind E1/E2 use `tc netem` on `eth0`, which delays **collector↔API** (not API↔controller — local/`lo` delivery). See `docs/THREAT-MODEL.md`. |
| Suppressions | Logged in each `report.json` (`suppressions[]`). |

## Results table

| Exp | Fault | Runs | Status | Events (min–max) | Proxy mean (ms) | Within ±10% target |
| --- | --- | --- | --- | --- | --- | --- |
| E0 | 0ms baseline | 5 | PASS | 18–21 | ~0.9 | yes (target 0) |
| E1 | 500ms delay | 5 | PASS | 9–10 | ~503 | **yes** |
| E2 | 2000ms delay | 5 | PASS | 7–7 | ~2003 | **yes** |
| E3 | clean CM restart (steady state) | 5 | PASS | 15–17 | ~0.9 | yes |

Matrix id: `matrix/runs/20260814T083135Z/` — each run has `trace.jsonl`, `report.json`, `meta.json`, `proxy-latency.json`.

**Historical matrix:** `20260726T210257Z` (Kind v1.31.6) superseded by this primary stamp for paper and README cite.

## Poll-gap signal (collector path)

From `experiments/analyze_poll_gaps.py` on this matrix (`SWEEP_GAP_MS=200`):

| Exp | Poll events (5 runs) | Same-object gap p50 (ms) | Inter-sweep gap p50 (ms) |
| --- | ---: | ---: | ---: |
| E0 | 97 | 1350 | 1135 |
| E1 | 46 | 6236 | 2073 |
| E2 | 35 | 59615 | 8070 |

Indirect evidence that `eth0` netem throttled the host collector path. Not calibrated RTT to 500/2000 ms and not controller↔API delay.

## Proxy delay distribution (self-test through `delay_proxy`)

- E1 (500ms): means ≈ 502.9–503.5 ms; variance ≪ 10%.  
- E2 (2000ms): means ≈ 2003.3–2003.5 ms; variance ≪ 10%.  

## Event completeness note

Under E1/E2, poll yields **fewer** ownership events (cluster slowed by `tc`). That is a **coverage reduction**, not an O1/O2 FAIL. PASS under reduced coverage still does not prove absence of missed dual-owner flashes. E0 retains higher event counts (deployment/replicaset/pod transitions present).

## False-positive / suppression log

Across all 20 matrix runs: **0** O1/O2 violations; **0** continuity INCONCLUSIVE marks. Fixture orphan path still records `orphan_observed` / `intended_orphan_then_adopt` suppressions when exercised offline.

## Scope note

This matrix is an **instrument-validation** artifact for the KOSV checker under stated lab faults. Host `delay_proxy` self-tests in each run remain **tool calibration** (±10% of configured delay). The matrix is not a vulnerability finding report and not a Kubernetes ownership-safety result.
