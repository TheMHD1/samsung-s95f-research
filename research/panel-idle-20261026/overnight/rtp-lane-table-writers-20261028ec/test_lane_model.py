#!/usr/bin/env python3
"""Explicit arithmetic/negative-assumption checks retained under Python -O."""
import json
from lane_model import band,observe,publish,local_admission
checks=0
def need(ok,msg):
 global checks
 checks+=1
 if not ok:raise ValueError(msg)
def refusal(f):
 try:f()
 except ValueError:need(True,'refused domain');return
 raise ValueError('unexpected model acceptance')
need(band(100,0)==(100,100),'zero factor is exact equality band')
for value in (0,99,101,4095):
 out=observe(100,0,0,value,0,0,0)
 need(out['counter']==out['flag']==out['aggregate']==1,'first outside observation threshold0')
need(observe(100,0,0,100,0,0,0)['counter']==0,'equal value inside')
count=flag=aggregate=0
for value,want_count,want_flag in [(101,1,0),(100,1,0),(101,2,0),(100,2,0),(101,3,1),(100,3,1)]:
 o=observe(100,0,2,value,count,flag,aggregate);count,flag,aggregate=o['counter'],o['flag'],o['aggregate']
 need((count,flag)==(want_count,want_flag),'cumulative not consecutive, sticky flag')
need(aggregate==1,'new flag only once')
o=observe(100,0,0,101,65535,0,0)
need(o['counter']==0 and o['flag']==0,'counter wrap before threshold comparison')
o=observe(100,0,0,101,65535,1,65535)
need(o['counter']==0 and o['flag']==1 and o['aggregate']==65535,'counter wrap does not clear old flag')
need(observe(100,0,0,101,0,0,65535)['aggregate']==0,'aggregate halfword wrap')
for mean in (0,1,100,4095,65535,0xffffffff):
 for factor in (0,1,25,255,256,257,65535):
  # Independent modulo before shift, then independent low-halfword coercion.
  delta=(mean*factor%(2**32))//256
  low=(mean-delta)%(2**16);high=(mean+delta)%(2**16)
  need(band(mean,factor)==(low,high),'target arithmetic, not unbounded product or clamping')
  for value in (0,1,99,100,4095,65535):
   o=observe(mean,factor,200,value,200,0,0)
   need(o['outside']==(value>high or value<low),'source strict comparisons/equal boundaries')
need(band(4095,65535)!=(0,4095),'no invented12bit clamp')
for counter in (0,1,2,200,32767,32768,65535):
 for flag in (0,1,2,255):
  word=publish(counter,flag)
  need(word==(2*counter+flag)%65536,'publication width')
  need(word&1==flag&1,'primary bit0 is flag lowbit on publisher path')
need(publish(0,1)==publish(32768,1),'primary loses counter highbit')
need(publish(0,0)==publish(32768,0),'zero primary does not prove zero counter history')
need(publish(7,0)==14,'other primarybits carry count, not disposable padding')
for primary in (0,1,2,3,0x100,0xfffe,0xffff):
 for secondary in (0,1,255):
  for aa in (0,1,2):
   for ac in (0,1,2):
    for override in (0,1,255):
     want=primary%2==0 and (secondary==0 or ((aa==1 or ac==1)and override>0))
     need(local_admission(primary,secondary,aa,ac,override)==want,'independent local gate truth table')
need(not local_admission(1,0,1,1,1),'primary bit cannot be bypassed by secondary override')
need(local_admission(0,2,1,0,1),'secondary nonzero can be bypassed without changing table')
for f in [lambda:band(True,0),lambda:band(0,-1),lambda:observe(0,0,0,65536,0,0,0),
          lambda:observe(0,0,0,0,0,256,0),lambda:publish(65536,0),lambda:publish(0,-1),
          lambda:local_admission(0,0,0,0,256)]:refusal(f)
print(json.dumps({'accepted':True,'checks':checks,'targetOperations':0,'modeledScope':'selected low-SRAM lane arithmetic and local eligibility only'},sort_keys=True))
