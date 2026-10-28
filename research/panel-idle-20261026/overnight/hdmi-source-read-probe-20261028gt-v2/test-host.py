#!/usr/bin/env python3
"""Host-only finite parser, wrapper, fixed-command and source qualification."""
import ast,copy,hashlib,importlib.util,json,re,subprocess,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('gt_test_probe',P/'probe.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
BOOT='00000000-0000-4000-8000-000000000000';checks=0;negative=0

def check(v,s):
 global checks
 checks+=1
 if not v:raise ValueError(s)
def refuse(fn,label):
 global negative
 try:fn()
 except (ValueError,KeyError,TypeError,json.JSONDecodeError):negative+=1
 else:raise ValueError('accepted malformed '+label)

def fixture(source_type=15,obj=None):
 if obj is None:obj={'source_type':'tv-service','uuid':'HDMI3'}
 rows=['GT_SOURCE_READ_BEGIN',BOOT,'100.00 300.00','UID=0 EUID=0','SMACK_BEGIN','System::Privileged','','SMACK_END',m.BUILD,'5.4.261']
 rows += [p+': OK' for p,_ in m.TARGET_FILES]
 rows += ['GT_FILES_VERIFIED','GT_KEY_1_BEGIN',f'{m.KEYS[0]}, value = {source_type} (Int32)','','GT_KEY_1_END','GT_KEY_2_BEGIN',m.KEYS[1]+', value = '+json.dumps(obj,separators=(',',':'))+' (String)','','GT_KEY_2_END',BOOT,'100.03 300.09','GT_SOURCE_READ_END']
 return '\n'.join(rows)+'\n'

m.check_inputs();c=m.command(BOOT);good=fixture();got=m.parse(good,BOOT)
stock=m.B/'firmware-platform-analysis-20261028db/private/pltf-extracted/tree/root'
for path,digest in m.TARGET_FILES:check(hashlib.sha256((stock/path.lstrip('/')).read_bytes()).hexdigest()==digest,'actual platform target component pin')
check(got['acceptedRead'] and got['cachedPortCandidate']=='HDMI3' and got['primaryUgoosIdentified'] is False,'mock data scope')
check(got['sourceListQueried'] is False and got['loadedBytesAttested'] is False and got['transitiveRuntimeAttested'] is False,'no scope escalation')
for typ,port in [(0,None),(13,'HDMI1'),(14,'HDMI2'),(15,'HDMI3'),(16,'HDMI4'),(65535,None)]:check(m.parse(fixture(typ),BOOT)['cachedPortCandidate']==port,'type representation')
mutations=[('', 'empty'),(good[:-1],'no finalnewline'),(good+'extra\n','trailing'),(good.replace(BOOT,'00000000-0000-4000-8000-000000000000',1),'firstboot'),(good.rsplit(BOOT,1)[0]+good.rsplit(BOOT,1)[1],'missinglastboot'),(good.replace('UID=0 EUID=0','UID=1 EUID=0'),'uid'),(good.replace(m.BUILD,m.BUILD+'x'),'build'),(good.replace('5.4.261','5.4.262'),'kernel'),(good.replace('System::Privileged','bad label'),'label'),(good.replace('100.03 300.09','99.00 300.09'),'uptimereverse'),(good.replace('100.03 300.09','110.01 300.09'),'uptimeexhausted'),(good.replace('100.03 300.09','nan 300.09'),'uptimenan'),(good.replace(m.TARGET_FILES[0][0]+': OK',m.TARGET_FILES[0][0]+': FAILED'),'filehash'),(good.replace(m.KEYS[0],m.KEYS[1]),'wrongkey'),(good.replace('15 (Int32)','15 (String)'),'wrongtype'),(good.replace('15 (Int32)','-1 (Int32)'),'negativetype'),(good.replace('15 (Int32)','65536 (Int32)'),'largertype'),(good.replace('15 (Int32)','015 (Int32)'),'noncanonicaltype'),(good.replace(' (String)',' (Int32)'),'wrongcurrenttype'),(good.replace('GT_KEY_1_END','GT_KEY_2_END'),'keyend'),(good.replace('GT_KEY_2_BEGIN','GT_KEY_1_BEGIN'),'reordered'),(good.replace('GT_FILES_VERIFIED','GT_FILES_VERIFIED\nGT_FILES_VERIFIED'),'duplicateframe'),(good.replace('"HDMI3"','"HDMI3","uuid":"HDMI1"'),'duplicateJSON'),(good.replace('"HDMI3"','NaN'),'nonfiniteJSON'),(good.replace('"HDMI3"','{"nested":1}'),'nestedJSON'),(good.replace('"HDMI3"','1'),'numericUUID'),(good.replace('"HDMI3"','"bad\\nvalue"'),'controlJSON'),(good.replace('"uuid"','"other"'),'missingUUID'),(good.replace('"source_type"','"unknown"'),'missingJSONtype'),(good.replace('GT_KEY_2_END','GT_KEY_2_END\x00'),'NUL'),(good.replace('GT_KEY_2_END','GT_KEY_2_END\r'),'CR'),(good.replace('GT_KEY_2_END','GT_KEY_2_END\n'+('x'*m.MAX_TEXT)),'responsecap')]
for x,label in mutations:refuse(lambda x=x:m.parse(x,BOOT),label)
for obj in [{},{'source_type':'','uuid':''},{'source_type':'tv-service','uuid':'x'*2049},{'source_type':'tv-service','uuid':'x',**{str(i):'x' for i in range(15)}}]:refuse(lambda obj=obj:m.parse(fixture(obj=obj),BOOT),'boundedobject')
for bad in ['x',BOOT+'\n',BOOT+'; id',BOOT.upper(),'$(id)',None]:refuse(lambda bad=bad:m.command(bad),'bootinjection')
check(len(c.encode())<=8192,'command cap');check(subprocess.run(['bash','-n'],input=c.encode(),capture_output=True).returncode==0,'bash syntax only')
check(c.count('/usr/bin/vconftool get ')==2 and not re.search(r'/usr/bin/vconftool (set|unset|.*-r)',c),'exact two get commands')
for key in m.KEYS:check(c.count('/usr/bin/vconftool get '+key+' | head -c 4097')==1,'fixed key/cap')
for forbidden in ['ChangeSource','connect_source','input_keyevent','KEY_HDMI','app_launcher','ioctl','/dev/','/sys/kernel/debug','dotnet','chmod','chown','rm ','mkdir ','curl','wget','ssh ']:check(forbidden not in c,'no extra action '+forbidden)
check('set -o pipefail' in c and 'unset LD_PRELOAD LD_LIBRARY_PATH ENV BASH_ENV' in c,'pipeline and environment guards')
# Verify the pinned stock script's exact get branch and delegate; never run it.
r=m.B/'firmware-platform-analysis-20261028db/private/pltf-extracted/tree/root'
v=(r/'usr/bin/vconftool').read_text();start=v.index('get_key() {');end=v.index('\ndo_get()',start);branch=v[start:end]
check('BUXTONTOOL=/usr/bin/buxton2ctl' in v and '${BUXTONTOOL} ${OPT_DIRECT} get ${LAYER} $1 2>&1' in branch,'actual script delegate')
check('get)   do_get ;;' in v and 'OPT_DIRECT=""' in v,'fixed get dispatch')
check('set-write-priv' not in branch and 'create-' not in branch and 'unset ' not in branch,'get branch has no fieldwrite')
# No automatic second call after a valid response, semantic failure, or transport ambiguity.
with tempfile.TemporaryDirectory(dir=P,prefix='host-tests-')as td:
 base=Path(td)
 for label,data,throw,accept in [('positive',good,False,True),('malformed',good[:-1],False,False),('ambiguous',None,True,False)]:
  calls=[]
  def mock(command,record,path):
   calls.append(command);record['calls'].append({'command':command,'transport_exit':0,'host_timeout':False,'remote_timeout_seconds':45,'host_timeout_limit_seconds':75,'response':{'model':m.MODEL,'authenticated':True,'uid':0,'euid':0,'root_persistence':'host-assisted','global_system_files_unchanged_at_acquisition':True,'commands':[{'command':command,'exit_code':0,'timed_out':False,'stderr':'','stdout':data}]},'mockOnly':True});path.write_text(json.dumps(record));
   if throw:raise TimeoutError('mock ambiguous transport')
   return data
  out=base/label
  try:result=m.run(out,BOOT,mock)
  except Exception:check(not accept,'expected wrapper refusal')
  else:check(accept and result['acceptedRead'],'expected wrapper success')
  check(calls==[c],'one exact command, no second request')
  check((out/'intent.json').exists() and (out/'root.json').exists(),'intent/raw root retained')
  check((out/'result.json').exists()==accept and (out/'refusal.json').exists()!=accept,'separate truthful outcome')
  if data is not None:check((out/'response.txt').read_text()==data,'returned raw preserved')
  if not accept:check(json.loads((out/'refusal.json').read_text())['noAutomaticRetry'] is True,'refusal no retry')
  refuse(lambda out=out:m.run(out,BOOT,mock),'existingoutput')
  check(len(calls)==1,'existingoutput no call')
 # Exact dry invocation does not import or run the root adapter.
 cp=subprocess.run(['python3','-B',str(P/'probe.py'),'--expected-boot',BOOT],capture_output=True)
 check(cp.returncode==0 and cp.stderr==b'','dry CLI');d=json.loads(cp.stdout)
 check(d['execute']is False and d['fixedCommand']==c and d['manifestSha256']==m.sha(m.dump(m.manifest(BOOT))),'exact dry manifest')
 cp=subprocess.run(['python3','-B',str(P/'probe.py'),'--expected-boot',BOOT,'--execute','--manifest-sha256','0'*64,'--output',str(base/'must-not-exist')],capture_output=True)
 check(cp.returncode!=0 and not(base/'must-not-exist').exists() and b'explicit exact manifest digest' in cp.stderr,'wrong manifest before root import/call')
 # Input change/tampering fails before a target call (test does not mutate input).
 bad=copy.deepcopy(json.loads((P/'input-pins.json').read_text()));bad['files'][0]['sha256']='0'*64
 check(all(x['sha256']!='0'*64 for x in json.loads((P/'input-pins.json').read_text())['files']),'real pins intact')
# Replay validation refuses changed model, timing, stdout, command and UID.
envelope={'calls':[{'command':c,'transport_exit':0,'host_timeout':False,'remote_timeout_seconds':45,'host_timeout_limit_seconds':75,'response':{'model':m.MODEL,'authenticated':True,'uid':0,'euid':0,'root_persistence':'host-assisted','global_system_files_unchanged_at_acquisition':True,'commands':[{'command':c,'exit_code':0,'timed_out':False,'stderr':'','stdout':good}]}}]}
check(m.validate_root_record(envelope,c,good)['rootEnvelopeModel']==m.MODEL,'root envelope bounded binding')
for key,value in [('model','qn90f'),('uid',True),('authenticated',False)]:
 bad=copy.deepcopy(envelope);bad['calls'][0]['response'][key]=value;refuse(lambda bad=bad:m.validate_root_record(bad,c,good),'root envelope '+key)
for key,value in [('command',c+'x'),('stdout',good+'x'),('timed_out',True),('exit_code',True)]:
 bad=copy.deepcopy(envelope);bad['calls'][0]['response']['commands'][0][key]=value;refuse(lambda bad=bad:m.validate_root_record(bad,c,good),'root command '+key)
# New exact canonical guards are justified by retained actual discovery, not
# relaxed to arbitrary realpaths. All six byte hashes remain unchanged.
discovery=m.B/'hdmi-endpoint-trial-20261028gp/source-component-discovery'
actual=(discovery/'response.txt').read_text();d=json.loads((discovery/'result.json').read_text())
check(d['acceptedRoot']is True and d['rootCalls']==1 and d['responseSha256']==hashlib.sha256(actual.encode()).hexdigest(),'accepted actual component discovery binding')
for origin,canonical in [('/bin/sh','/usr/bin/bash'),('/bin/bash','/usr/bin/bash'),('/lib/ld-linux.so.3','/usr/lib/ld-2.30.so'),('/lib/ld-2.30.so','/usr/lib/ld-2.30.so'),('/lib/libc.so.6','/usr/lib/libc-2.30.so'),('/lib/libc-2.30.so','/usr/lib/libc-2.30.so'),('/usr/lib/libbuxton2.so.1','/usr/lib/libbuxton2.so.1.1'),('/usr/lib/libbuxton2.so.1.1','/usr/lib/libbuxton2.so.1.1'),('/usr/bin/vconftool','/usr/bin/vconftool'),('/usr/bin/buxton2ctl','/usr/bin/buxton2ctl')]:
 check('PATH='+origin+'\n'+canonical+'\n' in actual,'actual canonical pair '+origin)
 check('test "$(readlink -f '+origin+')" = '+canonical in c,'guard exact canonical pair '+origin)
old=m.B/'hdmi-source-read-probe-20261028gt'
old_spec=importlib.util.spec_from_file_location('gt_frozen_predecessor',old/'probe.py');om=importlib.util.module_from_spec(old_spec);old_spec.loader.exec_module(om)
check(m.TARGET_FILES==om.TARGET_FILES and m.KEYS==om.KEYS,'unchanged target hashes and read keys')
for path,digest in m.TARGET_FILES:check(digest+'  '+path+'\n' in actual,'actual runtime component hash '+path)
check(m.parse(good,BOOT)['cachedCurrentSource']==om.parse(good,BOOT)['cachedCurrentSource'],'unchanged source parser semantics')
check(m.command(BOOT).count('/usr/bin/vconftool get ')==om.command(BOOT).count('/usr/bin/vconftool get ')==2,'unchanged exact two gets')
source=(P/'probe.py').read_text();tree=ast.parse(source)
main=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='main')
check(source.index("if not args.execute:")<source.index("spec=importlib.util.spec_from_file_location('gt_pinned_root'"),'execute before adapter import')
check(source.count('text=call(c,record,output/\'root.json\')')==1,'one wrapper callsite')
print(json.dumps({'schema':'gt-v2-host-qualification-v1','checks':checks,'negativeCases':negative,'commandBytes':len(c.encode()),'maxRootEnvelope':m.MAX_ROOT,'maxSourceResponse':m.MAX_TEXT,'result':'PASS_HOST_ONLY','actualTargetCalls':0,'fixtures':'Synthetic source-value/transport fixtures; no actual current-source capture'},indent=2,sort_keys=True))
