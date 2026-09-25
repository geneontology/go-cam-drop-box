# go-cam-drop-box — instructions for AI agents

This file is for AI agents (e.g. Claude) helping a GO curator **save a GO-CAM
model to the drop box**. Humans can read it too.

Your job: get the curator's model into this repo as a **pair of files with one
id** and open a pull request. CI enforces the contract; self-check first so the
PR is green on arrival.

## The contract (since 2026-09-24)

1. The model lives on **noctua-dev** as `gomodel:<id>` (the id minerva minted
   there). That id is the model's permanent id; it is kept on promotion.
2. The model is **stored** on noctua-dev (a store, not just in-memory edits —
   an unstored model is lost at the next dev restart) and its state is
   **`production`**.
3. The submission is two files exported **from that same stored state**:
   - `models/<id>.yaml` — gocam-py YAML (`barista export-model -f gocam-yaml`)
   - `models/<id>.ttl` — minerva's own Turtle export (see README for the call)
4. Both files pass the seven CI gates (README "What CI checks"): id/filename,
   LinkML, true-GO-CAM semantics, ontology terms, companion TTL, YAML↔TTL
   agreement, and the noctua-models SPARQL QC battery over the TTL.

The YAML is the review surface; the TTL is what enters production. Neither is
optional, and they must agree exactly — CI compares them.

## Do

- Build and fix the model **on noctua-dev**, through barista. Store it. Set the
  state. Then export both files in one step. If anything changes later, change
  it on dev and re-export **both**.
- Put comments on the model as **model annotations on dev**
  (`barista update-metadata --add --comment "..."`), not in the YAML by hand —
  CI checks that YAML and TTL comments match.
- When you remove evidence from an edge, remove the evidence individual too;
  the SPARQL battery rejects orphaned individuals.
- Self-check: `python validation/validate_model.py models/<id>.yaml` (with the
  QC queries fetched as in the README).
- Fork `geneontology/go-cam-drop-box`, add both files on a branch, commit, open
  the PR, and say in the PR what the model represents and its dev id.

## Don't

- Don't mint ids, don't reuse ids, don't rename the model — the dev id is the id.
- Don't hand-edit the YAML or the TTL. Every edit goes through noctua-dev and
  a re-export, or the pair will disagree and CI will refuse it.
- Don't invent ontology terms; every GO/RO/ECO/CHEBI/etc. id must be real and
  current.
- Don't submit against the Noctua **production** server; this is the staging
  path into production.
