# Promotions

Models that left this drop box for `geneontology/noctua-models` (production
Noctua). One row per model, in the order the drop-box PRs were opened. The
mechanism is being built up as the SOP settles; each batch records exactly what
was done.

## Batch 2026-09-24 (noctua outage, noctua#1134)

Twelve models. All twelve had been built on the Noctua dev server first, so
the production files are the dev server's native minerva Turtle under the
dev-minted ids, not a conversion of the YAML here: the YAML and the Turtle were
compared at the RDF level (activities, terms, causal edges, molecules,
evidence) before the port. Per model, the only change was one added model-level
`rdfs:comment "Created with GO AI HUB."`; `lego:modelstate` stayed
`development` for this first, test batch (visible in production Noctua, not in
production-state release products). Ids were not re-minted. The batch was
added to `noctua-models` as one commit (`ec35b471`) and re-serialised by the
outage's journal flush (`6518788a`); production Noctua serves each id.

| drop-box id | drop-box PR | noctua-models id | modelstate | title |
|---|---|---|---|---|
| `gcdb-1e1025ab-acce-4716-b393-c1fd0bbcc189` | #7 | `gomodel:6a4e740f00000478` | development | Rod opsin (RHO)-transducin coupling in phototransduction (Gb1/g1 adaptor)_Visual Perception (Human) |
| `gcdb-799a43d9-1b4c-4d34-9133-8224d14df6f7` | #8 | `gomodel:6a4e740f00000858` | development | Example for MF guidelines : Foxo1 regulation of G6pc1 in gluconeogenesis (mouse) |
| `gcdb-29b8acbc-087d-46c9-b5f3-43047161761d` | #10 | `gomodel:6a4e740f00001178` | development | Gbeta1-gamma2 (GNB1-GNG2) activation of GIRK2 (KCNJ6) inwardly rectifying potassium channel (Human) |
| `gcdb-40495a6a-7b39-41f1-bcb5-7f83e3547901` | #11 | `gomodel:6a4e740f00000268` | development | FOXO-CDKN1B signaling (HUMAN) |
| `gcdb-30df8e17-5470-4f62-9891-545b13bbe782` | #12 | `gomodel:6a4e740f00001071` | development | PGC-1a -> HNF4A -> G6PC1 gluconeogenesis triple (RAT) |
| `gcdb-a05168c5-ddec-42d4-8f3a-119b67501d0b` | #13 | `gomodel:6a607ed200000038` | development | FOXO-CDKN1B signaling (MOUSE) v2 |
| `gcdb-37f68fe9-33d5-458c-8f97-55eeeb8c320e` | #15 | `gomodel:6a607ed200000208` | development | Cone opsin(OPN1MW)-transducin coupling (Gb3/Gg8 adaptor)_Visual Perception (Human) |
| `gcdb-4052a312-61bb-4e6f-b3fb-dd2d937f136f` | #18 | `gomodel:6a6ba88c00001743` | development | IL-36 signaling in dendritic cell & T cell activation (Mouse) |
| `gcdb-752afd3e-c31e-496a-b8ab-d7dd94069c2b` | #18 | `gomodel:6a6ba88c00002503` | development | Interleukin-36 alpha (IL36A) receptor signaling via IL1RL2-IL1RAP (Human) |
| `gcdb-c6cd4329-d723-4a7f-82a5-a86345b8f02b` | #18 | `gomodel:6a6ba88c00002431` | development | Interleukin-36 gamma (IL36G) receptor signaling via IL1RL2-IL1RAP (Human) |
| `gcdb-eb5fcf46-8451-464c-9731-c3d87868b9ea` | #18 | `gomodel:6a6ba88c00001637` | development | Interleukin-36 signaling in neutrophils (Mouse) |
| `gcdb-9ac3a991-0960-44b7-b2a5-53134c0a56bb` | #22 | `gomodel:6a6ba88c00000472` | development | mGluR6-G(o)(GNAO1/GNB3/GNG13)-TRPM1 ON bipolar cascade_Visual Perception (Human) |

Removed from `models/` here by the batch's removal PR. Later removal from production, if ever,
is an exact-path `git rm` in `noctua-models` (the flush rewrote the files, so
a revert of `ec35b471` conflicts).

## Batch 2026-10-08 (noctua outage, noctua#1136)

Sixteen models, the first batch under the YAML + TTL pair convention
(go-cam-drop-box#25): the TTL in each submission is what was promoted, under
its dev-minted id, with no change to the file. `lego:modelstate` is
`development` for all sixteen. Preflight on the batch: SHA256SUMS verified, no
id collision with `noctua-models`, import + dump clean on the outage's
minerva-cli, `noctua-models` QC battery 0 rows. Added to `noctua-models` as one
commit (`591f99ae`) and re-serialised by the outage's journal flush
(`9619f04a`); production Noctua serves each id (`state=development`). Five of
the sixteen are the legacy recoveries listed below.

| drop-box PR | noctua-models id | modelstate | title |
|---|---|---|---|
| #31 | `gomodel:6ab067da00001730` | development | Endocytosis in IAV entry via TRIM62-WASH (Human-IAV) |
| #32 | `gomodel:6ab067da00001778` | development | TIP39-PTH2R signaling, keratinocyte differentiation (Human) |
| #34 | `gomodel:6ab067da00005685` | development | Autophagosome assembly via ATG2A lipid transfer (Human) |
| #35 | `gomodel:6ab067da00005862` | development | autophagosome assembly via ATG2A phosphatidylserine transfer (Human) |
| #36 | `gomodel:6ab067da00005793` | development | lysosomal membrane repair via PS-stimulated ATG2A lipid transfer (Human) |
| #37 | `gomodel:6ab067da00006156` | development | Restored_Example for MF guidelines : Foxo1 regulation of G6pc1 and Pck1 in gluconeogenesis (mouse) |
| #38 | `gomodel:6ab067da00006193` | development | nsp8 suppression of TRIM4-MDA5 signaling (Human-SARS-CoV-2) |
| #39 | `gomodel:6ab067da00002140` | development | Calcitonin-CTR-Gs/PKA inhibition of osteoclast bone resorption (Human) |
| #40 | `gomodel:6ab067da00006230` | development | Lipid storage via ATG2A-mediated diacylglycerol transfer to DGAT2 on lipid droplets (Human) |
| #42 | `gomodel:6ab067da00001588` | development | Interleukin-36 beta (IL36B) receptor signaling via IL1RL2-IL1RAP (Human) |
| #43 | `gomodel:6ab067da00001660` | development | Intermembrane phospholipid transfer at ER-PM via VPS13A-XK (Human) |
| #44 | `gomodel:6ab067da00001694` | development | DYRK1A phosphorylates CDKL5 to promote its nuclear export and cytoplasmic kinase activity (Hsap, ISS from mouse; PMID:27840050, PMID:30266824) |
| #45 | `gomodel:6ab067da00001712` | development | DYRK1A phosphorylates CDKL5 on Ser-308 to promote its cytoplasmic localization (Mmus, PMID:27840050) |
| #46 | `gomodel:6a6ba88c00001800` | development | IL-36R defense response to Gram-negative bacterium (Mouse) |
| #47 | `gomodel:6ab067da00005631` | development | UTS2-induced vascular SMC proliferation via RHOA-ROCK2 (Human) |
| #48 | `gomodel:6ab067da00006447` | development | ATG2A transfers phosphatidylinositol to ATG9A vesicles for PI3P synthesis in autophagosome assembly (Human) |

## Legacy `gcdb-` recoveries (go-cam-drop-box#29)

Merged legacy YAML-only submissions rebuilt on noctua-dev from the merged YAML,
stored, and re-submitted as YAML + TTL pairs under their dev ids. Content was
verified identical to the merged YAML (activities, terms, causal edges,
molecules, evidence). Promoted in the batch of 2026-10-08 above.

| old drop-box id | drop-box PR | new id | title |
|---|---|---|---|
| `gcdb-8d5b70a7-e685-42d8-b89b-b024b5ac57ec` | #18 | `gomodel:6a6ba88c00001800` | IL-36R defense response to Gram-negative bacterium (Mouse) (existing dev model, refactor replayed) |
| `gcdb-6a3a464f-87d2-40ef-9aae-a0cb309bda69` | #18 | `gomodel:6ab067da00001588` | Interleukin-36 beta (IL36B) receptor signaling via IL1RL2-IL1RAP (Human) |
| `gcdb-8478a448-eed7-44b4-9a9c-fb2100c27b9b` | #19 | `gomodel:6ab067da00001660` | Intermembrane phospholipid transfer at ER-PM via VPS13A-XK (Human) |
| `gcdb-056b6868-99d6-4e80-b88a-cd3b5666929e` | #5 | `gomodel:6ab067da00001694` | DYRK1A phosphorylates CDKL5 to promote its nuclear export and cytoplasmic kinase activity (Hsap, ISS from mouse; PMID:27840050, PMID:30266824) |
| `gcdb-bafd07d4-3d55-41cd-a9bf-1fb1fb5470e9` | #4 | `gomodel:6ab067da00001712` | DYRK1A phosphorylates CDKL5 on Ser-308 to promote its cytoplasmic localization (Mmus, PMID:27840050) |
