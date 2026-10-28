#!/usr/bin/env python3
"""GR finite source/retained-byte namespace audit. No target operations."""
from pathlib import Path
import base64, hashlib, importlib.util, json, re, struct, sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;B=HERE.parent
checks=0;pins={}
def need(ok,why):
 global checks
 if not ok:raise ValueError(why)
 checks+=1
def sha(x):return hashlib.sha256(x).hexdigest()
def read(rel):
 p=B/rel;d=p.read_bytes();pins[rel]={'path':rel,'bytes':len(d),'sha256':sha(d)};return d
def half(b,o):return struct.unpack_from('<H',b,o)[0]
def main():
 sys.path.insert(0,'/tmp/tcon-capstone');sys.path.insert(0,str(B/'predicate-binary-oracle-20261028gd/tools'))
 from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
 from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_MODE_MCLASS,UC_HOOK_CODE
 from unicorn.arm_const import UC_CPU_ARM_CORTEX_M4,UC_ARM_REG_R0,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R10,UC_ARM_REG_SP
 asset=read('selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin')
 need(len(asset)==0x500000 and sha(asset)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','package identity')
 image=asset[0x40200:0x60200];md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
 spans=[]
 for lo,hi,label in [(0xbe0c,0xbe34,'global selector/ordinary-loop and category flags'),(0xbcb2,0xbd2c,'global selector to formatter category'),(0xbfae,0xbfe0,'predicate category argument'),(0xc5d0,0xc5e6,'formatter argument capture'),(0xc63c,0xc706,'category-indexed publication stores/latches'),(0x1e68,0x1eb0,'predicate category/threshold selection'),(0x1fc0,0x203e,'category-indexed aggregate/comparison'),(0x38fc,0x3908,'real root getter'),(0x1b72c,0x1b760,'category string selector')]:
  spans.append({'name':label,'vaStart':hex(lo),'vaEndExclusive':hex(hi),'fileStart':hex(lo+0x40200),'sha256':sha(image[lo:hi])})
 def seq(lo,hi):return [(x.address,x.mnemonic,x.op_str) for x in md.disasm(image[lo:hi],lo)]
 need(seq(0xbe0c,0xbe16)==[(0xbe0c,'movw','r0, #0x2410'),(0xbe10,'ldrh','r0, [r0, r5]'),(0xbe12,'cmp','r0, #6'),(0xbe14,'bge','#0xbf14')],'root2410 is separate loop selector')
 need(seq(0xbcb2,0xbcbc)==[(0xbcb2,'movw','r0, #0x2410'),(0xbcb6,'ldrh','r0, [r0, r5]'),(0xbcb8,'cmp','r0, #4'),(0xbcba,'bne','#0xbce8')],'global four branch')
 need(seq(0xbcd0,0xbcd6)==[(0xbcd0,'movs','r0, #1'),(0xbcd2,'strd','r6, r0, [sp]')],'global four supplies formatter category one on stack')
 need(seq(0xc5dc,0xc5e0)==[(0xc5dc,'ldrd','sl, r4, [sp, #0x38]')],'formatter category reads second stacked word after prologue')
 need(seq(0xbfda,0xbfe0)==[(0xbfda,'movs','r0, #1'),(0xbfdc,'bl','#0x1e68')],'default predicate category one')
 need(struct.unpack_from('<I',image,0xc030)[0]==0x200004aa and struct.unpack_from('<I',image,0xc040)[0]==0x200004ac,'AA/AC literal binding')
 need(seq(0x1e6c,0x1e6e)==[(0x1e6c,'mov','r4, r0')],'predicate preserves caller category rather than loading global mode')
 need(struct.unpack_from('<I',image,0x206c)[0]==0x2000d0e4,'category1 H base')
 need(image[0x1b74c:0x1b753].rstrip(b'\x00')==b'NORMAL','category1 stock text NORMAL')
 def new(global_selector,aa,ac):
  u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M4)
  u.mem_map(0,0x40000);u.mem_write(0,image);u.mem_map(0x20000000,0x40000)
  u.mem_write(0x20012410,struct.pack('<H',global_selector));u.mem_write(0x200004aa,struct.pack('<H',aa));u.mem_write(0x200004ac,struct.pack('<H',ac))
  u.reg_write(UC_ARM_REG_R5,0x20010000);u.reg_write(UC_ARM_REG_SP,0x2003f000);return u
 source_cases=[]
 for global_selector in [1,3,4]:
  for aa,ac,expected in [(0,2,1),(1,2,4),(0,1,6)]:
   u=new(global_selector,aa,ac);called=[]
   def hook(uc,a,size,data):
    if a==0x1e68:called.append(uc.reg_read(UC_ARM_REG_R0));uc.emu_stop();return
    need(0xbfae<=a and a+size<=0xbfe0,'finite predicate selector block only')
   u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0xbfaf,0xbfe0,count=30)
   need(called==[expected],'separate predicate category selection')
   source_cases.append({'slice':'predicate selector only','globalSelector':global_selector,'aa':aa,'ac':ac,'category':called[0]})
 for global_selector in range(6):
  u=new(global_selector,0,2);u.reg_write(UC_ARM_REG_R6,200);u.reg_write(UC_ARM_REG_R10,100)
  reached=[]
  def fmt_hook(uc,a,size,data):
   if a==0xc5d0:reached.append(int.from_bytes(uc.mem_read(0x2003f004,4),'little'));uc.emu_stop();return
   if a==0xbd2a:uc.emu_stop();return
   need(0xbcb2<=a and a+size<=0xbd2a,'finite comparator-tail only')
  u.hook_add(UC_HOOK_CODE,fmt_hook);u.emu_start(0xbcb3,0xbd2c,count=50)
  need(reached==([1] if global_selector in [1,3,4] else []),'global selector and category are not equality test')
  source_cases.append({'slice':'ordinary comparator tail only, supplied difference200 > threshold100','globalSelector':global_selector,'formatterCategories':reached})
 observed=[]
 for folder in ['raised-capture-01','forty-capture-01']:
  rel='matched-saver-limit-trial-20261028gj/'+folder+'/native.receipt.json';receipt=json.loads(read(rel));need(receipt['accepted'] is True,'actual recorder receipt accepted')
  for group in ['controls','retained']:
   for cap in receipt[group]:
    for i,w in enumerate(cap['windows']):
     raw=base64.b64decode(w['raw'],validate=True);need(len(raw)==w['count'],'retained raw length')
     if w['name']=='R':
      need(len(raw)==256 and half(raw,16)==4,'actual retained global selector four')
      observed.append({'capture':folder,'group':group,'role':cap['role'],'cycle':cap['cycle'],'windowIndex':i,'name':'R','rawSha256':sha(raw),'globalSelector':half(raw,16)})
     if w['name']=='M':need(half(raw,10)==0 and half(raw,12)==2,'actual AA0/AC2 retained M')
 for folder in ['set-01','restore-01']:
  rel='matched-saver-limit-trial-20261028gj/'+folder+'/native.receipt.json';receipt=json.loads(read(rel));need(receipt['accepted'] is True,'actual FA accepted')
  for w in receipt['windows']:
   raw=base64.b64decode(w['base64'],validate=True);need(len(raw)==w['bytes'] and sha(raw)==w['sha256'],'FA raw binding')
   if w['name'].endswith('-R'):
    need(half(raw,16)==4,'FA actual global selector4')
    observed.append({'capture':folder,'name':w['name'],'rawSha256':sha(raw),'globalSelector':half(raw,16)})
 rel='hdmi-endpoint-trial-20261028gp/baseline-capture/native.receipt.json';receipt=json.loads(read(rel));need(receipt['accepted'] is True,'actual GP EB accepted')
 for w in receipt['windows']:
  raw=base64.b64decode(w['base64'],validate=True);need(len(raw)==w['bytes'] and sha(raw)==w['sha256'],'GP EB raw binding')
  if w['name'] in ['start-R','end-R']:
   need(half(raw,16)==4,'GP global selector4');observed.append({'capture':'GP baseline EB','name':w['name'],'rawSha256':sha(raw),'globalSelector':half(raw,16)})
  if w['name']=='M':need(half(raw,10)==0 and half(raw,12)==2,'GP AA0AC2')
 fa_source=read('selective-endpoint-limit-writer-20261028fa/Program.cs').decode()
 profile=bytes.fromhex(re.search(r'Profile=Convert.FromHexString\("([0-9a-f]+)"\)',fa_source).group(1))
 need(half(profile,16)==4,'native FA exact static profile4')
 need('Need(Half(m,10)==0&&Half(m,12)==2,"mode1 flags")' in fa_source,'FA historical label refers to AA/AC')
 parser_rel='selective-endpoint-limit-writer-20261028fa/parse-result.py';read(parser_rel)
 spec=importlib.util.spec_from_file_location('gr_fa_offline',B/parser_rel);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 receipt=json.loads(read('matched-saver-limit-trial-20261028gj/set-01/native.receipt.json'))
 raw=base64.b64decode(next(w['base64'] for w in receipt['windows'] if w['name']=='baseline-R'))
 module.validate_candidate_r(raw,40,module.PROFILE);need(True,'actual R4 passes frozen FA guard')
 rejected=[]
 for mode in [1,3,5,6]:
  mutated=bytearray(raw);struct.pack_into('<H',mutated,16,mode)
  try:module.validate_candidate_r(bytes(mutated),40,module.PROFILE)
  except ValueError as e:rejected.append({'selector':mode,'reason':str(e)})
  else:raise ValueError('FA static profile unexpectedly allowed global selector '+str(mode))
  need(True,'FA different selector refusal')
 fn_engine=read('combined-event-successor-20261028fn/Engine.cs').decode();context=fn_engine.split('static void Context(',1)[1].split('static PairResult WriteLogger',1)[0]
 need('Half(m,10)==0&&Half(m,12)==2' in context and 'Half(r,16)' not in context,'FN context AAAC not global selector1')
 fn_score=read('combined-event-successor-20261028fn/ScoreCheckpoints.cs').decode()
 need('Array.Copy(h,4,raw,at+6,4)' in fn_score,'compact sampled aggregate from H offset4')
 read('rtp-lane-gate-qualification-20261028ea/README.md')
 read('rtp-lane-gate-qualification-20261028ea/source-qualification.json')
 read('publication-score-dependency-20261028gn/README.md')
 read('publication-score-dependency-20261028gn/source-audit.json')
 read('matched-saver-limit-trial-20261028gj/raised-analysis/README.md')
 read('selective-endpoint-limit-writer-20261028fa/README-wrapper.md')
 out={'schema':'gr-mode-label-audit-v1','status':'PASS_WITH_EXPLICIT_TERMINOLOGY_CORRECTION','checks':checks,'image1Rule':'FILE=VA+0x40200','sourceSpans':spans,'sourceCases':source_cases,'observedFullR':observed,'observedFullRCount':len(observed),'fullRGlobalSelectors':sorted(set(x['globalSelector'] for x in observed)),'faProfileGlobalSelector':half(profile,16),'faGlobalMutationRefusals':rejected,'conclusion':{'globalSelectorAddress':'root+0x2410 / R+0x10','globalSelectorObserved':4,'rtpCategoryConditionalOnAA0AC2':1,'categoryIsGlobalOperatingMode':False,'faRequiresGlobalSelector4ByExactProfile':True,'fnExplicitlyRequiresGlobalSelector1':False,'compactRowsContainGlobalSelector':False,'historicalExecutedCategoryEveryRowProven':False,'officialGlobalEnumRecovered':False},'inputPins':list(pins.values()),'targetOperations':0,'physicalClaim':False}
 print(json.dumps(out,sort_keys=True,indent=2))
if __name__=='__main__':main()
