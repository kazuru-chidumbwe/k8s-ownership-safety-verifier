#!/usr/bin/env python3
"""Backfill cluster.json + kind_node fields into archived matrix stamps.

Attestation: Lab Test Server Kind cluster `kosv` still running kindest/node:v1.34.0
(kubelet v1.34.0) on 2026-08-15; matches deploy/kind/cluster-v1.34.yaml used for
primary / denser-poll / seeded archives. Original runners did not record the pin.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAMPS = [
    "20260814T083135Z",
    "20260815T023902Z",
    "seeded-20260814T055833Z",
]

CLUSTER = {
    "kind_node_image": "kindest/node:v1.34.0",
    "kubelet_version": "v1.34.0",
    "kind_node_name": "kosv-control-plane",
    "kind_cluster_name": "kosv",
    "deploy_config": "deploy/kind/cluster-v1.34.yaml",
    "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    "capture_method": "post_hoc_lab_attestation",
    "attestation": (
        "2026-08-15 Lab Test Server: docker inspect kosv-control-plane → "
        "kindest/node:v1.34.0; kubectl node kubeletVersion → v1.34.0. "
        "Same pin as deploy/kind/cluster-v1.34.yaml used for these stamps. "
        "Original runner did not emit this field; backfilled for archive self-description."
    ),
}


def patch_stamp(stamp: str) -> None:
    d = ROOT / "matrix" / "runs" / stamp
    if not d.is_dir():
        raise SystemExit(f"missing {d}")
    (d / "cluster.json").write_text(json.dumps(CLUSTER, indent=2) + "\n", encoding="utf-8")
    summary_path = d / "SUMMARY.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["kind_node_image"] = CLUSTER["kind_node_image"]
    summary["kubelet_version"] = CLUSTER["kubelet_version"]
    summary["cluster"] = CLUSTER
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    n = 0
    for meta_path in sorted(d.glob("*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["kind_node_image"] = CLUSTER["kind_node_image"]
        meta["kubelet_version"] = CLUSTER["kubelet_version"]
        meta["cluster"] = CLUSTER
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        n += 1
    print(f"{stamp}: cluster.json + SUMMARY + {n} meta.json")


def main() -> int:
    for s in STAMPS:
        patch_stamp(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
