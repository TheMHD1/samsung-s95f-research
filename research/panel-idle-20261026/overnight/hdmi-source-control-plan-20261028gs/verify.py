#!/usr/bin/env python3
"""Local source/metadata/evidence verification only. Never imports target helpers."""
from pathlib import Path
import hashlib,json,re,subprocess
P=Path(__file__).resolve().parent
H=Path('${S95F_EVIDENCE_ROOT}'); B=H/'panel-idle-20261026/overnight'; L=H/'live-cast'
checks=0
def need(ok,label):
 global checks
 checks+=1
 if not ok: raise ValueError(label)
def read(p): return p.read_text()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def method(text, token):
 marker='METHOD '+token+' '
 need(text.count(marker)==1,'unique method '+token)
 return text.split(marker,1)[1].split('\nMETHOD ',1)[0]
for x in json.loads(read(P/'input-pins.json'))['files']:
 p=Path(x['path']);need(p.is_file() and p.stat().st_size==x['bytes'] and sha(p)==x['sha256'],'input pin '+p.name)
r=L/'sdk/runtime/dotnet';il=L/'il-reader/bin/Release/net6.0/ILReader.dll';api=L/'api-reader/bin/Release/net6.0/ApiReader.dll'
for tool,assembly,filt,out in [(api,'Tizen.TV.Service.SourceList.dll',None,'source-list-api.txt'),(il,'Tizen.TV.Service.SourceList.dll',None,'source-list-il.txt'),(api,'Tizen.TV.Service.CoBA.Core.dll','CurrentSource','current-source-api.txt'),(il,'Tizen.TV.Service.CoBA.Core.dll','CurrentSourceInfo','current-source-il.txt'),(il,'Tizen.TV.Service.CoBA.Core.dll','CurrentSourceMonitor::CheckCurrentSource','current-monitor-il.txt')]:
 argv=[str(r),str(tool),str(L/'framework'/assembly)]+([filt] if filt else [])
 c=subprocess.run(argv,capture_output=True,timeout=20)
 need(c.returncode==0 and not c.stderr and c.stdout==(P/out).read_bytes(),'PEReader reproduction '+out)
c=subprocess.run([str(r),str(il),str(L/'shortcuts/bin/Release/net6.0/HabibiHomeShortcuts.dll'),'researcher.Home.Entry'],capture_output=True,timeout=20)
need(c.returncode==0 and not c.stderr and c.stdout==(P/'shortcut-entry-il.txt').read_bytes(),'compiled Entry IL reproduction')
s=read(P/'source-list-il.txt');a=read(P/'source-list-api.txt')
g=method(s,'0600001f');ch=method(s,'06000021');dec=method(s,'06000028');priv=method(s,'06000003')
for token in ['callvirt PrivilegeChecker','call get_source_list','call DecodeSourceList']:need(token in g,'list edge '+token)
need('call connect_source' in ch and ch.count('call connect_source')==1,'one source connect edge')
need('System.InvalidOperationException::.ctor' in ch,'connect failure throws')
need('http://tizen.org/privilege/internal/default/platform' in priv and 'CynaraCheck' in priv,'platform privilege checker')
need('System.Uri::UnescapeDataString' in dec and 'set_editName' in dec and 'set_detectedName' in dec and 'connect_source' not in dec,'decode edits returned names only')
for name in ['GetSourceList','ChangeSource','get_sourceType','get_editName','get_detectedName','get_uniqueKey','get_connectionState','get_powerState','get_mbrActivityIndex']:need(name in a,'public metadata '+name)
cur=read(P/'current-source-il.txt');getter=method(cur,'06000452');init=method(cur,'06000454')
need('FieldDefinition:0400023e' in getter and 'System.Linq.Enumerable::FirstOrDefault' in getter,'process dictionary currentgetter')
need('newobj' in init and 'stsfld FieldDefinition:0400023e' in init,'current dictionary initialized locally')
mon=read(P/'current-monitor-il.txt')
for v in ['memory/eden/source/current_source','FSConfigAdapter::GetConfigStr','ldstr "source_type"','ldstr "uuid"']:need(v in mon,'S95F source monitor key '+v)
e=method(read(P/'shortcut-entry-il.txt'),'06000010')
for v in ['/usr/share/dotnet.tizen/framework/Tizen.TV.Service.SourceList.dll','ldstr "ChangeSource"','System.Enum::Parse','org.tizen.tv-viewer','AppLauncher::LaunchApp']:need(v in e,'compiled HDMI route '+v)
need('/etc/tizen-release' not in e,'Activate does not repeat buildcheck')
need('Entry.Activate(InstanceID)' in read(L/'shortcuts/Entry.cs'),'tile dispatch')
need(sha(L/'shortcuts/bin/Release/net6.0/HabibiHomeShortcuts.dll')!='37e5ff4b5befa6e48d74a746b8a658d30266b47298af30420292a46447697391','local helper differs historicaldeployment')
need('37e5ff4b5befa6e48d74a746b8a658d30266b47298af30420292a46447697391' in read(L/'shortcut-actions-final.sh'),'historical staged pin')
cap=read(H/'root-access/source/src/samsung_tv_root/capabilities.py')
need('unsupported model:' in cap and 'configuration.model == "qn90f"' in cap and 'configuration.model == "qn90b"' in cap,'generic CLI model refusal')
k=B/'hdmi-blackout-20261027a';d=json.loads(read(k/'apps-to-ugoos-kernel.json'));raw=k/'apps-to-ugoos-kernel.txt'
need(d['accepted'] is True and d['selected_bytes']==raw.stat().st_size and d['selected_sha256']==sha(raw),'historical kernel selected binding')
need(len(d['calls'])==1,'one historical kernelcall')
c=d['calls'][0];need(c['transport_exit']==0 and c['response']['authenticated'] is True and c['response']['uid']==0 and c['response']['euid']==0,'historical root envelope')
need(len(c['response']['commands'])==1 and c['response']['commands'][0]['exit_code']==0 and c['response']['commands'][0]['timed_out'] is False,'historical command completed')
lines=[i for i,line in enumerate(read(raw).splitlines(),1) if '[EXT-HDMI3:' in line]
need(bool(lines),'positive historical HDMI3 literal')
for n,want in [('ugoos-menu-status.json','0x00000000'),('ugoos-movie-black-status.json','0x00000010')]:
 d=json.loads(read(k/n));z=d['execution']['result'];need(d['accepted'] is True and d['read_usable'] is True and d['cleanup_confirmed'] is True,'historical accepted status '+n)
 need(z['status_hex']==want and z['classification']=='kernel_output_written' and z['hardware_status_proved'] is False and z['controller_transaction_proved'] is False,'status bounded meaning '+n)
prog=read(B/'managed-tcon-status-read/Program.cs')
for v in ['0xc010749f','0x1f','0xa55a5aa5','/dev/tztv_tcon']:need(v in prog,'fixed status helper '+v)
remote=read(H/'s95f-remote.py');need('KEY_SOURCE' in remote and 'KEY_HDMI3' not in remote,'ordinary SOURCE only; no direct HDMI3 key')
print(json.dumps({'schema':'gs-local-source-verification-v1','checks':checks,'input_pins':27,'historical_hdmi3_lines':lines,'result':'PASS_HOST_SOURCE_ONLY','current_device_binding':False,'no_target_calls':True},indent=2,sort_keys=True))
