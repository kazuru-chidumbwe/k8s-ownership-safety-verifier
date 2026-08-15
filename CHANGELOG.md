# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Prefer **SemVer** (`vX.Y.Z`) for blog / package / paper citations; see [`docs/TAGS.md`](docs/TAGS.md).
Current public cite: **`v0.1.10`**.

## [0.1.10] — 2026-08-15

### Added

- `experiments/cluster_env.py` + live `kind_node_image` / `kubelet_version` capture in `run_matrix.py` and `run_seeded_violations.py` (`cluster.json` + SUMMARY + per-run `meta.json`).
- `experiments/backfill_cluster_pin.py` — Lab-attested pin for archived stamps.

### Changed

- Backfilled `matrix/runs/20260814T083135Z/`, `20260815T023902Z/`, and `seeded-20260814T055833Z/` with `kindest/node:v1.34.0` / kubelet `v1.34.0` (post-hoc Lab attestation; original runners did not emit the field).
- [`MATRIX-ANALYSIS.md`](MATRIX-ANALYSIS.md) notes self-describing cluster pin paths.

## [0.1.9] — 2026-08-15

### Added

- Primary matrix archive `matrix/runs/20260814T083135Z/` (20/20 PASS; Kind v1.34.0; Lab Test) — the submit Results stamp.
- Seeded live-trace archive `matrix/runs/seeded-20260814T055833Z/`.
- [`results/primary-poll-gaps-20260814T083135Z.json`](results/primary-poll-gaps-20260814T083135Z.json).

### Changed

- [`MATRIX-ANALYSIS.md`](MATRIX-ANALYSIS.md): primary stamp is now a committed archive path, not docs-only.

## [0.1.8] — 2026-08-15

### Added

- Matrix archive `matrix/runs/20260815T023902Z/` — Lab Test denser-poll sensitivity (Kind v1.34.0; `--poll-interval 0.2`; E0/E1 × 3; 6/6 PASS).
- [`results/dense-poll-gaps-20260815T023902Z.json`](results/dense-poll-gaps-20260815T023902Z.json) — gap p50s + \(d/T_{\text{eff}}\) detection-probability table.
- [`MATRIX-ANALYSIS.md`](MATRIX-ANALYSIS.md) denser-poll section with inter-sweep comparison vs primary and \(P \approx d/T_{\text{eff}}\) rows.

## [0.1.7] — 2026-08-15

### Added

- `experiments/run_matrix.py --poll-interval` (default `1.0`; denser sensitivity e.g. `0.2`). SUMMARY records `poll_interval_s` / `poll_seconds`.
- Fixture smokes: missing-UID skip, RV-regression INCONCLUSIVE, O2 delete-then-new-UID.
- `CITATION.cff` for GitHub citation metadata.

### Changed

- [`docs/SCHEMA.md`](docs/SCHEMA.md): explicit ADDED/MODIFIED/DELETED/UPDATE vocabulary; `(resource, uid)` note for versions/CRDs/aggregated APIs.
- Smoke summary `report` paths are repo-relative (no host absolute paths).

## [0.1.6] — 2026-08-14

### Added

- `experiments/run_seeded_violations.py`: observation-layer O1/O2 seeded violation arms (2/2 detected).
- `deploy/kind/cluster-v1.34.yaml`; default Kind pin **`kindest/node:v1.34.0`**.

### Changed

- Primary instrument-validation matrix stamp **`20260814T083135Z`** (20/20 PASS on v1.34.0).
- [`MATRIX-ANALYSIS.md`](MATRIX-ANALYSIS.md) and README updated with primary matrix cite and poll-gap p50 from v1.34 traces.

### Removed

- Git tag `blog-kosv01-2026-07` deleted (2026-08-04). It was a pre-fault-reach / pre-O2-identity-fix snapshot and contradicted current identity contract. **Do not cite.** Use `v0.1.10`.

## [0.1.5] — 2026-07-28

### Changed

- Locked **calibration** vs **validation** wording: `delay_proxy` self-tests stay calibration; smoke + matrix O1/O2 outcomes are instrument validation ([`docs/TERMINOLOGY.md`](docs/TERMINOLOGY.md)).
- README, MATRIX-ANALYSIS, SCHEMA, EXTENDING updated to match.

## [0.1.4] — 2026-07-28

### Changed

- [`docs/TAGS.md`](docs/TAGS.md) rewritten as ordinary release notes (removed checklist-style wording aimed at external audits).

## [0.1.3] — 2026-07-28

### Fixed

- O2 state (`last_ctrl`, `orphaned`) now keyed by `(resource, uid)`, matching `last_rv` and the documented identity contract. Prevents false O2 FAIL when synthetic traces reuse a UID string across resource types.

### Added

- Fixture `fixtures/o2-cross-resource-shared-uid.jsonl` (expect PASS) wired into `make smoke-fixtures`.

## [0.1.2] — 2026-07-28

### Added

- `experiments/analyze_poll_gaps.py` (Table B gap definitions pinned to code).
- SoftwareX-style Quick Start, architecture figure, and `Licence.txt` GitHub gate.
- Updated [`docs/TAGS.md`](docs/TAGS.md) commit column from `git rev-parse --short`.

### Fixed

- SemVer tags ordered to match commit chronology (`v0.1.0` → `v0.1.1` → `v0.1.2`).
- Spelling: SoftwareX → SoftwareX in public docs.
- [`REPRODUCTION.md`](REPRODUCTION.md) kept as an empty third-party template until an independent row is filled.

## [0.1.1] — 2026-07-27

### Fixed

- Scrubbed lab hostname from fault-reach evidence archives (`kosv-lab-01` publication alias; no identifying host strings).

## [0.1.0] — 2026-07-27

### Added

- First SemVer release for SoftwareX / package citation.
- `CHANGELOG.md` and SemVer tag policy in `docs/TAGS.md`.
- *(Historical note: essay tag `blog-kosv01-2026-07` was cut near this release and later **deleted** 2026-08-04 as superseded — see Unreleased.)*

[0.1.0]: https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.0
[0.1.1]: https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.1
[0.1.2]: https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.2
[0.1.3]: https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.3
[0.1.4]: https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.4
