from pathlib import Path
import json,re,yaml,sys,copy
from rdflib import Graph,Namespace,RDF,RDFS,OWL,BNode,Literal
from rdflib.namespace import SH
from pyshacl import validate
from jsonschema import Draft202012Validator
from src.generate_constraints import generate,load,fields_for,ROOT,CT

def test_all():
 summary=generate(); reg,m=load(); owl=Graph().parse(ROOT/'ontology/cutting-tool.owl',format='xml'); shapes=Graph().parse(ROOT/'shapes/generated-shapes.ttl',format='turtle')
 errors=[];passed=0
 def check(cond,msg):
  nonlocal passed
  passed+=1
  if not cond:errors.append(msg)
 for cls in reg['classes']:
  schema=json.loads((ROOT/'schemas'/f'{cls}.schema.json').read_text(encoding='utf-8')); check(Draft202012Validator.check_schema(schema) is None,'JSON schema invalid:'+cls)
  for key,spec in fields_for(reg,cls).items():
   uri=CT[m['owl_properties'][key]];check((uri,RDF.type,OWL.DatatypeProperty) in owl,'OWL field missing:'+cls+'.'+key)
   check((CT[cls+'Shape'],SH.property,None) in shapes,'SHACL shape missing:'+cls)
   check(key in schema['properties'],'JSON field missing:'+cls+'.'+key)
  if cls!='RecommendationRecord':
   check(re.search(r'FOR \(n:'+re.escape(cls)+r'\)',(ROOT/'neo4j/community-constraints.cypher').read_text()) is not None,'Neo4j label missing:'+cls)
 records=json.loads((ROOT/'examples/document-anchored-tool-identifiers.json').read_text(encoding='utf-8'))['entities'];record_results=[]
 for item in records:
  cl=item['type'];payload={k:v for k,v in item.items() if k in fields_for(reg,cl)}
  messages=[e.message for e in Draft202012Validator(json.loads((ROOT/'schemas'/f'{cl}.schema.json').read_text(encoding='utf-8'))).iter_errors(payload)]
  record_results.append({'model':item['name'],'class':cl,'schema_valid':not messages,'errors':messages})
  check(not messages,'known model data:'+item['name']+str(messages))
 # Validate document-derived identifiers as RDF/SHACL, not just JSON.
 rdf_document=Graph()
 for item in records:
  x=CT['document-'+item['id']];rdf_document.add((x,RDF.type,CT[item['type']]))
  for key,val in item.items():
   if key in fields_for(reg,item['type']):rdf_document.add((x,CT[m['owl_properties'][key]],Literal(val)))
 doc_ok,doc_report,doc_text=validate(data_graph=rdf_document,shacl_graph=shapes,ont_graph=owl,inference='rdfs')
 check(doc_ok,'Document-derived RDF SHACL failure: '+doc_text[:500])
 # SHACL semantic positive and negative fixtures
 data=Graph();unit=CT['fixture-insert']; data.add((unit,RDF.type,CT.Insert));data.add((unit,CT.id,Literal('TEST-INSERT')));data.add((unit,CT.name,Literal('演示刀片')));data.add((unit,CT.model,Literal('TEST-INSERT')));data.add((unit,CT.status,Literal('unknown')))
 a,report,_=validate(data_graph=data,shacl_graph=shapes,ont_graph=owl,inference='rdfs');check(a,'SHACL positive fixture failed '+str(report)[:250])
 invalid=Graph();invalid+=data;invalid.remove((unit,CT.id,None));b,_,_=validate(data_graph=invalid,shacl_graph=shapes,ont_graph=owl,inference='rdfs');check(not b,'SHACL missing id not detected')
 # OWL semantic labelling, mapping, object relations
 for c,info in reg['classes'].items():
  check((CT[c],RDF.type,OWL.Class) in owl,'OWL class missing '+c)
  if info.get('parent'):check((CT[c],RDFS.subClassOf,CT[info['parent']]) in owl,'OWL wrong inheritance '+c)
 # mapping relation names must exist as OWL object properties
 for rel in m.get('relations',[]):
  check((CT[rel['name']],RDF.type,OWL.ObjectProperty) in owl,'OWL relationship missing '+rel['name'])
 # JSON negative test
 bad={'id':'bad','name':'invalid label','model':'bad','status':'unknown','ic':-1};schema=json.loads((ROOT/'schemas/Insert.schema.json').read_text(encoding='utf-8'));check(not Draft202012Validator(schema).is_valid(bad),'JSON should reject negative ic')
 status='PASS' if not errors else 'FAIL';result={'status':status,'checks':passed,'failed':len(errors),'issues':errors,'generator':summary,'document_identifier_samples':record_results,'shacl_positive':bool(a),'shacl_document_samples':bool(doc_ok),'shacl_negative_rejected':not bool(b),'neo4j_runtime':'NOT_RUN_NO_SERVER','owl_dl_reasoner':'NOT_RUN','data_source_class':'user_document_identifiers_without_independent_catalog_verification'}
 (ROOT/'reports/verification.json').parent.mkdir(exist_ok=True)
 (ROOT/'reports/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'status':status,'checks':passed,'failures':errors[:15],'sample_count':len(records),'shacl_positive':bool(a),'shacl_negative_rejected':not bool(b)},ensure_ascii=False))
 if errors:raise SystemExit(1)
if __name__=='__main__':test_all()
