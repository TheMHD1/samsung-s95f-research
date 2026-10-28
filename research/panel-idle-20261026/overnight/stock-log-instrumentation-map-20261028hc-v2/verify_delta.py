#!/usr/bin/env python3
"""Exact additive v1/v2 production transformation; no target calls."""
import ast,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;B=HERE.parent;OLD=B/'stock-log-instrumentation-map-20261028hc'
checks=0

def need(v,why):
 global checks
 if not v:raise ValueError(why)
 checks+=1

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 old=(OLD/'stock_log.py').read_bytes();need(sha(old)=='f6730ccd8c9dd8bc928a60eb602e03f6aa9592f12d5a474f1d304fabf495ccf4','frozen v1 exact source')
 source=(HERE/'stock_log.py').read_text();s=old.decode()
 changes=[("SCHEMA = 's95f-stock-log-hc-v1'","SCHEMA = 's95f-stock-log-hc-v2'"),
 ("'/tmp/s95f-stock-log-' + nonce","'/tmp/s95f-stock-log-v2-' + nonce"),
 ("[ \"$(stat -c '%F:%u:%g:%a' \"$stage/kernel.raw\")\" = 'regular file:0:0:600' ]","[ -f \"$stage/kernel.raw\" ]\n[ \"$(stat -c '%u:%g:%a' \"$stage/kernel.raw\")\" = '0:0:600' ]"),
 ("[ \"$(stat -c '%F:%u:%g:%a' \"$stage/stderr.raw\")\" = 'regular file:0:0:600' ]","[ -f \"$stage/stderr.raw\" ]\n[ \"$(stat -c '%u:%g:%a' \"$stage/stderr.raw\")\" = '0:0:600' ]"),
 ("[ \"$(stat -c '%F:%u:%g:%a' \"$stage\")\" = 'directory:0:0:700' ]","[ -d \"$stage\" ]\n[ \"$(stat -c '%u:%g:%a' \"$stage\")\" = '0:0:700' ]"),
 ("[ \"$(stat -c '%F:%u:%g:%a:%s' \"$stage/kernel.raw\")\" = 'regular file:0:0:600:{row['rawBytes']}' ]","[ -f \"$stage/kernel.raw\" ]\n[ \"$(stat -c '%u:%g:%a:%s' \"$stage/kernel.raw\")\" = '0:0:600:{row['rawBytes']}' ]"),
 ("[ \"$(stat -c '%F:%u:%g:%a:%s' \"$stage/stderr.raw\")\" = 'regular file:0:0:600:{row['stderrBytes']}' ]","[ -f \"$stage/stderr.raw\" ]\n[ \"$(stat -c '%u:%g:%a:%s' \"$stage/stderr.raw\")\" = '0:0:600:{row['stderrBytes']}' ]")]
 for before,after in changes:
  need(s.count(before)==1,'one exact reviewed replacement');s=s.replace(before,after)
 need(s==source,'whole production source changes only explicit type proof/schema/prefix')
 a={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)}
 z={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
 need(a.keys()==z.keys(),'same functions')
 changed={'identifiers','capture_command','fetch_command'}
 for name in a:
  if name not in changed:need(a[name]==z[name],'byte-semantic unchanged function '+name)
 for guard in ['[ ! -L "$stage/kernel.raw" ]','[ ! -L "$stage/stderr.raw" ]',"= '0:0:600' ]","= '0:0:700' ]",'fileCount=2','ulimit -f 2048 && dmesg','sha256sum']:
  need(guard in source,'retained ownership/type/cap/hash contract '+guard)
 need('%F'not in source,'no human-description type equality remains')
 inspection=B/'menu-recovery-branch-trial-20261028hf/baseline-stage-inspection/response.txt';data=inspection.read_bytes();text=data.decode()
 need('regular file:0:0:600:500857'in text,'actual retained nonempty raw type')
 need('regular empty file:0:0:600:0'in text,'actual retained empty stderr type')
 need('fdfa320430224b166d3e37f03f51c297f18ee87b13b13f114b7c3f87424a0150'in text,'actual retained raw hash')
 return dict(schema='hc-v2-exact-delta-v1',checks=checks,v1SourceSha256=sha(old),v2SourceSha256=sha(source.encode()),
  exactReplacementCount=len(changes),unchangedFunctions=sorted(set(a)-changed),
  v1InventorySha256=sha((OLD/'source-inventory.json').read_bytes()),
  actualTypeObservation={'path':str(inspection.relative_to(B)),'bytes':len(data),'sha256':sha(data)},
  originalDmesgExitKnown=False,originalCapturePromoted=False,targetCalls=0,networkCalls=0)
if __name__=='__main__':print(json.dumps(main(),indent=2,sort_keys=True))
