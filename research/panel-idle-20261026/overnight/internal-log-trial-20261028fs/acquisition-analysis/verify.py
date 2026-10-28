#!/usr/bin/env python3
"""Private host-only strict FV/FP replay and bounded internal-log classification."""
from pathlib import Path
import base64,copy,hashlib,json,re,sys,tempfile,types
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;F=D.parent;P=F/'log-read-02';B=F.parent;FV=B/'tcon-log-runtime-group-adapter-20261028fv';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 checks+=1
 if not v:raise ValueError(s)
def j(p):return json.loads(p.read_bytes())
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
for ref in j(D/'input-pins.json')['files']:
 b=(B/ref['path']).read_bytes();need(len(b)==ref['bytes']and sha(b)==ref['sha256'],'frozen input '+ref['path'])
m=load(FV/'run-once.py');manifest,base,payload=m.build_manifest();mb=m.raw_manifest(manifest);need(mb==(P/'reviewed-manifest.json').read_bytes(),'composite exact manifest');parser=load(base.FK/'parse-receipt.py');receipt=(P/'read.receipt.json').read_bytes();native,meaning=parser.parse(receipt);need(meaning==j(P/'interpretation.json')and native['accepted'],'strict FK acceptance')
need(native['requestedCount']==native['allocatedBytes']==4096 and native['readResult']==2161 and native['readCallsMaximum']==1 and native['retries']==native['writesToDriver']==0,'one fixed4096 request')
need(all(native[k]==0 for k in ['openErrno','readErrno','closeErrno','clockFailureMask','exceptionMask'])and native['closeResult']==0,'lifecycle clean')
allocation=base64.b64decode(native['rawAllocationBase64'],validate=True);prefix=allocation[:2161];need(allocation==(P/'allocation.bin').read_bytes()and prefix==(P/'returned-prefix.bin').read_bytes(),'full raw allocation/prefix exact');need(allocation[2161:]==bytes([165])*(4096-2161),'tail initialized0xa5 retained, notcopycertificate')
record=j(P/'record.json');result=j(P/'result.json');family=j(P/'fv-result.json');calls=record['calls'];need(len(calls)==20 and record['nativeInvocations']==1 and record['nativeInvocationStatus']=='one_completed'and record['phase']=='complete'and not record['cleanupRequired'],'terminal20call lifecycle')
for c in calls:
 r=json.loads(base64.b64decode(c['transport_stdout']['data'],validate=True));need(c['transport_exit']==0 and not c['host_timeout']and c['transport_stderr']=={'data':'','encoding':'base64'}and r['authenticated']is True and r['uid']==r['euid']==0,'root transport');child=r['commands'];need(len(child)==1 and child[0]['command']==c['command']and child[0]['exit_code']==0 and not child[0]['timed_out']and child[0]['stderr']=='','exact root child');need(c['command_bytes']==len(c['command'].encode())<=8192 and c['remote_timeout_seconds']==45 and c['host_timeout_limit_seconds']==75,'root command/budgets')
need(sum(' --execute > 'in c['command']for c in calls)==1,'one execute submission')
actual=next(c for c in calls if ' --execute > 'in c['command']);need(actual['command']==base.run_command(payload),'actual exact fixed native command');envelope=(P/'native-envelope.txt').read_text();need(envelope==json.loads(base64.b64decode(actual['transport_stdout']['data']))['commands'][0]['stdout'],'native frame raw-root bound');metadata,framed=base.split_run(envelope);terminal,raw,out,err=base.parse_envelope(framed);need(terminal==record['nativeTerminal']and terminal['exitCode']==0 and terminal['receiptPresent'],'native terminal');need(raw==receipt and out==(P/'native.stdout').read_bytes()and err==(P/'native.stderr').read_bytes()==b'','separate framed receipt/diagnostics')
need(result['accepted']and family['accepted']and family['baseResultSha256']==sha((P/'result.json').read_bytes())and result['manifestSha256']==family['manifestSha256']==sha(mb),'delegate/derivative provenance')
class Replay:
 at=0
 def root(self,command,rec,path):
  need(self.at<len(calls),'no additional command');c=calls[self.at];self.at+=1;need(command==c['command'],'byte-exact actual command replay');rec['calls'].append(copy.deepcopy(c));base.save(path,rec);return json.loads(base64.b64decode(c['transport_stdout']['data']))['commands'][0]['stdout']
replay=Replay();artifacts=0
with tempfile.TemporaryDirectory(dir=D/'private')as tmp:
 dest=Path(tmp)/'acquisition';got=m.execute(dest,manifest,base,payload,replay,parser);need(got==family and replay.at==20,'whole accepted wrapper replay')
 for p in dest.iterdir():need(p.read_bytes()==(P/p.name).read_bytes(),'byte-exact generated artifact '+p.name);artifacts+=1
need(result['cleanup']=='FP_STAGE_ABSENT'and family['cleanup']=='FP_STAGE_ABSENT'and calls[-1]['command'].count('rm -- ')==1 and 'rm -r'not in calls[-1]['command'],'exact owned cleanup')
# No raw identifying text is copied to this analysis. Only categories, numerical claims and hashes.
need(prefix.isascii()and b'\0'not in prefix and prefix.count(b'\n')==110 and len(prefix.splitlines())==111,'110 terminated lines pluspartialtail');lines=prefix.splitlines();need(not prefix.endswith(b'\n')and len(lines[-1])==1,'one-byte unterminated tail')
ins=b'Msgbox ISR In Ch : 2';outs=b'Msgbox ISR out';start=lines.index(ins);mail=lines[start:-1];need(len(mail)==62 and all(x==(ins if i%2==0 else outs)for i,x in enumerate(mail)),'31complete textual mailboxpairs');need(prefix.lower().count(b'rtp')==0,'no RTP substring in returnedprefix scope')
durations=[]
for i,line in enumerate(lines,1):
 match=re.search(rb'(?:\(us\):?|\(us\))\s*:?\s*([0-9]+)$',line)
 if match:durations.append(dict(line=i,valueUs=int(match[1]),meaning='embedded_historical_diagnostic_claim_not_capture_timestamp'))
need(len(durations)==7,'seven embedded duration claims')
# Exact on-disk source-body check, not loaded-module attestation.
sys.path.insert(0,'/tmp/tcon-capstone');from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
module=B/'firmware-platform-analysis-20261028db/private/pltf-extracted/tree/root/lib/modules/5.4.261/kernel/soc/sdp_tcon.ko'
with module.open('rb')as fh:body=ELFFile(fh).get_section_by_name('.text').data()[0x61b0:0x634c]
dis={x.address:(x.mnemonic,x.op_str)for x in Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN).disasm(body,0x61b0)}
for at,op,args in [(0x61cc,'ldrh','w20, [x23]'),(0x6208,'add','w20, w20, #1'),(0x6214,'cmp','w20, #0xfff'),(0x6218,'b.hi','#0x6280'),(0x621c,'mov','x24, x20'),(0x62f0,'mov','x2, x24'),(0x62fc,'nop',''),(0x6300,'b','#0x6258'),(0x626c,'mov','x0, x20')]:need(dis[at]==(op,args),'source length/return anchor '+hex(at))
need(2160+1==2161<=4095 and 2161<4096,'conditional smallbranch advertised2160 plus1')
malformed=0
for k,value in [('requestedCount',4095),('allocatedBytes',4095),('readCallsMaximum',2),('retries',1),('writesToDriver',1),('readResult',4097),('readErrno',5),('closeResult',-1),('accepted',False),('copyCompletionAttested',True),('completeLogProven',True),('externalRtpProducerProven',True),('rawAllocationSha256','0'*64),('returnedPrefixBytes',2160),('returnedPrefixSha256','0'*64),('clockFailureMask',1)]:
 v=copy.deepcopy(native);v[k]=value
 try:parser.parse((json.dumps(v)+'\n').encode())
 except (ValueError,TypeError,KeyError):malformed+=1
 else:raise ValueError('malformed accepted '+k)
need(j(F/'log-read-01/result.json')['accepted']is False and j(F/'log-read-01/record.json')['nativeInvocations']==0,'old preflight refusal untouched')
summary=dict(schema='fs-independent-single-read-acquisition-v1',accepted=True,manifestSha256=sha(mb),nativeReceiptSha256=sha(receipt),allocation=dict(bytes=4096,sha256=sha(allocation),initializedTailBytes=1935,initializedTailByte=165),returnedPrefix=dict(bytes=2161,sha256=sha(prefix),ascii=True,newlineTerminatedLines=110,logicalSplitLines=111,unterminatedTailBytes=1,rtpSubstringOccurrences=0),nativeBracketsUs=native['bracketsUs'],openDurationUs=native['bracketsUs'][1]-native['bracketsUs'][0],readDurationUs=native['bracketsUs'][3]-native['bracketsUs'][2],closeDurationUs=native['bracketsUs'][5]-native['bracketsUs'][4],lineGroups=[dict(firstLine=1,lastLine=start,category='internal_tcon_boot_initialization_configuration_and_embedded_duration_text'),dict(firstLine=start+1,lastLine=start+62,category='alternating_mailbox_ISR_in_channel2_out',pairs=31),dict(firstLine=111,lastLine=111,category='unterminated_single_byte_tail_not_record_certificate')],embeddedDurationClaims=durations,sourceReadBody=dict(moduleSha256=sha(module.read_bytes()),textOffset='0x61b0',bytes=len(body),sha256=sha(body),conditionalAdvertisedHeader=2160,sourceSelectedCopyExtent=2161,positiveReturnDoesNotAttestCopyCompletion=True),rootCommandsReplayed=20,artifactsByteExact=artifacts,maxCommandBytes=max(c['command_bytes']for c in calls),malformedRefusals=malformed,checksPassed=checks,driverWrites=0,usbOperations=0,uiOperations=0,copyCompletionAttested=False,completeLogProven=False,producerFreshnessProven=False,externalRtpProducerProven=False,receiverExecutableIdentified=False,loadedModuleBytesAttested=False,physicalPictureObserved=False,oldPreflightRefusalPreserved=True,targetCallsDuringAnalysis=0,rootCallsDuringAnalysis=0,networkCalls=0)
raw=(json.dumps(summary,sort_keys=True,indent=2)+'\n').encode()
if '--write'in sys.argv:(D/'decoded.json').write_bytes(raw)
else:need(raw==(D/'decoded.json').read_bytes(),'exact derived output')
print(json.dumps({k:summary[k]for k in ['checksPassed','rootCommandsReplayed','artifactsByteExact','malformedRefusals','maxCommandBytes']},sort_keys=True))
