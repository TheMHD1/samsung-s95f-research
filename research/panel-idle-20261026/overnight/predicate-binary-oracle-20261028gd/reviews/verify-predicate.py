#!/usr/bin/env python3
"""Focused conditional execution/ABI audit of a captured authored oracle source."""
import hashlib,json,struct,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;G=D.parent;B=G.parent;checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
raw=(D/'reviewed-oracle.py').read_bytes();m=types.ModuleType('reviewed_conditional_predicate');m.__file__=str(G/'oracle.py');exec(compile(raw,str(G/'oracle.py'),'exec'),m.__dict__)
ck(m.unicorn.__version__=='2.1.4','pinned tool version')
image=m.selected_image();ck(len(image)==0x20000 and image==(m.PACKAGE.read_bytes())[0x40200:0x60200],'selected image mapping')
# Actual final Thumb pop is four bytes; entry excludes helper1e46 but calls it.
ck(image[0x203e:0x2042].hex()=='bde8f09f'and image[0x1e68:0x1e6c].hex()=='2de9f05f','real entry/return bounds')
ck(struct.unpack_from('<I',image,0x38f8)[0]==m.CTX and struct.unpack_from('<I',image,0x3904)[0]==m.SRAM+0x4e0,'actual getter literal identities')
original=m.Uc;instances=[];writes=[];reads=[]
def factory(*args):
 u=original(*args);instances.append(u);set_model=u.ctl_set_cpu_model
 def set_and_audit(model):
  set_model(model)
  u.hook_add(m.unicorn.UC_HOOK_MEM_WRITE,lambda uc,access,a,size,value,data:writes.append((a,size,value)))
  u.hook_add(m.unicorn.UC_HOOK_MEM_READ,lambda uc,access,a,size,value,data:reads.append((a,size)))
 u.ctl_set_cpu_model=set_and_audit
 return u
m.Uc=factory
cases=[]
for mode in range(1,7):
 for selector in [0,1,255]:
  for q in [0,4,65535]:cases.append({'mode':mode,'selector':selector,'q':q,'aggregate':0xfffffff0,'history':[65535,16,0,7],'source_count':65535,'event_bound':65534,'t':0xffffffff,'alternate_t':True})
cases += [{'aggregate':41,'t':0,'alternate_t':False},{'aggregate':40,'t':0},{'aggregate':39,'t':0},{'aggregate':65577,'gate':0},{'aggregate':65577,'gate':2}]
comparison_count=0;faults=0
for case in cases:
 writes.clear();reads.clear();v=m.emulate(image=image,**case);expected=m.model(**case)
 for k,value in expected.items():ck(v[k]==value,'independent boundary projection '+k)
 ck(v['returned']and v['instructionCount']<=1000,'bounded sentinel return and SP/callee-save assertions passed')
 ck(all(m.SRAM<=a and a+size<=m.SRAM+0x20000 for a,size,_ in writes),'no executable/MMIO write in conditional emulation')
 ck(all((0<=a and a+size<=0x20000)or(m.SRAM<=a and a+size<=m.SRAM+0x20000)for a,size in reads),'reads only selected code/literals or initialized SRAM model')
 # Data alias reads really reached the root-pointer seed; it is not just a modeled address label.
 ck((m.SRAM+0x4e0,4)in reads and (m.CTX+0x6c7,1)in reads or case.get('mode',1)in [2,4]and(m.SRAM+0x4e0,4)in reads,'actual getter/context reads')
 if case.get('gate',1)==1:
  qnew=expected['q'];diag=struct.unpack('<H',instances[-1].mem_read(m.ROOT+0x24a2,2))[0]
  ck(diag==(qnew if case.get('source_count',0)>case.get('event_bound',160)else 0),'source extra diagnostic store not included in core model output')
 if v['comparison']is not None:comparison_count+=1
 if v['faultTuple']==[1,4097,0]:faults+=1;ck(v['setter']=={'event':736,'lr':0x203f},'actual source setter callsite/argument')
# Whole authored run reproduces1000/7000 core sweep, still entirely host-only.
m.Uc=original;whole=m.run();ck(whole['cases']==1000 and whole['checks']==7004 and whole['setterCases']==291,'original independent full run')
witness=whole['currentControlCounterfactual'];ck(len(witness)==4 and [x['comparison']['threshold'] for x in witness]==[200,40,200,200] and [x['faultTuple'] for x in witness]==[[0,0,1],[1,4097,0],[0,0,1],[0,0,1]],'captured controls and supplied counterfactual outcomes')
ck(all(x['counterfactualNotObservedInvocation'] for x in witness),'counterfactual label')
for item in whole['currentControlInputs']:
 data=Path(item['path']).read_bytes();ck(len(data)==item['bytes'] and sha(data)==item['sha256'],'actual control raw bytes')
ck(whole['actualComparisonOperandsProven']is False and whole['actualTargetInvocationProven']is False,'scope preserved')
print(json.dumps({'schema':'gd-independent-predicate-validation-v1','reviewedSourceSha256':sha(raw),'currentSourceMatchesReviewedSnapshot':sha((G/'oracle.py').read_bytes())==sha(raw),'selectedPackageSha256':m.PACKAGE_SHA,'unicornVersion':m.unicorn.__version__,'checks':checks,'extraCases':len(cases),'extraComparisons':comparison_count,'extraSetters':faults,'originalCases':whole['cases'],'originalChecks':whole['checks'],'actualTargetInvocationProven':False,'actualTValueProven':False,'actualComparisonOperandsProven':False,'targetOperations':0,'rootCalls':0,'networkOperations':0},sort_keys=True,indent=2))
