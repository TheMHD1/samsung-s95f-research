#!/usr/bin/env python3
"""Pure bounded manual model of selected RTP aggregate/publication branches.
No target, root, network, OEM execution, external command or arbitrary output path.
T is an explicit hypothetical helper result, not an implementation of its producer.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib,json
@dataclass(frozen=True)
class State:
    aggregate:int=0
    q:int=0
    history:tuple=(0,0,0,0)
BLOCKED=frozenset((8,9,10,12,24,25))
def uint(v,bits,label):
    if type(v)is not int or not 0<=v<(1<<bits):raise ValueError(label)
def step(state,s,fp=40,bp=160,t=0):
    if type(state)is not State or type(state.history)is not tuple or len(state.history)!=4:raise ValueError('state')
    uint(state.aggregate,32,'aggregate');uint(state.q,5,'q')
    for x in state.history:uint(x,16,'history')
    for x,label in [(s,'s'),(fp,'fp'),(bp,'bp'),(t,'T')]:uint(x,16,label)
    q=((state.q<<1)&31)+int(s>bp)
    history=state.history[1:]+(s,)
    a=state.aggregate
    if q not in BLOCKED:
        a=(a+history[0])&0xffffffff
        if a>=t:a-=t
    score=a&0xffff
    return State(a,q,history),{'score':score,'fault':score>fp,'history_contribution':history[0],'aggregate_updated':q not in BLOCKED}
def trace(state,counts,fp=40,bp=160,t=0):
    if type(counts)is not list or len(counts)>1024:raise ValueError('bounded counts')
    out=[]
    for s in counts:
        state,r=step(state,s,fp,bp,t);out.append({'aggregate':state.aggregate,'q':state.q,'history':list(state.history),**r})
    return out

def publication(ordinal,qualifying,limit):
    """Aggregate-gate1 formatter: all inputs already pass its B-value filter.
    Returns source count modulo u16, ordinal and actual stored record indices.
    Does not model log throttle, alternate events, concurrency or time changes.
    """
    uint(ordinal,32,'ordinal');uint(limit,16,'limit');uint(qualifying,16,'qualifying')
    stored=[]
    for unused in range(qualifying):
        if ordinal<=limit:
            if ordinal<512:stored.append(ordinal)
            ordinal=(ordinal+1)&0xffffffff
    return {'ordinal':ordinal,'s':qualifying,'stored_indices':stored}

def main():
    checks=0
    def need(b,label):
        nonlocal checks
        checks+=1
        if not b:raise ValueError(label)
    D=Path(__file__).resolve().parent;B=D.parent
    package=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
    sha=lambda b:hashlib.sha256(b).hexdigest()
    need(sha(package)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','source pin')
    im=package[0x40200:0x60200]
    for a,h in [(0x1f14,'01ea4001'),(0x1f26,'00f01f01'),(0x1f7e,'814217dd'),(0x1fce,'0144'),(0x2002,'a0eb0a01'),(0x202a,'5f4507dd'),(0xb7f8,'002005e0'),(0xca8c,'42f82010'),(0xca92,'22f81010'),(0xca98,'42f82010'),(0xca9e,'22f81010'),(0xc6de,'13e0')]:need(im[a:a+len(bytes.fromhex(h))]==bytes.fromhex(h),'source landmark '+hex(a))
    initial=State(38,0,(4,0,2,0));old=trace(initial,[4,0,4,0]);new=trace(initial,[4,0,4,0],200)
    need([x['score'] for x in old]==[38,40,40,44],'CB compatible delayed sequence')
    need([x['fault'] for x in old]==[False,False,False,True],'strict threshold40')
    need(not any(x['fault'] for x in new),'same44 clean200')
    need([{k:v for k,v in x.items() if k!='fault'} for x in old]==[{k:v for k,v in x.items() if k!='fault'} for x in new],'threshold does not alter aggregate model')
    constant40=trace(State(),[4]*64);constant200=trace(State(),[4]*64,200)
    first=lambda rows:next((i+1 for i,x in enumerate(rows) if x['fault']),None)
    need(first(constant40)==14 and first(constant200)==54,'bounded repeated-small-count counterexample')
    need(constant40[13]['score']==44 and constant200[53]['score']==204,'counterexample scores')
    need(not step(State(40),0,40)[1]['fault'],'equality clean')
    need(step(State(41),0,40)[1]['fault'],'strict greater')
    need(step(State(0xfffffffF,0,(0,1,0,0)),0)[0].aggregate==0,'u32 add wrapping')
    need(step(State(65536),0)[1]['score']==0,'u16 score narrowing')
    need(step(State(10,0,(0,4,0,0)),0,t=5)[0].aggregate==9,'single T subtraction')
    need(step(State(0),0,t=5)[0].aggregate==0,'no unsigned T underflow')
    for q in range(32):
        for s in (0,160,161):
            st,r=step(State(10,q,(0,4,0,0)),s)
            want=((q<<1)&31)+int(s>160)
            need(st.q==want,'q progression')
            need(st.aggregate==(10 if want in BLOCKED else 14),'q gated add')
    p40=publication(0,220,40);p200=publication(0,220,200)
    need(p40['ordinal']==41 and len(p40['stored_indices'])==41,'bound40 admits41entries')
    need(p200['ordinal']==201 and len(p200['stored_indices'])==201,'bound200 admits201entries')
    need(p40['s']==p200['s']==220,'publication limit is not s cap')
    need(publication(41,4,40)['ordinal']==41 and publication(41,4,200)['ordinal']==45,'raising bound resumes publication')
    need(publication(512,2,65535)['stored_indices']==[],'capacity independent of ordinal increment')
    for a,h in [(0x18b00,'40f29513'),(0x18b1a,'02eb4202'),(0x18b1e,'03eb8221'),(0x18b3a,'5b22')]:need(im[a:a+len(bytes.fromhex(h))]==bytes.fromhex(h),'producer arithmetic '+hex(a))
    need((0x195<<16)//0xc00==8640 and (0x195<<16)==0xc00*2160*4,'exact channel/row stride arithmetic')
    need(0x5b*32==0xb60 and (2880//6)*4==1920 and 0xb60-2880==32,'copy and unpack extents')
    for bad in [lambda:step(State(),True),lambda:step(State(1<<32),0),lambda:step(State(q=32),0),lambda:trace(State(),[0]*1025),lambda:publication(0,65536,40)]:
        try:bad()
        except ValueError:checks+=1
        else:raise ValueError('invalid accepted')
    print(json.dumps({'schema':'de-limit-model-v1','qualification':'manual model with exact source landmarks, conditional aggregate gate1/wait0/selected slot; not live execution equivalence or a physical model','checks_passed':checks,'source_sha256':sha(package),'predicate_range':{'file_offset':'0x42068','bytes':0x1d6,'sha256':sha(im[0x1e68:0x203e])},'compatible_CB_trace':old,'counterfactual_same_inputs_limit200':new,'illustrative_constant_s4':{'initial':'A0/q/history zero;T0;noreset;not an observed trace','first_fault_limit40_invocation':first(constant40),'first_fault_limit200_invocation':first(constant200),'limit40_score':constant40[13]['score'],'limit200_score':constant200[53]['score']},'publication':{'limit40_ordinal':p40['ordinal'],'limit200_ordinal':p200['ordinal'],'same_source_count':p40['s'],'capacity':512},'tv_actions':0,'network_actions':0,'oem_executions':0},sort_keys=True))
if __name__=='__main__':main()
