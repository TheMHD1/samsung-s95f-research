#!/usr/bin/env python3
import json
from dataclasses import replace
from slg_model import First,Second,first,second,selector
checks=0
def need(ok,why):
 global checks
 if not ok:raise ValueError(why)
 checks+=1
f=First(1,1,0,30,30,0,(90,90,90,98),(99,99,99))
need(first(f)['e6']==1,'ce0 mature first output')
need(first(replace(f,x=(90,90,90)))['e6']==0,'strict greater boundary')
need(first(replace(f,x=(91,0,0)))['e6']==1,'any not all channel crossing')
need(first(replace(f,count0=29))['e6']==0 and first(replace(f,count0=29))['count_e2']==30,'threshold reached then next call matures')
need(first(replace(f,ce=1))['F0'] is False,'ce1 suppress first if all exceed P3')
need(first(replace(f,ce=1,x=(99,98,99)))['F0'],'ce1 first accepts one at P3')
need(first(replace(f,ce=1,x=(98,0,0),count1=30))['F1'],'F1 includes equality')
need(not first(replace(f,ce=1,x=(97,0,0),count1=30))['F1'],'F1 below boundary false')
need(first(replace(f,cc=0))['count_e2']==30 and first(replace(f,cc=0))['e6']==0,'disabled cc preserves old counter')
need(first(replace(f,ca=0))['e6']==0,'ca disables first output')
s=Second(1,1,3,30,0,30,30,5,1,5,1,6,2,(15,20,30),50,19,29,49,51,14,16)
need(second(s)['value_2fc']==3,'both mature secondary branches')
need(second(replace(s,ap_ag_92=6,ap_37a=1))['value_2fc']==2,'AP_AG bound')
need(second(replace(s,ap_ag_92=6,ap_37a=2))['value_2fc']==3,'second AP_AG/AP alternative')
for field,value in [('lane1_lower',20),('lane2_lower',30),('x0_lower',50),('x0_upper',50),('lane0_lower',15),('lane0_upper',15)]:
 need(second(replace(s,**{field:value}))['value_2fc']==1,'strict secondary boundary '+field)
need(second(replace(s,count0=29,count1=29))['value_2fc']==0,'secondary debounce threshold reached not yet mature')
need(second(replace(s,previous_2fc=3,count0=29,count1=29))['value_2fc']==3,'immature true retains already-set bits')
need(second(replace(s,mask=1,previous_2fc=2))['value_2fc']==3,'unselected bit retains old state')
need(second(replace(s,ca=0,previous_2fc=2))['value_2fc']==2,'outer gate skips secondary so stale state survives')
need(second(replace(s,enable=0,previous_2fc=3))['value_2fc']==0,'secondary global enable clears bitmask')
need(second(replace(s,mask=0,previous_2fc=3))['value_2fc']==0,'zero mask clears bitmask')
need(selector(2,0) is False and selector(1,0) is True and selector(0,2) is True,'selector uses only e6 bit0 but any2fc')
# Retained W numerical state, not event-time evidence.
f=First(1,1,0,30,30,0,(7464960,7464960,7464960,8128512),(8254590,8251261,8250967))
need(first(f)['e6']==1 and selector(first(f)['e6'],0),'W exact configured arithmetic')
print(json.dumps({'schema':'df-upstream-model-tests-v1','checks':checks,'target_operations':0,'source_table_units_identified':False,'physical_causation_established':False}))
