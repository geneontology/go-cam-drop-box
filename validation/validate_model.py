#!/usr/bin/env python3
"""Validate a submitted go-cam-drop-box model against the four merge gates:

  1. identifier & filename   (gomodel:<id>, file matches id; the id is the noctua-dev
                              minted id, e.g. gomodel:6ab067da00000569; legacy
                              gomodel:gcdb-<UUID> ids are still accepted for old files)
  2. LinkML schema conformance   (linkml-validate against the pinned gocam schema)
  3. "true GO-CAM" semantics   (modular, from validation/criteria.yaml)
  4. ontology-term validity   (oaklib: terms exist and are not obsolete)
  5. companion TTL            (models/<id>.ttl exists, parses, same id, same state)
  6. YAML <-> TTL agreement   (same activities, terms, edges, evidence)
  7. noctua-models SPARQL QC battery over the TTL (validation/sparql/*.rq)

Gates 5-7 apply to files under models/ (see validation/ttl_checks.py).

Usage:
    python validation/validate_model.py models/<id>.yaml [more.yaml ...]

Exit code 0 iff every gate passes for every file. Each gate is independent so
the bar can be tightened/loosened via criteria.yaml without touching this file.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

HERE = Path(__file__).resolve().parent
CRITERIA_PATH = HERE / "criteria.yaml"

# Primary form: the noctua-dev minted id (16 lowercase hex). Legacy form: gcdb-<UUID>
# (client-minted staging ids used before 2026-09-24; kept so old files still validate).
ID_RE = re.compile(r"^gomodel:(?P<local>(?P<hex>[0-9a-f]{16})|gcdb-(?P<uuid>[0-9a-fA-F-]{36}))$")
CURIE_RE = re.compile(r"^(?P<prefix>[A-Za-z][A-Za-z0-9]*):[^\s]+$")


class GateResult:
    def __init__(self, name: str):
        self.name = name
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def load_criteria() -> dict:
    with open(CRITERIA_PATH) as fh:
        return yaml.safe_load(fh)


# --- Gate 1: identifier & filename -----------------------------------------
def gate_identifier(path: Path, doc: dict) -> GateResult:
    r = GateResult("identifier & filename")
    model_id = doc.get("id")
    if not model_id:
        r.error("model has no top-level `id`")
        return r
    m = ID_RE.match(str(model_id))
    if not m:
        r.error(
            f"id {model_id!r} must be the model's noctua-dev id, 'gomodel:<16 hex>' "
            "(e.g. gomodel:6ab067da00000569); legacy 'gomodel:gcdb-<UUID>' is accepted for old files"
        )
        return r
    if m.group("uuid"):
        try:
            uuid.UUID(m.group("uuid"))
        except ValueError:
            r.error(f"id {model_id!r} does not contain a valid UUID")
        r.warn("legacy gcdb- id: new submissions use the noctua-dev id shared by the YAML and its TTL")
    expected_stem = m.group("local")
    if path.stem != expected_stem:
        r.error(
            f"filename stem {path.stem!r} must equal the id local part "
            f"{expected_stem!r} (rename to {expected_stem}.yaml). "
            "Matching filename==id is what guarantees uniqueness within models/."
        )
    return r


# --- Gate 2: LinkML schema conformance -------------------------------------
def _find_gocam_schema() -> Path | None:
    try:
        import gocam
    except ImportError:
        return None
    schema = Path(gocam.__file__).resolve().parent / "schema" / "gocam.yaml"
    return schema if schema.exists() else None


def gate_linkml(path: Path) -> GateResult:
    r = GateResult("LinkML schema conformance")
    schema = _find_gocam_schema()
    if schema is None:
        r.error(
            "could not locate the gocam LinkML schema (is `gocam` installed?); "
            "cannot check schema conformance"
        )
        return r
    proc = subprocess.run(
        ["linkml-validate", "-s", str(schema), "--target-class", "Model", str(path)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        detail = (proc.stdout + proc.stderr).strip()
        r.error(f"linkml-validate failed:\n{detail}")
    return r


# --- Gate 3: "true GO-CAM" semantics ---------------------------------------
def gate_true_gocam(doc: dict, criteria: dict) -> GateResult:
    r = GateResult("true GO-CAM semantics")
    try:
        from gocam.datamodel import Model
        from gocam.utils import all_evidence, model_to_digraph
    except ImportError as e:
        r.error(f"gocam not importable ({e}); cannot check semantics")
        return r
    try:
        model = Model.model_validate(doc)
    except Exception as e:  # pydantic.ValidationError etc.
        r.error(f"model does not load as a gocam Model: {e}")
        return r

    # status
    allowed = set(criteria.get("allowed_statuses", []))
    status = getattr(model.status, "value", model.status)
    if allowed and status not in allowed:
        r.error(f"status {status!r} not in allowed_statuses {sorted(allowed)}")

    graph = model_to_digraph(model)

    if criteria.get("require_causal_edge"):
        if graph.number_of_edges() < 1:
            r.error("no causal relationship between activities (require_causal_edge)")

    if criteria.get("require_no_orphan_activity"):
        orphans = [
            a.id
            for a in (model.activities or [])
            if a.id not in graph or graph.degree(a.id) == 0
        ]
        if orphans:
            r.error(f"disconnected activities (degree 0): {orphans}")

    if criteria.get("require_evidence"):
        if next(all_evidence(model), None) is None:
            r.error("no evidence found anywhere in the model (require_evidence)")

    return r


# --- Gate 4: ontology-term validity ----------------------------------------
def _collect_curies(node, prefixes: set[str], out: set[str]) -> None:
    if isinstance(node, dict):
        for v in node.values():
            _collect_curies(v, prefixes, out)
    elif isinstance(node, list):
        for v in node:
            _collect_curies(v, prefixes, out)
    elif isinstance(node, str):
        m = CURIE_RE.match(node)
        if m and m.group("prefix") in prefixes:
            out.add(node)


def gate_terms(doc: dict, criteria: dict) -> GateResult:
    r = GateResult("ontology-term validity")
    prefixes = set(criteria.get("ontology_prefixes", []))
    if not prefixes:
        return r
    curies: set[str] = set()
    _collect_curies(doc, prefixes, curies)
    if not curies:
        return r
    try:
        from oaklib import get_adapter
    except ImportError as e:
        r.error(f"oaklib not importable ({e}); cannot check terms")
        return r

    by_prefix: dict[str, list[str]] = {}
    for c in curies:
        by_prefix.setdefault(c.split(":", 1)[0], []).append(c)

    for prefix, terms in sorted(by_prefix.items()):
        try:
            adapter = get_adapter(f"sqlite:obo:{prefix.lower()}")
        except Exception as e:
            r.warn(f"no ontology adapter for prefix {prefix!r} ({e}); skipped {terms}")
            continue
        try:
            obsolete = set(adapter.obsoletes())
        except Exception as e:
            r.warn(f"could not enumerate obsoletes for {prefix} ({e})")
            obsolete = set()
        for c in sorted(set(terms)):
            if adapter.label(c) is None:
                r.error(f"term does not exist: {c}")
            elif c in obsolete:
                r.error(f"term is obsolete: {c}")
    return r


# --- Gates 5-7: the companion TTL -------------------------------------------
def gates_ttl(path: Path, doc: dict, criteria: dict) -> list[GateResult]:
    from ttl_checks import check_agreement, check_companion, run_sparql_battery

    g5 = GateResult("companion TTL (exists, parses, same id and state)")
    g6 = GateResult("YAML <-> TTL agreement")
    g7 = GateResult("noctua-models SPARQL QC battery (TTL)")
    errors, warnings, t = check_companion(doc, path.with_suffix(".ttl"))
    for e in errors:
        g5.error(e)
    for w in warnings:
        g5.warn(w)
    if t is None:
        g6.error("skipped: no usable companion TTL")
        g7.error("skipped: no usable companion TTL")
        return [g5, g6, g7]
    problems, notes = check_agreement(doc, t)
    for p in problems:
        g6.error(p)
    for n in notes:
        g6.warn(n)
    qdir = HERE / criteria.get("sparql_query_dir", "sparql")
    errors, warnings = run_sparql_battery(t, qdir)
    for e in errors:
        g7.error(e)
    for w in warnings:
        if criteria.get("sparql_required", True):
            g7.error(w)
        else:
            g7.warn(w)
    return [g5, g6, g7]


# --- driver ----------------------------------------------------------------
def validate_file(path: Path, criteria: dict) -> bool:
    print(f"\n=== {path} ===")
    try:
        with open(path) as fh:
            doc = yaml.safe_load(fh)
    except Exception as e:
        print(f"  FAIL  could not parse YAML: {e}")
        return False
    if not isinstance(doc, dict):
        print("  FAIL  file is not a single YAML mapping (a GO-CAM model)")
        return False

    gates = [
        gate_identifier(path, doc),
        gate_linkml(path),
        gate_true_gocam(doc, criteria),
        gate_terms(doc, criteria),
    ]
    is_legacy = str(doc.get("id", "")).startswith("gomodel:gcdb-")
    has_ttl = path.with_suffix(".ttl").exists()
    # Files added by this PR (CI passes them in NEW_FILES, one path per line).
    # A brand-new legacy-style submission is not grandfathered: it almost
    # certainly came from a session still running the pre-2026-09-24 save skill.
    new_files = {p for p in os.environ.get("NEW_FILES", "").split() if p}
    is_new = str(path) in new_files or path.as_posix() in new_files
    if is_legacy and is_new and path.parent.name == "models":
        g = GateResult("companion TTL")
        g.error(
            "new submission uses the retired gcdb- id form and has no TTL. Since 2026-09-24 a "
            "submission is <noctua-dev id>.yaml + <noctua-dev id>.ttl exported from the stored "
            "dev model. This usually means the save ran in a Claude session started before the "
            "skill update: exit that session, start `claude` again, and ask it to save the model "
            "to the drop box again."
        )
        gates.append(g)
    elif has_ttl or (criteria.get("require_companion_ttl") and path.parent.name == "models" and not is_legacy):
        gates.extend(gates_ttl(path, doc, criteria))
    elif is_legacy and path.parent.name == "models":
        g = GateResult("companion TTL")
        g.warn("legacy gcdb- submission without a TTL (pre-2026-09-24); cannot be promoted until re-exported from noctua-dev as an id-matched YAML + TTL pair")
        gates.append(g)
    all_ok = True
    for g in gates:
        status = "PASS" if g.ok else "FAIL"
        print(f"  [{status}] {g.name}")
        for w in g.warnings:
            print(f"         warn: {w}")
        for e in g.errors:
            print(f"         - {e}")
        all_ok = all_ok and g.ok
    return all_ok


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate go-cam-drop-box model files.")
    ap.add_argument("models", nargs="+", help="model YAML file(s) to validate (the companion .ttl is found by name)")
    args = ap.parse_args()
    criteria = load_criteria()
    results = [validate_file(Path(p), criteria) for p in args.models]
    ok = all(results)
    print(f"\n{'ALL PASSED' if ok else 'VALIDATION FAILED'} "
          f"({sum(results)}/{len(results)} files passed)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
