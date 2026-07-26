# Scope / isolation (v0)

| Item | v0 |
| --- | --- |
| Cluster | Kind, Kubernetes v1.31.x |
| Ownership path | Deployment → ReplicaSet → Pod |
| Collector | kubectl poll / watch of ownerReferences |
| Fault surface | TCP delay proxy (`injector/delay_proxy.py`) |
| Campaign | Smoke fixtures + Kind clean PASS |

## Deferred

- StatefulSet / Job / custom operators  
- MAAS / Charmed Kubernetes  
- O3/O4 belief-state measurement  
- Statistical multi-hundred fault campaigns  

## Validity note

Kind single-node control plane does not stand in for multi-apiserver production races. Report Kind results as lab evidence only.
