# Contributing

Thanks for submitting a GO-CAM model. Submissions come in as **pull requests**
that add one model to `models/` as a **pair of files with one id**, and are
gated by automated checks plus a maintainer review.

## Before you start

- A **GitHub account** that is a member of the GO organization.
- Your model built and **stored on noctua-dev**, in whatever state you consider
  right for it (`development` is fine; `delete` is refused). The
  id minerva gave it there (`gomodel:<16 hex>`) is the model's id here and in
  production. AI agents: see [CLAUDE.md](CLAUDE.md).

## Steps

1. **Export both files** from the stored dev model (see the README for the two
   commands): `models/<id>.yaml` and `models/<id>.ttl`.
2. **Validate locally** (catches everything CI checks, including the
   noctua-models QC battery over the TTL):
   ```sh
   pip install -r validation/requirements.txt
   python validation/validate_model.py models/<id>.yaml
   ```
3. **Fork** `geneontology/go-cam-drop-box`, clone your fork, create a branch,
   add both files, commit, and open a PR against `main`. Briefly describe what
   the model represents.
4. **Fixes go through noctua-dev.** If CI or review asks for a change, make it
   on the dev model and re-export both files; do not edit either file by hand.

## What has to pass before merge

Seven gates (README "What CI checks"): id/filename/uniqueness, LinkML schema
conformance, "true GO-CAM" semantics, ontology-term validity, companion TTL,
YAML↔TTL agreement, and the noctua-models SPARQL QC battery. All green, and a
maintainer merges.

## What happens after merge

Merged pairs are copied into `noctua-models` during a Noctua maintenance outage
and become production models **under the same id**; the pair is then removed
from `models/` and recorded in [`PROMOTIONS.md`](PROMOTIONS.md). Once merged,
the drop box is the source of truth for that model until it is promoted.

## Legacy submissions

Before 2026-09-24, submissions used client-minted `gomodel:gcdb-<UUID>` ids and
had no TTL. Those still validate (with a warning) but cannot be promoted until
re-exported from noctua-dev as an id-matched pair.
