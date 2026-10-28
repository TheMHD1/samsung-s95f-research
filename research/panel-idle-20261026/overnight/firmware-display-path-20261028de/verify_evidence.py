#!/usr/bin/env python3
"""Host-only exact source/extent/call/graph checks. No target or OEM execution."""
import hashlib,json,struct
from pathlib import Path
from analyze_elf import inspect
D=Path(__file__).resolve().parent;B=D.parent;P=B/'firmware-platform-analysis-20261028db/private'
E=json.loads((D/'evidence.json').read_text());G=json.loads((D/'evidence-graph.json').read_text());checks=0
def need(v,msg):
 global checks
 checks+=1
 if not v:raise ValueError(msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths={'prd-ave':P/'prd-extracted/tree/root/usr/lib/libave.so.0.1','pltf-dlog':P/'pltf-extracted/tree/root/usr/lib/libdlog.so.0.0.0','npc-json':P/'prd-extracted/tree/root/usr/bin/ave/pq/LUT_NPC_Point.json'}
for sid in ['prd-ave','pltf-dlog']:
 old=[f for f in E['functions'] if f['source_id']==sid];new,_=inspect(paths[sid],[f['name'] for f in old]);newby={f['name']:f for f in new['functions']}
 need(new['sha256']==next(s['sha256'] for s in E['sources'] if s['id']==sid),'whole-source pin')
 for f in old:
  n=newby[f['name']];need(all(n[k]==f[k] for k in ['va','file_offset','size','sha256']),'extent pin '+f['name'])
  for c in f['calls']:need(c in n['calls'],'relocation-resolved call '+hex(c['site']))
need(sha(paths['npc-json'])==next(s['sha256'] for s in E['sources'] if s['id']=='npc-json'),'NPC resource pin')
need(E['npc_resource_shape']['compensation_group_count']==3,'NPC groups')
need(E['npc_resource_shape']['entries_per_status']==[16],'NPC entry lengths')
need(any(x['vptr_relative_offset']==0x70 and 't_SetQdSeneDetect' in x['target'] for x in E['vtable']),'scene vtable')
need(any(x['vptr_relative_offset']==0x154 and 't_SetNpcLut' in x['target'] for x in E['vtable']),'LUT vtable')
r=paths['prd-ave'].read_bytes()
need((struct.unpack_from('<I',r,0x269c90)[0]+0x269788+0x58)&0xffffffff==0x5bfc78,'monitor latch PIC arithmetic')
need((struct.unpack_from('<I',r,0x269c54)[0]+0x26967a+0x3c)&0xffffffff==0x5bfc5c,'ERR counter PIC arithmetic')
providers={f['name']:f for f in E['provider_calls']}
for n in ['_tztv_frc_tcon_read_err_det_status','_tztv_frc_tcon_read_vdd_det_status','_tztv_frc_tcon_read_pmic_status']:
 calls=[x['target'] for x in providers[n]['calls']]
 for req in ['gpio_request','gpiod_direction_input','gpiod_get_raw_value_cansleep','gpio_free']:need(req in calls,'provider side effect '+n+req)
need('gpio_request' in [x['target'] for x in providers['_tztv_gpio_get_value']['calls']],'generic getter still requests line')
ids={n['id'] for n in G['nodes']};need(len(ids)==len(G['nodes']),'node uniqueness')
for edge in G['edges']:
 need(edge['from'] in ids and edge['to'] in ids,'graph endpoint');need(edge['evidence_type'] in ['observed','static','inferred','unknown'],'evidence type')
need(any(x['evidence_type']=='unknown' and x['to']=='de:ap-exco' for x in G['edges']),'unresolved EXCO edge explicit')
print(json.dumps({'accepted':True,'checks':checks,'tv_actions':0,'oem_executions':0,'network_actions':0}))
