"""Execute only retained QDF power body with synthetic memory/callbacks; no IO."""
import re,struct,sys
sys.dont_write_bytecode=True

def run(qdf,relocs,need):
 sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parent.parent/'predicate-binary-oracle-20261028gd/tools'))
 from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
 from unicorn import arm64_const as c
 code=qdf.get_section_by_name('.text').data();rs=relocs(qdf,'.text')
 from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
 md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
 instructions={x.address:x for x in md.disasm(code[0x11848:0x11b88],0x11848)}
 def reg(n):return getattr(c,'UC_ARM64_REG_'+n.upper())
 base=0x100000;bss=0x200000;stack=0x300000;globalsbase=0x400000;sentinel=0x500000
 names=sorted({r['name']for a,r in rs.items()if 0x11848<=a<0x11b88 and r['name'] not in ['.bss','.rodata','.rodata.str1.8']})
 globalsmap={n:globalsbase+4096*i for i,n in enumerate(names)}
 def target(rr):
  n=rr['name'];return ({'.bss':bss,'.rodata':0x600000,'.rodata.str1.8':0x610000}.get(n,globalsmap.get(n,0)))+rr['addend']
 cases=[]
 configs=[{'label':'all-null-on','on':1,'monitor':0,'platform':4,'callbacks':False}, {'label':'all-null-off','on':0,'monitor':0,'platform':4,'callbacks':False}]
 for mon,plat,on in [(0,4,0),(0,4,1),(1,4,0),(1,4,1),(0,3,0),(0,3,1),(2,3,0),(2,3,1)]:
  configs.append({'label':f'm{mon}-p{plat}-on{on}','on':on,'monitor':mon,'platform':plat,'callbacks':True})
 configs += [dict(label='err-high-normal-tail-skipped',on=1,monitor=0,platform=4,callbacks=True,err=1),dict(label='discarded-tail-negative',on=1,monitor=0,platform=4,callbacks=True,tail=-5),dict(label='reset-negative',on=1,monitor=0,platform=4,callbacks=True,reset=-5)]
 for cfg in configs:
  u=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
  for a,s in [(base,0x20000),(bss,0x1000),(stack,0x10000),(globalsbase,max(4096,len(names)*4096)),(sentinel,4096),(0x600000,0x20000)]:u.mem_map(a,s)
  u.mem_write(base,code);u.reg_write(c.UC_ARM64_REG_SP,stack+0xff00);u.reg_write(c.UC_ARM64_REG_LR,sentinel)
  def put(a,v,n=4):u.mem_write(a,int(v).to_bytes(n,'little',signed=False))
  put(bss+0x1a8,cfg['monitor']);put(bss+0x1ac,cfg['platform'])
  for n,a in globalsmap.items():put(a,0x700000+4096*names.index(n) if cfg['callbacks'] else 0,8)
  u.reg_write(c.UC_ARM64_REG_W0,cfg['on']);trace=[];returned=[]
  def hook(uc,a,size,data):
   if a==sentinel:returned.append(True);uc.emu_stop();return
   at=a-base;need(at in instructions,'bounded actual A64 body '+hex(at));x=instructions[at];rr=rs.get(at)
   if rr and x.mnemonic in ['adrp','add']:
    uc.reg_write(reg(x.op_str.split(',')[0]),target(rr));uc.reg_write(c.UC_ARM64_REG_PC,a+4);return
   if x.mnemonic in ['bl','blr']:
    arg=uc.reg_read(c.UC_ARM64_REG_W0);name=(rr or{}).get('name')
    if x.mnemonic=='bl':
     if not name:name='local:'+x.op_str
     val=cfg.get('tail',0)if at in [0x1192c,0x11930,0x11934]else 0
    else:
     ptr=uc.reg_read(reg(x.op_str));name=names[(ptr-0x700000)//4096]
     val=cfg.get('reset',0)if name=='tztv_set_sdp_jp_tcon_power_reset'else 0
     if name=='tztv_frc_tcon_read_err_det_status':put(uc.reg_read(c.UC_ARM64_REG_X0),cfg.get('err',0))
    trace.append({'at':hex(at),'callee':name,'argument0':arg,'stubResult':val});uc.reg_write(c.UC_ARM64_REG_W0,val&0xffffffff);uc.reg_write(c.UC_ARM64_REG_PC,a+4)
  u.hook_add(UC_HOOK_CODE,hook);u.emu_start(base+0x11848,sentinel+4,count=3000)
  need(bool(returned)and u.reg_read(c.UC_ARM64_REG_SP)==stack+0xff00,'body returned/balanced stack')
  result=u.reg_read(c.UC_ARM64_REG_W0);expected=cfg.get('reset',0)&0xffffffff
  need(result==expected,'actual returned callback aggregation '+cfg['label'])
  tail=[t for t in trace if t['at'] in ['0x1192c','0x11930','0x11934']]
  need(len(tail)==(3 if cfg['on'] and not cfg.get('err',0) else 0),'early ERR branch excludes tail')
  resets=[t['argument0']for t in trace if t['callee']=='tztv_set_sdp_jp_tcon_power_reset']
  need(resets==([0 if cfg['on'] else 1]if cfg['callbacks']and cfg['monitor']!=1 and cfg['platform']==4 else []),'branch-qualified mailbox callback')
  if cfg['on']:
   need(int.from_bytes(u.mem_read(bss+4,4),'little')==1 and int.from_bytes(u.mem_read(bss+0x40,4),'little')==1,'cached state becomes on even ERR-high or discarded negative tail')
  else:need(all(bytes(u.mem_read(bss+o,4))==bytes(4)for o in [4,0x10,0x40]),'cached state zeroed on off')
  cases.append({'configuration':cfg,'returnU32':result,'trace':trace,'syntheticCallbacks':True,'actualControllerExecutionProven':False})
 return cases

def emergency_tail(image,need):
 """Real tail only, synthetic magic words and service stubs; no MMIO maps."""
 from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_MODE_MCLASS,UC_HOOK_CODE
 from unicorn import arm_const as c
 from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
 md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
 instructions={i.address:i for i in md.disasm(image[0xb6be:0xb6fa],0xb6be)}
 cases=[]
 for a,b,late in [(0,0,False),(0x1234,0,False),(0,0xabcd,False),(0x1234,0xabcd,False),(0,0,True)]:
  u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);u.ctl_set_cpu_model(c.UC_CPU_ARM_CORTEX_M4)
  u.mem_map(0,0x40000);u.mem_write(0,image);u.mem_map(0x20000000,0x20000)
  ap=0x2000f0e0;exco=0x2000ff14;sp=0x2001f000;sentinel=0x30000
  u.mem_write(ap,struct.pack('<H',a));u.mem_write(exco,struct.pack('<H',b));u.reg_write(c.UC_ARM_REG_R6,exco);u.reg_write(c.UC_ARM_REG_SP,sp)
  u.mem_write(sp,struct.pack('<6I',0,0,0,0,0,sentinel|1));trace=[];loops=[];returned=[]
  def hook(uc,at,size,data):
   if at==sentinel:returned.append(True);uc.emu_stop();return
   need(at in instructions,'exact emergency tail execution only')
   if at==0xb6dc:
    loops.append(True)
    if late:
     uc.mem_write(ap,struct.pack('<H',0x1234));uc.mem_write(exco,struct.pack('<H',0xabcd))
    if len(loops)==3:uc.emu_stop();return
   x=instructions[at]
   if x.mnemonic=='bl':
    target=int(x.op_str[1:],16);trace.append(hex(target))
    if target==0xe670:uc.reg_write(c.UC_ARM_REG_R0,ap)
    else:uc.reg_write(c.UC_ARM_REG_R0,0)
    uc.reg_write(c.UC_ARM_REG_PC,(at+4)|1)
  u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0xb6bf,sentinel+4,count=150)
  expected=(a,b)==(0x1234,0xabcd)
  need(bool(returned)==expected,'magic words only initial bypass')
  need((len(loops)==0)if expected else(len(loops)==3),'non-magic tail loops finitely observed')
  if late:need(not returned,'later changed magic does not revisit initial bypass')
  cases.append({'initialMagicMatches':[a==0x1234,b==0xabcd],'mutateMagicAfterEnteringLoop':late,'returnedThroughPop':bool(returned),'loopEntryCount':len(loops),'stubbedCalls':trace,'sliceOnly':True,'emergencySideEffectsExecuted':False})
 return cases
