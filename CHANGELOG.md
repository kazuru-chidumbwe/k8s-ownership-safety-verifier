# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Prefer **SemVer** (`vX.Y.Z`) for blog / package / paper citations; see [`docs/TAGS.md`](docs/TAGS.md).
Current public cite: **`v0.1.5`**.

## Unreleased

### Removed

- Git tag `blog-kosv01-2026-07` deleted (2026-08-04). It was a pre-fault-reach / pre-O2-identity-fix snapshot and contradicted `v0.1.5` (UID-only O2 keying; incorrect eth0-as-controller-path framing). **Do not cite.** Use `v0.1.5`.

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
- Spelling: SoftwarX → SoftwareX in public docs.
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
