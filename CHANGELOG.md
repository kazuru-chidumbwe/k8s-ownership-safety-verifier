# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Citation / essay pins (`blog-*`) remain valid reproducibility anchors.
Prefer **SemVer** (`vX.Y.Z`) for SoftwareX / package citations; see [`docs/TAGS.md`](docs/TAGS.md).

## [0.1.3] — 2026-07-28

### Fixed

- O2 state (`last_ctrl`, `orphaned`) now keyed by `(resource, uid)`, matching `last_rv` and the documented identity contract. Prevents false O2 FAIL when synthetic traces reuse a UID string across resource types.

### Added

- Fixture `fixtures/o2-cross-resource-shared-uid.jsonl` (expect PASS) wired into `make smoke-fixtures`.

## [0.1.2] — 2026-07-28

### Added

- `experiments/analyze_poll_gaps.py` (Table B gap definitions pinned to code).
- SoftwareX-style Quick Start, architecture figure, and `Licence.txt` GitHub gate.
- Regenerated [`docs/TAGS.md`](docs/TAGS.md) commit hashes from `git rev-parse --short` (no hand-typed SHAs).

### Fixed

- SemVer tag order now matches commit chronology (`v0.1.0` → `v0.1.1` → `v0.1.2`).
- Spelling: SoftwarX → SoftwareX in public docs.
- [`REPRODUCTION.md`](REPRODUCTION.md) no longer names a specific pending reviewer; remains an empty independent-repro template until a third party fills a row.

## [0.1.1] — 2026-07-27

### Fixed

- Scrubbed lab hostname from fault-reach evidence archives (`kosv-lab-01` publication alias; no identifying host strings).

## [0.1.0] — 2026-07-27

### Added

- First SemVer release for SoftwareX / package citation.
- Essay pin `blog-kosv01-2026-07` (`e3532ce`) remains the KOSV-01 methodology cite.
- `CHANGELOG.md` and SemVer tag policy in `docs/TAGS.md`.

[0.1.0]: https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.0
[0.1.1]: https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.1
[0.1.2]: https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.2
[0.1.3]: https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.3
