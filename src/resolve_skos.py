"""Vocabulary-aware resolution and normalization layer.

Goal: turn the controlled SKOS taxonomies into an executable value-space for the
closed-world classes (ToolType / ProcessMethod / MaterialClass ...). Manufacturer
data enters as free text ("ISO车削", "端铣刀", "整体硬质合金铣刀"); this module
resolves any canonical label or alias back to the stable concept URI, which is the
anchor that alignment/standardization hangs on.

Design constraints:
- The application validator (src/validator.py) is a lightweight core that depends
  only on jsonschema. To keep it importable without rdflib, rdflib is imported
  *lazily* (inside load_taxonomy) and the parsed index is cached module-locally.
- A term that maps to several concepts returns all of them; the caller decides how
  to treat ambiguity (often: "cannot auto-align, route to human/exact match").
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOCAB = ROOT / "vocabulary"

# --------------------------------------------------------------------------
# Index
# --------------------------------------------------------------------------
_cache: dict | None = None


def load_taxonomy() -> dict:
    """Parse every vocabulary/*.ttl into scheme -> concept map. Cached.

    Returned shape (cache):
        {
          <scheme_stem>: "tool",
          <concept_uri>: {
              "scheme": "tool",
              "prefLabels": [ "铣削刀具@zh", ... ],
              "altLabels":   [ "整体硬质合金铣刀@zh", ... ],
              "contains": { <label>: True, ... }   # prefLabel + altLabel strings
          }
        }
    """
    global _cache
    if _cache is not None:
        return _cache
    import rdflib  # lazy: keep validator importable without rdflib
    from rdflib.namespace import SKOS
    from rdflib import RDF

    index: dict = {}
    for path in sorted(VOCAB.glob("*.ttl")):
        stem = path.stem  # e.g. "tool", "process", "material"
        g = rdflib.Graph()
        try:
            g.parse(path, format="turtle")
        except Exception:
            continue  # malformed files are caught by scripts/validate_skos
        for concept in g.subjects(RDF.type, SKOS.Concept):
            if (concept, SKOS.inScheme, None) not in g:
                continue  # a concept not anchored to a scheme is not resolvable
            entry = index.setdefault(
                str(concept),
                {"scheme": stem, "prefLabels": [], "altLabels": [], "contains": {}},
            )
            for label in g.objects(concept, SKOS.prefLabel):
                entry["prefLabels"].append(str(label))
                entry["contains"][str(label)] = True
            for label in g.objects(concept, SKOS.altLabel):
                entry["altLabels"].append(str(label))
                entry["contains"][str(label)] = True
    # Build a flat term -> set of concept URIs lookup across all schemes.
    lookup: dict[str, set[str]] = {}
    for uri, entry in index.items():
        if uri in ("__term__",):
            continue
        for term in entry["contains"]:
            lookup.setdefault(term, set()).add(uri)
    index["__lookup__"] = lookup
    # Normalized-term secondary index (catches whitespace/case/full-width/variant noise).
    norm_lookup: dict[str, set[str]] = {}
    for label, uris in lookup.items():
        norm_lookup.setdefault(normalize(label), set()).update(uris)
    index["__norm_lookup__"] = norm_lookup
    _cache = index
    return _cache


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def concept_exists(uri: str) -> bool:
    """True if `uri` is a known SKOS concept in any loaded vocabulary."""
    return uri in load_taxonomy()


def concept_in_scheme(uri: str, scheme_stem: str) -> bool:
    """True if `uri` is a concept that belongs to the given vocabulary file."""
    entry = load_taxonomy().get(uri)
    return bool(entry and entry["scheme"] == scheme_stem)


# --------------------------------------------------------------------------
# Normalization
# --------------------------------------------------------------------------
# Minimal explicit traditional->simplified fold for characters that appear in the
# vocabulary labels / aliases. A deterministic char table, NOT a full converter,
# and never a guess: it only widens the exact-match surface, never chooses a hit.
_CJK_TRAD_TO_SIMP = {
    "體": "体", "銑": "铣", "車": "车", "質": "质", "鋼": "钢", "鐵": "铁",
    "類": "类", "屬": "属", "號": "号", "數": "数", "軸": "轴", "齒": "齿",
    "鎢": "钨", "鈷": "钴", "鈦": "钛", "專": "专", "導": "导", "潤": "润",
}


def _fold_cjk(text: str) -> str:
    return "".join(_CJK_TRAD_TO_SIMP.get(ch, ch) for ch in text)


def _strip_lang_tag(term: str) -> str:
    return re.sub(r"@[A-Za-z]{2,}(?:-[A-Za-z]{2,})?$", "", term)


def normalize(term: str) -> str:
    """Canonical, collision-preserving key for a term or label.

    Strips a trailing language tag, NFKC-folds (full-width -> half-width, incl. the
    ideographic space), folds a small explicit traditional->simplified table, ASCII
    case-folds, then drops ALL whitespace. Deterministic; never disambiguating.
    """
    t = _strip_lang_tag(term)
    t = unicodedata.normalize("NFKC", t)
    t = _fold_cjk(t)
    t = t.casefold()
    return re.sub(r"[\s 　]+", "", t)


def schemes() -> list[str]:
    """Vocabulary file stems that define at least one scheme."""
    return sorted({e["scheme"] for u, e in load_taxonomy().items() if not u.startswith("__")})


def resolve(term: str, scheme_stem: str | None = None) -> list[str]:
    """Return every concept URI whose prefLabel or altLabel equals `term`
    (exact match first); if none, every concept whose normalized label matches via
    `normalize()`. ALWAYS returns all hits; ambiguity is surfaced, never guessed.

    - When `scheme_stem` is given, only concepts in that vocabulary are returned.
    - Ambiguity is surfaced by construction: multiple entries mean the term is not
      globally unique and the caller decides (return None to force a resolve).
    """
    idx = load_taxonomy()
    hits = sorted(idx["__lookup__"].get(term, ()))
    if not hits:
        hits = sorted(idx["__norm_lookup__"].get(normalize(term), ()))
    if scheme_stem:
        hits = [u for u in hits if idx.get(u, {}).get("scheme") == scheme_stem]
    return hits


def resolve_tokens(term: str, scheme_stem: str | None = None) -> list[str]:
    """Concepts whose normalized labels contain every normalized token of `term`.

    Token recall, NOT a guess: ALL matching concepts are returned (ambiguity is
    surfaced). Returns [] when no label contains all tokens.
    """
    idx = load_taxonomy()
    tokens = [normalize(t) for t in re.split(r"[\s\-_/、,，]+", term) if t]
    if not tokens:
        return []
    norm_labels = {uri: [normalize(l) for l in entry["contains"]]
                    for uri, entry in idx.items() if not uri.startswith("__")}
    hits = {uri for uri, labs in norm_labels.items()
            if any(all(tok in lab for tok in tokens) for lab in labs)}
    out = sorted(hits)
    if scheme_stem:
        out = [u for u in out if idx.get(u, {}).get("scheme") == scheme_stem]
    return out


def ambiguous_terms() -> list[str]:
    """Labels (prefLabel or altLabel) that resolve to more than one concept.

    These form the *human-review surface* of automatic normalization: the term is
    shared across branches (e.g. "硬质合金" names both an insert substrate and a
    workpiece N-branch alloy), so any auto-alignment must either scope to a scheme
    or route to an authoritative tie-break. Advisory, not an error.
    """
    return sorted(t for t, hits in load_taxonomy()["__lookup__"].items() if len(hits) > 1)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def _report() -> str:
    lines = ["Semantic alignment ledger (controlled vocabulary -> manufacturer aliases):"]
    for stem in schemes():
        lines.append(f"\n== {stem} ==")
        for uri in sorted(u for u in load_taxonomy() if not u.startswith("__") and load_taxonomy()[u]["scheme"] == stem):
            e = load_taxonomy()[uri]
            if e["altLabels"]:
                lines.append(f"  {uri}\n    pref: {', '.join(e['prefLabels'])} | aliases: {', '.join(e['altLabels'])}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if argv and argv[0] == "--report":
        print(_report())
        return 0
    if argv and argv[0] in ("--term", "-t") and len(argv) >= 2:
        term = argv[1]
        hits = resolve(term)
        if not hits:
            print(f"No concept resolves for term '{term}'")
            return 1
        for u in hits:
            print(u)
        return 0
    print("usage: python -m src.resolve_skos --term <label> | --report")
    return 0 if argv == ["--help"] else 2


if __name__ == "__main__":
    raise SystemExit(main())