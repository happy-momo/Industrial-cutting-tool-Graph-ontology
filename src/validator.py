from pathlib import Path
import json
from jsonschema import Draft202012Validator, RefResolver
ROOT=Path(__file__).resolve().parents[1]
SCHEMAS={p.name:json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'schemas').glob('*.schema.json')}

# Vocabulary-bound classes must anchor their concept_ref to a real SKOS concept
# in the declared scheme. Existence is checked against vocabulary/*.ttl via
# src.resolve_skos; rdflib is imported lazily so the lightweight (jsonschema-only)
# route still works when rdflib is absent, degrading to the schema's URI pattern.
_VOCAB=None
def _vocab_binding():
 global _VOCAB
 if _VOCAB is None:
  import yaml
  reg=yaml.safe_load((ROOT/'contract/field-registry.yaml').read_text(encoding='utf-8'))
  _VOCAB=reg.get('vocabulary') or {}
 return _VOCAB

def _concept_ref_errors(cls,data):
 stem=_vocab_binding().get(cls)
 if stem is None:return []  # class not bound to a controlled vocabulary
 ref=data.get('concept_ref')
 if not ref:return ['concept_ref is required for vocabulary-bound class '+cls]
 try:
  from src import resolve_skos
  if not resolve_skos.concept_in_scheme(ref,stem):
   return [f"concept_ref '{ref}' is not a concept in the '{stem}' vocabulary"]
 except ImportError:
  pass  # rdflib absent: schema-level URI pattern is the only guarantee
 return []
# feed_type and feed_unit must describe the same feed semantics.
# fn  -> mm/rev (feed per revolution)
# fz  -> mm/tooth (feed per tooth/fange)
# vf  -> mm/min (linear feed relative to time)
_FEED_UNITS = {'fn': 'mm/rev', 'fz': 'mm/tooth', 'vf': 'mm/min'}

def _feed_unit_errors(data):
    feed_type = data.get('feed_type')
    feed_unit = data.get('feed_unit')
    if not feed_type or not feed_unit:
        return []
    expected = _FEED_UNITS.get(feed_type)
    if expected is not None and feed_unit != expected:
        return [f"feed_unit '{feed_unit}' is inconsistent with feed_type '{feed_type}' (expected '{expected}')"]
    return []

def validate_entity(cls,data):
 schema=SCHEMAS[cls+'.schema.json']
 errors=[e.message for e in Draft202012Validator(schema).iter_errors(data)]
 for low,high in [('vc_min','vc_max'),('feed_min','feed_max'),('ap_min','ap_max'),('hardness_min','hardness_max')]:
  if low in data and high in data and data[low]>data[high]:errors.append(f'{low} must not exceed {high}')
 if cls=='CuttingParam':
  if all(k in data for k in ('vc_min','vc_max','vc_recommended')) and not data['vc_min']<=data['vc_recommended']<=data['vc_max']:errors.append('vc_recommended outside range')
  errors += _feed_unit_errors(data)
 errors += _concept_ref_errors(cls,data)
 return errors

def validate_recommendation(payload):
 errors=[]
 try:
  s=SCHEMAS['RecommendationRecord.schema.json']; store={v['$id']:v for v in SCHEMAS.values()}
  resolver=RefResolver.from_schema(s,store=store)
  errors += [e.message for e in Draft202012Validator(s,resolver=resolver).iter_errors(payload)]
 except Exception as exc: errors.append('schema validation error: '+str(exc))
 rec=payload.get('recommendation',{});links=payload.get('links',{})
 scope=rec.get('scope_type')
 expected={'tool':{'tool_id'},'series':{'series_id'},'grade':{'grade_id'},'series_grade':{'series_id','grade_id'}}.get(scope,set())
 present={k for k in ('tool_id','series_id','grade_id') if k in links}
 if scope in ('tool','series','grade','series_grade') and present!=expected:errors.append('scope target links mismatch')
 if not (links.get('material_class_id') or links.get('material_grade_id')):errors.append('missing material target')
 return errors
