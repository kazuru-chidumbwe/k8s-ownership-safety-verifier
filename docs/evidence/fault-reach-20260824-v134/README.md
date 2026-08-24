# Fault reach verification artifacts

**Stamp:** `fault-reach-20260824-v134`  
**Host:** `kosv-lab-01` (lab Kind cluster `kosv`)  
**Captured UTC:** 2026-08-24T12:56:02Z  
**Kind image:** `kindest/node:v1.34.0`  
**Fault under test:** `tc qdisc replace dev eth0 root netem delay 500ms` (E1-equivalent)

## Files

| File | Contents |
| --- | --- |
| [`fault-reach.txt`](fault-reach.txt) | Full capture: `controller-manager.conf` server, interfaces, `ip route get`, `tc qdisc`, `ss -tnp`, timing |
| [`fault-reach.json`](fault-reach.json) | Machine-readable summary |
| [`ss-controller-excerpt.txt`](ss-controller-excerpt.txt) | `kube-controller` ↔ API lines only (paper-friendly) |

## Conclusion (locked)

On this Kind node, `kube-controller-manager` targets `https://172.19.0.2:6443` (the node's own `eth0` IP). Linux delivers that destination **locally via `lo`** (`ip route get` → `dev lo`, `cache <local>`). Under `eth0` netem 500 ms, host `kubectl` mean latency ≈ 1688.4 ms while in-node HTTPS to the same API address ≈ 22.5 ms. Therefore v0 `eth0` netem delays the **collector↔API** path and does **not** delay controller↔API traffic.
