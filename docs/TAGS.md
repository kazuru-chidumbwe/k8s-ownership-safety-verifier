# Release tags

Annotated tags mark reproducible anchors. The default branch may move after a tag is cut — check out the tag when reproducing a cited result.

| Tag | Commit | Purpose |
| --- | --- | --- |
| [0.1.17](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.17) | dd9fbbc | **Current cite** — PeerJ CS; SoftX branding scrub; cite-pin docs match tag |
| [0.1.16](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.16) | 15efc98 | Prior cite — Zenodo archive (10.5281/zenodo.21950899); same tree as 0.1.15 |
| [0.1.15](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.15) | 15efc98 | CITATION.cff Zenodo-working pattern |
| [0.1.14](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.14) | 647b7f7 | Zenodo license metadata |
| [0.1.13](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.13) | 1acb992 | CITATION.cff affiliation for Zenodo |
| [0.1.12](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.12) | 6f3f27d | Same commit as 0.1.11 |
| [0.1.11](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.11) | 6f3f27d | Kind RepoDigest beside 0.1.10 cite |
| [0.1.10](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.10) | 89412b4 | Kind pin in archive metadata (cluster.json / kind_node_image); Lab RepoDigest kindest/node@sha256:7416a61b42b1662ca6ca89f02028ac133a309a2a30ba309614e8ec94d976dc5a |
| [0.1.9](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.9) | c5f5533 | primary matrix archive 20260814T083135Z + seeded arms |
| [0.1.8](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.8) | 6442987 | denser-poll archive 20260815T023902Z + d/T_eff table |
| [0.1.7](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.7) | 3f6ff7 | --poll-interval denser-poll CLI · schema vocabulary · fixture smokes |
| [0.1.6](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.6) | 722ff70 | Docs for primary matrix / seeded (archives deposited in v0.1.9) |
| [0.1.5](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.5) | 6c53e4e | Calibration vs validation lock |
| [0.1.4](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.4) | c86b558 | Ordinary release-notes voice in TAGS |
| [0.1.3](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.3) | 74b211f | O2 identity keyed by resource + uid |
| [0.1.2](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.2) | 777db4 | Docs and architecture figure refresh |
| [0.1.1](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.1) | e6295b5 | Fault-reach evidence hostname scrub |
| [0.1.0](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.0) | d054f47 | First SemVer release |
| [preanalysis-scale1000-2026-07-27](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/tree/preanalysis-scale1000-2026-07-27) | 984600 | Pre-analysis scale pin |

**Removed (2026-08-04):** log-kosv01-2026-07 — superseded pre-fault-reach / pre-O2-fix snapshot. Do not cite. Use **0.1.17**.

Short hashes are what git rev-parse --short <tag>^{commit} reports for that tag.

## Quick checkout

`ash
git checkout v0.1.17
make smoke-fixtures
python experiments/analyze_poll_gaps.py matrix/runs/20260814T083135Z --levels E0,E1,E2
`

## Tag policy

- Prefer SemVer tags (0.1.6 and later) for package, blog, and paper citations — see [CHANGELOG.md](../CHANGELOG.md).
- Do not cite a floating default-branch tip for published results.
- Cut a new SemVer tag when the release boundary changes, not on every documentation commit.
- Do not move a published SemVer tag; cut 0.1.18 / 0.2.0 instead.
- Do not resurrect log-kosv01-2026-07; it asserted incorrect eth0 path semantics and lacked the O2 (resource, uid) fix.
