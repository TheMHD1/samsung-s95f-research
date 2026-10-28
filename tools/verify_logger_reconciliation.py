#!/usr/bin/env python3
"""Offline sixth-fixture verifier; no original receipt, adapter or TV required."""
import argparse,base64,hashlib,json,struct
from pathlib import Path

def verify(f):
    checks=0
    def need(ok,why):
        nonlocal checks
        if not ok:raise ValueError(why)
        checks+=1
    def u16(b,n):return struct.unpack_from('<H',b,n)[0]
    def u32(b,n):return struct.unpack_from('<I',b,n)[0]
    def integer(n):return type(n)is int and 0<=n<=2**63-1
    def data(w,size):
        need(type(w['bytes'])is int and w['bytes']==size,'scientific extent');b=base64.b64decode(w['base64'],validate=True)
        need(len(b)==size and base64.b64encode(b).decode()==w['base64']and hashlib.sha256(b).hexdigest()==w['sha256'],'canonical scientific hash');return b
    def rt(b,state,gate):
        need(tuple(u16(b,n)for n in [0,10,14])=={'Clean':(0,0,1),'Quiescent':(0,0,0)}[state],'raw RT classification')
        need(u16(b,0xc4)==40 and u16(b,6)==gate,'raw limit/logger')
    def known(n,fields):
        need(n['phase']=='ReadyForHeader'and n['released']is True and n['closed']is True,'known closed phase')
        for k,v in fields.items():need(type(n[k])is int and n[k]==v,'exact integer '+k)
    need(set(f)=={'schema','notice','source','originalRefusal','restoration','finalValidation','finalCachedUi','resetsInSequence','thresholdWritesInSequence','cleanStateCausedByLoggerRestore','physicalPictureObserved','rootCauseFixEstablished'},'exact top-level schema')
    need(f['schema']=='public-logger-refusal-restoration-v1','schema')
    for k in ['cleanStateCausedByLoggerRestore','physicalPictureObserved','rootCauseFixEstablished']:need(f[k]is False,'unproved '+k)
    for k in ['resetsInSequence','thresholdWritesInSequence']:need(type(f[k])is int and f[k]==0,'zero '+k)
    a=f['originalRefusal'];need(a['accepted']is False and a['wrapperAccepted']is False,'original refusal remains false')
    known(a,{'headers':158,'bulks':316,'inputs':157,'writes':1,'retries':0,'threshold':40,'cyclesStarted':19,'cleanCycles':18,'quiescentCycles':0})
    need(a['restoreAttempted']is False and a['loggerMayRemain']is True and a['errorClass']=='C geometry/category/selector','unrestored semantic refusal')
    need(6+19*8==a['headers']and 5+19*8==a['inputs']and a['headers']+a['inputs']+a['writes']==a['bulks'],'source-accounted pairs, not full raw capture coverage')
    need(integer(a['startUs'])and integer(a['endUs'])and a['startUs']<a['endUs'],'original clock')
    rt(data(a['controls']['prearm-R'],256),'Clean',0);rt(data(a['controls']['armed-R'],256),'Clean',1)
    row=a['projection'];need(type(row['recordBytes'])is int and row['recordBytes']==50 and type(row['count'])is int and row['count']==18,'projection layout')
    packed=data(row,900);last=0
    for i in range(18):
        b=packed[i*50:(i+1)*50];need(b[0]==0 and b[1]==0 and u16(b,2)==u16(b,4)==40 and u32(b,6)==0,'18 sampled clean rows/H0/C7')
        before,after=u32(b,24),u32(b,28);need(last<=before<=after and a['startUs']+after<=a['endUs'],'sampled H pair clock');last=after
    need([(c['role'],c['cycle'])for c in a['retained']]==[('trigger-baseline',1),('last-complete',18),('current',19)],'retained epochs')
    decoded=[]
    for c in a['retained']:
        need([w['name']for w in c['windows']]==['R','M','C','H','R'],'scientific retained subset');raw=[];previous=a['startUs']
        for w,size in zip(c['windows'],[256,68,16,96,256]):
            raw.append(data(w,size));need(integer(w['beforeUs'])and integer(w['afterUs'])and previous<=w['beforeUs']<=w['afterUs']<=a['endUs'],'full selected-window bracket');previous=w['afterUs']
        r,m,cc,h,e=raw;state='Quiescent'if c['cycle']==19 else'Clean';rt(r,state,1);rt(e,state,1)
        need(u32(m,64)==0x20010000 and u16(m,10)==0 and u16(m,12)==2 and m[56]==1,'sampled M context')
        need(tuple(u16(cc,n)for n in [0,2,4])==(2160,1920,2880)and cc[6]==92,'C geometry')
        if c['cycle']<19:
            rr=packed[(c['cycle']-1)*50:c['cycle']*50]
            need(rr[:20]==bytes([0,cc[7]])+r[0xc4:0xc6]+e[0xc4:0xc6]+h[4:8]+h[28:30]+h[40:48],'retained raw/compact prefix')
            need(rr[32:46]==m[42:44]+m[2:6]+m[0x22:0x26]+e[0x60:0x62]+e[0x6e:0x70]and rr[46:50]==e[0xca:0xcc]+e[0x68:0x6a],'retained appended bytes')
            need(a['startUs']+u32(rr,24)==c['windows'][3]['beforeUs']and a['startUs']+u32(rr,28)==c['windows'][3]['afterUs'],'retained H clock match')
        decoded.append(raw)
    old=decoded[1][2];current=decoded[2][2];need([i for i in range(16)if old[i]!=current[i]]==[7,8]and old[7:9]==bytes([0,3])and current[7:9]==bytes([1,0]),'exact C7/C8 drift')
    r=f['restoration'];need(r['accepted']is True and r['restore']=='readback-zero'and r['restoreAttempted']is True and r['loggerMayRemain']is False,'independent restoration result')
    known(r,{'headers':5,'bulks':10,'inputs':4,'writes':1,'retries':0,'thresholdWrites':0,'arms':0,'uiOperations':0,'resets':0})
    need([w['name']for w in r['windows']]==['M','C','R','R'],'restore subset');m,c,b,z=[data(w,n)for w,n in zip(r['windows'],[68,16,256,256])]
    need(u32(m,64)==0x20010000 and u16(m,10)==0 and u16(m,12)==2 and m[56]in (0,1),'restore context root/mode/scan')
    need(tuple(u16(c,n)for n in [0,2,4])==(2160,1920,2880)and c[6]==92 and c[7]<=1 and c[8]in (0,3),'restore C finite geometry')
    rt(b,'Clean',1);rt(z,'Clean',0);need([i for i in range(256)if b[i]!=z[i]]==[6],'only logger byte changed')
    need(integer(r['startUs'])and integer(r['endUs'])and a['endUs']<r['startUs']<r['endUs'],'separate restoration clock')
    need(len(r['pairBracketsUs'])==5,'five pairs');previous=r['startUs']
    for pair in r['pairBracketsUs']:need(type(pair)is list and len(pair)==2 and all(integer(t)for t in pair)and previous<=pair[0]<=pair[1]<=r['endUs'],'restoration pair ordering');previous=pair[1]
    v=f['finalValidation'];need(all(v[k]is True for k in ['accepted','released','closed'])and v['protocolPhase']=='ReadyForHeader','final lifecycle')
    for k,n in [('headersSent',16),('bulkTransfers',32),('writes',0),('uiOperations',0)]:need(type(v[k])is int and v[k]==n,'final '+k)
    need(set(v['windows'])=={'start-R','end-R','M','C','start-N','end-N'},'final subset')
    x=data(v['windows']['start-R'],256);y=data(v['windows']['end-R'],256);rt(x,'Clean',0);rt(y,'Clean',0);need(x==y,'full final R equality')
    for name in ['start-N','end-N']:need(data(v['windows'][name],36)==bytes(36),'final N0')
    data(v['windows']['M'],68);data(v['windows']['C'],16);need(v['physicalPictureObserved']is False and f['finalCachedUi']=={'apps':True,'saver':True,'physicalPictureObserved':False},'cached UI is not optical')
    return {'schema':'public-logger-reconciliation-verification-v1','checks':checks,'originalWorkflowAccepted':False,'originalTerminalKnownReady':True,'originalPublishedCleanRows':18,'completeUnpublishedQuiescentCycle':19,'cChangedOffsets':[7,8],'loggerRestored':True,'restorationPreWriteState':'Clean','loggerByteChangedOffsets':[6],'finalSoftwareState':'Clean40/logger0/N0','cleanStateCausedByLoggerRestore':False,'physicalPictureObserved':False,'rootCauseFixEstablished':False,'originalTransportProvenanceReplayedByPublicFixture':False,'targetOperations':0}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',type=Path,default=Path(__file__).resolve().parents[1]/'fixtures/logger-refusal-restoration.json');a=p.parse_args();print(json.dumps(verify(json.loads(a.fixture.read_bytes())),sort_keys=True))
