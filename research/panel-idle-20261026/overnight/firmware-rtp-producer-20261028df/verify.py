#!/usr/bin/env python3
"""DF host-only source/window/logger verification; never contacts a device."""
import hashlib,json,struct,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent
PKG_SHA='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0'
def need(ok,msg):
 if not ok:raise ValueError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def header(a,n):
 need((a,n) in {(0x47000490,16),(0x4700ba28,36)},'fixed addon window only')
 return struct.pack('<III',0x101,a,n)
def decode_n(b):
 need(len(b)==36,'N exact length')
 return {'record_ordinals':list(struct.unpack_from('<6I',b)), 'source_counts':list(struct.unpack_from('<6H',b,24)), 'mode1_array_index':0,'array_modes':[1,2,3,4,5,6]}
def decode_p(b):
 need(len(b)==16,'P exact length')
 v=struct.unpack('<4I',b)
 return {'neighbor_490_raw':v[0],'dynamic_A_slot':v[1],'dynamic_B_slot':v[2],'neighbor_49c_raw':v[3], 'fixed_A_branch_determined':False}
def main():
 package=(P/'private/official-selected-package.bin').read_bytes();need(sha(package)==PKG_SHA and len(package)==5242880,'package pin')
 parent=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes();need(package==parent,'prior/package equality')
 factory=B.parents[1]/'firmware-extracted-20261028/factory_peq.img'
 member='tcon_data/QD/F_RSM1_BN9659934B_COMMON.bin'
 got=subprocess.run(['unsquashfs','-cat',str(factory),member],capture_output=True,check=True)
 need(got.stdout==package and not got.stderr,'official member exact equality')
 im=package[0x40200:0x60200]
 anchors={}
 for label,a,n in [('resource_binding',0x1bcde,12),('resource_lookup',0x1bc24,0x28),('get_context_pointer',0x38e8,12),('get_fixed_context',0x38f4,8),('alternate_byte_refresh',0x394a,20),('descriptor_refresh',0x3972,0x54),('ring_producer',0x18ae8,0x12c),('dynamic_pointer_dispatch',0xb80c,0x84),('counter_bound',0xc5f6,16),('count_increment',0xc708,20),('descriptor_changed_flag',0x18d84,0x28),('counter_literal',0xc84c,4),('count_literal',0xc88c,4)]:
  anchors[label]={'image':1,'address_domain':'image1_linked_VA','address':hex(a),'file_offset':hex(a+0x40200),'bytes':n,'sha256':sha(im[a:a+n])}
 need(im[0x1bd4c:0x1bd54]==b'AP_EXCO\0','resource binding name')
 need(struct.unpack_from('<I',im,0x1bd5c)[0]==0x200002cc,'resource binding pointer slot')
 need(struct.unpack_from('<I',im,0x38f0)[0]==0x200002cc,'runtime context getter')
 need(struct.unpack_from('<I',im,0x38f8)[0]==0x20000500,'fixed context getter')
 need(struct.unpack_from('<I',im,0xc84c)[0]==0x2000ba28,'ordinal array')
 need(struct.unpack_from('<I',im,0xc88c)[0]==0x2000ba40,'source count array')
 need(header(0x47000490,16).hex()=='010100009004004710000000','P bytes')
 need(header(0x4700ba28,36).hex()=='0101000028ba004724000000','N bytes')
 fixture=struct.pack('<6I6H',*range(41,47),*range(44,50));need(decode_n(fixture)['source_counts']==list(range(44,50)),'N offsets')
 need(decode_p(struct.pack('<4I',0,0x20253002,0x20253b6a,0))['dynamic_B_slot']==0x20253b6a,'P offsets')
 rejected=0
 for fn,n in [(decode_n,36),(decode_p,16)]:
  for z in [0,n-1,n+1,256]:
   try:fn(bytes(z))
   except ValueError:rejected+=1
   else:raise ValueError('malformed window accepted')
 for a,n in [(0x47000494,16),(0x4700ba28,35),(0x58601408,16),(0x60000000,16)]:
  try:header(a,n)
  except ValueError:rejected+=1
  else:raise ValueError('arbitrary window accepted')
 dt=B.parents[1]/'live-cast/sdk/runtime/dotnet';dll=P/'private/logger/bin/Release/net6.0/SynchronizedOnset.dll';runs=[]
 for arg in ['--self-test','--key-self-test']:
  r=subprocess.run([str(dt),str(dll),arg],capture_output=True,text=True,check=True);need(not r.stderr,'host tests stderr');runs.append(json.loads(r.stdout))
 r=subprocess.run([str(dt),str(dll),'--execute'],capture_output=True,text=True)
 need(r.returncode==63 and r.stdout.strip()=='DF_HOST_ONLY_CANDIDATE_NO_EXECUTION_ENTRYPOINT','execution refuses')
 print(json.dumps({'schema':'df-host-qualification-v1','target_operations':0,'package_sha256':PKG_SHA,'official_member':member,'source_anchors':anchors,'host_tests':runs,'negative_window_cases':rejected,'new_windows_target_qualified':False,'running_image_identity_proven':False,'physical_aperture_writer_proven':False},indent=2))
if __name__=='__main__':main()
