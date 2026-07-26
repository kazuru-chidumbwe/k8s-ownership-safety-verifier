# KOSV evidence pack (26 Jul 2026)

**One sentence:** O1/O2 checker trips synthetic dual-controller and unintended-transfer FAILs, PASSes intentional orphan→adopt, and PASSes a live Kind Deployment create/scale trace (16 events, zero violations).

## Lab environment

| Field | Value |
| --- | --- |
| Host | Lab VM (Ubuntu 24.04-class) |
| Kubernetes | Kind cluster `kosv` · node image `kindest/node:v1.31.6` |
| Tools | kind v0.27.0 · kubectl v1.31.x |

## Artifacts

| Artifact | Path | Verdict |
| --- | --- | --- |
| Checker | `verifier/check.py` | O1/O2 predicates |
| Delay proxy | `injector/delay_proxy.py` | TCP delay fault surface |
| Synthetic O1 | `fixtures/o1-dual-controller.jsonl` → `results/smoke-o1.json` | **FAIL O1** |
| Synthetic O2 | `fixtures/o2-unintended-transfer.jsonl` → `results/smoke-o2.json` | **FAIL O2** |
| Intended orphan | `fixtures/o2-intended-orphan-then-adopt.jsonl` → `results/smoke-o2-intended.json` | **PASS** |
| Kind clean | `traces/kind-clean.jsonl` → `results/kind-clean.json` | **PASS** (16 events) |

## What each trace demonstrates

1. **O1 FAIL** — one snapshot with two `controller=true` refs → checker FAILs O1.  
2. **O2 FAIL** — same UID ControllerRef A→B with no orphan/DELETE → checker FAILs O2.  
3. **Intended PASS** — A→B after orphan → not O2; **PASS**.  
4. **Kind PASS** — Deployment create → scale 2→3; polled ownership events; **O1 PASS; O2 PASS**.

## Reproduce

```bash
make smoke-fixtures
make smoke-kind
```

## Not claimed

- O3/O4 (belief-state)  
- Fault-injected campaign statistics  
- Production / multi-control-plane equivalence
