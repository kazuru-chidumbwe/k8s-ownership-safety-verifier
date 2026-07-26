#!/usr/bin/env python3
"""KOSV O1/O2 oracle checker over normalized ownership traces.

O1 (Snapshot SCOI): at any persisted event, count(controller=true) <= 1.
O2 (Unintended transfer): same object UID changes ControllerRef A->B without
   an intervening orphan (no controller owner) or DELETE of that UID.

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
class Report:
    status: str  # PASS | FAIL
    trace_id: str
    events: int
    violations: list[Violation] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "trace_id": self.trace_id,
            "events": self.events,
            "violations": [asdict(v) for v in self.violations],
            "notes": self.notes,
        }


def _controllers(owners: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for o in owners or []:
        if o.get("controller") is True:
            out.append(o)
    return out


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


def check_trace(events: list[dict[str, Any]], trace_id: str = "") -> Report:
    report = Report(status="PASS", trace_id=trace_id or "unknown", events=len(events))
    # uid -> last controller uid (None means orphaned / never owned)
    last_ctrl: dict[str, str | None] = {}
    # uid -> True if last ownership edge was an explicit orphan
    orphaned: dict[str, bool] = {}

    for idx, ev in enumerate(events):
        etype = str(ev.get("event") or ev.get("type") or "UPDATE").upper()
        uid = str(ev.get("uid") or "")
        resource = str(ev.get("resource") or ev.get("kind") or "object").lower()
        name = str(ev.get("name") or "")
        ns = str(ev.get("namespace") or "default")
        key = f"{resource}/{ns}/{name}"
        owners = ev.get("owners") or []

        if not uid:
            report.notes.append(f"event {idx}: missing uid; skipped")
            continue

        if etype in ("DELETE", "DELETED"):
            last_ctrl.pop(uid, None)
            orphaned.pop(uid, None)
            continue

        ctrls = _controllers(owners)
        if len(ctrls) > 1:
            report.violations.append(
                Violation(
                    oracle="O1",
                    object_key=key,
                    uid=uid,
                    detail=f"snapshot has {len(ctrls)} controller=true ownerReferences",
                    event_index=idx,
                    previous_controller=None,
                    new_controller=",".join(
                        str(c.get("uid") or c.get("name")) for c in ctrls
                    ),
                )
            )
            continue

        cur = _ctrl_uid(owners)
        if cur is None:
            # orphan / no managing controller
            if last_ctrl.get(uid) is not None:
                orphaned[uid] = True
            last_ctrl[uid] = None
            continue

        prev = last_ctrl.get(uid)
        if prev is not None and prev != cur:
            # Intended only if we observed orphan (controller cleared) since prev.
            if orphaned.get(uid):
                orphaned[uid] = False
                last_ctrl[uid] = cur
                continue
            report.violations.append(
                Violation(
                    oracle="O2",
                    object_key=key,
                    uid=uid,
                    detail="ControllerRef changed A->B without intervening orphan or DELETE",
                    event_index=idx,
                    previous_controller=prev,
                    new_controller=cur,
                )
            )
        last_ctrl[uid] = cur
        orphaned[uid] = False

    if report.violations:
        report.status = "FAIL"
    else:
        report.notes.append("O1 PASS; O2 PASS")
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="KOSV O1/O2 ownership verifier")
    p.add_argument("trace", type=Path, help="JSONL or JSON array trace")
    p.add_argument("--trace-id", default="", help="Trace identifier for report")
    p.add_argument("--expect", choices=["PASS", "FAIL"], default=None)
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
    return 0 if report.status == "PASS" or args.expect == "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
