#!/usr/bin/env python3
"""Capture Kind/node environment pin for matrix archives."""
from __future__ import annotations

import subprocess
from datetime import datetime, timezone

KIND_NODE = "kosv-control-plane"
DEFAULT_KIND_IMAGE = "kindest/node:v1.34.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _sh(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def capture_cluster_env() -> dict:
    """Record Kind/node pin into archive metadata (self-describing run stamp)."""
    env: dict = {
        "kind_node_image": None,
        "kubelet_version": None,
        "kind_node_name": KIND_NODE,
        "captured_at": utc_now(),
        "capture_method": "live",
    }
    img = _sh(["docker", "inspect", KIND_NODE, "--format", "{{.Config.Image}}"])
    if img.returncode == 0 and (img.stdout or "").strip():
        env["kind_node_image"] = img.stdout.strip()
    else:
        env["kind_node_image"] = DEFAULT_KIND_IMAGE
        env["capture_method"] = "fallback_default_image"
    kv = _sh(
        [
            "kubectl",
            "get",
            "node",
            "-o",
            "jsonpath={.items[0].status.nodeInfo.kubeletVersion}",
        ]
    )
    if kv.returncode == 0 and (kv.stdout or "").strip():
        env["kubelet_version"] = kv.stdout.strip()
    return env
