"""Pure negative-assumption and width/edge checks; no live operations."""
import json
from selector_model import refresh,reference_edge,auxiliary_edge,dispatch
checks=0

def need(ok,why):
 global checks
 checks+=1
 if not ok:raise ValueError(why)

for value in range(256):
 need(refresh(value)=={'selectorC7':value,'root24ca':value},'copy full byte without bool coercion')
 for old in (0,1,2,255,256,65535):
  for count in (0,1,2,65535):
   r=reference_edge(value,old,count)
   need(r['mirror4c2']==value,'halfword mirror receives current byte')
   need(r['counter4c4']==(count if value==old else int(value!=0)),'unchanged selector does not rearm')
 for old in (0,1,2,255):
  r=auxiliary_edge(value,old)
  need(r=={'mirror45d':value,'changedToNonzero':value!=old and value!=0},'separate edge mirror')
for index in range(256):
 for ptr in (0,0x18c95):
  for active in (0,1,2,255):
   r=dispatch(index,ptr,active)
   need(r['callbackSelected']==(ptr or None)if index==0 else r['callbackSelected']is None,'only slot zero dispatch')
   need(r['index']==(1 if index==0 and active else 0),'finite next index or clear')
   need(r['nextSlotOffset']==(8 if index==0 and active else None),'no invented periodic delay')
need(reference_edge(2,1,0)['counter4c4']==1,'changed nonzero byte also seeds')
need(auxiliary_edge(2,1)['changedToNonzero']is True,'edge is not strictly zero-to-one')
need(reference_edge(1,1,0)['counter4c4']==0,'nonzero is not continual rearming')
need(dispatch(1,0x18c95,1)['callbackSelected']is None,'a second callback is not inferred')
for after in (0,1,2,254,255):
 r=dispatch(0,0x18c95,1,after)
 need(r['index']==(after+1)&255 and r['nextSlotOffset']==((after+1)&255)*8,'postcallback index reread and u8 truncation')
for fn,args in [(refresh,(True,)),(refresh,(-1,)),(refresh,(256,)),
  (reference_edge,(0,65536,0)),(reference_edge,(0,0,65536)),
  (auxiliary_edge,(1,256)),(dispatch,(256,0,0)),(dispatch,(0,-1,0)),(dispatch,(0,0,256))]:
 try:fn(*args)
 except ValueError:need(True,'malformed input rejected')
 else:need(False,'malformed input accepted')
print(json.dumps({'accepted':True,'checks':checks,'targetCalls':0,'networkCalls':0},sort_keys=True))
