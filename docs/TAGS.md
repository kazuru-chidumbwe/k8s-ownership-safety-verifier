# Release tags

Annotated tags mark reproducible anchors. **`main` may advance** after a tag — always `git checkout <tag>` when reproducing a cited result.

| Tag | Commit | Purpose |
| --- | --- | --- |
| [`v0.1.0`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.0) | `1d51980` | SoftwarX instrument pin (fault-reach evidence + CHANGELOG) |
| [`blog-kosv01-2026-07`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/tree/blog-kosv01-2026-07) | `e3532ce` | KOSV-01 methodology essay freeze |
| [`preanalysis-scale1000-2026-07-27`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/tree/preanalysis-scale1000-2026-07-27) | `a984600` | Pre-analysis scale pin (not SoftwarX C1) |

## Quick checkout

```bash
git checkout v0.1.0
make smoke-fixtures
```

## Tag policy

- **SemVer / SoftwarX C1** → `v0.1.0` (see [`CHANGELOG.md`](../CHANGELOG.md)).
- Methodology essay pin → `blog-kosv01-2026-07`.
- Never cite floating `main` for published results.
- New SemVer tags when the release boundary changes — not on every doc commit.
- Do not force-move `v0.1.0` once published; cut `v0.1.1` / `v0.2.0` instead.
