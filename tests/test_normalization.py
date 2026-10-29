"""resolve_skos normalization: noisy real-world input resolves deterministically,
still returning ALL hits (no guessing)."""
from src import resolve_skos
from src import namespaces

T = namespaces.VOCAB_BASE + "tool#"
P = namespaces.VOCAB_BASE + "process#"


def test_normalize_collapses_whitespace_and_case():
    assert resolve_skos.normalize("  ISO车削  ") == resolve_skos.normalize("ISO车削")
    assert resolve_skos.normalize("Milling tools") == resolve_skos.normalize(" milling TOOLS ")


def test_resolve_trailing_and_leading_space():
    assert resolve_skos.resolve("ISO车削 ", "process") == [P + "turning"]
    assert resolve_skos.resolve(" 整体铣刀", "tool") == [T + "solid-milling"]


def test_resolve_full_width_space():
    assert resolve_skos.resolve("ISO　车削", "process") == [P + "turning"]


def test_resolve_ascii_casefold():
    assert resolve_skos.resolve("iso车削", "process") == [P + "turning"]
    assert resolve_skos.resolve("milling tools", "tool") == [T + "milling"]


def test_normalize_folds_traditional_to_simplified():
    assert resolve_skos.resolve("整體銑刀", "tool") == [T + "solid-milling"]


def test_ambiguity_still_surfaced_not_guessed():
    # 钻削 is ambiguous across milling / hole-making; noisy form must STILL return both
    hits = resolve_skos.resolve("钻削 ", "process")
    assert {P + "milling", P + "hole-making"} <= set(hits)


def test_exact_behavior_unchanged_exact_first():
    assert resolve_skos.resolve("ISO车削", "process") == [P + "turning"]


def test_resolve_tokens_subset_label():
    # 整体硬质合金铣刀 is an altLabel of solid-milling; a subset query returns it
    hits = resolve_skos.resolve_tokens("硬质合金铣刀", "tool")
    assert T + "solid-milling" in hits


def test_resolve_tokens_never_guesses_multiple_returned():
    hits = resolve_skos.resolve_tokens("钻削", "process")
    assert {P + "milling", P + "hole-making"} <= set(hits)


def test_resolve_tokens_empty_when_no_label_contains():
    assert resolve_skos.resolve_tokens("不存在的词XYZ", "tool") == []