# Release tags

Annotated tags mark reproducible anchors. **`main` may advance** after a tag — always `git checkout <tag>` when reproducing a cited result.

Hashes below are from `git rev-parse --short <tag>^{commit}` (do not hand-type).

| Tag | Commit | Purpose |
| --- | --- | --- |
| [`v0.1.3`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.3) | `74b211f` | **SoftwareX / blog cite pin** (O2 `(resource, uid)` identity fix) |
| [`v0.1.2`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.2) | `f777db4` | Docs / SemVer truth + figures |
| [`v0.1.1`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.1) | `e6295b5` | Hostname scrub in fault-reach evidence |
| [`v0.1.0`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/releases/tag/v0.1.0) | `d054f47` | First SemVer release (CHANGELOG + tag policy) |
| [`blog-kosv01-2026-07`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/tree/blog-kosv01-2026-07) | `e3532ce` | KOSV-01 methodology essay freeze |
| [`preanalysis-scale1000-2026-07-27`](https://github.com/kazuru-chidumbwe/k8s-ownership-safety-verifier/tree/preanalysis-scale1000-2026-07-27) | `a984600` | Pre-analysis scale pin (not SoftwareX C1) |

## Quick checkout

```bash
git checkout v0.1.3
make smoke-fixtures
```

## Tag policy

- **SemVer / SoftwareX C1** → `v0.1.3` (see [`CHANGELOG.md`](../CHANGELOG.md)).
- Methodology essay pin → `blog-kosv01-2026-07`.
- Never cite floating `main` for published results.
- New SemVer tags when the release boundary changes — not on every doc commit.
- Do not force-move a published SemVer tag; cut the next patch/minor instead.
- Sanity-check any cited SemVer: `git rev-parse --short <tag>^{commit}` must match this table on `main` (and `git cat-file -t <hash>` must succeed).
