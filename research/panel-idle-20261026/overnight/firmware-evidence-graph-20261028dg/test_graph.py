import copy,hashlib,tempfile,unittest
import json
from unittest.mock import patch
from pathlib import Path
from validate_graph import validate,GraphError
class Tests(unittest.TestCase):
 def graph(self):
  ref={'path':'proof.md','sha256':hashlib.sha256(b'proof').hexdigest()}
  return {'schema':'s95f-evidence-graph-v1','nodes':[{'id':'n.a','kind':'state','label':'clean','source_refs':[ref]},{'id':'n.b','kind':'gap','label':'physical edge unknown','source_refs':[ref]}],'edges':[{'id':'e.1','from':'n.a','to':'n.b','relation':'does_not_close','evidence_type':'observed','observation_class':'native_capture','evidence_refs':[dict(ref,locator='sample')]}]}
 def refuse(self,g):
  with self.assertRaises(GraphError):validate(g)
 def test_valid_independent_minimal_and_pinned_report(self):
  g=self.graph();self.assertFalse(validate(g)['semantic_truth_verified'])
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'proof.md').write_bytes(b'proof');self.assertTrue(validate(g,p)['source_hashes_verified']);(p/'proof.md').write_bytes(b'changed')
   with self.assertRaises(GraphError):validate(g,p)
 def test_dangling_duplicate_and_unknown_provenance(self):
  g=self.graph();g['nodes'].append(copy.deepcopy(g['nodes'][0]));self.refuse(g)
  for key,value in [('from','missing'),('evidence_type','proved'),('observation_class','physical_from_screenshot')]:
   g=self.graph();g['edges'][0][key]=value;self.refuse(g)
  g=self.graph();g['edges'].append(copy.deepcopy(g['edges'][0]));self.refuse(g)
 def test_source_path_digest_and_address_domain(self):
  for path in ['/etc/shadow','../outside.md','x/private/secret.json','asset.bin']:
   g=self.graph();g['nodes'][0]['source_refs'][0]['path']=path;self.refuse(g)
  g=self.graph();g['nodes'][0]['source_refs'][0]['sha256']='x'*64;self.refuse(g)
  g=self.graph();g['nodes'][0]['address']='0x47012400';self.refuse(g)
 def test_unobserved_class_no_fake_percent_or_secrets(self):
  g=self.graph();g['edges'][0].pop('observation_class');self.refuse(g)
  for key in ['confidence_percent','nonce_hex','salt_bytes','rsa_signature_bytes']:
   g=self.graph();g['nodes'][0][key]=99;self.refuse(g)
 def test_actual_graph_is_structural_not_truth_promotion(self):
  g=json.loads(Path(__file__).with_name('graph.json').read_text());r=validate(g);self.assertGreater(r['nodes'],30);self.assertFalse(r['running_identity_proved'])
  self.assertEqual({x['owner'] for x in g['contributions']},{'de','df'})
  self.assertTrue(any(e['relation']=='unproved_register_to_field_bridge' and e['evidence_type']=='unknown' for e in g['edges']))
  self.assertTrue(any(e['relation']=='remote_resource_alias_then_mirror_to_C_plus7' and e['evidence_type']=='static' for e in g['edges']))
 def test_frozen_contribution_normalization_and_drift(self):
  import build_graph as b
  original={'nodes':[{'id':'de:f','kind':'function','label':'function','source_refs':[{'path':'PRD:/usr/lib/example.so','sha256':'a'*64,'address':16,'address_domain':'ELF link VA','file_offset':16}],'limitations':[]},{'id':'de:p','kind':'logger','label':'earlier prototype','source_refs':[{'path':'x/private/secret.cs','sha256':'b'*64}],'limitations':[]}], 'edges':[{'id':'de:e','from':'de:f','to':'de:p','relation':'unclosed','evidence_type':'unknown','confidence':'unknown','evidence_refs':[{'path':'PRD:/usr/lib/example.so','sha256':'a'*64,'locator':'call16'}],'limitations':[]}]}
  raw=json.dumps(original).encode();digest=hashlib.sha256(raw).hexdigest()
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'evidence';p.mkdir();(p/'evidence-graph.json').write_bytes(raw);(p/'findings.md').write_text('authored')
   with patch.multiple(b,ROOT=root,B='',CONTRIBUTIONS={'de':('evidence',digest,'findings.md')}):
    nodes=[];edges=[];proof=b.merge_contributions(nodes,edges)
    g={'schema':'s95f-evidence-graph-v1','nodes':nodes,'edges':edges,'contributions':proof};validate(g,root)
    self.assertNotIn('secret.cs',json.dumps(g));self.assertNotIn('"confidence":',json.dumps(g));self.assertEqual(nodes[0]['asset_anchors'][0]['file_offset'],16)
    self.assertEqual(nodes[1]['kind'],'interface');self.assertEqual(edges[0]['evidence_type'],'unknown')
    (p/'evidence-graph.json').write_bytes(raw+b' ')
    with self.assertRaisesRegex(ValueError,'frozen contribution changed'):b.merge_contributions([],[])
if __name__=='__main__':unittest.main()
