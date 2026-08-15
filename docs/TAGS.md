# Release tags

Annotated tags mark reproducible anchors. The default branch may move after a tag is cut — check out the tag when reproducing a cited result.

| Tag | Commit | Purpose |
| --- | --- | --- |
| [`v0.1.10`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.10) | `89412b4` | **Current cite** — Kind pin in archive metadata (`cluster.json` / `kind_node_image`) |
| [`v0.1.9`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.9) | `c5f5533` | primary matrix archive `20260814T083135Z` + seeded arms |
| [`v0.1.8`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.8) | `6442987` | denser-poll archive `20260815T023902Z` + d/T_eff table |
| [`v0.1.7`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.7) | `a3f6ff7` | `--poll-interval` denser-poll CLI · schema vocabulary · fixture smokes |
| [`v0.1.6`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.6) | `722ff70` | Docs for primary matrix / seeded (archives deposited in v0.1.9) |
| [`v0.1.5`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.5) | `6c53e4e` | Calibration vs validation lock |
| [`v0.1.4`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.4) | `c86b558` | Ordinary release-notes voice in TAGS |
| [`v0.1.3`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.3) | `74b211f` | O2 identity keyed by resource + uid |
| [`v0.1.2`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.2) | `f777db4` | Docs and architecture figure refresh |
| [`v0.1.1`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.1) | `e6295b5` | Fault-reach evidence hostname scrub |
| [`v0.1.0`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.0) | `d054f47` | First SemVer release |
| [`preanalysis-scale1000-2026-07-27`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/tree/preanalysis-scale1000-2026-07-27) | `a984600` | Pre-analysis scale pin |

**Removed (2026-08-04):** `blog-kosv01-2026-07` — superseded pre-fault-reach / pre-O2-fix snapshot. Do not cite. Use **`v0.1.10`**.

Short hashes are what `git rev-parse --short <tag>^{commit}` reports for that tag. After cutting `v0.1.10`, replace `89412b4` with that short hash.

## Quick checkout

```bash
git checkout v0.1.10
make smoke-fixtures
python experiments/analyze_poll_gaps.py matrix/runs/20260814T083135Z --levels E0,E1,E2
```

## Tag policy

- Prefer SemVer tags (`v0.1.6` and later) for package, blog, and paper citations — see [`CHANGELOG.md`](../CHANGELOG.md).
- Do not cite a floating default-branch tip for published results.
- Cut a new SemVer tag when the release boundary changes, not on every documentation commit.
- Do not move a published SemVer tag; cut `v0.1.10` / `v0.2.0` instead.
- Do not resurrect `blog-kosv01-2026-07`; it asserted incorrect eth0 path semantics and lacked the O2 `(resource, uid)` fix.
