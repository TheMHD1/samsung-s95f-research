#!/usr/bin/env python3
"""Standalone offline verification of bounded reference-run DP40/DT scientific data; no TV tools."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct

DP_SPECS={'R':(0x47012400,256),'M':(0x470004a0,68),'C':(0x47000bc0,16),
          'P':(0x47000490,16),'N':(0x4700ba28,36),'H':(0x4700d0e0,96),'L':(0x47010f00,64)}
DM_SPECS=[('start-R',0x47012400,256),('M',0x470004a0,68),('C',0x47000bc0,16),
          ('start-N',0x4700ba28,36),('D',0x4700a60a,48),('X',0x47011000,96),
          ('Y',0x47011400,96),('RGB',0x47011800,96),('B',0x47011c00,96),
          ('Diff',0x47012000,96),('fixed-top-candidate',0x47015354,104),('fixed-bottom-candidate',0x47016264,104),('end-N',0x4700ba28,36),('end-R',0x47012400,256)]
DP_KEYS=set(('schema','scoreCheckpoints','intervention','observationAccepted','terminalReason','protocolPhase','opened','claimed','released','closed','accepted','onsetObserved','onsetMissed','physicalPictureObserved','busContentsAltered','writes','retries','cyclesStarted','cleanCyclesCompleted','cleanCyclesDiscarded','bulkTransfers','headersSent','inputsCompleted','startUs','deadlineUs','endUs','overshootUs','retained'))
DM_KEYS=set(('packingQualified','schema','protocolPhase','opened','claimed','released','closed','accepted','headersSent','bulkTransfers','writes','uiOperations','atomicSnapshot','physicalPictureObserved','steps','windows','errors'))


def verify(fixture):
    checks=0;windows=0;raw_bytes=0
    def need(ok,label):
        nonlocal checks
        checks+=1
        if not ok:raise ValueError(label)
    def integer(v):return type(v)is int and 0<=v<2**63
    def half(b,o):return struct.unpack_from('<H',b,o)[0]
    def state(b):return tuple(half(b,o)for o in (0,10,14))
    def raw(encoded,digest,size):
        nonlocal windows,raw_bytes
        need(type(encoded)is str and type(digest)is str,'encoding types')
        data=base64.b64decode(encoded,validate=True)
        need(len(data)==size and base64.b64encode(data).decode()==encoded and hashlib.sha256(data).hexdigest()==digest,'exact raw length/hash/canonical encoding')
        windows+=1;raw_bytes+=size
        return data
    def flags(n):
        for name in ('accepted','opened','claimed','released','closed'):need(n[name]is True,'accepted cleanup')
        need(n['protocolPhase']=='ReadyForHeader' and n['physicalPictureObserved']is False,'phase/physical scope')
        need(type(n['writes'])is int and n['writes']==0,'zero writes')
    def transfer(t,name,direction,count,last):
        need(type(t)is dict and set(t)=={'name','direction','expected','count','errno','beforeUs','afterUs'},'scientific transfer fields')
        need(t['name']==name and t['direction']==direction,'transfer ordering')
        need(all(type(t[k])is int for k in ('expected','count','errno')) and t['expected']==t['count']==count and t['errno']==0,'transfer count/error')
        need(integer(t['beforeUs']) and integer(t['afterUs']) and last<=t['beforeUs']<=t['afterUs'],'monotonic pair times')
        return t['afterUs']
    need(type(fixture)is dict and set(fixture)=={'schema','notice','source','dp40','dtBaseline','dtFault'},'fixture fields')
    need(fixture['schema']=='public-rtp-reference-fixture-v1','fixture schema')
    need(set(fixture['source'])=={'workstream','captures','selected_asset_sha256','image1_file_offset_formula','function_vas'},'source whitelist')
    need(fixture['source']['selected_asset_sha256']=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected static source identity')
    dp=fixture['dp40'];need(set(dp)==DP_KEYS and dp['schema']=='managed-usb-rt-synchronized-key-dp-v1','DP scientific fields/schema');flags(dp)
    for k in ('observationAccepted','onsetObserved'):need(dp[k]is True,'DP observation accepted')
    for k in ('onsetMissed','busContentsAltered'):need(dp[k]is False,'DP scope')
    need(dp['terminalReason']=='TransitionCaptured' and type(dp['retries'])is int and type(dp['overshootUs'])is int and dp['retries']==dp['overshootUs']==0,'DP terminal')
    need(all(integer(dp[k])for k in ('cyclesStarted','cleanCyclesCompleted','cleanCyclesDiscarded','headersSent','inputsCompleted','bulkTransfers')),'integer global counters')
    need({k:dp[k]for k in ('cyclesStarted','cleanCyclesCompleted','cleanCyclesDiscarded','headersSent','inputsCompleted','bulkTransfers')}=={'cyclesStarted':6,'cleanCyclesCompleted':5,'cleanCyclesDiscarded':4,'headersSent':48,'inputsCompleted':48,'bulkTransfers':96},'global counts; retained baseline is not extra cycle')
    groups=dp['retained'];need([(g['role'],g['cycleIndex'])for g in groups]==[('trigger-baseline',1),('last-clean',5),('transition',6),('post-fault',6)],'DP retention roles')
    data_groups={};r_pairs=[];last=0
    for g,names in zip(groups,[['R','M','C','P','N','H','L','R']]*2+[['R'],['M','C','P','N','H','L','R']],strict=True):
        need(set(g)=={'role','cycleIndex','windows','transfers'} and [w['name']for w in g['windows']]==names and len(g['transfers'])==2*len(names),'DP retained frame')
        decoded=[]
        for i,w in enumerate(g['windows']):
            name=w['name'];address,size=DP_SPECS[name]
            fields={'name','address','expected','count','complete','rawBase64','sha256'}
            if name=='R':fields.add('observedRtState')
            need(set(w)==fields,'DP bounded window fields')
            need(w['address']==hex(address) and type(w['expected'])is int and type(w['count'])is int and w['expected']==w['count']==size and w['complete']is True,'DP source window')
            data=raw(w['rawBase64'],w['sha256'],size);decoded.append((name,data))
            h,t=g['transfers'][2*i:2*i+2];last=transfer(h,name+'-header','OUT',12,last);last=transfer(t,name+'-data','IN',size,last)
            if name=='R':
                triple=state(data);classification='Clean'if triple==(0,0,1)else'Faulted'if triple==(1,0x1001,0)else'Unexpected'
                need(w['observedRtState']==dict(zip(('stop','fault','ordinaryGate'),triple),classification=classification),'DP independent RT classification')
                r_pairs.append((classification,h['beforeUs'],t['afterUs']))
        data_groups[g['role']]=decoded
    need([s[0]for s in r_pairs]==['Clean']*4+['Faulted']*2,'DP clean/fault sequence')
    key=dp['intervention'];need(set(key)=={'key','trigger','attempted','completed','armedUs','endUs','uiReceiptObserved','physicalPictureObserved','calls'},'key scientific fields')
    need(key['key']=='Left' and key['trigger']=='first-full-clean-cycle' and key['attempted']is True and key['completed']is True and key['uiReceiptObserved']is False and key['physicalPictureObserved']is False,'one key with no UI/physical claim')
    need([c['phase']for c in key['calls']]==['down','up'],'down/up')
    for c in key['calls']:
        need(set(c)=={'phase','beforeUs','afterUs','exitCode','started','reaped','timedOut','stdoutBytes','stderrBytes'},'key call whitelist')
        need(c['started']is True and c['reaped']is True and c['timedOut']is False and all(type(c[k])is int and c[k]==0 for k in ('exitCode','stdoutBytes','stderrBytes')) and integer(c['beforeUs']) and integer(c['afterUs']) and c['beforeUs']<=c['afterUs'],'successful bounded key call')
    down,up=key['calls'];need(r_pairs[1][2]<key['armedUs']<=down['beforeUs']<=down['afterUs']<up['beforeUs']<=up['afterUs']<=key['endUs']<r_pairs[3][1]<r_pairs[4][2],'key bracket precedes software bracket')
    need(dp['startUs']<r_pairs[0][1] and last<=dp['endUs']<=dp['deadlineUs'],'DP observation interval')
    cp=dp['scoreCheckpoints'];need(set(cp)=={'schema','recordBytes','count','rawBase64','sha256'} and cp['schema']=='dp-score-checkpoints-v1' and cp['recordBytes']==34 and cp['count']==5,'checkpoint schema/size')
    packed=raw(cp['rawBase64'],cp['sha256'],170);scores=[];mirrors=[];last_h=0
    for i in range(5):
        status,c7,lim0,lim1,a,q,h0,h1,h2,h3,ordinal,before,after,mirror=struct.unpack_from('<BBHHIH4HIIIH',packed,i*34)
        need(status==0 and lim0==lim1==40 and q==0,'clean checkpoint state/limits')
        need(dp['startUs']+before<=dp['startUs']+after and last_h<=before,'checkpoint H monotonic bracket');last_h=after
        scores.append(a);mirrors.append(mirror)
    need(scores==[0,0,0,0,28] and mirrors==[200,200,200,40,40],'exact compact scores/mirrors')
    clean=dict(data_groups['last-clean']);post=dict(data_groups['post-fault'])
    need(struct.unpack_from('<I',clean['H'],4)[0]==28 and struct.unpack_from('<I',post['H'],4)[0]==42 and half(post['H'],28)==0,'full H score28 to42')
    need(list(struct.unpack_from('<4H',clean['H'],40))==[0,2,0,2] and list(struct.unpack_from('<4H',post['H'],40))==[2,0,2,0],'delayed history observations')
    need(struct.unpack_from('<I',post['N'])[0]==41 and struct.unpack_from('<6H',post['N'],24)==(0,)*6,'postfault ordinal41/current counts0')
    decoded_dm={}
    for label in ('dtBaseline','dtFault'):
        n=fixture[label];need(set(n)==DM_KEYS and n['schema']=='dt-rtp-fixed-reference-v1' and n['packingQualified']is True,'DM scientific whitelist');flags(n)
        need(type(n['headersSent'])is int and n['headersSent']==14 and type(n['bulkTransfers'])is int and n['bulkTransfers']==28 and type(n['uiOperations'])is int and n['uiOperations']==0 and n['atomicSnapshot']is False and n['errors']==[],'DM exact readonly count/scope')
        need(len(n['windows'])==14 and len(n['steps'])==28,'DM frame');decoded={};last=0
        for i,(w,(name,address,size)) in enumerate(zip(n['windows'],DM_SPECS,strict=True)):
            need(set(w)=={'name','address','bytes','sha256','base64'} and w['name']==name and w['address']==address and w['bytes']==size,'DM window spec')
            decoded[name]=raw(w['base64'],w['sha256'],size)
            for j in (0,1):
                step=n['steps'][2*i+j];need(set(step)=={'name','direction','expected','count','errno','beforeUs','afterUs','before','after'},'DM step fields')
                need(step['before']==('ReadyForHeader'if j==0 else'ExpectingIn') and step['after']==('ExpectingIn'if j==0 else'ReadyForHeader'),'DM phase')
                t={k:v for k,v in step.items()if k not in ('before','after')};last=transfer(t,name+('-header'if j==0 else'-data'),'OUT'if j==0 else'IN',12 if j==0 else size,last)
        need(decoded['start-R']==decoded['end-R'] and decoded['start-N']==decoded['end-N'],'DM matching endpoint brackets; not atomicity')
        need(struct.unpack_from('<I',decoded['M'],64)[0]==0x20010000 and half(decoded['M'],6)==2880 and half(decoded['M'],8)==1920 and half(decoded['M'],32)==0 and struct.unpack_from('<3H',decoded['C'])==(2160,1920,2880),'DT exact packing prerequisite')
        need(state(decoded['start-R'])==((0,0,1)if label=='dtBaseline'else(1,0x1001,0)),'DM clean/fault state')
        decoded_dm[label]=decoded
    fault=decoded_dm['dtFault'];need(half(fault['M'],32)==0 and struct.unpack_from('<3H',fault['C'])==(2160,1920,2880),'fault xbase/geometry')
    columns={name:struct.unpack('<48H',fault[name])for name in ('X','Y','RGB','B','Diff')};by_x={}
    for i in range(41):
        x,y,r,b,d=(columns[n][i]for n in ('X','Y','RGB','B','Diff'))
        need(y==2159 and r==0 and b<500 and d>500 and b+d<=4095,'conditional restricted-domain A')
        by_x.setdefault(x,set()).add(b+d)
    expected={570:1857,571:1857,624:3053,625:3053,632:1717,633:1717}
    need(by_x=={x:{a}for x,a in expected.items()},'stable conditional A by coordinate')
    def unpack_fixed(data):
        need(len(data)==104,'fixed extent104')
        values=[]
        for offset in range(0,102,6):
            word,tail=struct.unpack_from('<IH',data,offset)
            values.extend((word&4095,(word>>12)&4095,(word>>24)|((tail&15)<<8),tail>>4))
        return {x:values[x-568]for x in (570,571,622,623,624,625,632,633)}
    fixed={kind:unpack_fixed(fault['fixed-'+kind+'-candidate'])for kind in ('top','bottom')}
    need(fixed['bottom']=={570:1857,571:1857,622:454,623:454,624:3053,625:3053,632:1717,633:1717},'exact fixed bottom packed amplitudes')
    need(fixed['top']=={570:2168,571:2168,622:2160,623:2160,624:2149,625:2149,632:2157,633:2157},'exact fixed top packed amplitudes')
    bottom_matches=top_mismatches=0
    for i in range(41):
        x,b,d=columns['X'][i],columns['B'][i],columns['Diff'][i]
        bottom_matches+=b+d==fixed['bottom'][x]
        top_mismatches+=b+d!=fixed['top'][x]
    need(bottom_matches==41 and top_mismatches==41,'all conditional records match bottom and differ from top')
    need(622 not in by_x and 623 not in by_x,'two absent coordinates in this run')
    bracket={'beforeUs':r_pairs[3][1],'afterUs':r_pairs[4][2],'widthUs':r_pairs[4][2]-r_pairs[3][1]}
    need(bracket['widthUs']==253126,'DP software bracket')
    return {'schema':'public-rtp-reference-verification-v1','accepted':True,'checks':checks,'rawWindows':windows-1,'checkpointBytes':170,'rawBytesIncludingCheckpoints':raw_bytes,'dpCleanScores':scores,'dpPostfaultA0':42,'dpSoftwareBracket':bracket,'dtConditionalAByX':expected,'fixedCandidates':fixed,'conditionalBottomMatches':bottom_matches,'topMismatches':top_mismatches,'absent622623BSourceObserved':False,'wholeLiveImageAttested':False,'recordEpochProven':False,'actualFixedABranchProven':False,'physicalPictureObserved':False,'preventionEstablished':False,'targetOperations':0}


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('fixture',nargs='?',type=Path,default=Path(__file__).resolve().parents[1]/'fixtures/rtp-reference-run.json')
    print(json.dumps(verify(json.loads(cli.parse_args().fixture.read_text())),indent=2,sort_keys=True))
