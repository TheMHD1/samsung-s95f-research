#!/usr/bin/env python3
"""Offline CB operands; bus values and conditional selected-image meanings."""
from pathlib import Path
import hashlib,json,struct
P=Path(__file__).resolve().parent;CB=P.parent;B=CB.parent
PACKAGE=B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'
PACKAGE_HASH='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0'
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
def u16(b,n):return struct.unpack_from('<H',b,n)[0]
def u32(b,n):return struct.unpack_from('<I',b,n)[0]
R_FIELDS={'stop':0,'logger_gate':6,'fault':10,'ordinary_gate':14,'scan_control':16,'mode1_threshold_normal':0x30,'mode2_threshold':0x32,'mode4_threshold':0x40,'event344_enable':0x4a,'event351_enable':0x4e,'mode1_action_bucket':0x86,'mode2_action_bucket':0x88,'mode4_6_action_bucket':0x8c,'mode1_record_id_latch':0x90,'mode4_6_record_id_latch':0x92,'event344_latch':0x9a,'event351_latch':0x9c,'aggregate_gate':0x9e,'BP_count_limit':0xa0,'q_publish_latch':0xa2,'mode6_threshold_normal':0xc0,'alternate_fp_threshold':0xc4,'T_selector':0xd2,'T_helper_count_limit':0xd6}
def decode(name,b):
 if name=='R':return {k:u16(b,v) for k,v in R_FIELDS.items()}
 if name=='M':
  aa,ac=u16(b,10),u16(b,12)
  return {'root':hex(u32(b,64)),'scan_status_counter':u16(b,0),'aa':aa,'ac':ac,'mode_if_flags_current':4 if aa==1 else 6 if ac==1 else 1,'input_header_4b0':u16(b,16),'input_header_4b2':u16(b,18),'input_header_4b4':u16(b,20),'normal_diff_limit_A_lt_B':u16(b,22),'mode4_diff_limit_A_lt_B':u16(b,24),'normal_diff_limit_A_ge_B':u16(b,26),'mode4_diff_limit_A_ge_B':u16(b,28),'alternate_numeric_mirror':u16(b,34),'alternate_refresh_counter_not_boolean_invariant':u16(b,36),'formatter_B_excluded_upper':u16(b,38),'formatter_B_excluded_lower':u16(b,40),'record_ID_bound_mirror':u16(b,42),'diagnostic_y':u16(b,48),'neighbor_header_4d2':u16(b,50),'diagnostic_RGB':u16(b,52),'scan_enable_d8':b[56],'neighbor_d9_raw':b[57]}
 if name=='C':return {'startup_halfwords':[u16(b,x) for x in [0,2,4]],'local_byte_6':b[6],'alternate_selector_byte_7':b[7],'AP_EXCO_byte0_mirror_at8':b[8],'volatile_tail_raw_hex':b[9:].hex()}
 if name=='H':return {'prefix_word_raw':u32(b,0),'A_u32':[u32(b,4+4*x) for x in range(6)],'q_u16':[u16(b,28+2*x) for x in range(6)],'history_u16x4':[[u16(b,40+8*x+2*y) for y in range(4)] for x in range(6)],'tail_d138_d13f_hex':b[88:].hex()}
 if name=='L':return {'T_latch':u16(b,4),'mode6_score_latch':u16(b,6),'non_mode6_score_latch':u16(b,8)}
 raise ValueError('unknown window')
def main():
 native_raw=(CB/'native.stdout.bin').read_bytes();native=json.loads(native_raw.decode().splitlines()[0]);result=json.loads((CB/'result.json').read_text());raws={x['name']:x for x in result['rawFiles']};package=PACKAGE.read_bytes();need(sha(package)==PACKAGE_HASH,'package hash')
 anchors={}
 for name,va,n in [('predicate',0x1e68,0x1d8),('mode1_bucket_or',0x1c0e6,16),('common_setter',0xc1e0,0x32),('unpacker_threshold_selection',0xbddc,0x30),('formatter_bound',0xc5f6,16),('formatter_count_after_id_bypass',0xc6de,2),('count_increment',0xc708,20),('alternate_counter_later_reset',0x1c18e,16),('reset_ap_rtp_table',0,0)]:
  if n:anchors[name]={'image':1,'va':hex(va),'file_offset':hex(0x40200+va),'bytes':package[0x40200+va:0x40200+va+n].hex(),'sha256':sha(package[0x40200+va:0x40200+va+n])}
 need(anchors['predicate']['sha256']=='c3afd8863cf7f6d098fe7459ef91da9fd8827662041e77cd29497dccb2aae57a','predicate body')
 captures=[];all_windows=[]
 for capture in native['retained']:
  windows=[]
  for index,w in enumerate(capture['windows']):
   token=capture['role'].replace('-','_');filename=next(n for n in raws if token in n and f'cycle{capture["cycleIndex"]:03d}-{index:02d}-{w["name"]}.bin' in n)
   raw=(CB/filename).read_bytes();need(len(raw)==w['expected']==raws[filename]['bytes'] and sha(raw)==w['sha256']==raws[filename]['sha256'],'raw pin '+filename)
   pair=capture['transfers'][2*index:2*index+2];need(len(pair)==2 and pair[0]['direction']=='OUT' and pair[1]['direction']=='IN','read pair')
   base=int(w['address'],16)
   entry={'name':w['name'],'file':filename,'bus_base':w['address'],'bytes':len(raw),'sha256':sha(raw),'out_before_us':pair[0]['beforeUs'],'in_after_us':pair[1]['afterUs'],'conditional_decoded':decode(w['name'],raw),'all_raw_bytes_hex':raw.hex(),'all_u16_le':[{'bus_address':hex(base+i),'value':u16(raw,i)} for i in range(0,len(raw),2)]}
   windows.append(entry);all_windows.append((capture['role'],entry,raw))
  captures.append({'role':capture['role'],'cycle':capture['cycleIndex'],'windows':windows})
 # All raw changes are reported, including fields for which semantics are unknown.
 changes=[]
 for left,right in [('trigger-baseline','last-clean'),('last-clean','post-fault')]:
  for name in 'RMCHL':
   a=[(w,b) for role,w,b in all_windows if role==left and w['name']==name][-1:]
   z=[(w,b) for role,w,b in all_windows if role==right and w['name']==name][-1:]
   if not a or not z:continue
   aw,ab=a[0];zw,zb=z[0];base=int(aw['bus_base'],16)
   changes.append({'from':left,'to':right,'window':name,'from_file':aw['file'],'to_file':zw['file'],'changed_bytes':[{'bus_address':hex(base+i),'before':x,'after':y} for i,(x,y) in enumerate(zip(ab,zb)) if x!=y]})
 def get(role,name):return next(w for c in captures if c['role']==role for w in c['windows'] if w['name']==name)
 last_R=[w for c in captures if c['role']=='last-clean' for w in c['windows'] if w['name']=='R'][-1];fault_R=get('transition','R')
 # A shortest compatible *model*, not an inferred event trace. Conditions:
 # coherent same-slot samples, no reset/other writer, mode1, q0, T0 throughout.
 state={'A':38,'q':0,'history':[4,0,2,0]};steps=[]
 for s in [4,0,4,0]:
  state['q']=(2*state['q'])&31
  state['history']=state['history'][1:]+[s]
  if s>160:state['q']+=1
  if state['q'] not in {8,9,10,12,24,25}:state['A']=(state['A']+state['history'][0])&0xffffffff
  steps.append({'s':s,'A':state['A'],'q':state['q'],'history':state['history'][:],'greater_than_40':(state['A']&65535)>40})
 need(state=={'A':44,'q':0,'history':[4,0,4,0]},'compatible model')
 output={'scope':'offline bus samples; source meanings conditional on selected running image/mapping','transport_audit_is_separate':True,'source_package_sha256':PACKAGE_HASH,'native_stdout_sha256':sha(native_raw),'result_sha256':sha((CB/'result.json').read_bytes()),'source_anchors':anchors,'captures':captures,'changed_bytes':changes,'conservative_clean_to_fault_bracket_us':[last_R['out_before_us'],fault_R['in_after_us']],'bracket_width_us':fault_R['in_after_us']-last_R['out_before_us'],'minimum_gap_between_brackets_us':fault_R['out_before_us']-last_R['in_after_us'],'key_intervention':native['intervention'],'physical_darkness_reported_by_owner_to_parent_not_native_timestamped':True,'event_code_736_directly_logged_in_CB':False,'compatible_four_invocation_model':steps,'compatible_model_is_unique_trace':False,'next_omitted_count_window_candidate':{'bus_address':'0x4700ba28','bytes':36,'CPU_meaning_conditional':'six record IDs + six source counts','target_qualification_required':True},'target_operations_by_this_analysis':0}
 print(json.dumps(output,indent=2,sort_keys=True))
if __name__=='__main__':main()
