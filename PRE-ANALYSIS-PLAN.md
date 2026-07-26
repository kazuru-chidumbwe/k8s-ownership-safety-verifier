# Pre-analysis plan — KOSV scale-1000 (registered before campaign)

**Registered:** 2026-07-26  
**Campaign:** 1000 runs on Kind Kubernetes v1.31.6  
**Status:** LOCKED before first scale-1000 execution  

This document pre-registers analysis choices so post-hoc results cannot be re-cut into findings.

## 1. Primary endpoints (instrument validity — not security findings)

| Endpoint | Definition | Success criterion |
| --- | --- | --- |
| O1 FAIL rate | Fraction of runs with status FAIL and ≥1 O1 violation | Report rate; **no Class-A finding claim** |
| O2 FAIL rate | Fraction with ≥1 O2 violation | Same |
| INCONCLUSIVE rate | Fraction with status INCONCLUSIVE | Report; investigate if >5% |
| Event coverage | Events per run by experiment cell | Descriptive |
| Proxy fidelity | mean/p95/p99 vs configured delay | Flag cell if \|mean−target\|/target > 10% |

## 2. Experimental design (N=1000)

**Factorial (locked):**

| Factor | Levels |
| --- | --- |
| Delay (ms) | 0, 100, 500, 1000, 2000 |
| Controller restart | no, yes |

Cells: 5 × 2 = **10**. Replicates per cell: **100**. Total: **1000**.

Kind version pinned: `kindest/node:v1.31.6` (single version this campaign; v1.30 deferred).

## 3. Fault implementation (locked)

- Delay: `delay_proxy` calibrated **once per delay level** (n=30 probes) at cell start; in-cluster observation delay via `tc netem` on Kind node `eth0` for the run window when delay>0.  
- Restart: `kill -TERM` of `kube-controller-manager` during scale (static pod restart).  
- Workload: Deployment create (replicas=2) → scale to 3; poll collector.

## 4. Statistical comparisons (locked)

1. **FAIL rate vs baseline (delay=0, restart=no):** two-proportion z-test (or Fisher if counts <5). α=0.05 **before** Bonferroni.  
2. **Multiple comparisons:** Bonferroni across **9** non-baseline cells (α_adj = 0.05/9).  
3. **No sequential peeking:** analysis after full 1000 completes (or pre-declared checkpoint at 1000 only).  
4. **INCONCLUSIVE** excluded from FAIL-rate numerator and denominator separately reported.

## 5. What we will NOT claim

- Dual-owner “bugs” in Kubernetes from PASS/FAIL rates alone  
- O3/O4 belief-state results  
- Production Charmed / multi-apiserver equivalence  
- That PASS proves absence of short-lived O1 violations (collector incompleteness stands)

## 6. Artifacts to archive per run

`trace.jsonl`, `report.json`, `meta.json`  
Per delay level: `proxy-latency-D{ms}.json` (once)

## 7. Deliverable after campaign

`SCALE-1000-ANALYSIS.md` — rates by cell, proxy fidelity, FAIL/INCONCLUSIVE inventory, pre-registered tests only.
