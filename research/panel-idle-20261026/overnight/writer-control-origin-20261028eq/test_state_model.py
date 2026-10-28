#!/usr/bin/env python3
"""Small pure-integer regression table, no target or source mutation."""
import json
from state_model import arm,pause,finish,gate_on,gate_off,dispatch_gate
checks=0
def need(ok):
 global checks
 if not ok:raise ValueError('model mismatch')
 checks+=1
for args,want in [((0,0,1),1),((0,1,1),0),((0,0,0),0),((1,0,1),1),((2,0,1),2),((3,0,0),1),((3,9,0),1),((4,0,1),4)]:need(arm(*args)==want)
for state in(0,1,2,3,4,65535):
 need(pause(state,0)==(3 if state==1 else state));need(pause(state,1)==state)
 need(finish(state,1)==((2,True)if state==1 else(state,False)))
 need(finish(state,0)==((2,False)if state==1 else(state,False)))
 need(gate_on(state)==(1 if state==0 else state));need(gate_off(state)==(0 if state==1 else state))
for mode in(0,1,4,7,8,9,10,11,65535):
 need(dispatch_gate(mode,0)==(1 if mode in(8,10)else 0));need(dispatch_gate(mode,1)==(1 if mode in(8,10)else 0))
# Gate-off does not imply stop/fault stores. A sequential observer can capture
# this source-compatible triplet without a fault-setter having run.
triplet=(0,0,1);need((triplet[0],triplet[1],gate_off(triplet[2]))==(0,0,0))
for call in(lambda:arm(-1,0,1),lambda:finish(True,0),lambda:gate_off(65536)):
 try:call()
 except ValueError:checks+=1
 else:raise ValueError('bad integer admitted')
print(json.dumps({'schema':'eq-state-model-validation-v1','checksPassed':checks,'targetOperations':0,'completeStateMachineProven':False},sort_keys=True))
