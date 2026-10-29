from pathlib import Path
import json,yaml,sys
from rdflib import Graph,Namespace,RDF,RDFS,OWL,URIRef,Literal,BNode
from rdflib.namespace import XSD,SH
ROOT=Path(__file__).resolve().parents[1]
from src.namespaces import ON as CT
DTD={'string':XSD.string,'number':XSD.decimal,'integer':XSD.integer,'boolean':XSD.boolean}
def load():
 r=yaml.safe_load((ROOT/'contract/field-registry.yaml').read_text(encoding='utf-8'))
 m=yaml.safe_load((ROOT/'mappings/ontology-neo4j.yaml').read_text(encoding='utf-8'))
 return r,m
def fields_for(reg,cls):
 info=reg['classes'][cls]; parent=info.get('parent'); out=fields_for(reg,parent) if parent else {}
 out.update(info.get('fields') or {})
 return out
def generate():
 r,m=load(); (ROOT/'schemas').mkdir(exist_ok=True); (ROOT/'shapes').mkdir(exist_ok=True); (ROOT/'neo4j').mkdir(exist_ok=True)
 owl=Graph().parse(ROOT/'ontology/cutting-tool.owl',format='xml')
 shapes=Graph();shapes.bind('ct',CT);shapes.bind('sh',SH)
 errors=[]
 # Vocabulary binding: a class bound to a SKOS scheme must (a) name an existing
 # vocabulary file and (b) actually declare a concept_ref field; conversely a
 # concept_ref field without a binding is an alignment gap.
 vocab = r.get('vocabulary') or {}
 for cls, stem in vocab.items():
  if cls not in r['classes']: errors.append('vocabulary binds unknown class '+cls)
  if not (ROOT/'vocabulary'/f'{stem}.ttl').exists(): errors.append('vocabulary scheme file missing for '+cls+': '+stem)
 for cls in r['classes']:
  has_ref='concept_ref' in fields_for(r,cls); bound=cls in vocab
  if has_ref and not bound: errors.append(cls+' declares concept_ref but is not bound to a vocabulary')
  if bound and not has_ref: errors.append(cls+' is bound to '+vocab[cls]+' but declares no concept_ref')
 for cls,info in r['classes'].items():
  if (CT[cls],RDF.type,OWL.Class) not in owl:errors.append('OWL class missing '+cls)
  parent=info.get('parent');
  if parent and (CT[cls],RDFS.subClassOf,CT[parent]) not in owl:errors.append('parent mismatch '+cls)
  merged=fields_for(r,cls)
  props={};required=[]
  shape=CT[cls+'Shape'];shapes.add((shape,RDF.type,SH.NodeShape));shapes.add((shape,SH.targetClass,CT[cls]))
  for key,spec in merged.items():
   owlkey=m['owl_properties'].get(key)
   if not owlkey:errors.append('OWL property mapping missing '+key);continue
   if (CT[owlkey],RDF.type,OWL.DatatypeProperty) not in owl:errors.append('OWL data property missing '+owlkey)
   opts={k:v for k,v in spec.items() if k not in ['required']}
   props[key]=opts
   if spec.get('required'):required.append(key)
   ps=BNode();shapes.add((shape,SH.property,ps));shapes.add((ps,SH.path,CT[owlkey]))
   if spec.get('required'):shapes.add((ps,SH.minCount,Literal(1)))
   shapes.add((ps,SH.maxCount,Literal(1)))
   if spec['type'] in DTD:shapes.add((ps,SH.datatype,DTD[spec['type']]))
   for keyword,predicate in [('minimum',SH.minInclusive),('maximum',SH.maxInclusive),('exclusiveMinimum',SH.minExclusive),('exclusiveMaximum',SH.maxExclusive),('minLength',SH.minLength),('maxLength',SH.maxLength),('pattern',SH.pattern)]:
    if keyword in spec:shapes.add((ps,predicate,Literal(spec[keyword])))
   if 'enum' in spec:
    from rdflib.collection import Collection
    head=BNode();Collection(shapes,head,[Literal(v) for v in spec['enum']]);shapes.add((ps,SH['in'],head))
  schema={'$schema':'https://json-schema.org/draft/2020-12/schema','title':cls,'type':'object','additionalProperties':False,'properties':props,'required':required}
  (ROOT/'schemas'/f'{cls}.schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n')
 if errors:raise ValueError('\n'.join(sorted(set(errors))))
 shapes.serialize(ROOT/'shapes/generated-shapes.ttl',format='turtle')
 common=[];enterprise=[]
 import re
 for cls in r['classes']:
  nm='ct_'+re.sub(r'(?<!^)(?=[A-Z])','_',cls).lower()+'_id'
  common.append(f'CREATE CONSTRAINT {nm} IF NOT EXISTS FOR (n:{cls}) REQUIRE n.id IS UNIQUE;')
  enterprise.append(f'CREATE CONSTRAINT {nm}_exists IF NOT EXISTS FOR (n:{cls}) REQUIRE n.id IS NOT NULL;')
 (ROOT/'neo4j/community-constraints.cypher').write_text('// Neo4j 5+ Community; uniqueness does not imply existence\n'+'\n'.join(common)+'\n')
 (ROOT/'neo4j/enterprise-constraints.cypher').write_text('// Neo4j Enterprise additional existence constraints\n'+'\n'.join(enterprise)+'\n')
 return {'classes':len(r['classes']),'json_schemas':len(r['classes']),'shacl_triples':len(shapes),'neo4j_uniques':len(common),'neo4j_exists':len(enterprise)}
if __name__=='__main__':print(json.dumps(generate(),ensure_ascii=False,indent=2))
