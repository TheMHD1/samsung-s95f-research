#!/usr/bin/env python3
"""Replay one fixed accepted DP baseline and subsequent DM capture, offline only."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent
DP = BASE / 'rtp-score-checkpoints-20261028dp'
DM = BASE / 'rtp-record-capture-20261028dm'
TRIAL = BASE / 'volatile-limit-trial-20261028dk'
checks = 0

def need(condition, message):
    global checks
    checks += 1
    if not condition:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def u16(raw, off):
    return struct.unpack_from('<H', raw, off)[0]

def decode(name, raw):
    if name == 'R':
        return {k:u16(raw, off) for k,off in (
            ('stop',0),('fault',10),('ordinaryGate',14),('normalThreshold',0x30),
            ('actionBucket',0x86),('mode1RecordLatch',0x90),('alternateThreshold',0xc4))}
    if name == 'H':
        return {'aU32':list(struct.unpack_from('<6I',raw,4)),
                'qU16':list(struct.unpack_from('<6H',raw,28)),
                'historyU16x4':[list(struct.unpack_from('<4H',raw,40+8*i)) for i in range(6)]}
    if name == 'N':
        return {'ordinals':list(struct.unpack_from('<6I',raw)),
                'sourceCounts':list(struct.unpack_from('<6H',raw,24))}
    if name == 'M':
        return {'aa':u16(raw,10),'ac':u16(raw,12),'publicationBoundMirror':u16(raw,42)}
    if name == 'C':
        return {'geometryU16':list(struct.unpack_from('<3H',raw)), 'selectorC7':raw[7]}
    return None

def analyze():
    pins = json.loads((HERE/'input-pins.json').read_text())
    need(pins['base']==str(BASE), 'fixed input base')
    for item in pins['files']:
        data=(BASE/item['path']).read_bytes()
        need(len(data)==item['bytes'] and sha(data)==item['sha256'], 'source pin '+item['path'])
    # Explicit known frozen source anchors, independent of generated input inventory.
    for p,h in [(DP/'parse-result.py','9b5e476a50e73439e11a6e5ed78bae0079a1d802c054212a8974e079f77d6b3a'),
                (DM/'parse-result.py','fa2401bf270583fd793d44150b5db70915504c72e39878a8dd9f24a9be6446ca'),
                (DP/'deployment-manifest.json','ba02517d7f8bb5cae6aa4257c426b7cc50780bfdfd5e0a73a7838e2386dff9ee')]:
        need(sha(p.read_bytes())==h,'frozen source '+p.name)
    native,_,files,gc,qualification=load(DP/'parse-result.py','dp_frozen').parse_native((TRIAL/'score-baseline-01/native.receipt.json').read_text())
    need(gc==[] and qualification['trialQualified'] is True,'strict qualified receipt')
    need(qualification==json.loads((TRIAL/'score-baseline-01/interpretation.json').read_text()), 'saved DP interpretation exact replay')
    for name,data,digest in files:
        need(sha(data)==digest and (TRIAL/'score-baseline-01'/name).read_bytes()==data,'DP saved raw '+name)
    packed=(TRIAL/'score-baseline-01/score-checkpoints.bin').read_bytes()
    need(len(packed)==5*34,'five compact full-clean checkpoints only')
    rows=[]
    for i in range(5):
        r=packed[34*i:34*i+34]
        row={'cycleIndex':i+1,'startRtClass':r[0]>>4,'endRtClass':r[0]&15,'selectorC7':r[1],
             'startRc4':u16(r,2),'endRc4':u16(r,4),'a0U32':struct.unpack_from('<I',r,6)[0],
             'q0':u16(r,10),'history0':list(struct.unpack_from('<4H',r,12)),
             'ordinal0':struct.unpack_from('<I',r,20)[0],
             'hHeaderBeforeUs':native['startUs']+struct.unpack_from('<I',r,24)[0],
             'hDataAfterUs':native['startUs']+struct.unpack_from('<I',r,28)[0],
             'publicationBoundMirror':u16(r,32)}
        q=qualification['scoreCheckpoints']['rows'][i]
        for k,v in [('a0U32',row['a0U32']),('selectorC7',row['selectorC7']),('publicationBoundMirror',row['publicationBoundMirror']),
                    ('q0U16',row['q0']),('recordOrdinal0U32',row['ordinal0']),('history0U16x4',row['history0'])]:
            need(q[k]==v,'independent checkpoint '+k)
        need(q['hReadBracket']=={'headerBeforeUs':row['hHeaderBeforeUs'],'dataAfterUs':row['hDataAfterUs']},'independent H bracket')
        need(row['startRtClass']==row['endRtClass']==0 and row['startRc4']==row['endRc4']==40,'clean alternate40 bracket')
        rows.append(row)
    need([r['a0U32'] for r in rows]==[0,0,0,0,38],'actual clean A0')
    need([r['selectorC7'] for r in rows]==[0,0,1,1,1],'actual selector progression')
    need([r['publicationBoundMirror'] for r in rows]==[200,200,200,40,40],'actual mirror progression')
    captures=[]
    for cap in native['retained']:
        windows=[]
        for j,w in enumerate(cap['windows']):
            raw=base64.b64decode(w['rawBase64'],validate=True)
            need(sha(raw)==w['sha256'] and len(raw)==w['expected']==w['count'],'retained raw hash/extent')
            t=cap['transfers'][2*j:2*j+2]
            need(len(t)==2 and t[0]['beforeUs']<=t[1]['afterUs'],'paired bracket')
            windows.append({'name':w['name'],'address':w['address'],'sha256':sha(raw),
                            'headerBeforeUs':t[0]['beforeUs'],'dataAfterUs':t[1]['afterUs'],
                            'decoded':decode(w['name'],raw)})
        captures.append({'role':cap['role'],'cycleIndex':cap['cycleIndex'],'windows':windows})
    byrole={x['role']:x for x in captures}
    get=lambda role,name:[w for w in byrole[role]['windows'] if w['name']==name]
    lastH=get('last-clean','H')[0]; postH=get('post-fault','H')[0]
    need(lastH['decoded']['aU32'][0]==38 and postH['decoded']['aU32'][0]==42,'actual fault42, not44')
    need(lastH['decoded']['historyU16x4'][0]==[0,4,0,4] and postH['decoded']['historyU16x4'][0]==[4,0,4,0],'actual history shift')
    need(get('last-clean','N')[0]['decoded']['sourceCounts']==[4,0,0,0,0,0],'last-clean current source counts')
    need(get('post-fault','N')[0]['decoded']['sourceCounts']==[0]*6,'post-fault current source counts')
    cleanR=get('last-clean','R')[-1];faultR=get('transition','R')[0]
    bracket={'headerBeforeUs':cleanR['headerBeforeUs'],'dataAfterUs':faultR['dataAfterUs'],
             'widthUs':faultR['dataAfterUs']-cleanR['headerBeforeUs']}
    order=qualification['ordering']
    need(bracket['headerBeforeUs']==order['softwareTransitionBracket']['beforeUs'] and bracket['dataAfterUs']==order['softwareTransitionBracket']['afterUs'],'transition software bracket exact')
    key=native['intervention'];need(bracket['headerBeforeUs']>key['calls'][0]['afterUs'],'bracket strictly after keydown return')
    dm,dmfiles,dmi=load(DM/'parse-result.py','dm_frozen').parse_native((TRIAL/'record-fault-01/native.receipt.json').read_text())
    need(dmi==json.loads((TRIAL/'record-fault-01/interpretation.json').read_text()),'DM saved interpretation exact replay')
    for name,data,digest in dmfiles:
        need(sha(data)==digest and (TRIAL/'record-fault-01'/name).read_bytes()==data,'DM raw '+name)
    need(dmi['startR']==dmi['endR'] and dmi['startN']==dmi['endN'],'matching sequential DM R/N')
    need(dmi['startR']['fault']==4097 and dmi['startN']['ordinals'][0]==41,'postfault DM latch')
    need(dmi['recordEpochProven'] is False and dmi['actualFixedABranchProven'] is False,'DM limited claims')
    need(native['headersSent']==native['inputsCompleted']==48 and native['bulkTransfers']==96,'original transport counters')
    need(native['cleanCyclesCompleted']==5 and native['cleanCyclesDiscarded']==4 and native['cyclesStarted']==6,'original cycle counters')
    need(sum(len(c['windows']) for c in captures)==24,'retained windows include duplicate baseline')
    # Six cycles: five complete sets (40 pairs), partial transition R (1), postfault set (7).
    # Saved trigger baseline duplicates an already-counted full cycle; not an extra cycle.
    result={'schema':'dp-live-baseline-independent-analysis-v1','checks':checks,
            'transport':{k:native[k] for k in ('headersSent','bulkTransfers','inputsCompleted','cleanCyclesCompleted','cleanCyclesDiscarded','cyclesStarted','writes','retries','released','closed','protocolPhase')},
            'uniqueRetainedWindows':24,'rawWindowsFromFiveCleanPlusTransitionPlusPostfault':48,
            'checkpointRows':rows,'retainedCaptures':captures,'keyWorkflow':key,
            'softwareTransitionBracket':bracket,'qualification':qualification,
            'postfaultDM':dmi,
            'conclusions':{'actualPostfaultA0':42,'lastCleanA0':38,'sampledCleanAbove40Witness':False,
             'absenceOfWitnessExcludesUnsampledCrossing':False,'actualFpProven':False,
             'actualSelectedAProven':False,'keyCausedFaultProven':False,'physicalPictureObserved':False,
             'mode1FromRetainedAaAc':True,'retainedWindowCountDoesNotReplaceTransportCounts':True},
            'sourceAnchors':{'score':'H+4 u32, low16 compared; q0 H+28; history0 H+40..47',
             'sourceCounts':'N+24..35 six u16, reset every dispatch; not lifetime totals',
             'ordinal':'N+0..23 six u32; publication bound inclusive, 40 allows indices0..40 then ordinal41',
             'mode':'M+10 aa0/M+12 ac2 -> mode1 in selected image1 VA1e68..203e',
             'threshold':'mode1 C+7 nonzero chooses R+c4; zero chooses R+30; M+2a is sequential publication mirror',
             'records':'selected image1 VAc666/c676/c686/c696/c6a6 stores X/Y/RGB/B/absdiff (type6 zero)',
             'fixedA':'actual Bheader+6 and decision-time registers not captured; current M row is not Bheader'}}
    return result

if __name__=='__main__':
    result=analyze()
    text=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if sys.argv[1:]==['--check']:
        need((HERE/'decoded.json').read_text()==text,'reproducible decoded artifact')
        print(json.dumps({'accepted':True,'checks':checks,'decodedSha256':sha(text.encode()),'hostOnly':True}))
    elif not sys.argv[1:]:
        (HERE/'decoded.json').write_text(text)
        print(json.dumps({'accepted':True,'checks':checks,'decodedSha256':sha(text.encode()),'hostOnly':True}))
    else:
        raise SystemExit('usage: analyze.py [--check]')
