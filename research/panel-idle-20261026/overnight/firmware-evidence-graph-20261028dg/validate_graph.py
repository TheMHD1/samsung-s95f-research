"""Data-only graph structural/provenance checks; never execute graph attributes."""
import hashlib,re
from pathlib import Path
class GraphError(ValueError):pass
def need(value,label):
 if not value:raise GraphError(label)
KINDS={'asset','function','interface','state','observation','hypothesis','action','gap','case','configuration','evidence','report'}
TYPES={'observed','static','inferred','unknown'}
OBS={'native_capture','owner_report','cached_ui','host_validation'}
ID=re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z');SHA=re.compile(r'[0-9a-f]{64}\Z')
def validate(graph,root=None):
 need(type(graph) is dict and graph.get('schema')=='s95f-evidence-graph-v1','schema')
 nodes=graph.get('nodes');edges=graph.get('edges');need(type(nodes) is list and 1<=len(nodes)<=10000 and type(edges) is list and len(edges)<=50000,'graph bounds')
 def refs(items,locator=False):
  need(type(items) is list and 1<=len(items)<=32,'evidence refs')
  for ref in items:
   need(type(ref) is dict,'ref object');p=ref.get('path');h=ref.get('sha256')
   need(type(p) is str and 0<len(p)<=1024,'ref path')
   path=Path(p);need(not path.is_absolute() and '..' not in path.parts and 'private' not in [x.lower() for x in path.parts],'bounded public report path')
   need(path.suffix.lower() in {'.md','.json','.txt','.disasm','.py','.cs'},'report/source reference type')
   need(type(h) is str and bool(SHA.fullmatch(h)),'ref SHA')
   if locator:need(type(ref.get('locator')) is str and 0<len(ref['locator'])<=2048,'edge locator')
   if root is not None:
    base=Path(root).resolve();f=(base/path).resolve();need(base in f.parents and f.is_file(),'source containment')
    need(f.stat().st_size<=8_000_000,'bounded report input')
    need(hashlib.sha256(f.read_bytes()).hexdigest()==h,'source hash mismatch')
 def no_confidence(value):
  if isinstance(value,dict):
   need(not any(k.lower() in {'confidence','probability','confidence_percent','nonce_hex','salt_bytes','signature_bytes','rsa_signature_bytes'} for k in value),'unsupported confidence or private field')
   for v in value.values():no_confidence(v)
  elif isinstance(value,list):
   for v in value:no_confidence(v)
 no_confidence(graph);ids=set()
 for n in nodes:
  need(type(n) is dict and type(n.get('id')) is str and bool(ID.fullmatch(n['id'])),'node id');need(n['id'] not in ids,'duplicate node');ids.add(n['id'])
  need(n.get('kind') in KINDS and type(n.get('label')) is str and 0<len(n['label'])<=4096,'node kind/label');refs(n.get('source_refs'))
  if 'address' in n:need(type(n.get('address_domain')) is str and bool(n['address_domain']),'address domain missing')
 edgeids=set()
 for e in edges:
  need(type(e) is dict and type(e.get('id')) is str and bool(ID.fullmatch(e['id'])),'edge id');need(e['id'] not in edgeids,'duplicate edge');edgeids.add(e['id'])
  need(e.get('from') in ids and e.get('to') in ids,'dangling endpoint');need(e.get('evidence_type') in TYPES,'evidence type')
  need(type(e.get('relation')) is str and 0<len(e['relation'])<=256,'relation');refs(e.get('evidence_refs'),True)
  if e['evidence_type']=='observed':need(e.get('observation_class') in OBS,'observed class missing')
 return {'nodes':len(nodes),'edges':len(edges),'source_hashes_verified':root is not None,'semantic_truth_verified':False,'running_identity_proved':False,'target_calls':0}
if __name__=='__main__':
 import argparse,json
 p=argparse.ArgumentParser();p.add_argument('graph',type=Path,nargs='?',default=Path(__file__).with_name('graph.json'));p.add_argument('--retained-root',type=Path);a=p.parse_args();print(json.dumps(validate(json.loads(a.graph.read_text()),a.retained_root),sort_keys=True))
