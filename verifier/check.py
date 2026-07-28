#!/usr/bin/env python3
"""KOSV O1/O2 oracle checker over normalized ownership traces.

O1 (Snapshot SCOI — Single Controller Ownership Invariant): at any persisted event, count(controller=true) <= 1.
     Evaluated per event; object identity includes resource type + uid.
     Negative results do NOT prove absence — poll/watch may miss short-lived revisions.
O2 (Unintended transfer): same (resource, uid) changes ControllerRef A->B without
     an intervening orphan (no controller owner) or DELETE of that object.
     Handoff within one observed owner-set uses prior timeline state (last_ctrl).
     last_ctrl / orphaned are keyed by (resource, uid) — same identity as last_rv —
     so a pod and an unrelated ReplicaSet must never share O2 state even if a
     synthetic fixture reuses the same UID string.

O3/O4 are out of scope until belief-state instrumentation exists.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Violation:
    oracle: str
    object_key: str
    uid: str
    detail: str
    event_index: int
    previous_controller: str | None = None
    new_controller: str | None = None


@dataclass
class Suppression:
    reason: str
    object_key: str
    uid: str
    event_index: int
    detail: str


@dataclass
class Report:
    status: str  # PASS | FAIL | INCONCLUSIVE
    trace_id: str
    events: int
    violations: list[Violation] = field(default_factory=list)
    suppressions: list[Suppression] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    event_type_counts: dict[str, int] = field(default_factory=dict)
    resource_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "trace_id": self.trace_id,
            "events": self.events,
            "violations": [asdict(v) for v in self.violations],
            "suppressions": [asdict(s) for s in self.suppressions],
            "notes": self.notes,
            "event_type_counts": self.event_type_counts,
            "resource_counts": self.resource_counts,
            "caveats": [
                "O1 is incomplete under poll/watch gaps; PASS does not prove absence of short-lived dual-owner states.",
                "Events are evaluated in time order; no pre-O1 dedup of same resourceVersion.",
            ],
        }


def _controllers(owners: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [o for o in (owners or []) if o.get("controller") is True]


def _ctrl_uid(owners: list[dict[str, Any]]) -> str | None:
    cs = _controllers(owners)
    if not cs:
        return None
    return str(cs[0].get("uid") or cs[0].get("name") or "")


def load_trace(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json" and text.lstrip().startswith("["):
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("JSON trace must be a list of events")
        return data
    for i, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}:{i}: invalid JSON: {e}") from e
    return events


def _sort_events(events: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    """Stable time-ordered view; keep original indices for reporting."""
    indexed = list(enumerate(events))

    def key(item: tuple[int, dict[str, Any]]) -> tuple:
        ev = item[1]
        return (str(ev.get("time") or ""), item[0])

    return sorted(indexed, key=key)


def check_trace(events: list[dict[str, Any]], trace_id: str = "") -> Report:
    report = Report(status="PASS", trace_id=trace_id or "unknown", events=len(events))
    # O2 + RV continuity share the same object identity: (resource, uid).
    # Never key O2 state by uid alone — synthetic/adversarial fixtures may reuse
    # UID strings across resource types; real API-server UUIDs do not collide.
    last_ctrl: dict[tuple[str, str], str | None] = {}
    orphaned: dict[tuple[str, str], bool] = {}
    last_rv: dict[tuple[str, str], int] = {}
    gaps = 0

    for orig_idx, ev in _sort_events(events):
        etype = str(ev.get("event") or ev.get("type") or "UPDATE").upper()
        uid = str(ev.get("uid") or "")
        resource = str(ev.get("resource") or ev.get("kind") or "object").lower()
        name = str(ev.get("name") or "")
        ns = str(ev.get("namespace") or "default")
        # resource type is part of identity — never merge pod vs replicaset by RV or O2 state
        key = f"{resource}/{ns}/{name}"
        rk = (resource, uid)
        owners = ev.get("owners") or []

        report.event_type_counts[etype] = report.event_type_counts.get(etype, 0) + 1
        report.resource_counts[resource] = report.resource_counts.get(resource, 0) + 1

        if not uid:
            report.suppressions.append(
                Suppression(
                    reason="missing_uid",
                    object_key=key,
                    uid="",
                    event_index=orig_idx,
                    detail="event skipped",
                )
            )
            continue

        # Continuity: monotonic resourceVersion per (resource, uid)
        rv_raw = str(ev.get("resourceVersion") or "")
        if rv_raw.isdigit() and etype not in ("DELETE", "DELETED"):
            rv = int(rv_raw)
            prev_rv = last_rv.get(rk)
            if prev_rv is not None and rv < prev_rv:
                gaps += 1
                report.suppressions.append(
                    Suppression(
                        reason="resourceVersion_regression",
                        object_key=key,
                        uid=uid,
                        event_index=orig_idx,
                        detail=f"rv {prev_rv} -> {rv}; marked continuity gap",
                    )
                )
            # Large forward jumps are expected under poll; note only if jump > 1 and we care
            last_rv[rk] = rv

        if etype in ("DELETE", "DELETED"):
            last_ctrl.pop(rk, None)
            orphaned.pop(rk, None)
            last_rv.pop(rk, None)
            continue

        # O1 — evaluate this snapshot before any dedup; dual controller = FAIL
        ctrls = _controllers(owners)
        if len(ctrls) > 1:
            report.violations.append(
                Violation(
                    oracle="O1",
                    object_key=key,
                    uid=uid,
                    detail=f"snapshot has {len(ctrls)} controller=true ownerReferences",
                    event_index=orig_idx,
                    previous_controller=None,
                    new_controller=",".join(str(c.get("uid") or c.get("name")) for c in ctrls),
                )
            )
            continue

        cur = _ctrl_uid(owners)
        if cur is None:
            if last_ctrl.get(rk) is not None:
                orphaned[rk] = True
                report.suppressions.append(
                    Suppression(
                        reason="orphan_observed",
                        object_key=key,
                        uid=uid,
                        event_index=orig_idx,
                        detail="controller owner cleared; subsequent adopt may be intended",
                    )
                )
            last_ctrl[rk] = None
            continue

        prev = last_ctrl.get(rk)
        if prev is not None and prev != cur:
            if orphaned.get(rk):
                orphaned[rk] = False
                last_ctrl[rk] = cur
                report.suppressions.append(
                    Suppression(
                        reason="intended_orphan_then_adopt",
                        object_key=key,
                        uid=uid,
                        event_index=orig_idx,
                        detail=f"A={prev} -> orphan -> B={cur}",
                    )
                )
                continue
            report.violations.append(
                Violation(
                    oracle="O2",
                    object_key=key,
                    uid=uid,
                    detail="ControllerRef changed A->B without intervening orphan or DELETE",
                    event_index=orig_idx,
                    previous_controller=prev,
                    new_controller=cur,
                )
            )
        last_ctrl[rk] = cur
        orphaned[rk] = False

    if report.violations:
        report.status = "FAIL"
    elif gaps > 0:
        report.status = "INCONCLUSIVE"
        report.notes.append(
            f"INCONCLUSIVE: {gaps} resourceVersion continuity issue(s); no O1/O2 FAIL"
        )
    else:
        report.notes.append("O1 PASS; O2 PASS")
        report.notes.append(
            "Caveat: PASS does not prove absence of unobserved short-lived dual-owner states"
        )
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="KOSV O1/O2 ownership verifier")
    p.add_argument("trace", type=Path, help="JSONL or JSON array trace")
    p.add_argument("--trace-id", default="", help="Trace identifier for report")
    p.add_argument("--expect", choices=["PASS", "FAIL", "INCONCLUSIVE"], default=None)
    p.add_argument("--expect-oracle", default=None, help="e.g. O1 or O2 when expecting FAIL")
    p.add_argument("-o", "--output", type=Path, default=None)
    args = p.parse_args(argv)

    events = load_trace(args.trace)
    tid = args.trace_id or args.trace.stem
    report = check_trace(events, trace_id=tid)
    payload = report.to_dict()
    text = json.dumps(payload, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")

    if args.expect:
        if report.status != args.expect:
            print(
                f"EXPECTATION MISMATCH: want {args.expect} got {report.status}",
                file=sys.stderr,
            )
            return 2
        if args.expect == "FAIL" and args.expect_oracle:
            oracles = {v.oracle for v in report.violations}
            if args.expect_oracle not in oracles:
                print(
                    f"EXPECTATION MISMATCH: want oracle {args.expect_oracle} in {oracles}",
                    file=sys.stderr,
                )
                return 2
    if report.status == "FAIL" and args.expect != "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
