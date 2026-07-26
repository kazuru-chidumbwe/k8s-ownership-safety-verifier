# Threat model (v0)

**Instrument:** Kubernetes Ownership Safety Verifier (KOSV)  
**Oracles in scope:** O1 (snapshot SCOI), O2 (unintended ControllerRef transfer)  
**Out of scope:** O3/O4 (controller belief-state) until reconcile-time instrumentation exists

## Adversary (experiment profiles)

| Field | v0 values |
| --- | --- |
| Position | `observation-path` (API↔controller delay) · `controller-lifecycle` (restart) |
| Capability | Delay or starve observations; restart controller-manager |
| Win condition | O1 FAIL · O2 FAIL |

## Trust assumptions

- API server validation remains honest (≤1 `controller=true` enforced on persist).
- Controllers may use eventually consistent informers.
- Lab / Kind only — not a production cluster claim.

## Not in threat model

Privileged clients that intentionally forge or replace ControllerRefs.
