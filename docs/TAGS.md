# Release tags

Annotated tags mark reproducible anchors. The default branch may move after a tag is cut — check out the tag when reproducing a cited result.

| Tag | Commit | Purpose |
| --- | --- | --- |
| [`v0.1.4`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.4) | `c86b558` | Current package / paper cite |
| [`v0.1.3`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.3) | `74b211f` | O2 identity keyed by resource + uid |
| [`v0.1.2`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.2) | `f777db4` | Docs and architecture figure refresh |
| [`v0.1.1`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.1) | `e6295b5` | Fault-reach evidence hostname scrub |
| [`v0.1.0`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.0) | `d054f47` | First SemVer release |
| [`blog-kosv01-2026-07`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/tree/blog-kosv01-2026-07) | `e3532ce` | KOSV-01 methodology essay freeze |
| [`preanalysis-scale1000-2026-07-27`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/tree/preanalysis-scale1000-2026-07-27) | `a984600` | Pre-analysis scale pin |

Short hashes are what `git rev-parse --short <tag>^{commit}` reports for that tag.

## Quick checkout

```bash
git checkout v0.1.4
make smoke-fixtures
```

## Tag policy

- Prefer SemVer tags (`v0.1.4` and later) for package and SoftwareX citations — see [`CHANGELOG.md`](../CHANGELOG.md).
- Prefer `blog-kosv01-2026-07` when citing the methodology essay pin.
- Do not cite a floating default-branch tip for published results.
- Cut a new SemVer tag when the release boundary changes, not on every documentation commit.
- Do not move a published SemVer tag; cut `v0.1.4` / `v0.2.0` instead.
