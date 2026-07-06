# go-cam-drop-box

A staging "drop box" where GO curators submit **complete, production-worthy
GO-CAM models** as pull requests. Every submission is validated by CI before a
maintainer merges it. Validated models are intended to flow into the main
GO-CAM / Noctua workflows by a mechanism that is **still to be designed** (see
"Status" below).

> **Status: early / forming.** The contract and the CI gates below are real and
> working, but the promotion path into production is not yet built, and details
> may still change.

## What a submission looks like

- **Format:** a GO-CAM model serialized as **[gocam-py](https://github.com/geneontology/gocam-py) YAML**
  (the LinkML data model for GO-CAMs).
- **Identifier:** the model `id` is in the `gomodel:` namespace with a
  drop-box-specific internal id: **`gomodel:gcdb-<UUID>`**.
- **Filename:** the file lives at **`models/gcdb-<UUID>.yaml`** and its name
  must match the model `id`.

You mint the `gcdb-<UUID>` yourself (a UUID guarantees it can never collide with
a production model id — those are hex, minted by Noctua/minerva). See
[CONTRIBUTING.md](CONTRIBUTING.md).

## What CI checks (the merge gates)

A PR can only be merged once **all** of these pass on each added/changed model:

1. **Identifier & filename.** `id` matches `gomodel:gcdb-<UUID>` (valid UUID),
   the filename matches the id, and the id is unique within `models/`.
2. **LinkML schema conformance.** The model validates against the pinned
   gocam-py GO-CAM LinkML schema.
3. **"True GO-CAM" semantics.** The model is complete and production-worthy —
   `production` status, a connected causal graph (no orphan activities), and
   evidence. These criteria live in [`validation/criteria.yaml`](validation/criteria.yaml)
   and are intentionally modular so the bar can be loosened later.
4. **Ontology-term validity.** Every ontology term used (GO, RO, ECO, CHEBI,
   NCBITaxon, …) exists and is not obsolete, checked with
   [oaklib](https://github.com/INCATools/ontology-access-kit).

Run all four locally before opening a PR:

```sh
pip install -r validation/requirements.txt
python validation/validate_model.py models/gcdb-<UUID>.yaml
```

## Who can contribute

GitHub organization members. Anyone can technically open a PR on a public repo,
but merge is gated on the CI checks above **and** a maintainer's review; we only
support submissions from GO-org members at this time.

## Layout

| Path | What |
|---|---|
| `models/` | Submitted models, `gcdb-<UUID>.yaml` each |
| `examples/` | Reference model(s) that demonstrate the format and pass all gates |
| `validation/` | The validator (`validate_model.py`) + the modular criteria + pinned deps |
| `.github/workflows/validate.yml` | The CI that runs the four gates on each PR |
| `CLAUDE.md` | Instructions for AI agents that author/submit models on a curator's behalf |
