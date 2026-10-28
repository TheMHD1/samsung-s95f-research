#!/usr/bin/env python3
"""One GE Live+saver MODE2 prerequisite experiment; dry default, no UI keys."""
import argparse,hashlib,json,re,time,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;B=HERE.parent
ROOT=B/'managed-ui-tab-launch/root-with-margin.py';ROOT_SHA='bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
BV=B/'recovery-quickpath-20261027bv/recover.py';BV_SHA='4fddc3f6e933a19b15ba208e1ffc029ccd7df323c66cdb7ae24157f374e64a0f'
SOURCE_NAMES=['run-once.py','helper.py','policy.py','admit-fault.py','prepare-readiness.py','verify-source.py','test-host.py','README.md','build-host.sh','finalize.py','input-pins.json','production-delta.json']
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def save(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def load(path,pin,name):
 raw=path.read_bytes();need(sha(raw)==pin,'pinned local source '+name)
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(raw,str(path),'exec'),m.__dict__);return m

def build_manifest():
 pins=json.loads((HERE/'input-pins.json').read_bytes())['files']
 for row in pins:
  raw=(B/row['path']).read_bytes();need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'frozen source dependency')
 helper=load(HERE/'helper.py',sha((HERE/'helper.py').read_bytes()),'ge_manifest_helper');payload=helper.contract()
 sources={name:{'bytes':len((HERE/name).read_bytes()),'sha256':sha((HERE/name).read_bytes())}for name in SOURCE_NAMES}
 return {'schema':'ge-live-saver-init-manifest-v1','sources':sources,'nativePayloads':{name:{'bytes':len(raw),'sha256':sha(raw)}for name,raw in payload.items()},'operation':41,'mode':2,'nativeDeadlineSeconds':12,'nativeInvocationsMaximum':1,'wrapperUiOperations':0,'automaticRetries':0,'thresholdWrites':0,'vendorReads':0,'rootTimeoutSeconds':45,'hostTimeoutSeconds':75,'rootCommandCap':8192,'rootResponseCap':65536,'nativeReceiptCap':8192,'nativeStderrCap':4096,'cachedContext':'Live+saver+CSFS','finalQueryToSubmitMaxNs':1000000000,'readinessSchema':'ge-live-saver-init-readiness-decision-v1','physicalPictureObserved':False,'newInstanceAndFreshEbAreParentPostconditions':True},payload

def manifest_bytes(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()

BOOT='00000000-0000-4000-8000-000000000000'
META_KEYS = ['boot', 'sysfsRealpath', 'sysfsStat', 'busnum', 'devnum', 'deviceNode', 'nodeStat',
             'descriptorsSha256', 'configuration', 'authorized', 'runtimeStatus',
             'interfaceNumber', 'alternate', 'interfaceClass', 'interfaceSubClass', 'interfaceProtocol']
DESCRIPTORS = '12010002ef020140e8040120500201020301090262000301048032080b00020202010a09040000010202010a052400100105240100010424020205240600010705830308001009040100020a00000a07050102400010070581024000000904020002ff0000000705820200020007050202000200'

def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON field ' + key)
            result[key] = value
        return result
    def bad(value):
        raise ValueError('non-JSON constant ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)

def load_readiness(path, digest):
    need(type(digest) is str and re.fullmatch('[0-9a-f]{64}', digest), 'readiness digest required')
    need(path.is_absolute() and not path.is_symlink() and path.is_file(), 'local readiness regular absolute file')
    with path.open('rb') as source:
        raw = source.read(32769)
    need(len(raw) <= 32768 and sha(raw) == digest, 'readiness bytes/digest')
    value = strict_json(raw)
    need(type(value) is dict and set(value) == {'schema', 'accepted', 'identity', 'interfaceUnbound',
         'noHolders', 'closedWorldVendorOutLineage', 'evidence', 'endpointQueueProof'}, 'readiness exact fields')
    need(value['schema'] == 'ge-live-saver-init-readiness-decision-v1' and value['accepted'] is True,
         'readiness accepted decision')
    need(value['interfaceUnbound'] is True and value['noHolders'] is True and
         value['endpointQueueProof'] is False, 'readiness metadata/premise distinction')
    premise = value['closedWorldVendorOutLineage']
    need(type(premise) is dict and set(premise) == {'accepted', 'statement', 'evidenceSha256'} and
         premise['accepted'] is True and type(premise['statement']) is str and
         40 <= len(premise['statement']) <= 4096 and
         re.fullmatch('[0-9a-f]{64}', premise['evidenceSha256'] or ''), 'parent closed-world lineage premise')
    need(type(value['evidence']) is list and 1 <= len(value['evidence']) <= 32, 'readiness evidence list')
    for row in value['evidence']:
        need(type(row) is dict and set(row) == {'path', 'sha256'} and type(row['path']) is str and
             1 <= len(row['path']) <= 1024 and re.fullmatch('[0-9a-f]{64}', row['sha256'] or ''), 'evidence reference')
    identity = value['identity']
    need(type(identity) is dict and set(identity) == set(META_KEYS) and
         all(type(item) is str for item in identity.values()), 'readiness exact identity')
    need(identity['boot'] == BOOT and identity['busnum'] == '7' and
         re.fullmatch('[1-9][0-9]{0,2}', identity['devnum']) and int(identity['devnum']) <= 127,
         'readiness boot/bus/address')
    need(identity['deviceNode'] == '/dev/bus/usb/007/' + f"{int(identity['devnum']):03}", 'node address')
    need(re.fullmatch(r'/sys/devices/[A-Za-z0-9_./:+-]+/7-1', identity['sysfsRealpath']) and
         '..' not in identity['sysfsRealpath'].split('/'), 'sysfs realpath')
    need(re.fullmatch('[0-9]+:[0-9]+', identity['sysfsStat']) and
         re.fullmatch(r'bd:[0-9a-f]+:[0-9]+', identity['nodeStat']), 'instance stat identity')
    need(int(identity['nodeStat'].split(':')[1], 16) == 768 + int(identity['devnum']) - 1, 'USB node minor')
    expected = {'descriptorsSha256': sha(bytes.fromhex(DESCRIPTORS)), 'configuration': '1',
                'authorized': '1', 'runtimeStatus': 'active', 'interfaceNumber': '02', 'alternate': '0',
                'interfaceClass': 'ff', 'interfaceSubClass': '00', 'interfaceProtocol': '00'}
    need(all(identity[key] == item for key, item in expected.items()), 'readiness native metadata')
    return value, raw

def metadata_body(*args,**kwargs):
 policy=load(HERE/'policy.py',sha((HERE/'policy.py').read_bytes()),'ge_metadata_policy');return policy.wrapper().metadata_body(*args,**kwargs)
def parse_metadata(*args,**kwargs):
 policy=load(HERE/'policy.py',sha((HERE/'policy.py').read_bytes()),'ge_metadata_policy');return policy.wrapper().parse_metadata(*args,**kwargs)

def execute(output,readiness,readiness_raw,manifest_raw,payload,admission,adapter,clock=time.monotonic_ns):
 need(output.is_absolute()and not output.exists()and not output.is_symlink(),'fresh absolute output')
 output.mkdir(mode=0o700)
 for name,raw in [('readiness-decision.json',readiness_raw),('reviewed-manifest.json',manifest_raw)]: (output/name).write_bytes(raw)
 save(output/'source-fault-admission.json',admission)
 policy=load(HERE/'policy.py',sha((HERE/'policy.py').read_bytes()),'ge_fixed_policy')
 helper=load(HERE/'helper.py',sha((HERE/'helper.py').read_bytes()),'ge_fixed_helper')
 gates=load(BV,BV_SHA,'ge_public_gates')
 result={'schema':'ge-live-saver-init-result-v1','accepted':False,'sourceFaultAdmitted':True,'nativeInvocations':0,'nativeTerminalAccepted':False,'helperCleanupConfirmed':False,'postCachedContextQualified':False,'newInstanceQualified':False,'freshEbBaselineQualified':False,'initializationPrerequisiteQualified':False,'wrapperUiOperations':0,'automaticRetries':0,'thresholdWrites':0,'vendorReads':0,'physicalPictureObserved':False,'rootCauseFixEstablished':False,'manifestSha256':sha(manifest_raw),'readinessSha256':sha(readiness_raw)}
 record={'schema':'ge-initial-context-v1','calls':[]};record_path=output/'initial-root.json'
 try:
  policy.identity_checkpoint(adapter,record,record_path,output,readiness['identity'],'GE_INITIAL_READY')
  result['initialCachedContext']=policy.snapshot(adapter,record,record_path,output,'initial',clock)
  public=output/'initial-public';public.mkdir(mode=0o700);gates.public_gate(public,adapter_module=adapter)
  recovery=helper.execute(output/'mode2',payload,adapter,readiness['identity'],clock)
  result.update(nativeInvocations=1,nativeTerminalAccepted=recovery['accepted'],helperCleanupConfirmed=recovery['cleanup_confirmed'],helperResult=recovery)
  post_record={'schema':'ge-post-context-v1','calls':[]}
  result['postCachedContext']=policy.snapshot(adapter,post_record,output/'post-root.json',output,'post',clock)
  result.update(postCachedContextQualified=True,accepted=True)
 except Exception as error:
  result['errorType']=type(error).__name__;result['error']=str(error)
  # Preserve the helper's own submission/lifecycle evidence on any failure.
  path=output/'mode2/root.json'
  if path.is_file():
   helper_record=json.loads(path.read_bytes());result['nativeInvocations']=helper_record['nativeInvocations'];result['nativeInvocationStatus']=helper_record['nativeInvocationStatus']
  raise
 finally:
  terminal=output/'mode2/helper-terminal.json'
  if terminal.is_file():result['nativeTerminalAccepted']=json.loads(terminal.read_bytes())['nativeTerminalAccepted']
  save(output/'result.json',result)
 return result

def main():
 cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--execute',action='store_true');cli.add_argument('--print-manifest',action='store_true');cli.add_argument('--manifest-sha256');cli.add_argument('--capture',type=Path);cli.add_argument('--capture-result-sha256');cli.add_argument('--readiness',type=Path);cli.add_argument('--readiness-sha256');cli.add_argument('--output',type=Path);args=cli.parse_args()
 need(not(args.execute and args.print_manifest),'one mode')
 if not args.execute and not args.print_manifest:
  print(json.dumps({'schema':'ge-live-saver-init-dry-v1','targetOperations':0,'nativeInvocations':0,'plannedNativeMaximum':1,'operation':41,'mode':2,'nativeDeadlineSeconds':12,'rootTimeoutSeconds':45,'hostTimeoutSeconds':75,'wrapperUiOperations':0,'vendorReads':0,'thresholdWrites':0,'automaticRetries':0,'liveSaverPremiseNotEstablished':True,'parentPostconditionsRequired':True}));return
 manifest,payload=build_manifest();raw=manifest_bytes(manifest)
 if args.print_manifest:print(raw.decode(),end='');return
 need(args.manifest_sha256==sha(raw),'reviewed manifest exact pin')
 need(args.readiness is not None and args.capture is not None and args.output is not None,'explicit source/readiness/output required')
 need(args.output.is_absolute()and not args.output.exists()and not args.output.is_symlink(),'fresh absolute output')
 readiness,ready_raw=load_readiness(args.readiness,args.readiness_sha256)
 for row in readiness['evidence']:
  path=Path(row['path']);need(path.is_absolute()and not path.is_symlink()and path.is_file()and sha(path.read_bytes())==row['sha256'],'current readiness evidence bytes')
 admit=load(HERE/'admit-fault.py',sha((HERE/'admit-fault.py').read_bytes()),'ge_source_admission')
 admission=admit.admit(args.capture,args.capture_result_sha256,readiness['identity'])
 # All local source/phase/receipt admissions precede loading the real root transport.
 adapter=load(ROOT,ROOT_SHA,'ge_fixed_root')
 need(adapter.REMOTE_TIMEOUT_SECONDS==45 and adapter.HOST_TIMEOUT_SECONDS==75 and adapter.MAX_COMMAND==8192 and adapter.MAX_RESPONSE==65536,'root bounds')
 result=execute(args.output,readiness,ready_raw,raw,payload,admission,adapter)
 print(json.dumps(result))
if __name__=='__main__':main()
