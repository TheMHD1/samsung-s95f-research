#!/usr/bin/env python3
"""Original host-only model of selected AP_EXCO selector decision branches.
Inputs are integer field values, not device handles or writable configuration.
The model does not identify source table units, physical producer or cadence.
"""
from dataclasses import dataclass

def need(ok, why):
    if not ok: raise ValueError(why)

def debounce(condition, count, threshold):
    need(type(count) is int and 0 <= count <= 65535, 'u16 count')
    need(type(threshold) is int and 0 <= threshold <= 65535, 'u16 threshold')
    if not condition: return 0, False
    if count >= threshold: return count, True
    return count + 1, False

@dataclass(frozen=True)
class First:
    ca: int
    cc: int
    ce: int
    threshold: int
    count0: int
    count1: int
    p: tuple
    x: tuple

def first(v):
    need(len(v.p)==4 and len(v.x)==3 and all(type(n) is int and 0<=n<=0xffffffff for n in (*v.p,*v.x)), 'u32 aggregate fields')
    c0=c1=False;count0,count1=v.count0,v.count1
    if not v.ca: return {'e6':0,'count_e2':count0,'count_e4':count1,'F0':False,'F1':False}
    if v.cc:
        c0=any(x>p for x,p in zip(v.x,v.p[:3]))
        if v.ce: c0=c0 and any(x<=v.p[3] for x in v.x)
        count0,f0=debounce(c0,count0,v.threshold)
    else: f0=False  # branch bypasses the counter write as well as decision
    if v.ce:
        c1=any(x>=v.p[3] for x in v.x)
        count1,f1=debounce(c1,count1,v.threshold)
    else: f1=False
    return {'e6':int(f0)|(int(f1)<<1),'count_e2':count0,'count_e4':count1,'F0':f0,'F1':f1}

@dataclass(frozen=True)
class Second:
    ca: int
    enable: int
    mask: int
    threshold: int
    previous_2fc: int
    count0: int
    count1: int
    ap_ag_92: int
    ap_37a: int
    ag_bound0: int
    ap_code0: int
    ag_bound1: int
    ap_code1: int
    raw_lane_bin15: tuple
    x0: int
    lane1_lower: int
    lane2_lower: int
    x0_lower: int
    x0_upper: int
    lane0_lower: int
    lane0_upper: int

def second(v):
    need(type(v.previous_2fc) is int and 0<=v.previous_2fc<=65535,'u16 bitmask')
    bits=v.previous_2fc;c0,c1=v.count0,v.count1
    if not v.ca: return {'value_2fc':bits,'counter_300':c0,'counter_302':c1,'skipped':True}
    if not v.enable or not v.mask: return {'value_2fc':0,'counter_300':c0,'counter_302':c1,'skipped':False}
    if v.mask&1:
        condition=(v.ap_ag_92<=v.ag_bound0 and v.ap_37a==v.ap_code0) or (v.ap_ag_92<=v.ag_bound1 and v.ap_37a==v.ap_code1)
        c0,mature=debounce(condition,c0,v.threshold)
        # A true but immature branch does not clear an already-set bit.
        if not condition: bits &= ~1
        elif mature: bits |= 1
    if v.mask&2:
        lane0,lane1,lane2=v.raw_lane_bin15
        condition=lane1>v.lane1_lower and lane2>v.lane2_lower and v.x0>v.x0_lower and v.x0<v.x0_upper and lane0>v.lane0_lower and lane0<v.lane0_upper
        c1,mature=debounce(condition,c1,v.threshold)
        if not condition: bits &= ~2
        elif mature: bits |= 2
    return {'value_2fc':bits,'counter_300':c0,'counter_302':c1,'skipped':False}

def selector(e6, value_2fc): return bool((e6&1) or value_2fc)
