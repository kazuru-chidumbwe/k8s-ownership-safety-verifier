# PeerJ CS — artifact path map (KOSV)

Maps manuscript tables/figures to paths in the frozen release tree. Cite **`v0.1.21`** @ `aadfcb9` · Zenodo https://doi.org/10.5281/zenodo.22081925.

| Manuscript | Artifact path |
| --- | --- |
| Primary matrix (RQ3) | `matrix/runs/20260814T083135Z/` |
| Denser-poll (Section 4.4(C)) | `matrix/runs/20260815T023902Z/` |
| Seeded arms (Table 7) | `matrix/runs/seeded-20260814T055833Z/` |
| StatefulSet path (Section 4.6) | `matrix/runs/20260823T123056Z/` |
| Kind v1.35 confirmation (Section 4.6) | `matrix/runs/20260824T100725Z/` |
| Fault-reach v1.34 (RQ2) | `docs/evidence/fault-reach-20260824-v134/` |
| Fault-reach v1.35 (RQ2) | `docs/evidence/fault-reach-20260824-v135/` |
| Historical fault-reach | `docs/evidence/fault-reach-2026-07-27/` |
| Per-run files | `matrix/runs/<stamp>/<cell>/{trace.jsonl,report.json,meta.json}` |
| Stamp cluster pin | `matrix/runs/<stamp>/cluster.json` |
| Poll-gap analyzer (Fig. 5) | `experiments/analyze_poll_gaps.py` |
| Matrix runner | `experiments/run_matrix.py` |
| Fixtures (RQ1) | `fixtures/` |
| Figure numbering notes | `docs/figures/README.md` |

Paper figure SVGs for PeerJ live in the manuscript tree, not this repo folder (see `docs/figures/README.md`).
