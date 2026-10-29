"""Single source of truth for the project namespace.

Placeholder value (example.org) is retained until a persistent, project-owned
namespace is established. To swap: change ON_BASE / VOCAB_BASE here, regenerate
shapes + schemas, and re-run the full regression — every artifact derives from this.
"""
from rdflib import Namespace

# Ontology class / object-property / datatype-property IRIs (on fragment).
ON_BASE = "https://example.org/cutting-tool/ontology#"
ON = Namespace(ON_BASE)

# Vocabulary concept IRIs: VOCAB_BASE + <scheme-stem> + "#" + <local-name>.
VOCAB_BASE = "https://example.org/cutting-tool/vocabulary/"