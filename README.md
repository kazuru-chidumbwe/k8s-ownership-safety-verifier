# KOSV — Kubernetes Ownership Safety Verifier

**Framework for verifying Kubernetes resource ownership safety** under controlled conditions.

KOSV checks:

- **O1 Snapshot SCOI** — at any persisted event, ≤1 `ownerReference` with `controller=true`
- **O2 Unintended transfer** — ControllerRef A→B on the same UID without intervening orphan or DELETE

O3/O4 (controller belief vs API) are **not** implemented.

Author: [Seke Kazuru](https://orcid.org/0009-0002-4099-1059) · `kazuruuni@gmail.com`  
License: MIT

## Quick start

```bash
# Offline synthetic smoke (no cluster)
make smoke-fixtures

# Kind clean PASS (Docker + kind + kubectl)
make smoke-kind
```

## Layout

| Path | Role |
| --- | --- |
| [`verifier/check.py`](verifier/check.py) | O1/O2 predicates over JSONL traces |
| [`fixtures/`](fixtures/) | Synthetic O1 FAIL, O2 FAIL, intended orphan PASS |
| [`injector/delay_proxy.py`](injector/delay_proxy.py) | TCP delay proxy (observation-path fault) |
| [`collector/watch_collect.py`](collector/watch_collect.py) | kubectl collector |
| [`experiments/run_kind_smoke.py`](experiments/run_kind_smoke.py) | Deployment create/scale → verify |
| [`docs/THREAT-MODEL.md`](docs/THREAT-MODEL.md) | Threat model |
| [`docs/SCOPE-ISOLATION.md`](docs/SCOPE-ISOLATION.md) | Scope / isolation |
| [`EVIDENCE.md`](EVIDENCE.md) | Smoke evidence summary |

## Smoke evidence (pinned locally in tree)

| Case | Verdict |
| --- | --- |
| Dual `controller=true` | FAIL O1 |
| A→B without orphan | FAIL O2 |
| Orphan then adopt | PASS |
| Kind Deployment create/scale (v1.31.6) | PASS O1/O2 |

See [`EVIDENCE.md`](EVIDENCE.md) and [`results/`](results/).
