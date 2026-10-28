#!/usr/bin/env python3
"""Pure host model tests, no native helper or I/O operations."""
from dataclasses import replace
from state_model import *
checks=0

def need(v,s):
    global checks
    checks+=1
    if not v:raise ValueError(s)

def reject(fn):
    try:fn()
    except ValueError:need(True,'refused');return
    raise ValueError('unexpected admission')

for word in range(65536):
    installed=set_low_bit(word)
    need(installed&0xfffe==word&0xfffe and installed&1==1,'other15bits preserved')
    need(clear_low_bit(installed)==word&0xfffe,'clear only lowbit')
reject(lambda:admit_set(Context(),Context()))
reject(lambda:admit_set(Context(fingerprints_verified=True,rt=(False,0,True)),Context(fingerprints_verified=True,rt=(False,0,True))))
a=Context(fingerprints_verified=True);pending=admit_set(a,a);reject(lambda:admit_restore(pending,replace(a,primary=1),replace(a,primary=1)))
proof=Transfer();proof.header(12);proof.payload(2);proof.readback(1,1);owner=confirm_set(pending,proof,replace(a,primary=1),replace(a,primary=1));need(owner.original==0 and owner.installed==1 and owner.set_readback_verified,'fixed ownership only after full write/readback/source guards')
reject(lambda:confirm_set(pending,Transfer(),replace(a,primary=1),replace(a,primary=1)))
for primary in(1,2,3,32768,65534,65535):reject(lambda:admit_set(replace(a,primary=primary),replace(a,primary=primary)))
for field,value in [('root',0x20011000),('rows',2159),('lanes',1919),('packed_bytes',2878),('x_base',1),('aa',1),('ac',1),('operating_mode',6),('trainer',1),('writer_2460',1),('publisher_246e',1),('refresh_counter',1),('secondary',1),('selector',2),('selector_mirror',1),('phase','Unknown'),('fingerprints_verified',False),('rt',(0,0,0)),('other_primary_words',(1,)+(0,)*66),('other_secondary_bytes',(1,)+(0,)*66)]:
    bad=replace(a,**{field:value});reject(lambda:admit_set(bad,bad));reject(lambda:admit_restore(owner,replace(bad,primary=1),replace(bad,primary=1)))
reject(lambda:admit_set(a,replace(a,instance='another-instance')))
reject(lambda:admit_set(a,replace(a,selector=1,selector_mirror=1)))
reject(lambda:admit_set(replace(a,rt=(1,0x1001,0)),replace(a,rt=(1,0x1001,0))))
for rt in ((0,0,1),(1,0x1001,0)):
    r=replace(a,primary=1,selector=1,selector_mirror=1,rt=rt)
    need(admit_restore(owner,r,r)==0,'separate coherent clean/fault restore, expected exposure change allowed')
    reject(lambda:admit_restore(owner,r,replace(r,instance='different')))
    reject(lambda:admit_restore(owner,r,replace(r,rt=(0,0,1)if rt!=(0,0,1)else(1,0x1001,0))))
for word in(0,2,3,32769,65535):reject(lambda:admit_restore(owner,replace(a,primary=word),replace(a,primary=word)))
for changed in (replace(owner,set_readback_verified=False),replace(owner,phase='Unknown'),replace(owner,original=2)):
    reject(lambda:admit_restore(changed,replace(a,primary=1),replace(a,primary=1)))
for count in (-1,0,11,13,True,None):
    t=Transfer();t.header(count);need(t.phase=='Unknown'and t.write_may_have_changed,'ambiguous header not known unchanged');reject(lambda:t.header(12));reject(lambda:t.payload(2))
for count in (-1,0,1,3,True,None):
    t=Transfer();t.header(12);need(t.payload_obligated,'clock error must not cancel exact pending payload');t.payload(count);need(t.phase=='Unknown'and t.write_may_have_changed,'ambiguous payload stops');reject(lambda:t.header(12));reject(lambda:t.readback(1,1))
t=Transfer();t.header(12);t.payload(2);need(t.phase=='ReadyForHeader'and t.write_transport_complete and not t.readback_verified,'USB completion not RAM readback');reject(lambda:t.readback(0,1));t.readback(1,1);need(t.readback_verified,'readback necessary')
# A stock ABA publication can reproduce the same word with the same sampled
# controls. This model cannot detect it; it must remain an explicit limitation.
need(admit_restore(owner,replace(a,primary=1),replace(a,primary=1))==0,'sampled admission does not prove no indistinguishable stock ABA writer')
for fn in (lambda:set_low_bit(True),lambda:clear_low_bit(65536),lambda:set_low_bit(-1)):reject(fn)
import json
print(json.dumps({'accepted':True,'checks':checks,'targetOperations':0,'networkOperations':0,'stateModelOnly':True,'continuousWriterQuiescenceProven':False}))
