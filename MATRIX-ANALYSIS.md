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

**Environment pin (primary matrix):** Kind `kindest/node:v1.34.0` (kubelet `v1.34.0`; Lab RepoDigest `kindest/node@sha256:7416a61b42b1662ca6ca89f02028ac133a309a2a30ba309614e8ec94d976dc5a`); matrix id `20260814T083135Z`. Cite tag **`v0.1.10`** (commit `89412b4`). Self-describing archive fields: `matrix/runs/20260814T083135Z/cluster.json`, `SUMMARY.json` keys `kind_node_image` / `kubelet_version`, and each run `meta.json`.

```bash
python experiments/analyze_poll_gaps.py matrix/runs/20260814T083135Z --levels E0,E1,E2
```

**Historical matrix:** `20260726T210257Z` (Kind v1.31.6) superseded by this primary stamp for paper and README cite.

**Seeded live-trace arms:** `matrix/runs/seeded-20260814T055833Z/` (2/2 detection; observation-layer).

**Denser-poll sensitivity check:** `20260815T023902Z` (Lab Test; Kind v1.34.0; `--poll-interval 0.2`; E0/E1 × 3; 6/6 PASS) — see section below. Not a replacement for the twenty-run primary matrix.

## Poll-gap signal (collector path)

From `experiments/analyze_poll_gaps.py` on this matrix (`SWEEP_GAP_MS=200`):

| Exp | Poll events (5 runs) | Same-object gap p50 (ms) | Inter-sweep gap p50 (ms) |
| --- | ---: | ---: | ---: |
| E0 | 97 | 1350 | 1135 |
| E1 | 46 | 6236 | 2073 |
| E2 | 35 | 59615 | 8070 |

Indirect evidence that `eth0` netem throttled the host collector path. Not calibrated RTT to 500/2000 ms and not controller↔API delay.

## Denser-poll sensitivity (`20260815T023902Z`)

Supplementary Lab Test arm: Kind `kindest/node:v1.34.0`; configured sleep **0.2 s**; `--poll-seconds 30`; E0 and E1 only; **3 runs/cell**; **6/6 PASS** (0 O1, 0 O2, 0 INCONCLUSIVE). Archive: `matrix/runs/20260815T023902Z/` (`SUMMARY.json` records `poll_interval_s: 0.2`). Gap JSON: [`results/dense-poll-gaps-20260815T023902Z.json`](results/dense-poll-gaps-20260815T023902Z.json). Recompute:

```bash
python experiments/analyze_poll_gaps.py matrix/runs/20260815T023902Z --levels E0,E1
```

| Stamp | Exp | Configured sleep | Poll events | Same-object p50 (ms) | Inter-sweep p50 (ms) ≈ \(T_{\text{eff}}\) |
| --- | --- | ---: | ---: | ---: | ---: |
| Primary `20260814T083135Z` | E0 | 1.0 s | 97 (5 runs) | 1350 | 1135 |
| Dense `20260815T023902Z` | E0 | 0.2 s | 53 (3 runs) | 2444 | **357** |
| Primary | E1 | 1.0 s | 46 (5 runs) | 6236 | 2073 |
| Dense | E1 | 0.2 s | 30 (3 runs) | 5715 | 1860 |

E0 inter-sweep p50 falls 1135 → 357 ms. Under E1 eth0 netem, inter-sweep remains kubectl-runtime dominated (1860 vs 2073 ms).

### Detection probability vs transient duration (\(d / T_{\text{eff}}\))

Model used in the paper: when a dual-owner flash lasts duration \(d\) and the effective sampling period is the observed inter-sweep p50 \(T_{\text{eff}}\), detection probability is approximately \(\min(1, d/T_{\text{eff}})\) for \(d > 0\) (uniform phase; single-sample capture). Values below use **E0** \(T_{\text{eff}}\) from the table above.

| Flash duration \(d\) (ms) | \(P\) @ 1.0 s sleep (\(T_{\text{eff}}=1135\)) | \(P\) @ 0.2 s sleep (\(T_{\text{eff}}=357\)) |
| ---: | ---: | ---: |
| 100 | 0.09 | 0.28 |
| 200 | 0.18 | 0.56 |
| 357 | 0.31 | 1.00 |
| 500 | 0.44 | 1.00 |
| 1000 | 0.88 | 1.00 |
| 1135 | 1.00 | 1.00 |

This is a **bound from measured gaps**, not an injected short-lived dual-owner campaign. Sub-\(T_{\text{eff}}\) flashes can still be missed.

## Proxy delay distribution (self-test through `delay_proxy`)

- E1 (500ms): means ≈ 502.9–503.5 ms; variance ≪ 10%.  
- E2 (2000ms): means ≈ 2003.3–2003.5 ms; variance ≪ 10%.  

## Event completeness note

Under E1/E2, poll yields **fewer** ownership events (cluster slowed by `tc`). That is a **coverage reduction**, not an O1/O2 FAIL. PASS under reduced coverage still does not prove absence of missed dual-owner flashes. E0 retains higher event counts (deployment/replicaset/pod transitions present).

## False-positive / suppression log

Across all 20 matrix runs: **0** O1/O2 violations; **0** continuity INCONCLUSIVE marks. Fixture orphan path still records `orphan_observed` / `intended_orphan_then_adopt` suppressions when exercised offline.

## Scope note

This matrix is an **instrument-validation** artifact for the KOSV checker under stated lab faults. Host `delay_proxy` self-tests in each run remain **tool calibration** (±10% of configured delay). The matrix is not a vulnerability finding report and not a Kubernetes ownership-safety result.
