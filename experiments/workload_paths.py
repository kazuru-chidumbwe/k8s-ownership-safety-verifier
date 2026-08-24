"""Ownership-path configs for matrix and smoke runners."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkloadPath:
    name: str
    poll_resources: tuple[str, ...]
    singular_map: dict[str, str]
    rollout_kind: str  # deployment | statefulset


PATHS: dict[str, WorkloadPath] = {
    "deployment": WorkloadPath(
        name="deployment",
        poll_resources=("deployments", "replicasets", "pods"),
        singular_map={
            "deployments": "deployment",
            "replicasets": "replicaset",
            "pods": "pod",
        },
        rollout_kind="deployment",
    ),
    "statefulset": WorkloadPath(
        name="statefulset",
        poll_resources=("statefulsets", "pods"),
        singular_map={
            "statefulsets": "statefulset",
            "pods": "pod",
        },
        rollout_kind="statefulset",
    ),
}


def get_path(name: str) -> WorkloadPath:
    key = name.strip().lower()
    if key not in PATHS:
        raise ValueError(f"unknown path {name!r}; choose from {sorted(PATHS)}")
    return PATHS[key]
