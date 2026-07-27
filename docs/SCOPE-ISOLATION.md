# Scope / isolation (v0)

| Item | v0 |
| --- | --- |
| Cluster | Kind, Kubernetes v1.31.x (`kindest/node:v1.31.6` for pinned matrix) |
| Ownership path | Deployment → ReplicaSet → Pod |
| Collector | `kubectl` poll of `ownerReferences` into normalized JSONL ([SCHEMA.md](SCHEMA.md)) |
| Poll interval (Kind smoke / 20-run matrix) | **1.0 s** sleep between sweeps (+ `kubectl` runtime) |
| Fault surface | **Linux `tc netem` delay** on Kind control-plane node `eth0`; **`kube-controller-manager` restart** |
| Oracles evaluated | O1 and O2 only |

## Fault notes

- In-cluster observation delay for Kind campaigns uses **`tc netem`**, not a transparent proxy between controller-manager and the API server (Kind static-pod limitation).
- Host-side `injector/delay_proxy.py` may be used for latency self-tests; it is not the Kind matrix delay path.

## Deferred

- O3/O4 belief-state measurement  
- StatefulSet / Job / CronJob / custom operators  
- MAAS / Charmed Kubernetes / multi-control-plane  
- Production-cluster claims  

## Validity note

Kind’s single-node control plane is **laboratory evidence** only. It does not stand in for multi-apiserver production races.
