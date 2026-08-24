# Release tags

Annotated tags mark reproducible anchors. The default branch may move after a tag is cut — check out the tag when reproducing a cited result.

| Tag | Commit | Purpose |
| --- | --- | --- |
| [`v0.1.20`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.20) | `git rev-parse v0.1.20^{commit}` | **Current cite** — PeerJ CS; same science as `v0.1.19` plus `CITATION.cff` version DOI (no hash in this cell: a commit cannot contain its own hash) |
| [`v0.1.19`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.19) | `313f16f` | Prior cite — matrices + version-matched fault-reach; tag-tree `CITATION.cff` still had concept DOI |
| [`v0.1.18`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.18) | `0c2177f` | Prior cite — StatefulSet path + Kind v1.35 matrices (no 2026-08-24 fault-reach stamps) |
| [`v0.1.17`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.17) | `486e6ec` | SoftX branding scrub; Zenodo `10.5281/zenodo.22079811` (no breadth archives) |
| [`v0.1.16`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.16) | `15efc98` | Prior cite — Zenodo `10.5281/zenodo.21950899`; same tree as `v0.1.15` |
| [`v0.1.15`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.15) | `15efc98` | CITATION.cff Zenodo-working pattern |
| [`v0.1.14`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.14) | `647b7f7` | Zenodo license metadata |
| [`v0.1.13`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.13) | `1acb992` | CITATION.cff affiliation for Zenodo |
| [`v0.1.12`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.12) | `6f3f27d` | Same commit as `v0.1.11` |
| [`v0.1.11`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.11) | `6f3f27d` | Kind RepoDigest beside `v0.1.10` cite |
| [`v0.1.10`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.10) | `89412b4` | Kind pin in archive metadata (`cluster.json` / `kind_node_image`); Lab RepoDigest `kindest/node@sha256:7416a61b42b1662ca6ca89f02028ac133a309a2a30ba309614e8ec94d976dc5a` |
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

**Removed (2026-08-04):** `blog-kosv01-2026-07` — superseded pre-fault-reach / pre-O2-fix snapshot. Do not cite. Use **`v0.1.20`**.

Do not embed the *current* cite tag’s own commit hash in this table (it changes the hash). Historical tags may list a resolved short hash. Resolve the live pin with `git rev-parse v0.1.20^{commit}`.

## Quick checkout

```bash
git checkout v0.1.20
make smoke-fixtures
python experiments/analyze_poll_gaps.py matrix/runs/20260814T083135Z --levels E0,E1,E2
```

## Tag policy

Prefer annotated SemVer tags for paper / Zenodo cites. Do not move published tags after Zenodo has archived them.
