# Contributing

Thanks for submitting a GO-CAM model. Submissions come in as **pull requests**
that add one model file to `models/`, and are gated by automated checks plus a
maintainer review.

## Before you start

- A **GitHub account** that is a member of the GO organization.
- Your model as a **gocam-py GO-CAM YAML** file (see the [README](README.md) for
  the format and [`examples/`](examples/) for a complete reference). AI agents:
  see [CLAUDE.md](CLAUDE.md).

## Steps

1. **Mint an id.** Every model gets a fresh drop-box id:
   ```sh
   python3 -c "import uuid; print(f'gcdb-{uuid.uuid4()}')"
   ```
   Use it as the model `id` (`gomodel:gcdb-<UUID>`) and as the filename
   (`models/gcdb-<UUID>.yaml`). They must match.

2. **Fork** `geneontology/go-cam-drop-box`, clone your fork, and create a branch.

3. **Add your file** at `models/gcdb-<UUID>.yaml`.

4. **Validate locally** (catches everything CI checks):
   ```sh
   pip install -r validation/requirements.txt
   python validation/validate_model.py models/gcdb-<UUID>.yaml
   ```

5. **Commit and open a PR** against `main`. Briefly describe what the model
   represents.

## What has to pass before merge

CI runs four gates on each added/changed model (see the [README](README.md) for
detail): **id/filename/uniqueness**, **LinkML schema conformance**, **"true
GO-CAM" semantics** (complete + production-worthy), and **ontology-term
validity**. All four must be green, and a maintainer merges.

## Notes

- The `gcdb-` id is a **staging** identifier. If a model is later promoted into
  production, it will be re-minted with a production `gomodel:` id.
- The bar is intentionally strict for now (complete, production-worthy models
  only). The semantic criteria live in
  [`validation/criteria.yaml`](validation/criteria.yaml) and may be relaxed over
  time.
