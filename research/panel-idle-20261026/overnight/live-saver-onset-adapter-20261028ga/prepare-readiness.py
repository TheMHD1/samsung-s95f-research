#!/usr/bin/env python3
"""Dry-default GA cached identity/census decision; no wake or preparation action."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

HERE=Path(__file__).resolve().parent
B=HERE.parent
ROOT=B/'managed-ui-tab-launch/root-with-margin.py'
ROOT_SHA='bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
WRAPPERS={'ga':('live-saver-onset-adapter-20261028ga/run-once.py','ga-live-saver-event-readiness-decision-v1')}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(path,digest,name):
 raw=path.read_bytes()
 if sha(raw)!=digest:raise ValueError(name+' frozen source identity')
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def main():
 cli=argparse.ArgumentParser(description=__doc__)
 cli.add_argument('--wrapper',required=True,choices=WRAPPERS)
 cli.add_argument('--wrapper-sha256',required=True)
 cli.add_argument('--manifest-sha256',required=True)
 cli.add_argument('--execute',action='store_true')
 cli.add_argument('--identity',required=True,type=Path)
 cli.add_argument('--phase-note',required=True,type=Path)
 cli.add_argument('--evidence',action='append',default=[],type=Path)
 cli.add_argument('--output',required=True,type=Path)
 args=cli.parse_args();relative,schema=WRAPPERS[args.wrapper]
 wrapper=load(B/relative,args.wrapper_sha256,'ga_readiness_wrapper')
 manifest,_=wrapper.build_manifest();manifest_raw=wrapper.manifest_bytes(manifest)
 if sha(manifest_raw)!=args.manifest_sha256 or manifest_raw!=(HERE/'deployment-manifest.json').read_bytes():raise ValueError('sealed GA manifest')
 if not args.output.is_absolute()or args.output.exists()or args.output.is_symlink():raise ValueError('fresh absolute output')
 paths=[args.phase_note,args.identity,*args.evidence]
 if len(paths)>30 or len(set(paths))!=len(paths):raise ValueError('bounded distinct evidence with two fresh slots')
 evidence=[]
 for path in paths:
  if not path.is_absolute()or path.is_symlink()or not path.is_file():raise ValueError('ordinary absolute evidence')
  evidence.append({'path':str(path),'sha256':sha(path.read_bytes())})
 if args.identity.stat().st_size>32768 or args.phase_note.stat().st_size>8192:raise ValueError('bounded identity/phase bytes')
 identity=wrapper.strict_json(args.identity.read_bytes());note_raw=args.phase_note.read_bytes();statement=note_raw.decode().strip()
 if not 40<=len(statement)<=4096:raise ValueError('explicit bounded parent phase premise')
 candidate={'schema':schema,'accepted':True,'identity':identity,'interfaceUnbound':True,'noHolders':True,
  'closedWorldVendorOutLineage':{'accepted':True,'statement':statement,'evidenceSha256':sha(note_raw)},
  'evidence':evidence,'endpointQueueProof':False}
 # Reuse exact wrapper admission before any root import/command construction.
 scratch=HERE/'host-environment/tmp';scratch.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='ga-local-decision-',dir=scratch)as td:
  local=Path(td)/'decision.json';raw=(json.dumps(candidate,indent=2,sort_keys=True)+'\n').encode();local.write_bytes(raw);wrapper.load_readiness(local,sha(raw))
 if not args.execute:
  print(json.dumps({'mode':'dry','manifestSha256':args.manifest_sha256,'targetOperations':0,'cachedMetadataQueries':0,'wrapperUiOperations':0,'preparationPerformed':False}));return
 args.output.mkdir(mode=0o700)
 root=load(ROOT,ROOT_SHA,'ga_readiness_root');record={'schema':'ga-fresh-cached-readiness-v1','calls':[]}
 text=root.root('set -eu\n'+wrapper.metadata_body(identity,'GA_CURRENT_READY'),record,args.output/'metadata-root.json')
 (args.output/'metadata.txt').write_text(text);census=wrapper.parse_metadata(text,'GA_CURRENT_READY')
 (args.output/'census-summary.json').write_text(json.dumps(census,indent=2)+'\n')
 for name in ['metadata.txt','census-summary.json']:
  path=args.output/name;candidate['evidence'].append({'path':str(path),'sha256':sha(path.read_bytes())})
 path=args.output/'readiness.json';raw=(json.dumps(candidate,indent=2,sort_keys=True)+'\n').encode();path.write_bytes(raw);wrapper.load_readiness(path,sha(raw))
 for reference in candidate['evidence']:
  if sha(Path(reference['path']).read_bytes())!=reference['sha256']:raise ValueError('evidence changed after decision')
 print(json.dumps({'accepted':True,'readiness':str(path),'sha256':sha(raw),'census':census,'vendorTransfers':0,'wrapperUiOperations':0,'endpointQueueProof':False,'preparationPerformed':False}))

if __name__=='__main__':main()
