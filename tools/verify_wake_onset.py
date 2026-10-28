#!/usr/bin/env python3
"""Offline verifier for bounded GC/GF projections; never contacts a TV."""
import argparse,base64,hashlib,json,struct
from pathlib import Path

def verify(f):
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
    need(set(f)=={'schema','case','notice','source','native','workflow','ring','physicalPictureObserved','actualFpProven','executingPcProven','selectedAProven','keyConsumptionProven','forYouTransitionProven','rootCauseFixEstablished','thresholdPreventionEstablished','originalTransportProvenanceReplayed'},'top-level schema')
    need(f['schema']=='public-wake-onset-projection-v1'and f['case']in {'GC','GF'},'schema/case');fault=f['case']=='GF';count=26 if fault else 77
    for k in ['physicalPictureObserved','actualFpProven','executingPcProven','selectedAProven','keyConsumptionProven','forYouTransitionProven','rootCauseFixEstablished','thresholdPreventionEstablished','originalTransportProvenanceReplayed']:need(f[k]is False,'unproved '+k)
    need(f['source']=={'workstream':'live-saver-wake-trial-20261028gf'if fault else'wake-window-trial-20261028gc','originalRowBytes':58,'projection':'row[0:46]+row[54:58] removes both dynamic pointers'},'source/projection declaration')
    a=f['native'];need(a['accepted']is True and a['phase']=='ReadyForHeader'and a['released']is True and a['closed']is True,'accepted lifecycle')
    expected={'headers':8*count+12,'bulks':2*(8*count+12),'inputs':8*count+10,'writes':2,'retries':0,'threshold':40,'cyclesStarted':count,'cleanCycles':24 if fault else 76,'quiescentCycles':1}
    for k,v in expected.items():need(type(a[k])is int and a[k]==v,'native '+k)
    need(a['terminal']==('TransitionCaptured'if fault else'TimeLimit'),'terminal classification');need(integer(a['startUs'])and integer(a['endUs'])and a['startUs']<a['endUs'],'native clock')
    p=a['projection'];need(type(p['recordBytes'])is int and p['recordBytes']==50 and type(p['count'])is int and p['count']==count,'50-byte projection')
    rows=data(p,50*count);decoded=[];last=0
    for i in range(count):
        b=rows[i*50:(i+1)*50];s,e=b[0]>>4,b[0]&15;need(s in (0,1,3)and e in (0,1,3),'row state nibbles')
        need(s==e,'this capture endpoints agree');need(b[1]in (0,1)and u16(b,2)==u16(b,4)==40,'sampled selector/limit')
        before,after=u32(b,24),u32(b,28);need(last<=before<=after and a['startUs']+after<=a['endUs'],'H pair clock');last=after
        need(u16(b,32)in (40,200)and u16(b,34)==u16(b,36)==0 and u16(b,42)==u16(b,44)==u16(b,48)==0,'sampled writer controls')
        need(u16(b,38)==b[1]and u16(b,46)==b[1],'sampled selector mirrors')
        decoded.append({'state':s,'h':u32(b,6),'c7':b[1],'ordinal':u32(b,20),'before':before,'after':after})
    need(sum(x['state']==0 for x in decoded)==expected['cleanCycles']and sum(x['state']==3 for x in decoded)==1,'honest state counts')
    need([i+1 for i,x in enumerate(decoded)if x['state']==3]==[14 if fault else 19],'Q epoch')
    need(max(x['h']for x in decoded)==(48 if fault else 36),'observed maximum H')
    if fault:
        need([x['h']for x in decoded[19:]]==[8,16,24,24,32,40,48]and decoded[24]['state']==0 and decoded[25]['state']==1,'clean40 to fault48')
    else:need(all(x['state']!=1 and x['h']<=40 for x in decoded),'no sampled fault/above40 witness')
    need([(c['role'],c['cycle'])for c in a['retained']]==[('trigger-baseline',1),('last-complete',count),('current',count)],'retained epochs')
    baselineEnd=None;laterR=None;firstFaultR=None
    for c in a['retained']:
        need([w['name']for w in c['windows']]==['R','M','C','N','H','R'],'selected full windows');v=[];prev=a['startUs']
        for w,size in zip(c['windows'],[256,68,16,36,96,256]):
            v.append(data(w,size));need(integer(w['beforeUs'])and integer(w['afterUs'])and prev<=w['beforeUs']<=w['afterUs']<=a['endUs'],'full read-pair bracket');prev=w['afterUs']
        r,m,cc,n,h,e=v;need(u16(r,6)==u16(e,6)==1 and u16(r,0xc4)==u16(e,0xc4)==40,'observation logger/limit')
        need(u32(m,64)==0x20010000 and u16(m,10)==0 and u16(m,12)==2 and m[56]==1,'full mode/root/scan')
        need(tuple(u16(cc,k)for k in [0,2,4])==(2160,1920,2880)and cc[6]==92 and cc[8]==3,'C context')
        b=rows[(c['cycle']-1)*50:c['cycle']*50]
        reconstructed=bytes([(state(r)<<4)|state(e),cc[7]])+r[0xc4:0xc6]+e[0xc4:0xc6]+h[4:8]+h[28:30]+h[40:48]+n[:4]+struct.pack('<II',c['windows'][4]['beforeUs']-a['startUs'],c['windows'][4]['afterUs']-a['startUs'])+m[42:44]+m[2:6]+m[0x22:0x26]+e[0x60:0x62]+e[0x6e:0x70]+e[0xca:0xcc]+e[0x68:0x6a]
        need(b==reconstructed,'all50 retained row bytes')
        if c['cycle']==1:baselineEnd=c['windows'][-1]['afterUs']
        else:laterR=c['windows'][0]['beforeUs'];firstFaultR=c['windows'][0]['afterUs']
    controls=a['controls'];need(set(controls)=={'prearm-R','armed-R','prerestore-R','restored-R'},'four logger observations');controlraw={k:data(v,256)for k,v in controls.items()}
    for k,g in [('prearm-R',0),('armed-R',1),('prerestore-R',1),('restored-R',0)]:
        r=controlraw[k];need(u16(r,6)==g and u16(r,0xc4)==40,'logger readback');need(state(r)==(1 if fault and k in {'prerestore-R','restored-R'}else 0),'separate logger state')
    need([i for i in range(256)if controlraw['prerestore-R'][i]!=controlraw['restored-R'][i]]==[6],'only logger byte changes')
    key=a['intervention'];need(key['key']=='Left'and key['trigger']=='first-full-clean-cycle'and key['attempted']is True and key['completed']is True and key['uiReceiptObserved']is False and key['physicalPictureObserved']is False,'native key scope');need([x['phase']for x in key['calls']]==['down','up'],'key calls')
    prev=baselineEnd
    for x in key['calls']:
        need(integer(x['beforeUs'])and integer(x['afterUs'])and prev<=x['beforeUs']<=x['afterUs']<=a['endUs'],'key ordering');prev=x['afterUs']
        need(type(x['exitCode'])is int and x['exitCode']==0 and x['started']is True and x['reaped']is True and x['timedOut']is False,'key completion')
    need(baselineEnd<=key['armedUs']<=key['calls'][0]['beforeUs']<laterR and key['endUs']>=prev,'key exposure vs later OPTIONAL R')
    w=f['workflow'];need(type(w['wrapperUiOperations'])is int and w['wrapperUiOperations']==(0 if fault else 1)and type(w['nativeInvocations'])is int and w['nativeInvocations']==1 and w['keyExposureQualified']is True and w['cleanup']=='STAGE_ABSENT','wrapper/native scope')
    ring=f['ring'];need(ring['outsideCandidateDataUnchanged']is True,'bounded backing comparison')
    for k in ['chronologicalDeltaProven','lapCountProven','sharedEpochProven','twoLinesMeanTwoInvocations']:need(ring[k]is False,'ring limitation '+k)
    for cur in [ring['baselineCursors'],ring['postCursors']]:need(type(cur)is list and len(cur)==3 and all(type(x)is int for x in cur)and 0<=cur[0]<=15360 and 0<=cur[1]<=15360 and cur[2]in (0,1),'ring cursor bounds')
    need(ring['postCursors'][0]-ring['baselineCursors'][0]==ring['candidateBytes']==(1196 if fault else 2265),'endpoint candidate length')
    for k,v in [('normalInvocationCounter',56 if fault else 44),('baselineEvent736Lines',0),('postEvent736Lines',2 if fault else 0),('candidateEvent736Lines',2 if fault else 0)]:need(type(ring[k])is int and ring[k]==v,'typed ring '+k)
    need(data(ring['eventSuffix'],24 if fault else 0)==b'rtp_act_736\n'*(2 if fault else 0),'paired stock event text')
    if fault:need(ring['postCursors'][0]-ring['postCursors'][1]==24,'event suffix cursor relation')
    need(len(ring['details'])==(21 if fault else 41),'bounded detail count');ordinals=[]
    for d in ring['details']:
        need(set(d)=={'b','conditional12bitACandidates','diff','mode','ordinal','rgb','x','y'},'detail type')
        for k in ['b','diff','ordinal','rgb','x','y']:need(type(d[k])is int and d[k]>=0,'detail integer')
        need(d['mode']=='NORMAL'and d['rgb']==0 and d['y']==2159 and 0<=d['ordinal']<=40,'formatter metadata')
        candidates=sorted(set(v for v in [d['b']+d['diff'],d['b']-d['diff']]if 0<=v<=4095));need(d['conditional12bitACandidates']==candidates,'conditional A arithmetic');ordinals.append(d['ordinal'])
    need(ordinals==([0,1,2,3,8,9,10,11,16,17,18,19,24,25,26,27,32,33,34,35,40]if fault else list(range(41))),'printed ordinal subset')
    enclosure=None
    if fault:enclosure=firstFaultR-(a['startUs']+decoded[-2]['after']);need(enclosure==25476,'conservative adjacent-status enclosure')
    return {'case':f['case'],'checks':checks,'rows':count,'clean':expected['cleanCycles'],'quiescent':1,'faulted':1 if fault else 0,'maximumSampledH':max(x['h']for x in decoded),'terminal':a['terminal'],'paired736Lines':ring['candidateEvent736Lines'],'conservativeStatusEnclosureUs':enclosure,'originalTransportProvenanceReplayed':False,'physicalPictureObserved':False,'actualFpProven':False,'rootCauseFixEstablished':False,'targetOperations':0}
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--fixture',type=Path,required=True);x=a.parse_args();print(json.dumps(verify(json.loads(x.fixture.read_bytes())),sort_keys=True))
