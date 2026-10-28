#!/usr/bin/env python3
"""Host-only retained-input/model qualification. Never execute OEM or target code."""
from pathlib import Path
import hashlib,json,struct,sys,types
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;B=D.parent
m=types.ModuleType('pure_model');exec(compile((D/'profile_model.py').read_bytes(),'profile_model.py','exec'),m.__dict__);checks=0

def need(ok,msg):
 global checks
 if not ok:raise ValueError(msg)
 checks+=1

def reject(f):
 try:f()
 except ValueError:need(True,'negative model guard');return
 raise ValueError('negative unexpectedly accepted')
sha=lambda b:hashlib.sha256(b).hexdigest();p=types.ModuleType('dq_parser');p.__file__=str(B/'volatile-limit-native-binding-20261028dq/parse-result.py');exec(compile(Path(p.__file__).read_bytes(),p.__file__,'exec'),p.__dict__)
need(sha(Path(p.__file__).read_bytes())=='4c79318b8d1e5d6554bfd6bcd84c50674a3955c15a19aef443aba7356a3fe02d','frozen profile parser pin')
rows=[{'label':'frozen DQ profile','raw':p.PROFILE,'sourceSha256':sha(Path(p.__file__).read_bytes())}]
inputs=[]
for folder in ['record-baseline-01','record-fault-01','recovered-clean-01']:
 for name in ['start-R.bin','end-R.bin']:
  path=B/'volatile-limit-trial-20261028dk'/folder/name;raw=path.read_bytes();inputs.append({'path':str(path.relative_to(B)),'bytes':len(raw),'sha256':sha(raw)});rows.append({'label':folder+'/'+name,'raw':raw,'sourceSha256':sha(raw)})
path=B/'volatile-limit-trial-20261028dk/score-baseline-01/native.receipt.json';b=path.read_bytes();inputs.append({'path':str(path.relative_to(B)),'bytes':len(b),'sha256':sha(b)})
import base64
for cap in json.loads(b)['retained']:
 for i,w in enumerate(cap['windows']):
  if w['name']=='R':rows.append({'label':'score-baseline-01/'+cap['role']+'/'+str(i),'raw':base64.b64decode(w['rawBase64'],validate=True),'sourceSha256':sha(b)})
results=[]
for row in rows:
 predicted=m.profile_prediction(row['raw']);need(all(x['actual']==x['model']['endpoint']for x in predicted['modes'].values()),'retained endpoint model '+row['label']);results.append({k:v for k,v in row.items()if k!='raw'}|{'Rsha256':sha(row['raw']),'prediction':predicted})
# Later recovery selected mode6: diagnostics/alternate updated while normal retained3200.
# This is a retained counterexample to claiming both endpoints must always be fresh.
counterexamples=[]
later=B/'volatile-limit-trial-20261028dk/reference-recovered-clean-01'
for name in ['start-R.bin','end-R.bin','M.bin','C.bin']:
 path=later/name;b=path.read_bytes();inputs.append({'path':str(path.relative_to(B)),'bytes':len(b),'sha256':sha(b)})
for name in ['start-R.bin','end-R.bin']:
 raw=(later/name).read_bytes();observed=m.endpoint_observations(raw)
 need(observed['temperature']==24 and observed['modes']['normal']['actual']==3200 and not observed['modes']['normal']['matchesSharedDiagnostics'] and observed['modes']['alternate']['actual']==3161 and observed['modes']['alternate']['matchesSharedDiagnostics'],'retained alternate-only refresh')
 reject(lambda:m.profile_prediction(raw));reject(lambda:m.validate_candidate_r(raw,40,p.PROFILE))
 counterexamples.append({'label':'reference-recovered-clean-01/'+name,'Rsha256':sha(raw),'observations':observed,'restrictiveBothFreshPolicyAccepts':False})
need([m.u16((later/'M.bin').read_bytes(),o)for o in [10,12,38]]==[0,1,3161],'mode6 flags and selected alternate mirror')
reject(lambda:m.validate_candidate_context((later/'M.bin').read_bytes(),(later/'C.bin').read_bytes(),(later/'start-R.bin').read_bytes()))
# Verify exact u16→float32→multiply by1/16→vcvt truncation for every possible input.
for raw in range(65536):
 f=struct.unpack('<f',struct.pack('<f',float(raw)))[0];scaled=struct.unpack('<f',struct.pack('<f',f*0.0625))[0];need(int(scaled)==m.scaled_temperature(raw),'float32/u16 truncation equivalence');need(m.scaled_reference(raw)==(25 if int(scaled)>4000 else int(scaled)),'reference fallback equivalence')
# Fixed source parameters keep every allowed temperature output inside the exact floor/cap.
for t in range(4096):
 x=m.endpoint(2075,24,t,15,195,3000,3800);need(3000<=x['endpoint']<=3800,'all source temperatures bounded')
# Generic width tests include negative subtraction and32-bit multiply wrap.
for vals in [(1,2,0,65535,65535,0,65535),(65535,0,65535,65535,65535,100,3800),(2075,24,24,15,195,3000,3800),(2075,24,25,15,195,3000,3800)]:
 base,ref,t,c,s,f,cap=vals;x=m.endpoint(*vals);direct=(((base+c*(t-ref))&0xffffffff)*s)&0xffffffff;candidate=(direct>>7)&65535;need(x['productU32']==direct and x['endpoint']==(cap if candidate>cap else max(f,candidate)),'ARM modular width/branch semantics')
for offset in [0x94,0x96,0xae,0xb0,0xb2,0x2e,0xb6,0xb8,0xba,0x2c]:
 raw=bytearray(p.PROFILE);raw[offset]^=1;reject(lambda:m.profile_prediction(bytes(raw)))
for off,value in [(0x98,4096),(0xac,255),(0xac,256),(0x20,3184),(0xbc,3184)]:
 raw=bytearray(p.PROFILE);struct.pack_into('<H',raw,off,value);reject(lambda:m.profile_prediction(bytes(raw)))
raw=bytearray(p.PROFILE);struct.pack_into('<H',raw,0xac,0);need(m.profile_prediction(bytes(raw))['echo']==0 and m.pairwise_thermal_stable(p.PROFILE,bytes(raw)),'echo may vary independently within transaction')
need(not m.pairwise_thermal_stable(rows[1]['raw'],rows[5]['raw']),'temperature tuple differs across invocations')
# Full policy composition retains exact static profile and context, and changes only proven roles.
for folder in ['record-baseline-01','recovered-clean-01']:
 base=B/'volatile-limit-trial-20261028dk'/folder;raw=(base/'start-R.bin').read_bytes();m.validate_candidate_r(raw,40,p.PROFILE);m.validate_candidate_context((base/'M.bin').read_bytes(),(base/'C.bin').read_bytes(),raw);need(True,'clean retained context qualifies proposed model')
 changed=bytearray(raw);struct.pack_into('<H',changed,0xc4,200);struct.pack_into('<H',changed,0xac,0);m.validate_transaction_pair(raw,bytes(changed),40,200,p.PROFILE);m.validate_transaction_pair(bytes(changed),raw,200,40,p.PROFILE);need(True,'separate fixed set/restore candidate guard')
for i in range(256):
 if not m.legacy_historical_byte(i) and i not in m.ADDITIONAL_MODEL_BYTES|{0xc4,0xc5,0xca}:
  raw=bytearray(p.PROFILE);raw[i]^=1;reject(lambda:m.validate_candidate_r(bytes(raw),40,p.PROFILE))
reject(lambda:m.validate_candidate_r((B/'volatile-limit-trial-20261028dk/record-fault-01/start-R.bin').read_bytes(),40,p.PROFILE))
reject(lambda:m.validate_transaction_pair(rows[1]['raw'],rows[5]['raw'],40,40,p.PROFILE))
asset=B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin';ab=asset.read_bytes();need(sha(ab)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected asset pin');source=[]
for va,n in [(0x389d0,280),(0x21576,58),(0x3af16,48),(0x27670,16),(0x97e0,138),(0x9968,152)]:source.append({'image':0,'va':hex(va),'fileOffset':hex(va+0x200),'bytes':n,'sha256':sha(ab[va+0x200:va+0x200+n])})
need(struct.unpack_from('<f',ab,0x38aec+0x200)[0]==0.0625,'exact scale literal')
result={'schema':'du-pure-model-validation-v1','status':'PASS','checksPassed':checks,'targetOperations':0,'networkOperations':0,'writerImplemented':False,'inputs':inputs,'retainedPredictions':results,'retainedFreshnessCounterexamples':counterexamples,'sourceRanges':source,'allowlistedHalfwords':{'thermal':[hex(x)for x in m.THERMAL_HALFWORDS],'echo':hex(m.ECHO_HALFWORD)},'allOtherStaticGuardsRemainRequired':True}
(D/'validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'status':'PASS','checksPassed':checks,'retainedRPredictions':len(results),'validationSha256':sha((D/'validation.json').read_bytes()),'targetOperations':0}))
