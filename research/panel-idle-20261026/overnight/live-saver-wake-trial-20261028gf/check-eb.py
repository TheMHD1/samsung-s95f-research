#!/usr/bin/env python3
"""Parent offline EB receipt/raw consistency check; no target code import."""
from pathlib import Path
import argparse,hashlib,json,struct,types
P=Path(__file__).resolve().parent;B=P.parent
parserpath=B/'rtp-lane-gate-capture-20261028eb/parse-result.py'
if hashlib.sha256(parserpath.read_bytes()).hexdigest()!='e44f4c96989f895ec8ce8d1f72c9a1d8c1423a28cc1ec5358a885bd9f38d4523':raise ValueError('EBparserpin')
mod=types.ModuleType('eb_offline_parser');mod.__file__=str(parserpath);exec(compile(parserpath.read_bytes(),str(parserpath),'exec'),mod.__dict__)
a=argparse.ArgumentParser();a.add_argument('capture',type=Path);a.add_argument('output',type=Path);args=a.parse_args();c=args.capture
r=json.loads((c/'result.json').read_text());n,raws,i=mod.parse_native((c/'native.receipt.json').read_text())
if r['accepted']is not True or n['accepted']is not True or len(raws)!=16 or r['cleanup']!='STAGE_ABSENT':raise ValueError('acceptedcompletecapture')
if n['protocolPhase']!='ReadyForHeader'or n['released']is not True or n['closed']is not True or n['writes']!=0 or n['uiOperations']!=0:raise ValueError('knownterminal')
if n['headersSent']!=16 or n['bulkTransfers']!=32 or r['headersSent']!=16 or r['bulkTransfers']!=32:raise ValueError('exactcounts')
index={x['name']:x for x in r['rawFiles']}
if len(index)!=16:raise ValueError('uniqueindex')
for name,data,digest in raws:
 if (c/name).read_bytes()!=data or index[name]['bytes']!=len(data)or index[name]['sha256']!=digest or digest!=hashlib.sha256(data).hexdigest():raise ValueError('rawbytes '+name)
rs=[(c/name).read_bytes()for name in ['start-R.bin','end-R.bin']];u=lambda b,o:struct.unpack_from('<H',b,o)[0]
check={'schema':'gf-parent-eb-offline-check-v1','accepted':True,'rawFilesVerified':16,'headers':16,'bulks':32,'device':n['device'],'fullRStartEndEqual':rs[0]==rs[1],'rTuples':[[u(b,0),u(b,10),u(b,14),u(b,196)]for b in rs],'loggerHalfwords':[u(b,6)for b in rs],'bothNZero':all(not any((c/name).read_bytes())for name in ['start-N.bin','end-N.bin']),'c7':(c/'C.bin').read_bytes()[7],'c8':(c/'C.bin').read_bytes()[8],'scan':(c/'M.bin').read_bytes()[56],'protocolPhase':n['protocolPhase'],'released':n['released'],'closed':n['closed'],'cleanup':r['cleanup'],'physicalPictureObserved':False}
if args.output.exists():raise ValueError('freshcheckoutput')
args.output.write_text(json.dumps(check,indent=2)+'\n');print(json.dumps(check))
