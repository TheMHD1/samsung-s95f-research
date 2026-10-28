#!/usr/bin/env python3
"""Offline validation of the separate clean200/clean40 comparison; no TV code."""
import argparse,base64,hashlib,json,struct
from pathlib import Path
from verify_rtp import DP_KEYS,DP_SPECS

DV_KEYS=set(('schema','action','protocolPhase','stage','opened','claimed','released','closed',
             'writeAttempted','writeTransportComplete','readbackVerified','limitMayHaveChanged',
             'accepted','physicalPictureObserved','rootCauseFixEstablished','headersSent',
             'bulkTransfers','errors','steps','windows'))

def verify(f):
    checks=raw_bytes=raw_windows=0
    def need(ok,label):
        nonlocal checks
        checks+=1
        if not ok:raise ValueError(label)
    def num(v):return type(v)is int and 0<=v<2**63
    def half(b,o):return struct.unpack_from('<H',b,o)[0]
    def raw(w,size,field='base64'):
        nonlocal raw_bytes,raw_windows
        need(type(w[field])is str and type(w['sha256'])is str,'raw types')
        b=base64.b64decode(w[field],validate=True)
        need(len(b)==size and base64.b64encode(b).decode()==w[field]and hashlib.sha256(b).hexdigest()==w['sha256'],'raw extent/hash/canonical encoding')
        raw_bytes+=size;raw_windows+=1;return b
    def lifecycle(n):
        for k in ('accepted','opened','claimed','released','closed'):need(n[k]is True,'accepted lifecycle')
        need(n['protocolPhase']=='ReadyForHeader'and n['physicalPictureObserved']is False,'phase and physical scope')
    def step(s,name,direction,size,last,phases=None):
        fields={'name','direction','expected','count','errno','beforeUs','afterUs'}
        if phases:fields|={'before','after'}
        need(set(s)==fields,'transfer whitelist')
        need(s['name']==name and s['direction']==direction,'transfer identity')
        need(all(type(s[k])is int for k in ('expected','count','errno'))and s['expected']==s['count']==size and s['errno']==0,'transfer exact count')
        need(num(s['beforeUs'])and num(s['afterUs'])and last<=s['beforeUs']<=s['afterUs'],'transfer monotonic bracket')
        if phases:need((s['before'],s['after'])==phases,'transfer protocol phase')
        return s['afterUs']
    need(set(f)=={'schema','notice','source','set200','observe200','restore40','rechallenge40'}and f['schema']=='public-rtp-limit-comparison-v1','fixture schema')
    need(f['source']=={'workstream':'panel-idle-20261026/overnight/volatile-limit-trial-20261028dk','captures':['dv-set-01','dv-observation-01','dv-restore-01','dv-rechallenge-01'],'writeAddress':'0x470124c4','writeBytes':2,'writeHeaderHex':'02010000c424014702000000'},'fixed source/field mapping')
    def writer(label,old,new):
        n=f[label];need(set(n)==DV_KEYS and n['schema']=='dv-fixed-limit-v1','writer whitelist');lifecycle(n)
        need(n['action']==('set40to200'if new==200 else'restore200to40')and n['stage']=='complete','writer action')
        for k in ('writeAttempted','writeTransportComplete','readbackVerified'):need(n[k]is True,'write/readback acceptance')
        need(n['limitMayHaveChanged']is False and n['rootCauseFixEstablished']is False and n['errors']==[],'write scope and ambiguity')
        need(type(n['headersSent'])is int and n['headersSent']==7 and type(n['bulkTransfers'])is int and n['bulkTransfers']==14,'writer counts')
        names=[('callbacks',64),('baseline-R',256),('pre-M',68),('pre-C',16),('fresh-R',256),('readback-R',256)]
        need(len(n['windows'])==6 and len(n['steps'])==14,'writer frame')
        decoded={}
        for w,(name,size)in zip(n['windows'],names,strict=True):
            need(w['name']==name and type(w['bytes'])is int and w['bytes']==size,'writer window extent')
            if name=='callbacks':need(w=={'name':'callbacks','bytes':64,'rawOmitted':True},'OEM callback bytes omitted')
            else:
                need(set(w)=={'name','bytes','sha256','base64'},'writer scientific raw whitelist');decoded[name]=raw(w,size)
        last=0
        pairs=names[:5]+[('write',2)]+names[5:]
        for i,(name,size)in enumerate(pairs):
            write=name=='write';phase='ExpectingWritePayload'if write else'ExpectingReadIn'
            last=step(n['steps'][2*i],name+'-header','OUT',12,last,('ReadyForHeader',phase))
            last=step(n['steps'][2*i+1],name+('-payload'if write else'-data'),'OUT'if write else'IN',size,last,(phase,'ReadyForHeader'))
        for name in ('baseline-R','fresh-R','readback-R'):
            b=decoded[name];need(tuple(half(b,o)for o in (0,10,14))==(0,0,1),'clean writer RT state')
            need(half(b,0xc4)==(new if name=='readback-R'else old)and half(b,0x30)==half(b,0xc0)==200,'actual finite limit/readback')
        # Compare exactly the source's documented mutable fields. This fixture
        # does not replay the private callback or full native profile admission.
        dynamic=set(range(0x86,0x8a))|set(range(0x8c,0x8e))|set(range(0x90,0x94))|set(range(0xa2,0xa4))|{0xc4,0xac,0xad}
        for before,after in [('baseline-R','fresh-R'),('fresh-R','readback-R')]:
            need(all(a==b for i,(a,b)in enumerate(zip(decoded[before],decoded[after],strict=True))if i not in dynamic),'R whitelist changes')
        return n['steps'][0]['beforeUs'],last
    def observe(label,limit,expected_max):
        n=f[label];need(set(n)==DP_KEYS and n['schema']=='managed-usb-rt-synchronized-key-dp-v1','DP whitelist');lifecycle(n)
        need(n['observationAccepted']is True and n['onsetObserved']is False and n['onsetMissed']is False and n['busContentsAltered']is False,'accepted clean observation')
        need(n['terminalReason']=='TimeLimit'and type(n['writes'])is int and n['writes']==0 and type(n['retries'])is int and n['retries']==0,'readonly timed observation')
        counts={'cyclesStarted':80,'cleanCyclesCompleted':80,'cleanCyclesDiscarded':79,'headersSent':640,'inputsCompleted':640,'bulkTransfers':1280}
        need(all(type(n[k])is int and n[k]==v for k,v in counts.items()),'80 complete clean cycles counts')
        need(all(num(n[k])for k in ('startUs','endUs','deadlineUs','overshootUs'))and n['deadlineUs']-n['startUs']==20_000_000 and n['endUs']-n['deadlineUs']==n['overshootUs']and n['overshootUs']<250_000,'bounded observation interval')
        need([(g['role'],g['cycleIndex'])for g in n['retained']]==[('trigger-baseline',1),('last-clean',80)],'retention indices')
        last=n['startUs'];first_end=None
        for g in n['retained']:
            need(set(g)=={'role','cycleIndex','windows','transfers'}and len(g['windows'])==8 and len(g['transfers'])==16,'retained frame')
            for i,(w,name)in enumerate(zip(g['windows'],['R','M','C','P','N','H','L','R'],strict=True)):
                address,size=DP_SPECS[name];fields={'name','address','expected','count','complete','rawBase64','sha256'}|({'observedRtState'}if name=='R'else set())
                need(set(w)==fields and w['name']==name and w['address']==hex(address)and type(w['expected'])is int and type(w['count'])is int and w['expected']==w['count']==size and w['complete']is True,'DP bounded window')
                b=raw(w,size,'rawBase64')
                if name=='R':
                    need(w['observedRtState']=={'stop':0,'fault':0,'ordinaryGate':1,'classification':'Clean'}and tuple(half(b,o)for o in (0,10,14))==(0,0,1)and half(b,0xc4)==limit,'retained clean state and limit')
                last=step(g['transfers'][2*i],name+'-header','OUT',12,last)
                last=step(g['transfers'][2*i+1],name+'-data','IN',size,last)
            if first_end is None:first_end=last
        need(last<=n['endUs'],'retained within interval')
        cp=n['scoreCheckpoints'];need(set(cp)=={'schema','recordBytes','count','rawBase64','sha256'}and cp['schema']=='dp-score-checkpoints-v1'and type(cp['recordBytes'])is int and cp['recordBytes']==34 and type(cp['count'])is int and cp['count']==80,'checkpoint layout')
        packed=raw(cp,2720,'rawBase64');scores=[];c7s=set();previous=0
        for i in range(80):
            status,c7,normal,selected,a,q,h0,h1,h2,h3,ordinal,before,after,mirror=struct.unpack_from('<BBHHIH4HIIIH',packed,34*i)
            need(status==0 and c7 in (0,1)and normal==selected==limit and q==0,'checkpoint state/limits')
            need(previous<=before<=after<=n['endUs']-n['startUs'],'checkpoint monotonic H bracket');previous=after;scores.append(a);c7s.add(c7)
        need(max(scores)==expected_max and all(a<=40 for a in scores),'actual maxima; no greater-than40 witness')
        key=n['intervention'];need(set(key)=={'key','trigger','attempted','completed','armedUs','endUs','uiReceiptObserved','physicalPictureObserved','calls'},'key whitelist')
        need(key['key']=='Left'and key['trigger']=='first-full-clean-cycle'and key['attempted']is True and key['completed']is True and key['uiReceiptObserved']is False and key['physicalPictureObserved']is False,'one key scope')
        need([c['phase']for c in key['calls']]==['down','up'],'key phases');at=first_end
        for c in key['calls']:
            need(set(c)=={'phase','beforeUs','afterUs','exitCode','started','reaped','timedOut','stdoutBytes','stderrBytes'},'key call whitelist')
            need(c['started']is True and c['reaped']is True and c['timedOut']is False and all(type(c[k])is int and c[k]==0 for k in ('exitCode','stdoutBytes','stderrBytes'))and num(c['beforeUs'])and num(c['afterUs'])and at<=c['beforeUs']<=c['afterUs'],'bounded successful key');at=c['afterUs']
        need(first_end<key['armedUs']<=key['calls'][0]['beforeUs']and at<=key['endUs']<n['endUs'],'key inside observation')
        return {'maximumA0':max(scores),'cleanCycles':80,'limit':limit,'c7Values':sorted(c7s),'startUs':n['startUs'],'endUs':n['endUs']}
    set_at=writer('set200',40,200);high=observe('observe200',200,26);restore_at=writer('restore40',200,40);low=observe('rechallenge40',40,24)
    need(set_at[1]<high['startUs']<high['endUs']<restore_at[0]<restore_at[1]<low['startUs'],'set/observation/restore/rechallenge order')
    return {'schema':'public-rtp-limit-verification-v1','accepted':True,'checks':checks,'rawWindows':raw_windows-2,'checkpointBytes':5440,'rawBytesIncludingCheckpoints':raw_bytes,'observe200':high,'rechallenge40':low,'restoredValue':40,'greaterThan40WitnessAt200':False,'causalPreventionEstablished':False,'physicalPictureObserved':False,'callbackAdmissionReplayed':False,'targetOperations':0}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('fixture',nargs='?',type=Path,default=Path(__file__).resolve().parents[1]/'fixtures/rtp-limit-comparison.json')
    print(json.dumps(verify(json.loads(p.parse_args().fixture.read_text())),indent=2,sort_keys=True))
