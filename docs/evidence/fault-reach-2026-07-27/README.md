# Fault reach verification artifacts

**Stamp:** `fault-reach-2026-07-27`  
**Host:** `kosv-lab-01` (lab Kind cluster `kosv`)  
**Captured UTC:** 2026-07-27T11:39:23Z  
**Fault under test:** `tc qdisc replace dev eth0 root netem delay 500ms` (E1-equivalent)

## Files

| File | Contents |
| --- | --- |
| [`fault-reach.txt`](fault-reach.txt) | Full capture: `controller-manager.conf` server, interfaces, `ip route get`, `tc qdisc`, `ss -tnp`, timing |
| [`fault-reach.json`](fault-reach.json) | Machine-readable summary |
| [`ss-controller-excerpt.txt`](ss-controller-excerpt.txt) | `kube-controller` ↔ API lines only (paper-friendly) |

## Conclusion (locked)

On this Kind node, `kube-controller-manager` targets `https://172.18.0.2:6443` (the node’s own `eth0` IP). Linux delivers that destination **locally via `lo`** (`ip route get` → `dev lo`, `cache <local>`). Live sockets are `172.18.0.2:* → 172.18.0.2:6443`. Under `eth0` netem 500 ms, host `kubectl` mean latency ≈ 1605 ms while in-node HTTPS to the same API address ≈ 23 ms. Therefore v0 `eth0` netem delays the **collector↔API** path and does **not** delay controller↔API traffic.
