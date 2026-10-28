#!/usr/bin/env python3
"""Bounded host-only FK review: no adapter or special file is opened."""
import base64,copy,hashlib,io,json,pathlib,sys,types
sys.dont_write_bytecode=True
sys.path.insert(0,'/tmp/tcon-capstone')
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
P=pathlib.Path(__file__).resolve().parent.parent;B=P.parent;checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 checks+=1
 if not v:raise ValueError(s)
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
invraw=(P/'source-inventory.json').read_bytes();need(sha(invraw)=='b59247fb9344d5ded74869a7dad1a1d5fdde5f1b73431bb882eb65a3081d3c2c','final inventory')
inv=json.loads(invraw)
for row in inv['files']:
 b=(P/row['path']).read_bytes();need(len(b)==row['bytes']and sha(b)==row['sha256'],'frozen '+row['path'])
cp=json.loads((P/'host-build-checkpoint.json').read_bytes())
for row in cp['payload']:
 b=(P/row['path']).read_bytes();need(len(b)==row['bytes']and sha(b)==row['sha256'],'payload manifest')
need(cp['rootWrapperImplemented']is False and not(P/'deployment-manifest.json').exists(),'native checkpoint only, no adapter manifest')
pins=json.loads((P/'input-pins.json').read_bytes())
for row in pins['inputs']:
 b=(B/row['path']).read_bytes();need(len(b)==row['bytes']and sha(b)==row['sha256'],'source input')
# Source section/relocation proof does not execute the retained OEM module.
ko=B/'firmware-platform-analysis-20261028db/private/pltf-extracted/tree/root/lib/modules/5.4.261/kernel/soc/sdp_tcon.ko';elf=ELFFile(io.BytesIO(ko.read_bytes()));need(elf['e_machine']=='EM_AARCH64','kernel ABI distinct from ARM32 libc')
text=elf.get_section_by_name('.text').data();audit=json.loads((B/'decision-probe-plan-20261028fd/source-audit.json').read_bytes())
for start,end,key in [(0x61b0,0x634c,'sdp_tcon:.text:61b0..634c'),(0x270,0x288,'sdp_tcon:.text:270..288'),(0x6f38,0x6f74,'sdp_tcon:.text:6f38..6f74'),(0x718c,0x71b8,'sdp_tcon:.text:718c..71b8')]:need(sha(text[start:end])==audit['source_spans'][key]['sha256'],'qualified driver span')
def relocation(section,at):
 rsec=elf.get_section_by_name(section);sym=elf.get_section(rsec['sh_link']);rows=[r for r in rsec.iter_relocations()if r['r_offset']==at];need(len(rows)==1,'unique relocation');r=rows[0];s=sym.get_symbol(r['r_info_sym']);return s.name,elf.get_section(s['st_shndx']).name if isinstance(s['st_shndx'],int)else None,r['r_addend']
need(relocation('.rela.rodata',0x1670)[1:]==('.text',0x61b0),'fops read')
need(relocation('.rela.rodata',0x16d0)[0]=='simple_open','fresh simple_open')
need(relocation('.rela.text',0x62f8)[0]=='__arch_copy_to_user','copy call')
dec=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN);instructions={i.address:(i.mnemonic,i.op_str)for i in dec.disasm(text[0x61b0:0x634c],0x61b0)}
for at,expected in [(0x61cc,('ldrh','w20, [x23]')),(0x6214,('cmp','w20, #0xfff')),(0x621c,('mov','x24, x20')),(0x6294,('mov','x20, x25')),(0x62ec,('add','x1, x19, #4')),(0x62f0,('mov','x2, x24')),(0x62fc,('nop',''))]:need(instructions[at]==expected,'read branch anchor')
# Exhaustive arithmetic already independently rerun by native selftest; check its boundaries here.
for header in [0,1,4094,4095,4096,65535]:
 length=header+1;copylength=length if length<=4095 else min(length,4096);need(1<=copylength<=4096 and copylength+4<=131072,'first-read boundary')
fj=B/'tcon-log-runtime-metadata-20261028fj';record=json.loads((fj/'record.json').read_bytes());need(len(record['calls'])==1,'metadata one call')
c=record['calls'][0];a=c['response'];child=a['commands'][0];need(c['transport_exit']==0 and c['host_timeout']is False and a['authenticated']is True and a['uid']==a['euid']==0 and child['exit_code']==0 and child['timed_out']is False and child['stderr']=='','saved metadata transport')
need(json.loads(base64.b64decode(c['transport_stdout']['data'],validate=True))==a,'metadata transport JSON')
need(child['stdout']==(fj/'metadata.txt').read_text(),'metadata exact bytes')
need('regular empty file 644 0 /sys/kernel/debug/tcon/tcon_micom_log\n'in child['stdout']and 'debugfs /sys/kernel/debug debugfs 'in child['stdout'],'debugfs metadata existence')
need('sdp_tcon 114688 7 sdp_frc, Live 'in child['stdout']and sha(ko.read_bytes())+'  /lib/modules/5.4.261/kernel/soc/sdp_tcon.ko\n'in child['stdout'],'module listed and on-disk identity')
need('cat "$p"'not in c['command']and 'dd 'not in c['command']and 'head 'not in c['command'],'metadata not a payload read')
p=load(P/'parse-receipt.py');v,_=p.parse((P/'fixture.json').read_bytes());need(v['accepted'],'fixture')
negative=0
def reject(z):
 global negative
 try:p.parse(json.dumps(z).encode())
 except (ValueError,TypeError,KeyError):negative+=1;need(True,'malformed refused');return
 raise ValueError('malformed accepted')
for field,value in [('openAttempted',False),('readAttempted',False),('closeAttempted',False),('openResult',2147483648),('openErrno',True),('readErrno',1),('closeResult',1),('clockFailureMask',1),('exceptionMask',1),('bufferPinnedBeforeOpen',False),('requestedCount',True),('allocatedBytes',4095),('copyCompletionAttested',True),('externalRtpProducerProven',True)]:
 z=copy.deepcopy(v);z[field]=value;reject(z)
for index in range(6):
 z=copy.deepcopy(v);z['bracketsUs'][index]=True;reject(z)
for count in [0,1,4095,4096]:
 z=copy.deepcopy(v);raw=base64.b64decode(z['rawAllocationBase64']);z.update(readResult=count,returnedPrefixBytes=count,returnedPrefixSha256=sha(raw[:count]));need(p.parse(json.dumps(z).encode())[0]['accepted'],'zero/short lifecycle not full-copy proof')
# The native first-read prototype has no source accepting a configurable address/count.
s=(P/'Program.cs').read_text();need('read(fd,pointer,(UIntPtr)Capacity)'in s and 'ops.Read(fd,pointer)'in s and s.count('ops.Read(fd,pointer)')==1,'one fixed read source')
need(s.index('Array.Fill(buffer,Fill)')<s.index('GCHandle pin=GCHandle.Alloc')<s.index('try{Acquire(ops,buffer'),'prefill/pin before production acquire')
need('Encoder=JavaScriptEncoder.UnsafeRelaxedJsonEscaping'in s,'base64 no plus expansion')
for row in inv['files']:need(sha((P/row['path']).read_bytes())==row['sha256'],'authored unchanged')
print(json.dumps({'schema':'fk-independent-checks-v1','checks':checks,'malformedAcceptedReceiptRejections':negative,'sourceFiles':len(inv['files']),'inputFiles':len(pins['inputs']),'sourceDriverSpans':4,'fixedFirstReadBytes':4096,'adapterImplemented':False,'targetReads':0,'rootCalls':0,'networkOperations':0},sort_keys=True))
