#!/usr/bin/env python3
"""Offline smoke: synthetic O1 FAIL, O2 FAIL, intended orphan PASS, cross-resource UID PASS."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
CHECK = ROOT / "verifier" / "check.py"
FIX = ROOT / "fixtures"
RES = ROOT / "results"


def main() -> int:
    RES.mkdir(parents=True, exist_ok=True)
    cases = [
        (FIX / "o1-dual-controller.jsonl", RES / "smoke-o1.json", ["--expect", "FAIL", "--expect-oracle", "O1"]),
        (FIX / "o2-unintended-transfer.jsonl", RES / "smoke-o2.json", ["--expect", "FAIL", "--expect-oracle", "O2"]),
        (FIX / "o2-intended-orphan-then-adopt.jsonl", RES / "smoke-o2-intended.json", ["--expect", "PASS"]),
        # Regression: uid-only O2 keys false-FAIL across resource types; must PASS.
        (
            FIX / "o2-cross-resource-shared-uid.jsonl",
            RES / "smoke-o2-cross-resource-uid.json",
            ["--expect", "PASS"],
        ),
    ]
    failed = 0
    summary = []
    for trace, out, extra in cases:
        cmd = [PY, str(CHECK), str(trace), "-o", str(out), "--trace-id", trace.stem, *extra]
        print("+", " ".join(cmd), flush=True)
        code = subprocess.run(cmd).returncode
        if code != 0:
            failed += 1
        summary.append({"case": trace.name, "runner_exit": code, "report": str(out)})
    (RES / "smoke-fixtures-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
