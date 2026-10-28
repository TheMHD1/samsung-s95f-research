#!/usr/bin/env python3
"""Pure selective-update model/design: no writer, USB, ctypes native call, subprocess or network binding."""
import struct
STATIC={'base':2075,'reference':24,'coefficient':15,'scale':195,'floor':3000,'cap':3800,'b_lower':500}
THERMAL_HALFWORDS=(0x20,0x98,0xbc)
ECHO_HALFWORD=0xac

def need(ok,why):
 if not ok:raise ValueError(why)
def u16(raw,offset):return struct.unpack_from('<H',raw,offset)[0]
def scaled_temperature(raw_u16):
 need(type(raw_u16)is int and 0<=raw_u16<=65535,'raw getter u16')
 return raw_u16//16

def scaled_reference(raw_u16):
 ref=scaled_temperature(raw_u16)
 return 25 if ref>4000 else ref

def endpoint(base,reference,temp,coefficient,scale,floor,cap):
 for v in [base,reference,temp,coefficient,scale,floor,cap]:need(type(v)is int and 0<=v<=65535,'u16 operands')
 # ARM sub/MLA/MUL wrap at32bits. UBFX selects bits7..22, not arbitrary division.
 delta=(temp-reference)&0xffffffff
 mla=(base+coefficient*delta)&0xffffffff
 product=(mla*scale)&0xffffffff
 candidate=(product>>7)&65535
 # Actual branch first caps; only the non-capped branch applies the minimum.
 output=cap if candidate>cap else max(floor,candidate)
 return {'deltaU32':delta,'mlaU32':mla,'productU32':product,'extractedU16':candidate,'endpoint':output}

def endpoint_observations(raw):
 """Compute against shared diagnostics; neither endpoint is assumed freshly updated."""
 need(type(raw)is bytes and len(raw)==256,'R256')
 need(u16(raw,0x94)==STATIC['base']and u16(raw,0x96)==STATIC['reference'],'fixed base/reference mirrors')
 temp=u16(raw,0x98);need(temp<=4095,'temperature mirror source range')
 echo=u16(raw,ECHO_HALFWORD);need(echo<=254,'own protocol echo range / zero high byte')
 out={'temperature':temp,'echo':echo,'modes':{}}
 for name,at,co,sc,ca,fl in [('normal',0x20,0xae,0xb0,0xb2,0x2e),('alternate',0xbc,0xb6,0xb8,0xba,0x2c)]:
  need((u16(raw,co),u16(raw,sc),u16(raw,ca),u16(raw,fl))==(STATIC['coefficient'],STATIC['scale'],STATIC['cap'],STATIC['floor']),'fixed coefficient/scale/cap/floor '+name)
  calc=endpoint(STATIC['base'],STATIC['reference'],temp,STATIC['coefficient'],STATIC['scale'],STATIC['floor'],STATIC['cap'])
  need(STATIC['b_lower']<calc['endpoint']<=4095 and STATIC['floor']<=calc['endpoint']<=STATIC['cap'],'bounded B endpoint '+name)
  out['modes'][name]={'actual':u16(raw,at),'model':calc,'matchesSharedDiagnostics':u16(raw,at)==calc['endpoint']}
 return out

ALTERNATE_ENDPOINT_IMAGE=frozenset(endpoint(2075,24,t,15,195,3000,3800)['endpoint'] for t in range(4096))

def profile_prediction(raw):
 """Restrictive ordinary-current / alternate finite-preimage admission."""
 out=endpoint_observations(raw)
 need(out['modes']['normal']['matchesSharedDiagnostics'],'source-model endpoint normal')
 actual=out['modes']['alternate']['actual']
 need(actual in ALTERNATE_ENDPOINT_IMAGE,'alternate endpoint exact finite source image')
 out['modes']['alternate']['hasFiniteSourcePreimage']=True
 return out

def pairwise_thermal_stable(before,after):
 need(type(before)is bytes and type(after)is bytes and len(before)==len(after)==256,'R pair')
 return all(u16(before,o)==u16(after,o)for o in THERMAL_HALFWORDS)

# Design-only composition with the previous exact profile, not a native writer.
def legacy_historical_byte(i):return 0x86<=i<0x8a or 0x8c<=i<0x8e or 0x90<=i<0x94 or 0xa2<=i<0xa4
ADDITIONAL_MODEL_BYTES=frozenset(i+j for i in (*THERMAL_HALFWORDS,ECHO_HALFWORD)for j in [0,1])
def validate_candidate_r(raw,expected_limit,frozen_profile):
 need(type(raw)is bytes and len(raw)==256 and type(frozen_profile)is bytes and len(frozen_profile)==256,'R/profile extent')
 need(expected_limit in [40,200],'fixed action limit')
 for i,v in enumerate(raw):
  if not legacy_historical_byte(i) and i not in ADDITIONAL_MODEL_BYTES|{0xc4,0xc5,0xca}:need(v==frozen_profile[i],'remaining exact profile byte '+str(i))
 need(raw[0xca]<=1,'legacy observed selector domain')
 need(u16(raw,0)==u16(raw,10)==u16(raw,6)==0 and u16(raw,14)==1,'clean gate/logger')
 need(u16(raw,0xc4)==expected_limit and u16(raw,0x30)==u16(raw,0xc0)==200,'fixed action/normal limits')
 need(u16(raw,0x9e)==1 and all(u16(raw,o)==0 for o in [0x4a,0x4e,0x9a,0x9c]),'unchanged alternative gates/latches')
 return profile_prediction(raw)

def validate_candidate_context(m,c,r):
 need(type(m)is bytes and len(m)==68 and type(c)is bytes and len(c)==16,'M/C extents')
 need(struct.unpack_from('<I',m,64)[0]==0x20010000 and u16(m,10)==0 and u16(m,12)==2 and m[56]==1,'root/mode/scan')
 need([u16(m,o)for o in [22,24,26,28]]==[500,0,500,0] and u16(m,40)==500,'fixed directional/lower thresholds')
 need(u16(m,38)==u16(r,0x20),'M current ordinary endpoint mirror agreement')
 need(struct.unpack_from('<3H',c)==(2160,1920,2880) and c[6]==92 and c[7]<=1 and c[8]==3,'unchanged geometry/profile/selector')

def validate_transaction_pair(before,after,old_limit,new_limit,frozen_profile):
 validate_candidate_r(before,old_limit,frozen_profile);validate_candidate_r(after,new_limit,frozen_profile)
 need(before[0xca]==after[0xca],'legacy selector stable')
 need(pairwise_thermal_stable(before,after),'thermal tuple stable in one bounded write transaction')
 for i in range(256):
  if not legacy_historical_byte(i) and i not in {0xc4,0xac,0xad}:need(before[i]==after[i],'unchanged nonstatus byte '+str(i))
