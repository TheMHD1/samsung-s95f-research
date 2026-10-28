#!/usr/bin/env python3
"""Strict offline complete EB fault-source replay; no live adapter import."""
import copy,json,re,struct,tempfile,types
from pathlib import Path
import importlib.util
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ge_admission_policy',HERE/'policy.py');policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
need=policy.need;sha=policy.sha

def admit(capture,result_digest,identity):
 need(capture.is_absolute()and capture.is_dir()and not capture.is_symlink(),'ordinary absolute source capture')
 files=sorted(capture.iterdir());need(1<=len(files)<=128 and all(f.is_file()and not f.is_symlink()and f.stat().st_size<=2097152 for f in files),'bounded ordinary capture files')
 pins=[{'name':f.name,'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())}for f in files]
 w=policy.wrapper();p=policy.load(policy.EB/'parse-result.py',policy.EB_PARSER_SHA,'ge_eb_parser')
 need(re.fullmatch('[0-9a-f]{64}',result_digest or '')and sha((capture/'result.json').read_bytes())==result_digest,'explicit source result pin')
 manifest,payload=w.build_manifest();manifest_raw=w.manifest_bytes(manifest)
 need(sha(manifest_raw)==policy.EB_MANIFEST_SHA and (capture/'reviewed-manifest.json').read_bytes()==manifest_raw,'exact EB family/manifest')
 ready_raw=(capture/'readiness-decision.json').read_bytes();ready,_=w.load_readiness(capture/'readiness-decision.json',sha(ready_raw))
 need(ready['identity']==identity,'same exact current fault instance')
 for row in ready['evidence']:
  path=Path(row['path']);need(path.is_absolute()and path.is_file()and not path.is_symlink()and sha(path.read_bytes())==row['sha256'],'saved readiness reference unchanged')
 native,raws,q=p.parse_native((capture/'native.receipt.json').read_text())
 need(native['accepted']is True and native['protocolPhase']=='ReadyForHeader'and native['released']is True and native['closed']is True and native['headersSent']==16 and native['bulkTransfers']==32 and str(native['device'])==identity['devnum'],'full ready/released/closed EB source')
 result=w.strict_json((capture/'result.json').read_bytes());record=w.strict_json((capture/'record.json').read_bytes())
 need(result['accepted']is True and type(result['nativeInvocations'])is int and result['nativeInvocations']==1 and result['cleanup']=='STAGE_ABSENT'and result['retries']==0 and result['wrapperUiOperations']==0,'accepted once/cleaned source result')
 inventory=[{'name':n,'bytes':len(raw),'sha256':h}for n,raw,h in raws]
 need(len(raws)==16 and result['rawFiles']==record['retained_raw_files']==inventory,'exact 16 raw inventory')
 for n,raw,h in raws:need((capture/n).read_bytes()==raw and sha(raw)==h,'native/raw binding '+n)
 start=(capture/'start-R.bin').read_bytes();end=(capture/'end-R.bin').read_bytes()
 need(start==end and [struct.unpack_from('<H',start,i)[0]for i in [0,6,10,14,0xc4]]==[1,0,0x1001,0,40],'stable full fault40/logger0 source')
 need(q==w.strict_json((capture/'interpretation.json').read_bytes()),'exact native interpretation')
 calls=record['calls'];need(type(calls)is list and 1<=len(calls)<=128,'bounded source call ledger')
 for call in calls:policy.call_stdout(call)
 need(record['cleanup_required']is False and record['cleanup_stdout']=='STAGE_ABSENT\n','source cleanup claim')
 need(re.fullmatch('/tmp/researcher-eb-[0-9a-f]{32}',record['remote_stage'])is not None,'source stage identity')
 class Replay:
  def __init__(self):self.position=0
  def root(self,command,replay_record,path):
   need(self.position<len(calls),'no extra replay call');c=calls[self.position];self.position+=1
   need(command==c['command'],'exact frozen EB command order');replay_record['calls'].append(copy.deepcopy(c));w.save(path,replay_record);return c['response']['commands'][0]['stdout']
 replay=Replay();w.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_stage'].split('-')[-1]))
 scratch=HERE/'host-environment/tmp';scratch.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='fault-replay-',dir=scratch)as tmp:
  output=Path(tmp)/'capture';replayed=w.execute(output,ready,ready_raw,manifest_raw,payload,replay,p)
  need(replayed==result and replay.position==len(calls),'exact accepted wrapper replay')
  need({f.name for f in output.iterdir()}=={f.name for f in files},'exact complete saved artifact set')
  for f in output.iterdir():need(f.read_bytes()==(capture/f.name).read_bytes(),'every saved artifact byte-exact '+f.name)
 # No target action was used by the replay; pins rechecked after consumption.
 need(pins==[{'name':f.name,'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())}for f in files],'source unchanged during admission')
 return {'schema':'ge-source-fault-admission-v1','accepted':True,'capture':str(capture),'resultSha256':result_digest,'files':pins,'sameInstance':True,'exactRootCommandsReplayed':len(calls),'headers':16,'bulks':32,'stableFault40Logger0':True,'phase':'ReadyForHeader','released':True,'closed':True,'cleanup':'STAGE_ABSENT','endpointQueueProof':False,'physicalPictureObserved':False}
