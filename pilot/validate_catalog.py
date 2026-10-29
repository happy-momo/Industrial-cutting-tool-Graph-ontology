"""Validate a pilot catalog: entities pass validate_entity (+ concept_ref semantics),
and relationships are consistent with field-registry definitions and internal ids."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import yaml

from src.validator import validate_entity

ROOT = Path(__file__).resolve().parents[1]


def load_mapping():
    reg = yaml.safe_load((ROOT / "contract/field-registry.yaml").read_text(encoding="utf-8"))
    mapping = yaml.safe_load((ROOT / "mappings/ontology-neo4j.yaml").read_text(encoding="utf-8"))
    return reg, mapping


def _parent_chain(reg: dict) -> dict[str, set[str]]:
    """For each class, the set of its ancestor class names (Insert -> {Tool, Entity})."""
    chain: dict[str, set[str]] = defaultdict(set)
    for cls, info in reg["classes"].items():
        p = info.get("parent")
        while p and p != "null":
            chain[cls].add(p)
            chain[cls] |= chain.get(p, set())
            p = reg["classes"].get(p, {}).get("parent")
    return dict(chain)


def _compatible(decl_cls: str, ent_type: str, chain: dict[str, set[str]]) -> bool:
    """The relationship's declared source/target class must match the entity's
    concrete type, accepting subclass (an Insert entity satisfies a declared Tool)."""
    return decl_cls == ent_type or decl_cls in chain.get(ent_type, set())


def validate_catalog(data: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    reg, _ = load_mapping()
    rel_defs = {r["name"]: r for r in reg.get("relationships", [])}
    chain = _parent_chain(reg)

    # --- entities ---
    for ent in data.get("entities", []):
        cls = ent.get("type")
        if cls not in reg["classes"]:
            errors.append(f"unknown entity type {cls!r}")
            continue
        payload = {k: v for k, v in ent.items() if k != "type"}
        errors += [f"{cls}:{ent.get('id')}: {m}" for m in validate_entity(cls, payload)]

    # --- relationships ---
    by_id = {e.get("id"): e.get("type") for e in data.get("entities", [])}

    for rel in data.get("relationships", []):
        name = rel.get("name")
        if name not in rel_defs:
            errors.append(f"relationship '{name}' is not declared in field-registry")
            continue
        d = rel_defs[name]
        s_ent = by_id.get(rel.get("source_id"))
        t_ent = by_id.get(rel.get("target_id"))
        if not s_ent:
            errors.append(f"relationship '{name}' source id {rel.get('source_id')} not present")
        elif not _compatible(d["source"], s_ent, chain):
            errors.append(f"relationship '{name}' source {s_ent} is not a {d['source']}")
        if not t_ent:
            errors.append(f"relationship '{name}' target id {rel.get('target_id')} not present")
        elif not _compatible(d["target"], t_ent, chain):
            errors.append(f"relationship '{name}' target {t_ent} is not a {d['target']}")
    return (not errors), errors