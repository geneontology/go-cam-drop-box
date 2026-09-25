"""TTL-side checks for a drop-box submission.

A submission is a PAIR: models/<id>.yaml (gocam-py YAML) and models/<id>.ttl (the
model's native minerva Turtle, exported from noctua-dev). Both carry the same
model id. The YAML is validated by the existing gates; this module checks the TTL:

  5. companion TTL: exists, parses, has exactly one owl:Ontology whose IRI is the
     YAML id, and its lego:modelstate equals the YAML status.
  6. YAML <-> TTL agreement: every activity, term, context chain, molecule link,
     causal edge and evidence item in the YAML is present in the TTL, and the TTL
     has no model-level fact the YAML lacks. (Evidence `with` is compared as a
     subset: gocam-py currently keeps only one of several `with` annotations.)
  7. noctua-models SPARQL QC battery: every query in validation/sparql/*.rq is run
     over the TTL; any returned row is a failure. The queries are fetched from
     geneontology/noctua-models at CI time (see the workflow), so the two repos
     cannot drift.
"""
from __future__ import annotations

import glob
import json
import os
from pathlib import Path

from rdflib import RDF, RDFS, Graph, Literal, Namespace, URIRef

HERE = Path(__file__).resolve().parent
OWL = Namespace("http://www.w3.org/2002/07/owl#")
DC = Namespace("http://purl.org/dc/elements/1.1/")
LEGO = Namespace("http://geneontology.org/lego/")
OBO = "http://purl.obolibrary.org/obo/"
GOMODEL = "http://model.geneontology.org/"

REL = {
    "part_of": OBO + "BFO_0000050",
    "occurs_in": OBO + "BFO_0000066",
    "enabled_by": OBO + "RO_0002333",
    "has_part": OBO + "BFO_0000051",
    "happens_during": OBO + "RO_0002092",
    "located_in": OBO + "RO_0001025",
}
# minerva stores some molecule links molecule->MF; gocam-py folds them into the
# activity as the inverse. Normalise TTL facts to the activity-side form.
INVERSE = {
    OBO + "RO_0002352": OBO + "RO_0002233",
    OBO + "RO_0002353": OBO + "RO_0002234",
    OBO + "RO_0012005": OBO + "RO_0012001",
    OBO + "RO_0012006": OBO + "RO_0012002",
}


def _load_ctx() -> dict[str, str]:
    ctx: dict[str, str] = {}
    for name in ("obo_context.jsonld", "go_context.jsonld"):
        with open(HERE / "curie" / name) as fh:
            for k, v in json.load(fh)["@context"].items():
                if isinstance(v, dict):
                    v = v.get("@id")
                if isinstance(v, str):
                    ctx[k] = v
    return ctx


CTX = _load_ctx()


def expand(curie: str) -> str:
    p, _, local = curie.partition(":")
    return CTX[p] + local if p in CTX else curie


def contract(iri: str) -> str:
    iri = str(iri)
    for p, base in sorted(CTX.items(), key=lambda kv: -len(kv[1])):
        if iri.startswith(base):
            return f"{p}:{iri[len(base):]}"
    return iri


def _aslist(x):
    return x if isinstance(x, list) else ([] if x is None else [x])


class TtlModel:
    def __init__(self, path: Path, model_local: str):
        self.g = Graph()
        self.g.parse(str(path), format="turtle")
        self.model = URIRef(GOMODEL + model_local)
        self.prefix = GOMODEL + model_local + "/"
        self.ind_types: dict[URIRef, set[str]] = {}
        for s, o in self.g.subject_objects(RDF.type):
            if o != OWL.NamedIndividual and str(s).startswith(self.prefix):
                self.ind_types.setdefault(s, set()).add(contract(o))
        self.facts: dict[tuple, dict] = {}
        for s, p, o in self.g:
            if s in self.ind_types and o in self.ind_types and p != RDF.type:
                self.facts[(s, str(p), o)] = {"evidence": set(), "contributor": set(), "date": set()}
        for ax in self.g.subjects(RDF.type, OWL.Axiom):
            key = (self.g.value(ax, OWL.annotatedSource), str(self.g.value(ax, OWL.annotatedProperty)), self.g.value(ax, OWL.annotatedTarget))
            if key not in self.facts:
                continue
            for ev in self.g.objects(ax, LEGO.evidence):
                eco = next(iter(self.ind_types.get(ev, {"?"})))
                src = str(self.g.value(ev, DC.source) or "")
                withs = frozenset(w.strip() for lit in self.g.objects(ev, LEGO["evidence-with"]) for w in str(lit).split("|") if w.strip())
                self.facts[key]["evidence"].add((eco, src, withs))
            self.facts[key]["contributor"] |= {str(c) for c in self.g.objects(ax, DC.contributor)}
            self.facts[key]["date"] |= {str(d) for d in self.g.objects(ax, DC.date)}
        for (s, p, o) in list(self.facts):
            if p in INVERSE:
                self.facts[(o, INVERSE[p], s)] = self.facts.pop((s, p, o))

    def ontologies(self) -> list[URIRef]:
        return list(self.g.subjects(RDF.type, OWL.Ontology))

    def state(self) -> list[str]:
        return [str(x) for x in self.g.objects(self.model, LEGO.modelstate)]


def _ev_set(assoc) -> set:
    out = set()
    for e in _aslist((assoc or {}).get("evidence")):
        out.add((e.get("term"), e.get("reference") or "", frozenset(e.get("with_objects") or [])))
    return out


def check_companion(yaml_doc: dict, ttl_path: Path) -> tuple[list[str], list[str], TtlModel | None]:
    """Gate 5. Returns (errors, warnings, parsed model or None)."""
    errors: list[str] = []
    warnings: list[str] = []
    if not ttl_path.exists():
        return [f"companion TTL missing: {ttl_path.name} (every submission is a YAML + TTL pair with the same id)"], warnings, None
    model_id = str(yaml_doc.get("id", ""))
    local = model_id.split(":", 1)[1] if ":" in model_id else model_id
    try:
        t = TtlModel(ttl_path, local)
    except Exception as e:  # noqa: BLE001
        return [f"companion TTL does not parse as Turtle: {e}"], warnings, None
    onts = t.ontologies()
    if len(onts) != 1:
        errors.append(f"TTL must declare exactly one owl:Ontology (found {len(onts)})")
    elif onts[0] != t.model:
        errors.append(f"TTL ontology IRI {onts[0]} != YAML id {model_id} (expected {t.model})")
    st = t.state()
    ystatus = str(yaml_doc.get("status") or "")
    if st != [ystatus]:
        errors.append(f"TTL lego:modelstate {st} != YAML status {ystatus!r} (set the state on noctua-dev, then re-export both files)")
    return errors, warnings, t


def check_agreement(yaml_doc: dict, t: TtlModel) -> tuple[list[str], list[str]]:
    """Gate 6: YAML and TTL describe the same model."""
    problems: list[str] = []
    notes: list[str] = []
    expected: set[tuple] = set()
    U = lambda local: URIRef(t.prefix + local)  # noqa: E731
    local = lambda yid: str(yid).rsplit("/", 1)[1]  # noqa: E731

    def expect_fact(s_iri, rel, o_iri, assoc, label):
        key = (s_iri, REL[rel] if rel in REL else expand(rel), o_iri)
        expected.add(key)
        if key not in t.facts:
            problems.append(f"fact in YAML but not in TTL: {label}")
            return
        f = t.facts[key]
        ye, te = _ev_set(assoc), set(f["evidence"])
        if len(ye) != len(te):
            problems.append(f"evidence count differs on {label}: yaml={len(ye)} ttl={len(te)}")
            return
        unmatched = set(te)
        for (eco, ref, wy) in ye:
            hit = next((x for x in unmatched if x[0] == eco and x[1] == ref and wy <= x[2]), None)
            if hit is None:
                problems.append(f"evidence differs on {label}: yaml={(eco, ref, sorted(wy))} ttl={sorted((x[0], x[1], sorted(x[2])) for x in te)}")
            else:
                unmatched.discard(hit)
                if wy < hit[2]:
                    notes.append(f"YAML kept only {sorted(wy)} of TTL with-values {sorted(hit[2])} on {label} (gocam-py limitation)")

    def expect_type(iri, term, label) -> bool:
        if iri not in t.ind_types:
            problems.append(f"individual in YAML but not in TTL: {label} ({iri})")
            return False
        if term not in t.ind_types[iri]:
            problems.append(f"type differs on {label}: yaml={term} ttl={sorted(t.ind_types[iri])}")
            return False
        return True

    def follow(subj, rel, assoc, label):
        if not assoc:
            return None
        cands = [o for (s, p, o) in t.facts if s == subj and p == REL[rel] and assoc.get("term") in t.ind_types.get(o, set())]
        if not cands:
            problems.append(f"fact in YAML but not in TTL: {label} {rel} {assoc.get('term')}")
            return None
        o = cands[0]
        expect_fact(subj, rel, o, assoc, f"{label} {rel} {assoc.get('term')}")
        for nk in ("part_of", "happens_during"):
            sub = assoc.get(nk)
            for sb in _aslist(sub):
                follow(o, nk, sb, f"{label}>{assoc.get('term')}")
        return o

    mols = {m["id"]: m for m in (yaml_doc.get("molecules") or [])}
    for a in yaml_doc.get("activities") or []:
        aid = local(a["id"])
        mf = U(aid)
        lab = f"activity {aid}"
        if not expect_type(mf, (a.get("molecular_function") or {}).get("term"), lab + " MF"):
            continue
        eb = a.get("enabled_by") or {}
        gp = follow(mf, "enabled_by", eb, lab)
        if gp is not None:
            for hp in _aslist(eb.get("has_part")):
                m = follow(gp, "has_part", hp, lab + " complex")
                if m is not None:
                    for po in _aslist(hp.get("part_of")):
                        follow(m, "part_of", po, lab + " member")
            for po in _aslist(eb.get("part_of")):
                follow(gp, "part_of", po, lab + " gene product")
        follow(mf, "part_of", a.get("part_of"), lab)
        follow(mf, "occurs_in", a.get("occurs_in"), lab)
        follow(mf, "happens_during", a.get("happens_during"), lab)
        for ma in _aslist(a.get("molecular_associations")):
            mid = local(ma["molecule"])
            mi = U(mid)
            mnode = mols.get(ma["molecule"])
            if mnode and expect_type(mi, mnode["term"], f"{lab} molecule {mid}"):
                expect_fact(mf, ma["predicate"], mi, ma, f"{lab} {ma['predicate']} {mnode['term']}")
                follow(mi, "located_in", mnode.get("located_in"), f"{lab} molecule {mid}")
        for ca in _aslist(a.get("causal_associations")):
            expect_fact(mf, ca["predicate"], U(local(ca["downstream_activity"])), ca, f"{lab} {ca['predicate']} activity {local(ca['downstream_activity'])}")
    for (s, p, o) in t.facts:
        if (s, p, o) not in expected:
            problems.append(f"fact in TTL but not in YAML: {str(s).rsplit('/', 1)[1]} {contract(p)} {str(o).rsplit('/', 1)[1]} [{sorted(t.ind_types[s])} -> {sorted(t.ind_types[o])}]")
    title = str(t.g.value(t.model, DC.title) or "")
    if (yaml_doc.get("title") or "").strip() != title.strip():
        problems.append(f"title differs: yaml={yaml_doc.get('title')!r} ttl={title!r}")
    ttl_comments = {str(c) for c in t.g.objects(t.model, RDFS.comment)}
    yaml_comments = set(yaml_doc.get("comments") or [])
    if yaml_comments != ttl_comments:
        only_y = sorted(yaml_comments - ttl_comments)
        only_t = sorted(ttl_comments - yaml_comments)
        problems.append(
            f"model comments differ: {len(only_y)} only in YAML, {len(only_t)} only in TTL "
            "(comments are model annotations; add them on noctua-dev with `barista update-metadata --add --comment ...`, then re-export both)"
        )
    taxon = t.g.value(t.model, URIRef("https://w3id.org/biolink/vocab/in_taxon"))
    if taxon is not None and yaml_doc.get("taxon") != contract(taxon):
        problems.append(f"taxon differs: yaml={yaml_doc.get('taxon')} ttl={contract(taxon)}")
    return problems, notes


def run_sparql_battery(t: TtlModel, query_dir: Path) -> tuple[list[str], list[str]]:
    """Gate 7: noctua-models QC queries; any row is a failure."""
    errors: list[str] = []
    warnings: list[str] = []
    queries = sorted(glob.glob(str(query_dir / "*.rq")))
    if not queries:
        warnings.append(f"no SPARQL queries found in {query_dir} (fetch them from geneontology/noctua-models/sparql first); battery skipped")
        return errors, warnings
    for q in queries:
        with open(q) as fh:
            text = fh.read()
        try:
            rows = list(t.g.query(text))
        except Exception as e:  # noqa: BLE001
            errors.append(f"{os.path.basename(q)}: query failed to run: {e}")
            continue
        if rows:
            shown = "; ".join(", ".join(str(v) for v in r) for r in rows[:5])
            more = f" (+{len(rows) - 5} more)" if len(rows) > 5 else ""
            errors.append(f"{os.path.basename(q)}: {len(rows)} row(s): {shown}{more}")
    return errors, warnings
