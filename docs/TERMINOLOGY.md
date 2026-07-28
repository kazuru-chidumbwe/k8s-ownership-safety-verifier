# Terminology: calibration vs validation

KOSV uses both words on purpose. Do not treat them as synonyms.

| Term | Means | Where it applies |
| --- | --- | --- |
| **Calibration** | Checking a tool’s output against a **known target** and (if needed) adjusting or accepting within tolerance | Host `delay_proxy` self-tests (±10% of configured 500/2000 ms). Code: `calibrate_proxy` / `proxy-latency.json`. |
| **Validation** | Checking that the **instrument behaves correctly** under known conditions (catch planted lies; do not false-positive on intended paths; stay operational under stated lab faults) | Fixture smoke, Kind clean smoke, 20-run E0–E3 matrix O1/O2 outcomes |

Kind `eth0` netem on E1/E2 is a **collector↔API** fault used for instrument validation. It is not controller↔API delay and is not “calibration” of Kubernetes ownership.

Paper drafts and blog posts should keep this split.
