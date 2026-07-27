# KOSV — Kubernetes Ownership Safety Verifier

Research instrument for measuring Kubernetes ownership safety (`ownerReferences` / ControllerRef) with explicit oracles, normalized traces, and calibrated fault injection.

KOSV is aimed at researchers studying controller / ownership correctness under controlled conditions. It is not an operator dashboard and does not claim that Kubernetes is safe or unsafe.

## Oracles (v0)

| Oracle | Predicate | Status |
| --- | --- | --- |
| O1 Snapshot SCOI (Single Controller Ownership Invariant) | At any recorded event, `count(controller=true) ≤ 1` | Implemented |
| O2 Unintended transfer | ControllerRef A→B on same UID without expected orphan/DELETE | Implemented |
| O3 Observation mismatch | Controller belief ≠ API ControllerRef | Defined, not implemented |
| O4 Behavioral thrash | Ownership fight / thrash while O1 holds | Defined, not implemented |

Author: [Seke Kazuru](https://orcid.org/0009-0002-4099-1059) · `kazuruuni@gmail.com`  
License: MIT

## One-command demo (offline, ≪10 minutes)

```bash
git clone https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier.git
cd k8s-ownership-safety-verifier
# Prefer a frozen SemVer tag when citing (example):
# git checkout v0.1.0   # same tree as blog-kosv01-2026-07

make smoke-fixtures
```

This runs synthetic O1 FAIL, O2 FAIL, and intended-orphan PASS fixtures through the verifier. No cluster required. Dependencies: Python 3 standard library only (see [`requirements.txt`](requirements.txt)).

### Optional Kind lab smoke

```bash
make smoke          # fixtures + Kind clean Deployment create/scale
# or: make smoke-kind
```

Requires Docker, `kind`, and `kubectl`.

### Calibration matrix (lab)

```bash
make matrix         # 20-run E0–E3 calibration (needs Kind)
```

## Documentation

| Doc | Role |
| --- | --- |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Components + diagram |
| [`docs/SCHEMA.md`](docs/SCHEMA.md) | Normalized JSONL trace schema |
| [`docs/THREAT-MODEL.md`](docs/THREAT-MODEL.md) | Adversary / trust assumptions |
| [`docs/evidence/fault-reach-2026-07-27/`](docs/evidence/fault-reach-2026-07-27/) | Primary evidence: eth0 netem path reach |
| [`docs/TAGS.md`](docs/TAGS.md) | SemVer + citation pins |
| [`CHANGELOG.md`](CHANGELOG.md) | SemVer history |
| [`REPRODUCTION.md`](REPRODUCTION.md) | Independent cold-reproduction record |
| [`docs/SCOPE-ISOLATION.md`](docs/SCOPE-ISOLATION.md) | Kind lab scope / isolation |
| [`docs/EXTENDING.md`](docs/EXTENDING.md) | Add ownership path or oracle |
| [`EVIDENCE.md`](EVIDENCE.md) | Smoke evidence summary |
| [`MATRIX-ANALYSIS.md`](MATRIX-ANALYSIS.md) | 20-run calibration analysis |

## Layout

| Path | Role |
| --- | --- |
| `verifier/check.py` | O1/O2 predicates over JSONL traces |
| `fixtures/` | Synthetic O1 FAIL, O2 FAIL, intended orphan PASS |
| `collector/` | kubectl-oriented collection helpers |
| `injector/` | Delay tooling (`tc netem` on Kind `eth0` = collector↔API path; optional host delay_proxy for self-tests) |
| `experiments/` | Fixture smoke, Kind smoke, matrix, scale runners |
| `results/` | Committed smoke reports |
| `matrix/runs/` | Calibration archives |

## How to cite

Cite a frozen SemVer tag (and later the SoftwareX article / Zenodo DOI when available), not `main`.
Essay pin `blog-kosv01-2026-07` aliases the same tree — see [`docs/TAGS.md`](docs/TAGS.md).

```text
Seke Kazuru. KOSV: Kubernetes Ownership Safety Verifier.
https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier
Tag: v0.1.0
```

## Claim discipline

- Smoke + matrix results validate the instrument.
- They are not Kubernetes vulnerability findings.
- Poll-based collection is incomplete; PASS ≠ proof of absence.
