# Pre-analysis plan — KOSV scale-1000

**Document path (canonical):** `docs/PRE-ANALYSIS-PLAN.md`  
**Registered:** 2026-07-27  
**Campaign name:** `scale-1000`  
**Status:** DEPOSITED for sponsor review — **campaign execution NOT authorized until this plan is approved**  
**Cluster:** Kind, `kindest/node:v1.31.6`  
**Ownership path:** Deployment → ReplicaSet → Pod  
**Collector:** `kubectl` poll; **poll interval:** 1.0 s sleep between sweeps (+ `kubectl` runtime)  
**Oracles in scope for this campaign:** **O1 and O2 only**  
**Oracles out of scope:** O3 and O4 (not implemented; no O3/O4 rates will be reported)

This document locks the analysis design **before** any scale-1000 execution. Post-hoc redefinition of endpoints, tests, or exclusion rules is forbidden. SoftwarX Paper A does **not** depend on this campaign.

---

## 1. Exact parameter grid

| Factor | Symbol | Levels | Type |
| --- | --- | --- | --- |
| Observation-path delay (ms) | \(D\) | `{0, 100, 500, 1000, 2000}` | fixed |
| Controller-manager restart during scale | \(R\) | `{no, yes}` | fixed |
| Replicates per cell | \(n_{\mathrm{cell}}\) | `100` | fixed |

| Quantity | Value |
| --- | --- |
| Cells | \(5 \times 2 = 10\) |
| Runs per cell | 100 |
| **Total runs** | **1000** |
| Workload (every run) | Create Deployment `replicas=2` → wait available → scale to `3` → collect → verify |
| Delay fault | Linux **`tc netem`** on Kind control-plane node `eth0` for the run window when \(D>0\); cleared after collection |
| Restart fault | `kill -TERM` of `kube-controller-manager` during scale when \(R=\mathrm{yes}\) (static pod restarts) |
| Cell id | `D{delay}-R{Y\|N}` (e.g. `D500-RY`) |
| Experiment id | `{cell}-r{rep:03d}` (e.g. `D500-RY-r017`) |

No other factors (Kubernetes version, ownership path, poll interval, oracle set) vary in this campaign.

---

## 2. Primary outcome

**Primary endpoint**

- **O1 FAIL rate** per cell:  
  \[
  \hat{p}_{O1}(c) = \frac{N_{\mathrm{FAIL\text{-}O1}}(c)}{N_{\mathrm{analyzable}}(c)}
  \]
  where a run is **FAIL-O1** iff the frozen verifier report has `status=FAIL` and ≥1 violation with `oracle=O1`.

**Secondary endpoints (pre-registered; not primary)**

| Endpoint | Definition |
| --- | --- |
| O2 FAIL rate | Same denominator; numerator = runs with ≥1 `oracle=O2` violation |
| Any-FAIL rate | Runs with `status=FAIL` (O1 and/or O2) |
| INCONCLUSIVE rate | \(N_{\mathrm{INCONCLUSIVE}}(c) / N_{\mathrm{executed}}(c)\) (descriptive; see §8) |
| Event coverage | Events per run by cell (descriptive: min / median / max) |
| Delay calibration fidelity | For each \(D\in\{100,500,1000,2000\}\): mean (and p95) of calibration probes vs target; **flag** if \(\lvert\mathrm{mean}-D\rvert/D > 0.10\) |

**Explicitly not endpoints**

- O3 mismatch rate — **not measured** (belief-state not instrumented)  
- O4 thrash rate — **not measured**  
- “Kubernetes is safe/unsafe,” CVE/Class findings, production equivalence  

---

## 3. Statistical hypotheses

### 3.1 Baseline cell

Baseline \(c_0\): \(D=0\), \(R=\mathrm{no}\) (`D0-RN`).

### 3.2 Primary family (O1)

For each non-baseline cell \(c \in \{1,\ldots,9\}\):

- **Null \(H_0^{(c)}\):** \(p_{O1}(c) = p_{O1}(c_0)\)  
- **Alternative \(H_1^{(c)}\):** \(p_{O1}(c) \neq p_{O1}(c_0)\) (two-sided)

**Test statistic**

- Two-proportion **z-test** (unpooled SE under \(H_0\)) when all of \(N_{\mathrm{analyzable}}(c)\hat{p}\), \(N(1-\hat{p})\) for both cells are ≥5.  
- Otherwise **Fisher’s exact test** on the \(2\times 2\) table of FAIL-O1 vs not, among analyzable runs.

**Significance level**

- Family-wise α = **0.05** before multiplicity correction (§4).

### 3.3 Secondary family (O2)

Same hypothesis structure and tests for \(p_{O2}(c)\) vs baseline, reported as secondary (see multiplicity in §4).

### 3.4 What we will **not** claim from non-significance

Failure to reject \(H_0\) is **not** an equivalence / non-inferiority claim.  
**No TOST / equivalence test** is pre-registered.  
**No power analysis for equivalence** is claimed.  

If needed later, a separate amended plan must deposit equivalence margins and power **before** any such claim.

### 3.5 Reporting

For each cell: \(N_{\mathrm{executed}}\), \(N_{\mathrm{analyzable}}\), \(\hat{p}_{O1}\), \(\hat{p}_{O2}\), Wilson **95% CI** for each rate (descriptive), and the pre-registered test p-value vs baseline where applicable.

---

## 4. Multiplicity correction

| Family | Comparisons | Correction | Decision threshold |
| --- | --- | --- | --- |
| Primary (O1) | 9 cells vs baseline | **Bonferroni** | \(\alpha_{\mathrm{adj}} = 0.05/9\) |
| Secondary (O2) | 9 cells vs baseline | **Bonferroni** (separate family) | \(\alpha_{\mathrm{adj}} = 0.05/9\) |

- Primary and secondary families are **not** pooled into one 18-test Bonferroni.  
- Any-FAIL rate, INCONCLUSIVE rate, event coverage, and calibration fidelity are **descriptive** (no confirmatory p-values).  
- No other oracle×fault confirmatory tests are authorized under this plan.

---

## 5. Stopping rule

| Rule | Lock |
| --- | --- |
| Planned \(N\) | Complete all **1000** runs (100 per cell) |
| Early stop for signal | **None.** No peeking-based early stop for elevated FAIL rates |
| Early stop for futility | **None** |
| Operational interrupt | Allowed only for lab failure (disk, Kind dead, host reboot). Resume with `--resume-latest` until 1000 analyzable-or-executed slots are filled per §8 |
| Interim looks | **Forbidden** for changing hypotheses, α, or exclusions. Status/HEARTBEAT may be monitored for ops health only |

Analysis for confirmatory tests occurs **only after** the campaign reaches 1000 executed attempts under this plan (or sponsor-approved amendment).

---

## 6. False-positive classification procedure

Committed for this campaign to the behavior of the **frozen verifier** (§9) as implemented in `verifier/check.py`, including:

| Mechanism | Campaign commitment |
| --- | --- |
| O1 | Dual `controller=true` on one recorded event → O1 violation (FAIL) |
| O2 | ControllerRef A→B on same UID without intervening orphan or DELETE → O2 violation |
| Suppression `intended_orphan_then_adopt` | Orphan then adopt → **not** O2 FAIL |
| Suppression `orphan_observed` | Logged; enables intended adopt |
| Suppression `missing_uid` | Event skipped |
| `resourceVersion_regression` gaps | Contribute to **INCONCLUSIVE** if no O1/O2 FAIL |
| UID identity | Object key includes resource type + UID; name-only “changes” are not O2 |
| PASS caveat | PASS ≠ proof of absence of sub-poll-interval dual-owner states |

Atlas/SPEC prose mentioning `converge_grace_ms` / time-window convergence that is **not** implemented in the frozen verifier is **out of scope** for this campaign (not applied). Only suppressions present in the frozen `check.py` apply.

Every reported FAIL in the analysis deliverable must cite: `experiment_id`, `trace_id`, `oracle`, artifact path under the campaign stamp directory.

---

## 7. Blinding

| Step | Protocol |
| --- | --- |
| Scoring | **Fully automatic.** Each run’s `report.json` is produced by the frozen verifier on that run’s `trace.jsonl` at collection time (and re-checked at analysis time with the same frozen binary/script — §9) |
| Manual review | Allowed **only** to inventory FAIL and INCONCLUSIVE cases for the analysis write-up (quote violation fields, check artifact presence) |
| Forbidden | Manually changing PASS/FAIL/INCONCLUSIVE after seeing cell aggregates; tuning suppressions mid-campaign; dropping FAIL runs without §8 rules |
| Unblinding | Cell labels (\(D\), \(R\)) are known to the runner (faults must be applied). There is **no** human adjudicating oracle outcomes under blind labels. Blinding here means **no post-hoc human override** of automatic scores |

---

## 8. Data exclusion rules (decided before data)

Let \(N_{\mathrm{executed}}(c)\) = runs that wrote `meta.json` for cell \(c\).

### 8.1 Analyzable set (denominator for FAIL rates)

Include a run in \(N_{\mathrm{analyzable}}\) iff:

1. `meta.json` and `report.json` exist; and  
2. `report.status` ∈ `{PASS, FAIL}`; and  
3. The run is **not** excluded under §8.2.

**INCONCLUSIVE** runs are **excluded** from the FAIL-rate numerator **and** denominator. Their rate is reported separately (§2).

### 8.2 Exclusions (pre-registered)

Exclude from \(N_{\mathrm{analyzable}}\) (and do not count as FAIL) if **any** hold:

| Code | Condition |
| --- | --- |
| `E-INFRA` | Runner recorded infrastructure exception with empty/unusable trace (status INCONCLUSIVE with `error` in meta), e.g. kubectl/API hard failure |
| `E-EMPTY` | Zero events in `trace.jsonl` |
| `E-DUP` | Duplicate `experiment_id` (keep first complete archive by mtime; exclude later duplicates) |

### 8.3 Replacement

If exclusions would leave a cell with \(N_{\mathrm{analyzable}} < 100\) after 100 executed attempts, **do not** silently add runs beyond the grid in this plan. Report reduced \(n\) and note power loss. A follow-on top-up requires a **written amendment** to this plan before extra runs.

### 8.4 Calibration files

Missing delay-calibration JSON for \(D>0\) does **not** exclude ownership runs; it flags the delay-fidelity secondary endpoint for that \(D\).

---

## 9. Analysis code freeze

| Item | Lock |
| --- | --- |
| Verifier entrypoint | `verifier/check.py` |
| Campaign runner | `experiments/run_scale1000.py` (execution only; does not redefine oracles) |
| Freeze mechanism | Git tag **`preanalysis-scale1000-2026-07-27`** on the commit that deposits **this** file at `docs/PRE-ANALYSIS-PLAN.md` |
| Analysis rule | All confirmatory scoring for scale-1000 uses `verifier/check.py` **exactly as in that tag** (byte-identical). Re-run `check.py` from the tag over archived traces at analysis time; do not use a newer verifier unless an amended plan names a new tag |
| Smoke gate before start | After approval to start: `make smoke-fixtures` must PASS on the freeze tag before `campaign_ctl.py start` |

**Note:** SoftwarX documentation commits may land on `main` after this tag; they must **not** change analysis unless a new freeze tag is deposited and approved.

---

## 10. Artifacts and deliverable

**Per run:** `trace.jsonl`, `report.json`, `meta.json`  
**Per delay level:** calibration summary JSON (historical filename may include `proxy-latency`; fault remains **`tc netem`**)  
**Campaign:** `SUMMARY.json`, `HEARTBEAT.json`, stamp directory under `matrix/scale1000/`

**Deliverable after completion:** `SCALE-1000-ANALYSIS.md` containing only pre-registered endpoints and tests above — **no** findings inflation, **no** O3/O4 results, **no** production claims.

---

## 11. Claim discipline (campaign)

This campaign may support **Paper B / KOSV-02** after analysis. It does **not** contribute SoftwarX Paper A evidence beyond what smoke + the separate 20-run calibration already provide.

We will **not** claim:

- Kubernetes ownership bugs from FAIL rates alone  
- Safety or unsafety of Kubernetes  
- That PASS proves absence of transient O1 states shorter than the poll interval  
- O3/O4 results  
- Production / Charmed / multi-control-plane generalization  

---

## 12. Amendment rule

Any change to §§1–9 requires:

1. A new dated section or successor file;  
2. Sponsor acknowledgment **before** further runs that depend on the change;  
3. A new analysis freeze tag if `check.py` changes.

Until sponsor **approves** this deposited plan, **`campaign_ctl.py start` is forbidden.**
