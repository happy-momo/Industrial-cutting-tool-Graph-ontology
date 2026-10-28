from pathlib import Path
import json
from jsonschema import Draft202012Validator, RefResolver
ROOT=Path(__file__).resolve().parents[1]
SCHEMAS={p.name:json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'schemas').glob('*.schema.json')}
def validate_entity(cls,data):
 schema=SCHEMAS[cls+'.schema.json']
 errors=[e.message for e in Draft202012Validator(schema).iter_errors(data)]
 for low,high in [('vc_min','vc_max'),('feed_min','feed_max'),('ap_min','ap_max'),('hardness_min','hardness_max')]:
  if low in data and high in data and data[low]>data[high]:errors.append(f'{low} must not exceed {high}')
 if cls=='CuttingParam' and all(k in data for k in ('vc_min','vc_max','vc_recommended')) and not data['vc_min']<=data['vc_recommended']<=data['vc_max']:errors.append('vc_recommended outside range')
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
