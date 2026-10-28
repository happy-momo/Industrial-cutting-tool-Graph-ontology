import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from validator import validate_entity,validate_recommendation
base=Path(__file__).resolve().parents[1]
for c in ['Insert','CuttingParam','CuttingRecommendation']:
 obj=json.loads((base/'examples'/f'{c}.json').read_text(encoding='utf-8'))
 err=validate_entity(c,obj)
 assert not err,(c,err)
record=json.loads((base/'examples/RecommendationRecord.json').read_text(encoding='utf-8'))
assert not validate_recommendation(record)
invalid=json.loads((base/'tests/bad-cutting-param.json').read_text(encoding='utf-8'))
assert validate_entity('CuttingParam',invalid)
from xml.etree import ElementTree
ElementTree.parse(base/'ontology/cutting-tool.owl')
print('PASS: entity schemas, application cross-field constraints, negative tests, OWL XML syntax')
try:
 from rdflib import Graph
 from pyshacl import validate
 shape=Graph().parse(base/'shapes/generated-shapes.ttl',format='turtle')
 ont=Graph().parse(base/'ontology/cutting-tool.owl',format='xml')
 data=Graph().parse(base/'examples/example.ttl',format='turtle')
 conforms,report,_=validate(data,shacl_graph=shape,ont_graph=ont,inference='rdfs')
 assert conforms,str(report)
 print('PASS: RDF parse and SHACL validation')
except ImportError:print('SKIPPED: rdflib/pyshacl optional dependencies not installed')
