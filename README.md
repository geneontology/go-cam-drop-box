# go-cam-drop-box

A staging "drop box" where GO curators submit **complete
GO-CAM models** as pull requests. Every submission is validated by CI before a
maintainer merges it. Merged models are copied into
[`noctua-models`](https://github.com/geneontology/noctua-models) during a Noctua
maintenance outage and become production models (see
[`PROMOTIONS.md`](PROMOTIONS.md) for what has moved and when).

> **Status: working, still forming.** The contract below is real and enforced.
> It changed on 2026-09-24: a submission is now a **pair of files with one id**.

## What a submission is

A submission is **one model in two formats, with the same id**:

| File | What | Role |
|---|---|---|
| `models/<id>.yaml` | the model as [gocam-py](https://github.com/geneontology/gocam-py) YAML | review and validation surface; the gocam-py ecosystem artifact |
| `models/<id>.ttl` | the model's native minerva Turtle, exported from **noctua-dev** | the artifact that is promoted into `noctua-models` |

- **The id is the noctua-dev id** the model was built under, e.g.
  `gomodel:6ab067da00000569`. It is the YAML `id`, the TTL ontology IRI, and
  the filename stem of both files. It is kept unchanged on promotion.
- **Both files come from the same stored state of the same dev model.** Build
  (or fix) the model on noctua-dev, store it, set its state, then export both.
  Do not hand-edit either file; edit the model on noctua-dev and re-export.
- **The model must be complete**: a connected causal graph with evidence. Its
  **state is whatever the curator set on noctua-dev** (`development`,
  `production`, ...; anything but `delete`) and is the same in both files.
  Half-finished experiments are still rejected by the structural gates.

Older submissions used client-minted `gomodel:gcdb-<UUID>` ids and had no TTL.
Those files still validate (with a warning) but cannot be promoted until they
are re-exported from noctua-dev as an id-matched pair.

## What CI checks (the merge gates)

A PR can only be merged once **all** of these pass for each added/changed pair:

1. **Identifier & filename.** `id` is `gomodel:<16 hex>` (the dev id), both
   filenames match it, and the id is unique within `models/`.
2. **LinkML schema conformance** of the YAML against the pinned gocam-py schema.
3. **"True GO-CAM" semantics** (YAML): a connected causal graph, no orphan
   activities, evidence present, and a real model state (any but `delete`).
   [`validation/criteria.yaml`](validation/criteria.yaml) holds the knobs.
4. **Ontology-term validity** (YAML): every GO/RO/ECO/CHEBI/CL/UBERON/PO term
   exists and is not obsolete (oaklib).
5. **Companion TTL** exists, parses, declares exactly one `owl:Ontology` whose
   IRI is the YAML id, and its `lego:modelstate` equals the YAML `status`.
6. **YAML ↔ TTL agreement.** Every activity, term, context chain, molecule
   link, causal edge, evidence item, comment, title and taxon in the YAML is in
   the TTL, and the TTL has no model fact the YAML lacks.
7. **noctua-models QC battery** over the TTL: every query in
   `noctua-models/sparql/*.rq` (fetched at CI time) must return no rows. Today
   that catches disconnected individuals (e.g. orphaned evidence) and multiply
   reified edges — the same checks production runs.

Run everything locally before opening a PR:

```sh
pip install -r validation/requirements.txt
mkdir -p validation/sparql && for u in $(gh api repos/geneontology/noctua-models/contents/sparql --jq '.[] | select(.name|endswith(".rq")) | .download_url'); do curl -sfO --output-dir validation/sparql "$u"; done
python validation/validate_model.py models/<id>.yaml     # finds models/<id>.ttl by name
```

## Getting the two files from noctua-dev

With the model stored on noctua-dev as `gomodel:<id>` (its state is left as the
curator set it; `barista update-metadata --model <id> --state ...` changes it):

```sh
# YAML (gocam-py, via noctua-py)
barista export-model --model <id> -f gocam-yaml > models/<id>.yaml
# TTL (minerva's own export; no token needed on the public dev endpoint)
curl -s -X POST http://barista-dev.berkeleybop.org/api/minerva_public_dev/m3Batch \
  --data-urlencode "requests=[{\"entity\":\"model\",\"operation\":\"export\",\"arguments\":{\"model-id\":\"gomodel:<id>\"}}]" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["export-model"])' > models/<id>.ttl
```

## Who can contribute

GitHub organization members. Anyone can technically open a PR on a public repo,
but merge is gated on the CI checks above **and** a maintainer's review; we only
support submissions from GO-org members at this time.

## Layout

| Path | What |
|---|---|
| `models/` | Submitted models, `<id>.yaml` + `<id>.ttl` per model |
| `examples/` | Reference pair that passes all seven gates (plus one legacy YAML-only example) |
| `validation/` | The validator (`validate_model.py`, `ttl_checks.py`), the modular criteria, vendored CURIE maps, pinned deps |
| `.github/workflows/validate.yml` | The CI that runs the gates on each PR |
| `PROMOTIONS.md` | Log of models copied into `noctua-models`, by outage |
| `CLAUDE.md` | Instructions for AI agents that author/submit models on a curator's behalf |
