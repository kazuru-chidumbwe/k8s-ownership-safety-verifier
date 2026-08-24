# Threat model (v0)

**Instrument:** Kubernetes Ownership Safety Verifier (KOSV)  
**Oracles in scope:** O1 (snapshot SCOI — Single Controller Ownership Invariant), O2 (unintended ControllerRef transfer)  
**Out of scope:** O3/O4 (controller belief-state) until reconcile-time instrumentation exists

## Adversary (experiment profiles)

| Field | v0 values |
| --- | --- |
| Position | `collector-to-api` (host/`kubectl` poll path delay via Kind node `eth0` `tc netem`) · `controller-lifecycle` (restart) |
| Capability | Delay or starve **collector** observations of API ownership state; restart controller-manager |
| Win condition | O1 FAIL · O2 FAIL |

## What v0 delay is (and is not)

On single-node Kind, `kube-controller-manager` reaches the API server at the node’s own address (e.g. `https://172.18.0.2:6443`). Linux delivers that traffic as **local** (`ip route get` → `dev lo`, cache `<local>`). A `tc netem` qdisc on **`eth0` therefore does not delay controller↔API traffic**.

Verified on the kosv Kind node (lab). Historical capture: `docs/evidence/fault-reach-2026-07-27/`. Version-matched captures on the primary and confirmation images: `docs/evidence/fault-reach-20260824-v134/` (`kindest/node:v1.34.0`; host `kubectl` mean 1688.4 ms vs in-node 22.5 ms under 500 ms `eth0` netem) and `docs/evidence/fault-reach-20260824-v135/` (`kindest/node:v1.35.0`; 1650.4 ms vs 32.6 ms). In both, `controller-manager.conf` server is the node `eth0` IP `:6443` and `ip route get` returns `dev lo` (`cache <local>`).

v0 E1/E2 therefore study **collector-to-API observation delay** (external poller path), which matches KOSV’s poll-based collector architecture. They are **not** a claim of API↔controller informer delay. True controller↔API delay requires a different injector (e.g. `lo` netem or control-plane interception) and is future work.

## Trust assumptions

- API server validation remains honest (≤1 `controller=true` enforced on persist).
- Controllers may use eventually consistent informers (not directly delayed by v0 `eth0` netem).
- Lab / Kind only — not a production cluster claim.

## Not in threat model

Privileged clients that intentionally forge or replace ControllerRefs.
