# Independent cold reproduction

**Purpose:** Record a successful clone → smoke run by someone **other than** the author, with no guidance beyond this README / `make` targets.

## Instructions (reproducer)

```bash
git clone https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier.git
cd k8s-ownership-safety-verifier
git checkout v0.1.0   # or the SoftwarX pin tag when frozen

make smoke-fixtures
# Optional (needs Docker + kind + kubectl):
# make smoke-kind
```

Then fill the table below and open a PR (or send the filled file to the author).

## Record

| Field | Value |
| --- | --- |
| Reproducer name | _pending — request to Prof Harsh_ |
| Date (UTC) | |
| Machine / OS | |
| Python version | |
| Git tag / commit | `v0.1.0` |
| `make smoke-fixtures` exit code | |
| Notable output (PASS/FAIL lines) | |
| `make smoke-kind` attempted? | yes / no |
| `make smoke-kind` exit code | n/a or … |
| Notes | zero guidance beyond README |

## Author note

Author/lab runs are **not** a substitute for this artifact. Until an independent row is filled, treat this file as a request template.
