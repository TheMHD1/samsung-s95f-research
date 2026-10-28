"""Host-only synthetic P/N extension of SHA-pinned old test fixtures."""
import base64,copy,hashlib

def upgrade(original):
 value=copy.deepcopy(original)
 for cap in value['retained']:
  windows=[];transfers=[]
  for i,w in enumerate(cap['windows']):
   windows.append(w);transfers.extend(cap['transfers'][2*i:2*i+2])
   if w['name']=='C':
    stamp=transfers[-1]['afterUs']
    for name,address,n in [('P','0x47000490',16),('N','0x4700ba28',36)]:
     raw=bytes(n)
     windows.append({'name':name,'address':address,'expected':n,'count':n,'complete':True,'rawBase64':base64.b64encode(raw).decode(),'sha256':hashlib.sha256(raw).hexdigest()})
     for direction,part,expected in [('OUT','header',12),('IN','data',n)]:
      t=copy.deepcopy(transfers[-2] if direction=='OUT' else transfers[-1]);t.update(name=name+'-'+part,direction=direction,expected=expected,count=expected,beforeUs=stamp,afterUs=stamp);transfers.append(t)
  cap['windows']=windows;cap['transfers']=transfers
 clean=value['cleanCyclesCompleted'];term=value['terminalReason']
 if term=='TransitionCaptured':
  width=len(next(c for c in value['retained'] if c['role']=='transition')['windows']);headers=clean*8+width+7
 elif term=='AlreadyFaulted':headers=8
 else:
  partial=next((c for c in value['retained'] if c['role']=='current-partial'),None);headers=clean*8+(len(partial['windows']) if partial else 0)
 value.update(headersSent=headers,inputsCompleted=headers,bulkTransfers=headers*2)
 return value
