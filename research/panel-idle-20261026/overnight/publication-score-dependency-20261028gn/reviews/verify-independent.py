#!/usr/bin/env python3
"""Focused GN source review. Reads retained files; executes isolated Thumb only."""
from pathlib import Path
import hashlib, json, struct, subprocess, sys
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
GN = HERE.parent
B = GN.parent
checks = 0

def need(ok, why):
    global checks
    if not ok:
        raise ValueError(why)
    checks += 1

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    need(sha((GN/'source-inventory.json').read_bytes()) == 'f154d57f2be5eae4caad70a544df853c14334b245640ad5fb78eead0344f96d3', 'frozen author inventory')
    inventory = json.loads((GN/'source-inventory.json').read_text())
    for row in inventory['files']:
        data = (GN/row['path']).read_bytes()
        need(len(data) == row['bytes'] and sha(data) == row['sha256'], 'author file '+row['path'])
    # Auditor has been inspected: only reads inputs, runs isolated Unicorn, prints JSON.
    original = json.loads((GN/'validation.normal.json').read_text())
    for mode in [[], ['-O']]:
        run = subprocess.run([sys.executable, *mode, '-B', str(GN/'audit.py')], capture_output=True, timeout=120)
        need(run.returncode == 0 and not run.stderr, 'author source auditor normal/optimized')
        need(json.loads(run.stdout) == original, 'author audit reproduces frozen result')
    sys.path.insert(0, '/tmp/tcon-capstone')
    sys.path.insert(0, str(B/'predicate-binary-oracle-20261028gd/tools'))
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
    from unicorn.arm_const import (UC_CPU_ARM_CORTEX_M4, UC_ARM_REG_R0, UC_ARM_REG_R1,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
        UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)
    asset = (B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
    need(len(asset) == 0x500000 and sha(asset) == 'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0', 'selected asset identity')
    image = asset[0x40200:0x60200]
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    def ins(lo, hi):
        return [(x.address, x.mnemonic, x.op_str) for x in md.disasm(image[lo:hi], lo)]
    need(ins(0x202a,0x203e) == [(0x202a,'cmp','r7, fp'),(0x202c,'ble','#0x203e'),(0x202e,'uxtb','r0, r4'),(0x2030,'movs','r1, #4'),(0x2032,'bl','#0x1c0c8'),(0x2036,'mov.w','r0, #0x2e0'),(0x203a,'bl','#0xc1e0')], 'strict comparison/helper-before-setter ordering')
    setter = ins(0xc1e0,0xc214)
    need([v for a,m,v in setter if m=='bl'] == ['#0x38fc','#0x1b8c8','#0x1b8c8'], 'setter does not call status helper')
    need(ins(0xc63c,0xc644) == [(0xc63c,'movs','r1, #2'),(0xc63e,'mov','r0, r4'),(0xc640,'bl','#0x1c0c8')], 'formatter mask two')
    need(ins(0x38fc,0x3902) == [(0x38fc,'ldr','r0, [pc, #4]'),(0x38fe,'ldr','r0, [r0]'),(0x3900,'bx','lr')], 'real mutable root getter')
    need(struct.unpack_from('<I',image,0x3904)[0] == 0x200004e0, 'root pointer cell')
    root=0x20010000
    def new():
        u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS)
        u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M4)
        u.mem_map(0,0x40000);u.mem_write(0,image)
        u.mem_map(0x20000000,0x40000);u.mem_map(0x20200000,0x20000)
        u.mem_write(0x200004e0,struct.pack('<I',root))
        u.reg_write(UC_ARM_REG_SP,0x2003f000)
        u.reg_write(UC_ARM_REG_R5,root)
        return u
    def put(u,a,n,size=2):u.mem_write(a,int(n).to_bytes(size,'little'))
    def get(u,a,size=2):return int.from_bytes(u.mem_read(a,size),'little')
    records=[]
    # Start AFTER earlier B qualification, with detail printing suppressed by its
    # existing budget. Execute the real helper/root getter; no callee stubs here.
    for mode in [1,4,6]:
        for alternate in [0,1]:
            for ordinal,bound in [(40,40),(41,40),(41,200),(200,200),(201,200),(512,512)]:
                u=new(); lane=42
                for reg,value in [(UC_ARM_REG_R4,mode),(UC_ARM_REG_R6,lane),(UC_ARM_REG_R7,123),(UC_ARM_REG_R8,2159),(UC_ARM_REG_R9,0),(UC_ARM_REG_R10,77)]:u.reg_write(reg,value)
                put(u,0x2000ba28+4*(mode-1),ordinal,4)
                put(u,0x200004ca,bound);put(u,0x200004be,4,1)
                put(u,0x200004c0,3);put(u,root+0x24d2,alternate)
                put(u,0x2000ba40+2*(mode-1),17)
                put(u,0x2020af10+lane,9,1)
                writes=[]; pcs=[]
                def hook(uc,a,size,data):
                    pcs.append(a)
                    if a==0xc738:uc.emu_stop();return
                    need((0xc5f6 <= a and a+size <= 0xc738) or (0x1c0c8 <= a and a+size <= 0x1c12c) or (0x38fc <= a and a+size <= 0x3902), 'publication execution stays in bounded source slices')
                u.hook_add(UC_HOOK_CODE,hook)
                u.hook_add(UC_HOOK_MEM_WRITE,lambda uc,access,a,s,v,data:writes.append((a,s,v)))
                u.emu_start(0xc5f7,0xc73c,count=200)
                need(pcs[-1]==0xc738,'common count/lane join reached')
                admitted=ordinal<=bound
                need(get(u,0x2000ba40+2*(mode-1))==18,'count increments on both paths')
                need(get(u,0x2020af10+lane,1)==(10 if alternate else 9),'alternate lane increment')
                need(get(u,0x2020b698+lane,1)==(0 if alternate else 1),'ordinary lane set')
                need(get(u,0x2000ba28+4*(mode-1),4)==ordinal+int(admitted),'ordinal changes only on publication admission')
                off={1:0x2486,4:0x248c,6:0x248c}[mode]
                need(get(u,root+off)==(2 if admitted else 0),'status OR2 only on admitted path')
                expected=[] if not(admitted and ordinal<512) else [(root+base+2*ordinal,2,value) for base,value in [(0x1000,45),(0x1400,2159),(0x1800,0),(0x1c00,123),(0x2000,77)]]
                actual=[w for w in writes if root+0x1000 <= w[0] < root+0x2400]
                need(actual==expected,'exact five stores and independent 512 capacity bound')
                records.append({'mode':mode,'alternate':alternate,'ordinal':ordinal,'bound':bound,'published':admitted,'recordStores':len(actual),'commonCountIncrement':True,'commonLaneUpdate':True})
    # Inspect nonaggregate branch with real helper and real setter. Only waitready
    # and logger are stubbed explicitly, so this is not a complete firmware model.
    branch=[]
    for aggregate,wait in [(1,0),(0,0),(0,1)]:
        u=new();u.reg_write(UC_ARM_REG_R4,1)
        put(u,root+0x249e,aggregate);put(u,0x2000ba28,201,4)
        put(u,0x200004ca,200);put(u,0x2000ba40,18)
        logs=[];calls=[];stopped=[]
        def branch_hook(uc,a,size,data):
            if a in [0xc796,0xc79e]:stopped.append(a);uc.emu_stop();return
            if a==0x35a4:
                calls.append('waitready');uc.reg_write(UC_ARM_REG_R0,wait);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
            if a==0x1b8c8:
                logs.append(uc.reg_read(UC_ARM_REG_R1));uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
            need((0xc738<=a and a+size<=0xc79e) or (0x1c0c8<=a and a+size<=0x1c12c) or (0xc1e0<=a and a+size<=0xc214) or (0x38fc<=a and a+size<=0x3902),'nonaggregate execution bounded')
        u.hook_add(UC_HOOK_CODE,branch_hook)
        u.emu_start(0xc739,0xc7a0,count=200)
        fault=(aggregate!=1 and wait==0)
        need(bool(stopped),'nonaggregate branch terminal')
        need(logs==([824,824] if fault else []),'separate event824 setter path')
        need(get(u,root+0x2486)==(4 if fault else 0),'nonaggregate OR4')
        need(get(u,root+0x2400)==int(fault) and get(u,root+0x240a)==(0x1001 if fault else 0),'separate setter stores')
        need(get(u,0x2000ba28,4)==(183 if aggregate!=1 and wait else 201),'nonaggregate busy adjustment')
        branch.append({'aggregateConfiguration':aggregate,'waitStub':wait,'event824SetterCalled':fault,'loggerArguments':logs})
    print(json.dumps({'schema':'gn-independent-source-review-v1','status':'PASS_BOUNDED_HOST_SOURCE_REVIEW','checks':checks,'authorAudit':original,'publicationEntryCondition':'after earlier B qualification; detail print budget >=4','publicationCases':records,'nonaggregateCases':branch,'nonaggregateStubs':['35a4 waitready','1b8c8 logger'],'selectedAssetSha256':sha(asset),'targetOperations':0,'wholeAliasClosureProven':False,'globalScoreIndependenceProven':False,'physicalOrCausalClaim':False},sort_keys=True,indent=2))

if __name__=='__main__':main()
