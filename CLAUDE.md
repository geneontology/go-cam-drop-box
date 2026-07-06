# go-cam-drop-box — instructions for AI agents

This file is for AI agents (e.g. Claude) helping a GO curator **save a GO-CAM
model to the drop box**. Humans can read it too.

Your job: produce a valid GO-CAM model file and open a pull request that adds it
to `models/`. The repo's CI enforces the contract — but you should self-check
locally first so the PR is green on arrival.

## The contract

A submission is a single YAML file that:

1. Is a **gocam-py GO-CAM model** (the LinkML data model — see
   `examples/` for a complete reference, and the gocam-py schema for the full
   spec).
2. Has `id: gomodel:gcdb-<UUID>` at the top level.
3. Is saved as `models/gcdb-<UUID>.yaml` — **filename must match the id.**
4. Passes all four CI gates (see README "What CI checks"): id/filename,
   LinkML conformance, "true GO-CAM" semantics, and ontology-term validity.

Right now the semantic gate is **strict**: the model must be *complete and
production-worthy* — `status: production`, at least one causal relationship
between activities, no disconnected activities, and evidence on assertions. A
half-finished experiment will be rejected. (This may be loosened later.)

## Minting the id

Generate a UUID and prefix it with `gcdb-`:

```sh
python3 -c "import uuid; print(f'gcdb-{uuid.uuid4()}')"
```

Use that value as `gomodel:gcdb-<UUID>` for the model `id` and as the filename
stem. Activity ids under it take the form `gomodel:gcdb-<UUID>/<local-id>`.

## Two ways to produce the YAML

The drop box validates the **artifact, not its provenance** — any path that
yields a passing model file is fine.

- **Author it directly (preferred for agents).** Write the gocam-py YAML from
  scratch, following the schema and the `examples/` reference. No Noctua round-
  trip needed. Build a complete, connected, evidenced, `production`-status model.
- **Export from a Noctua dev-server model.** If the curator built a model on the
  Noctua/barista dev server, fetch its minerva JSON and convert with gocam-py:
  `gocam.translation.MinervaWrapper.minerva_object_to_model(minerva_json)` →
  `Model` → serialize to YAML. Then set `id` to `gomodel:gcdb-<UUID>`.

## Self-check, then submit

1. Validate locally and fix anything it flags:
   ```sh
   pip install -r validation/requirements.txt
   python validation/validate_model.py models/gcdb-<UUID>.yaml
   ```
2. Fork `geneontology/go-cam-drop-box`, add the file on a branch, commit, and
   open a PR (do the git/`gh` plumbing for the curator). Summarize in the PR
   what the model represents.

## Don't

- Don't reuse or guess an existing `gomodel:` id — always mint a fresh
  `gcdb-<UUID>`.
- Don't invent ontology terms; every GO/RO/ECO/CHEBI/etc. id must be real and
  current (the CI term-check will catch fabrications).
- Don't submit against the Noctua **production** server or claim production
  provenance — this is a staging drop box.
