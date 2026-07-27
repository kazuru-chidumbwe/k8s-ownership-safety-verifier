# Extending KOSV

Audience: researchers adding ownership paths or oracles.

## Add a new ownership path (e.g. StatefulSet)

1. **Collector** — extend the poll/watch resource list (e.g. `statefulsets`, owned pods) in `experiments/run_kind_smoke.py` / matrix runners and any shared collector helpers so events include the new `resource` singular name.
2. **Normalizer** — emit the same JSONL fields as [`SCHEMA.md`](SCHEMA.md); map `ownerReferences` into `owners[]`.
3. **Workload generator** — add a fixture or experiment script that creates/scales the path with a unique `experiment_id`.
4. **Fixtures** — add synthetic JSONL under `fixtures/` for expected O1/O2 PASS/FAIL on that path.
5. **Smoke** — wire a Makefile target or extend `experiments/run_fixture_smoke.py`.
6. **Docs** — update [`SCOPE-ISOLATION.md`](SCOPE-ISOLATION.md) (in-scope path list) and record Kind version.

No verifier change is required for O1 if events already expose `owners[].controller`. O2 intended-transfer rules may need path-specific suppressions (document them).

## Add a new oracle

1. **Define** the predicate formally (inputs, FAIL vs MEASURE, suppressions) in a short design note.
2. **Implement** in `verifier/check.py` (or `verifier/oracles/<name>.py` if split) consuming only normalized events — or a **new** belief-trace schema for O3.
3. **Report** — extend `Violation.oracle` / `Report` fields; keep PASS/FAIL/INCONCLUSIVE semantics stable.
4. **Fixtures** — add synthetic traces that trip and that correctly suppress.
5. **Caveats** — state incompleteness (e.g. poll gaps) in `Report.caveats`.

### O3 / O4 (not implemented)

O3 (controller belief ≠ API ControllerRef) and O4 (thrash under O1) require instrumentation beyond API polling. Do not mark them implemented until reconcile-time belief traces exist.

## Add a fault model

Prefer deterministic, documented injectors. For Kind observation delay, prefer **`tc netem`** on the node. Document calibration method and ±tolerance. Avoid claiming proxy-in-the-middle semantics unless the control plane is actually intercepted.
