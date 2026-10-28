#!/usr/bin/env python3
"""Verify the bounded GJ 200/40 projection offline; no device or network access."""
import argparse,base64,hashlib,json,struct
from pathlib import Path

def verify_case(f,fault):
    checks=0
    def need(ok,why):
        nonlocal checks
        if not ok:raise ValueError(why)
        checks+=1
    def integer(n):return type(n)is int and 0<=n<2**63
    def u16(b,n):return struct.unpack_from('<H',b,n)[0]
    def u32(b,n):return struct.unpack_from('<I',b,n)[0]
    def data(w,size):
        need(type(w)is dict and type(w['bytes'])is int and w['bytes']==size,'extent');b=base64.b64decode(w['base64'],validate=True)
        need(len(b)==size and base64.b64encode(b).decode()==w['base64']and hashlib.sha256(b).hexdigest()==w['sha256'],'canonical bytes/hash');return b
    def state(r):
        tup=tuple(u16(r,n)for n in [0,10,14]);need(tup in {(0,0,1),(0,0,0),(1,4097,0)},'known RT tuple');return {(0,0,1):0,(0,0,0):3,(1,4097,0):1}[tup]
    a=f['native'];need(a['accepted']is True and a['phase']=='ReadyForHeader'and a['released']is True and a['closed']is True,'accepted lifecycle')
    count=27 if fault else 56;limit=40 if fault else 200
    expected={'headers':8*count+12,'bulks':2*(8*count+12),'inputs':8*count+10,'writes':2,'retries':0,'threshold':limit,'cyclesStarted':count,'cleanCycles':25 if fault else 55,'quiescentCycles':1}
    for k,v in expected.items():need(type(a[k])is int and a[k]==v,'native '+k)
    need(a['terminal']==('TransitionCaptured'if fault else'CycleLimit'),'terminal classification');need(integer(a['startUs'])and integer(a['endUs'])and a['startUs']<a['endUs'],'native clock')
    p=a['projection'];need(type(p['recordBytes'])is int and p['recordBytes']==50 and type(p['count'])is int and p['count']==count,'50-byte projection')
    rows=data(p,50*count);decoded=[];last=0
    for i in range(count):
        b=rows[i*50:(i+1)*50];s,e=b[0]>>4,b[0]&15;need(s in (0,1,3)and e in (0,1,3),'row state nibbles')
        need(s==e,'this capture endpoints agree');need(b[1]in (0,1)and u16(b,2)==u16(b,4)==limit,'sampled selector/limit')
        before,after=u32(b,24),u32(b,28);need(last<=before<=after and a['startUs']+after<=a['endUs'],'H pair clock');last=after
        need((u16(b,32)in (40,200)if fault else u16(b,32)==200)and u16(b,34)==u16(b,36)==0 and u16(b,42)==u16(b,44)==u16(b,48)==0,'sampled writer controls')
        need(u16(b,38)==b[1]and u16(b,46)==b[1],'sampled selector mirrors')
        decoded.append({'state':s,'h':u32(b,6),'c7':b[1],'ordinal':u32(b,20),'before':before,'after':after})
    need(sum(x['state']==0 for x in decoded)==expected['cleanCycles']and sum(x['state']==3 for x in decoded)==1,'honest state counts')
    need([i+1 for i,x in enumerate(decoded)if x['state']==3]==[15 if fault else 16],'Q epoch')
    need(max(x['h']for x in decoded)==(48 if fault else 36),'observed maximum H')
    if fault:
        need([x['h']for x in decoded[17:]]==[0,0,0,8,16,24,32,32,40,48]and decoded[25]['state']==0 and decoded[26]['state']==1,'clean40 to fault48')
    else:need(all(x['state']!=1 and x['h']<=40 for x in decoded),'no sampled fault/above40 witness')
    need([(c['role'],c['cycle'])for c in a['retained']]==[('trigger-baseline',1),('last-complete',count),('current',count)],'retained epochs')
    baselineEnd=None;laterR=None;firstFaultR=None
    for c in a['retained']:
        need([w['name']for w in c['windows']]==['R','M','C','N','H','R'],'selected full windows');v=[];prev=a['startUs']
        for w,size in zip(c['windows'],[256,68,16,36,96,256]):
            v.append(data(w,size));need(integer(w['beforeUs'])and integer(w['afterUs'])and prev<=w['beforeUs']<=w['afterUs']<=a['endUs'],'full read-pair bracket');prev=w['afterUs']
        r,m,cc,n,h,e=v;need(u16(r,6)==u16(e,6)==1 and u16(r,0xc4)==u16(e,0xc4)==limit and u16(r,16)==u16(e,16)==4,'observation logger/limit/retainedR16')
        need(u32(m,64)==0x20010000 and u16(m,10)==0 and u16(m,12)==2 and m[56]in ((1,)if c['cycle']==1 else (0,1)),'full mode/root/scan')
        need(tuple(u16(cc,k)for k in [0,2,4])==(2160,1920,2880)and cc[6]==92 and cc[8]==3,'C context')
        b=rows[(c['cycle']-1)*50:c['cycle']*50]
        reconstructed=bytes([(state(r)<<4)|state(e),cc[7]])+r[0xc4:0xc6]+e[0xc4:0xc6]+h[4:8]+h[28:30]+h[40:48]+n[:4]+struct.pack('<II',c['windows'][4]['beforeUs']-a['startUs'],c['windows'][4]['afterUs']-a['startUs'])+m[42:44]+m[2:6]+m[0x22:0x26]+e[0x60:0x62]+e[0x6e:0x70]+e[0xca:0xcc]+e[0x68:0x6a]
        need(b==reconstructed,'all50 retained row bytes')
        if c['cycle']==1:baselineEnd=c['windows'][-1]['afterUs']
        else:laterR=c['windows'][0]['beforeUs'];firstFaultR=c['windows'][0]['afterUs']
    controls=a['controls'];need(set(controls)=={'prearm-R','armed-R','prerestore-R','restored-R'},'four logger observations');controlraw={k:data(v,256)for k,v in controls.items()}
    for k,g in [('prearm-R',0),('armed-R',1),('prerestore-R',1),('restored-R',0)]:
        r=controlraw[k];need(u16(r,6)==g and u16(r,0xc4)==limit and u16(r,16)==4,'logger readback/retainedR16');need(state(r)==(1 if fault and k in {'prerestore-R','restored-R'}else 0),'separate logger state')
    need([i for i in range(256)if controlraw['prerestore-R'][i]!=controlraw['restored-R'][i]]==[6],'only logger byte changes')
    key=a['intervention'];need(key['key']=='Left'and key['trigger']=='first-full-clean-cycle'and key['attempted']is True and key['completed']is True and key['uiReceiptObserved']is False and key['physicalPictureObserved']is False,'native key scope');need([x['phase']for x in key['calls']]==['down','up'],'key calls')
    prev=baselineEnd
    for x in key['calls']:
        need(integer(x['beforeUs'])and integer(x['afterUs'])and prev<=x['beforeUs']<=x['afterUs']<=a['endUs'],'key ordering');prev=x['afterUs']
        need(type(x['exitCode'])is int and x['exitCode']==0 and x['started']is True and x['reaped']is True and x['timedOut']is False,'key completion')
    need(baselineEnd<=key['armedUs']<=key['calls'][0]['beforeUs']<laterR and key['endUs']>=prev,'key exposure vs later OPTIONAL R')
    w=f['workflow'];need(type(w['wrapperUiOperations'])is int and w['wrapperUiOperations']==0 and type(w['nativeInvocations'])is int and w['nativeInvocations']==1 and w['keyExposureQualified']is True and w['cleanup']=='STAGE_ABSENT','wrapper/native scope')
    ring=f['ring'];need(ring['outsideCandidateDataUnchanged']is True,'bounded backing comparison')
    for k in ['chronologicalDeltaProven','lapCountProven','sharedEpochProven','twoLinesMeanTwoInvocations']:need(ring[k]is False,'ring limitation '+k)
    for cur in [ring['baselineCursors'],ring['postCursors']]:need(type(cur)is list and len(cur)==3 and all(type(x)is int for x in cur)and 0<=cur[0]<=15360 and 0<=cur[1]<=15360 and cur[2]in (0,1),'ring cursor bounds')
    need(ring['postCursors'][0]-ring['baselineCursors'][0]==ring['candidateBytes']==(1186 if fault else 6153),'endpoint candidate length')
    for k,v in [('normalInvocationCounter',14 if fault else 3),('baselineEvent736Lines',0),('postEvent736Lines',2 if fault else 0),('candidateEvent736Lines',2 if fault else 0)]:need(type(ring[k])is int and ring[k]==v,'typed ring '+k)
    need(data(ring['eventSuffix'],24 if fault else 0)==b'rtp_act_736\n'*(2 if fault else 0),'paired stock event text')
    if fault:need(ring['postCursors'][0]-ring['postCursors'][1]==24,'event suffix cursor relation')
    need(len(ring['details'])==(21 if fault else 112),'bounded detail count');ordinals=[]
    for d in ring['details']:
        need(set(d)=={'b','conditional12bitACandidates','diff','mode','ordinal','rgb','x','y'},'detail type')
        for k in ['b','diff','ordinal','rgb','x','y']:need(type(d[k])is int and d[k]>=0,'detail integer')
        need(d['mode']=='NORMAL'and d['rgb']==0 and d['y']==2159 and 0<=d['ordinal']<=(40 if fault else 200),'formatter metadata')
        candidates=sorted(set(v for v in [d['b']+d['diff'],d['b']-d['diff']]if 0<=v<=4095));need(d['conditional12bitACandidates']==candidates,'conditional A arithmetic');ordinals.append(d['ordinal'])
    need(ordinals==([0,1,2,3,8,9,10,11,16,17,18,19,24,25,26,27,32,33,34,35,40]if fault else list(range(112))),'printed ordinal subset')
    return {'rows':count,'clean':expected['cleanCycles'],'quiescent':1,'faulted':int(fault),'maxH':max(x['h']for x in decoded),'cleanAbove40':sum(x['state']==0 and x['h']>40 for x in decoded),'baselineR':data(a['retained'][0]['windows'][0],256),'checks':checks}

def verify(f):
    checks=0
    def need(ok,why):
        nonlocal checks
        if not ok:raise ValueError(why)
        checks+=1
    def u16(b,n):return struct.unpack_from('<H',b,n)[0]
    def u32(b,n):return struct.unpack_from('<I',b,n)[0]
    def data(w,size):
        need(type(w['bytes'])is int and w['bytes']==size,'extent');b=base64.b64decode(w['base64'],validate=True)
        need(len(b)==size and hashlib.sha256(b).hexdigest()==w['sha256']and base64.b64encode(b).decode()==w['base64'],'canonical bytes/hash');return b
    need(set(f)=={'schema','notice','source','set200','raised200','restore40','control40','finalValidation','sequence','physicalPictureObserved','actualFpProven','executingPcProven','matchedAllHistoryProven','thresholdPreventionEstablished','rootCauseFixEstablished','originalTransportProvenanceReplayed'},'top schema')
    need(f['schema']=='public-matched-wake-contrast-v1','schema')
    for k in ['physicalPictureObserved','actualFpProven','executingPcProven','matchedAllHistoryProven','thresholdPreventionEstablished','rootCauseFixEstablished','originalTransportProvenanceReplayed']:need(f[k]is False,'unproved '+k)
    need(f['source']=={'workstream':'matched-saver-limit-trial-20261028gj','rowProjection':'58-byte row[0:46]+row[54:58] removes dynamic P4/P8','sameUsbInstanceForContrast':'private-evidence premise; identifying fields omitted'},'source declaration')
    raised=verify_case(f['raised200'],False);control=verify_case(f['control40'],True)
    need([i for i,(a,b)in enumerate(zip(raised['baselineR'],control['baselineR']))if a!=b]==[0x90,0xc4],'explicit baseline R difference')
    for field in ['C','N','H']:
        a=next(w for w in f['raised200']['native']['retained'][0]['windows']if w['name']==field);b=next(w for w in f['control40']['native']['retained'][0]['windows']if w['name']==field);need(a==b or data(a,a['bytes'])==data(b,b['bytes']),'selected baseline equality '+field)
    for name,old,new in [('set200',40,200),('restore40',200,40)]:
        t=f[name];need(t['accepted']is True and t['phase']=='ReadyForHeader'and t['released']is True and t['closed']is True and t['readbackVerified']is True and t['limitMayHaveChanged']is False and t['cleanup']=='STAGE_ABSENT','writer lifecycle')
        need(type(t['headers'])is int and t['headers']==7 and type(t['bulks'])is int and t['bulks']==14,'writer counts')
        need(set(t['windows'])=={'baseline-R','fresh-R','readback-R'},'writer window names')
        for k,v in [('baseline-R',old),('fresh-R',old),('readback-R',new)]:
            r=data(t['windows'][k],256);need(tuple(u16(r,i)for i in [0,10,14])==(0,0,1)and u16(r,6)==0 and u16(r,0xc4)==v and u16(r,16)==4,'clean writer limit/readback/globalR16')
    v=f['finalValidation'];need(v['accepted']is True and v['phase']=='ReadyForHeader'and v['released']is True and v['closed']is True and v['cleanup']=='STAGE_ABSENT','final lifecycle')
    for k,n in [('headers',16),('bulks',32),('writes',0),('uiOperations',0)]:need(type(v[k])is int and v[k]==n,'final counts '+k)
    sizes={'start-R':256,'end-R':256,'M':68,'C':16,'start-N':36,'end-N':36,'X':96,'Y':96,'RGB':96,'B':96,'Diff':96};need(set(v['windows'])==set(sizes),'final windows');w={k:data(v['windows'][k],n)for k,n in sizes.items()}
    need(w['start-R']==w['end-R'],'final R bracket exact');r=w['start-R'];need(tuple(u16(r,i)for i in [0,10,14])==(0,0,1)and u16(r,6)==0 and u16(r,0xc4)==40 and u16(r,16)==4,'final clean40 mode4 logger0')
    m,c=w['M'],w['C'];need(u16(m,10)==0 and u16(m,12)==1 and u16(m,42)==200 and m[56]==1 and u32(m,64)==0x20010000 and c[7]==0 and c[8]==3,'final context')
    need(w['start-N']==w['end-N'],'final N bracket');n=w['end-N'];need([u32(n,i*4)for i in range(6)]==[0,0,0,0,0,52]and [u16(n,24+i*2)for i in range(6)]==[0]*6,'zero current counts retain ordinal52')
    nonzero={k:sum(u16(w[k],i)!=0 for i in range(0,96,2))for k in ['X','Y','RGB','B','Diff']};need(nonzero=={'X':48,'Y':48,'RGB':26,'B':22,'Diff':0},'retained populated column caveat')
    need(f['sequence']=={'fixedSet':1,'fixedRestore':1,'stockMode2At40':2,'stockMode2At200':0,'ghFault200RecoveryUsed':False,'finalCachedUi':'Apps+saver+CSFS'},'bounded sequence')
    return {'checks':checks+raised['checks']+control['checks'],'raised200':{k:v for k,v in raised.items()if k not in {'baselineR','checks'}},'control40':{k:v for k,v in control.items()if k not in {'baselineR','checks'}},'retainedR16':4,'retainedFullRWindows':28,'finalCurrentCountsZero':True,'finalOrdinal5':52,'finalColumnNonzero':nonzero,'physicalPictureObserved':False,'thresholdPreventionEstablished':False,'rootCauseFixEstablished':False,'originalTransportProvenanceReplayed':False,'targetOperations':0}
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--fixture',type=Path,required=True);x=a.parse_args();print(json.dumps(verify(json.loads(x.fixture.read_bytes())),sort_keys=True))
