#!/usr/bin/env python3
"""Verify the public CB scientific fixture offline, without importing device tools."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct

SPECS={'R':('0x47012400',256),'M':('0x470004a0',68),'C':('0x47000bc0',16),'H':('0x4700d0e0',96),'L':('0x47010f00',64)}


def verify(fixture: dict) -> dict:
    checks=0
    def need(ok, message):
        nonlocal checks
        if not ok:raise ValueError(message)
        checks+=1
    def integer(value):return type(value) is int and value>=0
    need(fixture['schema']=='public-onset-scientific-fixture-v1','fixture schema')
    native=fixture['native']
    need(native['schema']=='managed-usb-rt-synchronized-key-v1','native schema')
    for field in ['accepted','observationAccepted','onsetObserved','opened','claimed','released','closed']:
        need(native[field] is True,'native acceptance/cleanup '+field)
    for field in ['onsetMissed','physicalPictureObserved','busContentsAltered']:
        need(native[field] is False,'native scope '+field)
    for field in ['writes','retries','overshootUs']:need(type(native[field]) is int and native[field]==0,'zero '+field)
    need(native['terminalReason']=='TransitionCaptured' and native['protocolPhase']=='ReadyForHeader','terminal phase')
    groups=native['retained']
    need([(g['role'],g['cycleIndex']) for g in groups]==[('trigger-baseline',1),('last-clean',5),('transition',6),('post-fault',6)],'retained roles/cycles')
    names=[['R','M','C','H','L','R'],['R','M','C','H','L','R'],['R'],['M','C','H','L','R']]
    rt=[];total_bytes=0;windows=0;previous_end=0;hashes=[]
    for group,expected_names in zip(groups,names,strict=True):
        need([w['name'] for w in group['windows']]==expected_names,'window order')
        need(len(group['transfers'])==2*len(expected_names),'one OUT/IN pair per window')
        for index,window in enumerate(group['windows']):
            name=window['name'];address,size=SPECS[name]
            need(window['address']==address,'fixed read address')
            need(type(window['expected']) is int and type(window['count']) is int and window['expected']==window['count']==size and window['complete'] is True,'complete bounded window')
            data=base64.b64decode(window['rawBase64'],validate=True)
            need(len(data)==size and hashlib.sha256(data).hexdigest()==window['sha256'],'window length/hash')
            hashes.append(window['sha256']);total_bytes+=len(data);windows+=1
            header,reply=group['transfers'][2*index:2*index+2]
            for transfer,direction,count in [(header,'OUT',12),(reply,'IN',size)]:
                need(transfer['direction']==direction and transfer['name']==name+('-header' if direction=='OUT' else '-data'),'transfer role')
                need(all(type(transfer[k]) is int for k in ['expected','count','errno']) and transfer['expected']==transfer['count']==count and transfer['errno']==0,'transfer completion')
                need(integer(transfer['beforeUs']) and integer(transfer['afterUs']) and previous_end<=transfer['beforeUs']<=transfer['afterUs'],'monotonic transfer ordering')
                previous_end=transfer['afterUs']
            if name=='R':
                triple=tuple(struct.unpack_from('<H',data,offset)[0] for offset in (0,10,14))
                classification='Clean' if triple==(0,0,1) else 'Faulted' if triple==(1,0x1001,0) else 'Unexpected'
                need(window['observedRtState']==dict(zip(('stop','fault','ordinaryGate'),triple),classification=classification),'independent RT halfwords')
                rt.append({'cycle':group['cycleIndex'],'role':group['role'],'beforeUs':header['beforeUs'],'afterUs':reply['afterUs'],'classification':classification})
    need(windows==18 and len(rt)==6,'retained inventory')
    need([r['classification'] for r in rt]==['Clean']*4+['Faulted']*2,'clean/fault sequence')
    counts={k:native[k] for k in ['cyclesStarted','cleanCyclesCompleted','cleanCyclesDiscarded','headersSent','inputsCompleted','bulkTransfers']}
    need(all(integer(v) for v in counts.values()),'integer counters')
    need(counts==dict(cyclesStarted=6,cleanCyclesCompleted=5,cleanCyclesDiscarded=4,headersSent=36,inputsCompleted=36,bulkTransfers=72),'global counts')
    need(counts['headersSent']==counts['cleanCyclesCompleted']*6+1+5 and counts['bulkTransfers']==2*counts['headersSent'],'pair arithmetic; baseline duplicate counted once')
    key=native['intervention'];calls=key['calls']
    need(key['key']=='Left' and key['trigger']=='first-full-clean-cycle' and key['attempted'] is True and key['completed'] is True,'one triggered Left workflow')
    need([c['phase'] for c in calls]==['down','up'],'exact down/up')
    for call in calls:
        need(all(call[k] is True for k in ['started','reaped']) and call['timedOut'] is False,'key child completion')
        need(all(type(call[k]) is int and call[k]==0 for k in ['exitCode','stdoutBytes','stderrBytes']),'key result')
        need(integer(call['beforeUs']) and integer(call['afterUs']) and call['beforeUs']<=call['afterUs'],'key time')
    down,up=calls
    need(rt[1]['afterUs']<key['armedUs']<=down['beforeUs']<down['afterUs']<up['beforeUs']<up['afterUs']<=key['endUs'],'baseline then successful down/up ordering')
    clean,fault=rt[3:5]
    need(up['afterUs']<clean['beforeUs']<=clean['afterUs']<fault['beforeUs']<=fault['afterUs'],'last clean and first fault after key Up return')
    need(integer(native['startUs']) and native['startUs']<rt[0]['beforeUs'] and previous_end<=native['endUs']<=native['deadlineUs'],'observation bounds')
    need(key['uiReceiptObserved'] is False and key['physicalPictureObserved'] is False,'key scope')
    physical=fixture['ownerObservation']
    need(physical['darkPanelReported'] is True and physical['exactPhysicalTransitionTimeUs'] is None and physical['physicalLightWithinSoftwareBracketProved'] is False and physical['causalityEstablished'] is False,'separate physical report limits')
    return {'schema':'public-onset-verification-v1','checks':checks,'rawWindows':windows,'rawBytes':total_bytes,'rawWindowSha256':hashes,'globalCounters':counts,'softwareBracket':{'beforeUs':clean['beforeUs'],'afterUs':fault['afterUs'],'widthUs':fault['afterUs']-clean['beforeUs']},'keyUpReturnUs':up['afterUs'],'softwareOnsetObserved':True,'ownerReportedDarkPanel':True,'exactPhysicalTransitionTimeUs':None,'causalityEstablished':False,'scope':'Checks the public scientific subset and internal consistency; original authenticated transport and closed-world phase readiness were independently reviewed privately and are not reauthenticated here. No target operations.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture',nargs='?',type=Path,default=Path(__file__).resolve().parents[1]/'fixtures/onset-cb.json')
    args=parser.parse_args()
    print(json.dumps(verify(json.loads(args.fixture.read_text())),indent=2))
