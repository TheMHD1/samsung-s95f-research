#!/usr/bin/env python3
"""Host-only fixed-contract/source/pin qualification; never opens the debugfs path."""
import base64,copy,hashlib,json,pathlib,subprocess,types
P=pathlib.Path(__file__).resolve().parent
B=P.parent
SDK=pathlib.Path('${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet')
checks=0
def need(v,m):
 global checks
 checks+=1
 if not v: raise RuntimeError(m)
s=(P/'Program.cs').read_text()
for absent in ['extern int ioctl','extern IntPtr mmap','extern int lseek','File.ReadAllBytes(Target','File.OpenRead(Target','Thread.Sleep','while(']:need(absent not in s,'forbidden operation '+absent)
for exact in ['internal const int Capacity = 4096','open(Target,0x88000,0)','read(fd,pointer,(UIntPtr)Capacity)','GCHandleType.Pinned','Array.Fill(buffer,Fill)','copyCompletionAttested=false','externalRtpProducerProven=false','completeLogProven=false','0x10b','IntPtr.Size==4','Architecture.Arm']:
 need(exact in s,'fixed source '+exact)
need('Encoder=JavaScriptEncoder.UnsafeRelaxedJsonEscaping'in s,'base64 ASCII does not expand into HTML Unicode escapes')
need(s.count('ops.Read(fd,pointer)')==1,'one direct read call site')
need(s.count('ops.Open()')==1,'one target open call site')
need(s.count('ops.Close(fd)')==1,'one target close call site')
exe=s[s.index('static int Execute()'):s.index('internal sealed class FakeOps')]
need(exe.index('Array.Fill')<exe.index('GCHandle.Alloc')<exe.index('Acquire('),'allocation/pin before acquisition')
need(exe.index('Architecture.Arm')<exe.index('RealOps.getuid()'),'ABI before native libc')
need('1|0x40|0x80|0x80000|0x8000,0x180' in exe,'exclusive0600 receipt nofollow')
pins=json.loads((P/'input-pins.json').read_text())
for f in pins['inputs']:
 p=B/f['path'];b=p.read_bytes();need(len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],'source pin '+f['path'])
lib=B/pins['libcPath']
symbols=subprocess.run(['readelf','-Ws',str(lib)],check=True,capture_output=True,text=True).stdout
for name in ['open','read','close','statx','getuid','geteuid']:need(name+'@@GLIBC_' in symbols,'retained libc symbol '+name)
header=subprocess.run(['readelf','-h',str(lib)],check=True,capture_output=True,text=True).stdout
need('ELF32' in header and 'ARM' in header and 'little endian' in header,'installed-source ARM32 ABI')
native=json.loads((P/'native-tests.json').read_text());need(native['checks']>=131260 and native['targetReads']==native['targetOpens']==0,'pure fake tests')
module=types.ModuleType('fk_receipt');module.__file__=str(P/'parse-receipt.py');exec(compile((P/'parse-receipt.py').read_bytes(),module.__file__,'exec'),module.__dict__)
fixture=(P/'fixture.json').read_bytes();v,info=module.parse(fixture);need(v['accepted']and info['returnedBytes']==4096,'full mock receipt')
mutations=0
def refuse(f):
 global mutations
 try:f()
 except(ValueError,KeyError,TypeError,UnicodeError):need(True,'strict malformed rejection');mutations+=1;return
 raise RuntimeError('unexpected receipt acceptance')
for field in v:
 z=copy.deepcopy(v)
 if type(z[field])is bool:z[field]=not z[field]
 elif type(z[field])is int:z[field]='bad'
 elif type(z[field])is list:z[field]=z[field][:-1]
 else:z[field]='bad'
 refuse(lambda:module.parse(json.dumps(z).encode()))
for field in ['openResult','readResult','closeResult','readErrno','clockFailureMask','exceptionMask']:
 z=copy.deepcopy(v);z[field]=False;refuse(lambda:module.parse(json.dumps(z).encode()))
for index in range(6):
 z=copy.deepcopy(v);z['bracketsUs'][index]=-1;refuse(lambda:module.parse(json.dumps(z).encode()))
refuse(lambda:module.parse(fixture+b'x'))
refuse(lambda:module.parse(b'{"schema":"x",'+fixture[1:]))
refuse(lambda:module.parse(b'x'*16385))
z=copy.deepcopy(v);b=bytearray(base64.b64decode(z['rawAllocationBase64']));b[1:16]=b'\xa5'*15;z.update(readResult=16,returnedPrefixBytes=16,returnedPrefixSha256=hashlib.sha256(b[:16]).hexdigest(),rawAllocationBase64=base64.b64encode(b).decode(),rawAllocationSha256=hashlib.sha256(b).hexdigest());need(module.parse(json.dumps(z).encode())[1]['copyCompletionAttested']is False,'positive-but-partial remains unattested')
z=copy.deepcopy(v);z.update(accepted=False,readResult=-1,readErrno=4,returnedPrefixBytes=0,returnedPrefixSha256=None);need(module.parse(json.dumps(z).encode())[1]['accepted']is False,'read EINTR refusal not promoted')
z=copy.deepcopy(v);z.update(accepted=False,closeResult=-1,closeErrno=4);need(module.parse(json.dumps(z).encode())[1]['accepted']is False,'close EINTR remains refused without retry')
z=copy.deepcopy(v);fill=bytes([165])*4096;z.update(accepted=False,openResult=-1,openErrno=2,readAttempted=False,closeAttempted=False,readResult=-1,readErrno=0,closeResult=-1,closeErrno=0,returnedPrefixBytes=0,returnedPrefixSha256=None,bracketsUs=[1,2,-1,-1,-1,-1],rawAllocationBase64=base64.b64encode(fill).decode(),rawAllocationSha256=hashlib.sha256(fill).hexdigest());need(module.parse(json.dumps(z).encode())[1]['accepted']is False,'open refusal extent/brackets retained')
z.update(openAttempted=False,openErrno=0,bracketsUs=[-1]*6,clockFailureMask=1);need(module.parse(json.dumps(z).encode())[1]['accepted']is False,'preopen clock refusal no IO')
z=copy.deepcopy(v);z.update(accepted=False,clockFailureMask=8);z['bracketsUs'][3]=-1;need(module.parse(json.dumps(z).encode())[1]['accepted']is False,'late clock failure remains refusal')
worst=copy.deepcopy(v)
for k in worst:
 if type(worst[k])is bool:worst[k]=False
for k in ['openResult','readResult','closeResult']:worst[k]=-9223372036854775808
for k in ['openErrno','readErrno','closeErrno']:worst[k]=4095
worst['clockFailureMask']=63;worst['exceptionMask']=31
worst['bracketsUs']=[9223372036854775807]*6
worst_bytes=len(json.dumps(worst,separators=(',',':')).encode())+1;need(len(fixture)<=worst_bytes<16384,'structural receipt bound')
dry=subprocess.run([str(SDK),str(P/'bin/Release/net6.0/TconLogSingleRead.dll')],check=True,capture_output=True,text=True)
need(json.loads(dry.stdout)['targetReads']==0 and not dry.stderr,'default dry')
bad=subprocess.run([str(SDK),str(P/'bin/Release/net6.0/TconLogSingleRead.dll'),'--path','/other'],capture_output=True,text=True)
need(bad.returncode==64 and not bad.stdout,'no arbitrary path option')
abi=subprocess.run([str(SDK),str(P/'bin/Release/net6.0/TconLogSingleRead.dll'),'--execute'],capture_output=True,text=True)
need(abi.returncode==64 and abi.stderr=='FK refused: InvalidOperationException\n' and not abi.stdout,'host ABI refusal before native target path')
print(json.dumps({'schema':'fk-host-qualification-v1','checks':checks,'nativeChecks':native['checks'],'nativeCases':native['cases'],'malformedReceiptRejections':mutations,'pins':len(pins['inputs']),'targetReads':0,'hostExecuteRefusedBeforeNative':True,'loadedModuleBytesAttested':False,'wrapperImplemented':False,'mockReceiptBytes':len(fixture),'structuralReceiptUpperBound':worst_bytes,'receiptCap':16384,'fixedTargetOpenCap':1,'fixedTargetReadCap':1,'fixedTargetCloseCap':1},sort_keys=True))
