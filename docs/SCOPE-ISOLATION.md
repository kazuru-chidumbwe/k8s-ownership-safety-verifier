# Scope / isolation (v0)

| Item | v0 |
| --- | --- |
| Cluster | Kind, Kubernetes **v1.34.0** / **v1.35.0** (`kindest/node` pins in `deploy/kind/`) |
| Ownership path | Deployment → ReplicaSet → Pod; **StatefulSet → Pod** (matrix `ownership_path` from `v0.1.18`) |
| Collector | `kubectl` poll of `ownerReferences` into normalized JSONL ([SCHEMA.md](SCHEMA.md)) |
| Poll interval (Kind smoke / 20-run matrix) | **1.0 s** sleep between sweeps (+ `kubectl` runtime) |
| Fault surface | **`tc netem` on Kind node `eth0`** (delays **host collector ↔ API** egress/response path) · **`kube-controller-manager` restart** |
| Oracles evaluated | O1 and O2 only |

## Fault notes

- Kind matrix delay uses **`tc netem` on `eth0`**, which shapes traffic that leaves the node toward the Docker/host network. Host-side `kubectl` collection is on that path.
- On single-node Kind, controller-manager→API uses the node’s own IP and is delivered **locally via `lo`**, so **`eth0` netem does not delay API↔controller**. See [THREAT-MODEL.md](THREAT-MODEL.md).
- Host-side `injector/delay_proxy.py` may be used for latency self-tests; it is not the Kind matrix delay path.
- Transparent proxy between controller-manager and the API server is **not** used in v0 (Kind static-pod limitation).

## Deferred

- True API↔controller observation delay (`lo` netem or control-plane interception)  
- O3/O4 belief-state measurement  
- DaemonSet / Job / CronJob / custom operators  
- MAAS / Charmed Kubernetes / multi-control-plane  
- Production-cluster claims  

## Validity note

Kind’s single-node control plane is **laboratory evidence** only. It does not stand in for multi-apiserver production races.
