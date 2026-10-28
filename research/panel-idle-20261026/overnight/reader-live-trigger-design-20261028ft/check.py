#!/usr/bin/env python3
"""Design-only finite source and predicate cases; no live imports or helpers."""
from pathlib import Path
import hashlib,json,sys
D=Path(__file__).resolve().parent;B=D.parent;n=0
def need(v,s):
 global n
 n+=1
 if not v:raise ValueError(s)
refs=json.loads((D/'input-pins.json').read_bytes())['files']
for r in refs:
 b=(B/r['path']).read_bytes();need(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'pin '+r['path'])
nav=(B/'ui-navigation-20261027br/navigate.py').read_text();wake=(B/'combined-event-successor-20261028fn/wake-check.py').read_text();wrapper=(B/'combined-event-successor-20261028fn/run-once.py').read_text()
need("'d/ug.tab@Live': [('up', 'd/ug.tab@Live'), ('up', 'd/ug.tab@Live'),\n                               ('left', 'd/ug.tab@ForYou')]"in nav,'existing Live header path')
need(wrapper.index('wake.perform(output')>wrapper.index("run('selftest'"),'staging/selftest before wake')
need('MAX_SNAPSHOTS=10;SETTLE_SECONDS=.25;BUDGET_NS=10000000000;AGE_NS=1000000000'in wake,'finite unchanged timing model')
need("tabs==['memory/eden/current_tab, value = d/apps.tab (String)']"in wake,'explicit old predicate to replace, not wildcard')
# Pure proposed admission predicate over already parsed observations; no shell/native code.
def candidate(tabs,saver,csfs,age):return tabs==['d/ug.tab@Live']and not saver and csfs and type(age)is int and 0<=age<=1000000000
for tabs,saver,csfs,age,expected in [(['d/ug.tab@Live'],False,True,0,True),(['d/ug.tab@Live'],False,True,1000000000,True),(['d/apps.tab'],False,True,0,False),(['d/ug.tab@ForYou'],False,True,0,False),([],False,True,0,False),(['d/ug.tab@Live']*2,False,True,0,False),(['d/ug.tab@Live'],True,True,0,False),(['d/ug.tab@Live'],False,False,0,False),(['d/ug.tab@Live'],False,True,-1,False),(['d/ug.tab@Live'],False,True,1000000001,False),(['d/ug.tab@Live'],False,True,False,False)]:need(candidate(tabs,saver,csfs,age)==expected,'finite candidate policy')
print(json.dumps(dict(schema='ft-design-checks-v1',checks=n,inputs=len(refs),implementationProvided=False,targetCalls=0,rootCalls=0,networkCalls=0),sort_keys=True))
