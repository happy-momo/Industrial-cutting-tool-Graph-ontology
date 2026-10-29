"""Single source of truth for the feed-type / feed-unit pairing.

`feed_type` (fn/fz/vf) and `feed_unit` (mm/rev, mm/tooth, mm/min) must describe
the same feed semantics. Consumed by the offline validator (src/validator.py)
and the online relationship-rule R4 (pilot/neo4j_rules.py).
"""
FEED_UNITS = {'fn': 'mm/rev', 'fz': 'mm/tooth', 'vf': 'mm/min'}