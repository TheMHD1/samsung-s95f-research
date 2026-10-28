#!/usr/bin/env python3
"""Host-only reconstructed Fault200 EB fixture. Never imported by production."""
import base64,copy,hashlib,json,struct,types
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent
SOURCE=B/'live-saver-wake-trial-20261028gf/fault-capture'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def load(path):
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m

def construct(output,limit=200,logger=0,stop=1,fault=0x1001,ordinary=0,unstable=False):
 """Rebuild all 32 EB artifacts and 28 transport calls, with explicit mock provenance."""
 policy=load(P/'policy.py');w=policy.wrapper();parser=policy.load(policy.EB/'parse-result.py',policy.EB_PARSER_SHA,'gh_fixture_parser')
 record=w.strict_json((SOURCE/'record.json').read_bytes());old=w.strict_json((SOURCE/'native.receipt.json').read_bytes());native=copy.deepcopy(old)
 for win in native['windows']:
  if win['name']in ['start-R','end-R']:
   raw=bytearray(base64.b64decode(win['base64'],validate=True))
   for offset,value in [(0,stop),(6,logger),(10,fault),(14,ordinary),(0xc4,limit)]:struct.pack_into('<H',raw,offset,value)
   if unstable and win['name']=='end-R':raw[0x20]^=1
   win['base64']=base64.b64encode(raw).decode();win['sha256']=sha(raw)
 receipt=(json.dumps(native,separators=(',',':'))+'\n').encode();parser.parse_native(receipt.decode())
 ready=w.strict_json((SOURCE/'readiness-decision.json').read_bytes());provenance=P/'fixture-provenance.json';proof=sha(provenance.read_bytes())
 ready['closedWorldVendorOutLineage']={'accepted':True,'statement':'SYNTHETIC HOST FIXTURE ONLY. Reconstructed from actual GF Fault40 source, with two complete R windows changed for fixed profile tests and a regenerated complete EB ledger. This is not actual Fault200 runtime evidence, not current device readiness and not an endpoint queue proof.','evidenceSha256':proof}
 ready['evidence']=[{'path':str(provenance),'sha256':proof}]
 ready_raw=(json.dumps(ready,indent=2,sort_keys=True)+'\n').encode()
 def envelope(original):
  need(original.startswith('IMMEDIATE_READY\n'),'source immediate receipt')
  terminal,old_receipt,stdout,stderr=w.receipt_envelope(original[len('IMMEDIATE_READY\n'):]);need(w.strict_json(old_receipt)==old,'source native receipt binding')
  blobs=[receipt,stdout,stderr]
  text='IMMEDIATE_READY\nEBMETA_BEGIN\n'+terminal['boot']+'\n'+terminal['uptime']+'\n'+str(terminal['exit_code'])+'\n'
  for blob in blobs:text+=str(len(blob))+'\n'+sha(blob)+'\n'
  text+='EBMETA_END\n'
  for label,blob in zip(['RECEIPT','STDOUT','STDERR'],blobs):text+=label+'_B64_BEGIN\n'+base64.b64encode(blob).decode()+'\n'+label+'_B64_END\n'
  return text+'EBRUN_COMPLETE\n'
 class SyntheticRoot:
  position=0
  def root(self,command,replay_record,path):
   need(self.position<len(record['calls']),'fixture source ledger extent');c=copy.deepcopy(record['calls'][self.position]);self.position+=1
   old_stdout=policy.call_stdout(c);text=envelope(old_stdout)if old_stdout.startswith('IMMEDIATE_READY\nEBMETA_BEGIN\n')else old_stdout
   # Only regenerated commands/echoes, native framing and transport serialization change.
   c['command']=command;c['command_bytes']=len(command.encode());c['response']['commands'][0].update(command=command,stdout=text)
   c['transport_stdout']={'encoding':'base64','data':base64.b64encode(json.dumps(c['response'],separators=(',',':')).encode()).decode()}
   policy.call_stdout(c);replay_record['calls'].append(c);w.save(path,replay_record);return text
 mock=SyntheticRoot();w.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_stage'].split('-')[-1]));manifest,payload=w.build_manifest()
 result=w.execute(output,ready,ready_raw,w.manifest_bytes(manifest),payload,mock,parser)
 need(mock.position==len(record['calls'])==28,'exact synthetic command count');need(result['accepted']and len(result['rawFiles'])==16,'complete reconstructed source')
 deltas=[]
 for win,oldwin in zip(native['windows'],old['windows']):
  before=base64.b64decode(oldwin['base64']);after=base64.b64decode(win['base64']);deltas.append({'window':win['name'],'changedByteOffsets':[i for i,(a,b)in enumerate(zip(before,after))if a!=b]})
 return {'synthetic':True,'sourceResultSha256':sha((SOURCE/'result.json').read_bytes()),'limit':limit,'stable':not unstable,'headers':16,'bulks':32,'rootCallsReconstructed':mock.position,'artifacts':len(list(output.iterdir())),'rawByteChanges':deltas,'resultSha256':sha((output/'result.json').read_bytes())}
