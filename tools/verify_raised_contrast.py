#!/usr/bin/env python3
"""Verify the separate EX scientific contrast offline, without any target helper."""
import argparse,base64,hashlib,json,struct
from pathlib import Path

def verify(f):
    checks=0
    def need(ok,message):
        nonlocal checks
        if not ok:raise ValueError(message)
        checks+=1
    def integer(x):return type(x)is int and 0<=x<=2**63-1
    def u16(raw,at):return struct.unpack_from('<H',raw,at)[0]
    def u32(raw,at):return struct.unpack_from('<I',raw,at)[0]
    def data(w,size):
        need(type(w['bytes'])is int and w['bytes']==size,'fixed scientific extent')
        raw=base64.b64decode(w['base64'],validate=True)
        need(len(raw)==size and hashlib.sha256(raw).hexdigest()==w['sha256'],'scientific byte integrity')
        return raw
    def lifecycle(n,headers,bulks):
        need(all(n[k]is True for k in ('accepted','released','closed')),'accepted cleanup')
        need(n['protocolPhase']=='ReadyForHeader','complete phase')
        need(type(n['headersSent'])is int and type(n['bulkTransfers'])is int and(n['headersSent'],n['bulkTransfers'])==(headers,bulks),'exact pair counts')
        need(n['physicalPictureObserved']is False,'no optical observation')
    def rt(raw,limit,expected):
        triple=tuple(u16(raw,i)for i in (0,10,14))
        classification={(0,0,1):'Clean',(1,0x1001,0):'Faulted',(0,0,0):'Quiescent'}.get(triple,'Unexpected')
        need(u16(raw,0xc4)==limit and classification==expected,'independent full R classification/limit')
    need(f['schema']=='public-raised-restored-contrast-v1','fixture schema')
    def observation(n,limit):
        lifecycle(n,448,896)
        need(n['observationAccepted']is True and n['onsetObserved']is False and n['terminalReason']=='CycleLimit','observation outcome')
        need(all(type(n[k])is int and n[k]==0 for k in ('writes','retries')),'zero reader writes/retries')
        need(integer(n['startUs'])and integer(n['endUs'])and n['startUs']<n['endUs'],'native monotonic extent')
        need(type(n['cyclesStarted'])is int and n['cyclesStarted']==56,'56 distinct cycles')
        p=n['projection'];need(type(p['recordBytes'])is int and p['recordBytes']==50 and type(p['count'])is int and p['count']==56,'projection layout/capacity')
        blob=data(p,2800);rows=[];previous=0
        for i in range(56):
            r=blob[i*50:(i+1)*50];code=r[0];c7=r[1]
            # Enum0=Clean,1=Faulted,2=Unexpected,3=Quiescent. Exact nibble pair only.
            need(code in (0x00,0x33),'retained clean or quiescent brackets; no relabeling')
            need(u16(r,2)==limit and u16(r,4)==limit,'both sampled limits')
            before,after=u32(r,24),u32(r,28)
            need(previous<=before<=after and n['startUs']+after<=n['endUs'],'H monotonic brackets')
            previous=after
            rows.append({'cycle':i+1,'state':'Clean'if code==0 else'Quiescent','c7':c7,'score':u32(r,6)&65535,'rawH0':u32(r,6),'q0':u16(r,10),'history':list(struct.unpack_from('<4H',r,12)),'ordinal':u32(r,20),'publicationMirror':u16(r,32),'trainer':u16(r,34),'aggregate':u16(r,36),'selectorMirror':u16(r,38),'refreshCounter':u16(r,40),'endR60':u16(r,42),'endR6e':u16(r,44),'endRca':u16(r,46),'endR68':u16(r,48)})
        clean=sum(r['state']=='Clean'for r in rows);quiet=56-clean
        need(type(n['cleanCyclesCompleted'])is int and type(n['quiescentCyclesCompleted'])is int and(n['cleanCyclesCompleted'],n['quiescentCyclesCompleted'])==(clean,quiet),'independent row counters')
        need([(c['role'],c['cycle'])for c in n['retained']]==[('trigger-baseline',1),('last-clean',56)],'full retained roles')
        contexts=[]
        for c in n['retained']:
            need([w['name']for w in c['windows']]==['R','M','C','H','R'],'retained scientific subset order')
            out=[];end=0
            for w,size in zip(c['windows'],(256,68,16,96,256),strict=True):
                raw=data(w,size);need(integer(w['beforeUs'])and integer(w['afterUs'])and n['startUs']<=w['beforeUs']<=w['afterUs']<=n['endUs']and end<=w['beforeUs'],'sequential full windows')
                end=w['afterUs'];out.append(raw)
            a,m,cc,h,z=out;rt(a,limit,'Clean');rt(z,limit,'Clean');row=blob[(c['cycle']-1)*50:c['cycle']*50]
            expected=bytes((0,cc[7]))+a[0xc4:0xc6]+z[0xc4:0xc6]+h[4:8]+h[28:30]+h[40:48]
            need(row[:20]==expected,'full retained R/C/H agrees with compact prefix')
            need(row[32:46]==m[42:44]+m[2:6]+m[0x22:0x26]+z[0x60:0x62]+z[0x6e:0x70]and row[46:50]==z[0xca:0xcc]+z[0x68:0x6a],'full M/endR agrees with appended fields')
            need(n['startUs']+u32(row,24)==c['windows'][3]['beforeUs']and n['startUs']+u32(row,28)==c['windows'][3]['afterUs'],'full H and compact times agree')
            contexts.append({'aa':u16(m,10),'ac':u16(m,12),'scan':m[56],'root':u32(m,64),'c7':cc[7],'score':u32(h,4)&65535,'selector':u16(z,0xca)})
        return rows,contexts
    raised,context=observation(f['raised200'],200);control,_=observation(f['firstControl40'],40)
    witnesses=[r['cycle']for r in raised if r['state']=='Clean'and r['c7']==1 and r['score']>40]
    need(sum(r['state']=='Clean'for r in raised)==55 and [r['cycle']for r in raised if r['state']=='Quiescent']==[19],'55 clean plus row19 quiescent')
    need(len(witnesses)==23 and max(r['score']for r in raised)==76 and raised[34]['score']==76,'independent sampled >40 witnesses/max/cycle')
    need(raised[-1]['score']==52 and context[-1]=={'aa':0,'ac':2,'scan':1,'root':0x20010000,'c7':1,'score':52,'selector':1},'last row full alternate context only')
    need(all(r['state']=='Clean'and r['score']==0 and r['c7']==0 for r in control),'first40 control different exposure, not reproduced')
    for name,before,after in [('set200',40,200),('restore40',200,40)]:
        n=f[name];lifecycle(n,7,14)
        need(all(n[k]is True for k in ('writeAttempted','writeTransportComplete','readbackVerified'))and n['rootCauseFixEstablished']is False,'fixed write/readback without fix claim')
        need(set(n['windows'])=={'fresh-R','readback-R'},'writer projection excludes callbacks')
        a=data(n['windows']['fresh-R'],256);z=data(n['windows']['readback-R'],256);rt(a,before,'Clean');rt(z,after,'Clean')
        need([i for i in range(256)if a[i]!=z[i]]==[0xc4],'only observed halfword low byte changed')
    def snapshot(n,limit,state):
        lifecycle(n,16,32);need(type(n['writes'])is int and n['writes']==0 and type(n['uiOperations'])is int and n['uiOperations']==0,'separate reader no writes/UI')
        need(set(n['windows'])=={'start-R','end-R','M','C','start-N','end-N'},'snapshot projection')
        w={k:data(v,{'start-R':256,'end-R':256,'M':68,'C':16,'start-N':36,'end-N':36}[k])for k,v in n['windows'].items()}
        need(w['start-R']==w['end-R'],'stable sampled fullR')
        rt(w['start-R'],limit,state);rt(w['end-R'],limit,state)
        return w
    post=snapshot(f['post200'],200,'Clean');fault=snapshot(f['explicitControl40'],40,'Faulted')
    need(post['C'][7]==1 and u16(post['M'],42)==200 and u32(post['start-N'],0)==201,'post200 C7/publication/ordinal')
    need(fault['C'][7]==1 and u16(fault['M'],42)==40 and(u16(fault['M'],10),u16(fault['M'],12))==(0,2)and u32(fault['start-N'],0)==41,'separate explicit40 fault context')
    return {'schema':'public-raised-contrast-verification-v1','checks':checks,'raisedRows':56,'cleanRows':55,'quiescentRows':1,'cleanC7OneScoreAbove40Cycles':witnesses,'maximumSampledH0Low16':76,'lastRetainedScore':52,'first40Control':{'rows':56,'cleanRows':56,'maximumSampledH0Low16':0,'c7OneRows':0},'explicit40Snapshot':'Faulted','thresholdWrites':2,'restorationReadbackObserved':True,'recoveryOrderingVerifiedByThisFixture':False,'pureThresholdCausalityEstablished':False,'actualFPSelectionObserved':False,'physicalPictureObserved':False,'permanentFixEstablished':False,'targetOperations':0,'notice':'Scientific subset integrity and internal consistency only. Original authenticated transport/readiness and restoration-before-MODE2 ordering are separately reviewed private evidence; this fixture contains no recovery record. Intermediate compact brackets are instrument classifications; full context exists only for retained rows. Both threshold and publication cap changed, exposures differ, and sequential reads are non-atomic.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('fixture',nargs='?',type=Path,default=Path(__file__).resolve().parents[1]/'fixtures/raised-restored-contrast.json');a=p.parse_args()
    print(json.dumps(verify(json.loads(a.fixture.read_text())),indent=2))
