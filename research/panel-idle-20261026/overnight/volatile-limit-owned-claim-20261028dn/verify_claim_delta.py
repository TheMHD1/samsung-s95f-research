#!/usr/bin/env python3
"""Host-only proof that DN keeps the frozen DL controller transaction logic."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;OLD=P.parent/'volatile-limit-receipt-20261028dl'
def sha(b):return hashlib.sha256(b).hexdigest()
def need(b,s):
 if not b:raise ValueError(s)
a=(OLD/'Program.cs').read_bytes();need(sha(a)=='d66128ae3faa00f907a3c017799a26f8ad06d783945deee3532f55312d09a307','frozen DL native source')
b=(P/'Program.cs').read_bytes();sa=a.decode();sb=b.decode()
def section(s,start,end):return s[s.index(start):s.index(end,s.index(start))]
checks={}
for name,start,end in [('fixed_headers','    static readonly Spec Callback=','    static void Need('),('profile_and_guards','    static readonly byte[] Profile=','    sealed class Controller'),('controller_transactions','    sealed class Controller','    static Outcome Run('),('run_state_machine','    static Outcome Run(','    static byte[] ReadCachedDescriptors'),('cached_descriptor_reader','    static byte[] ReadCachedDescriptors','    sealed class RealClock')]:
 x=section(sa,start,end);y=section(sb,start,end);need(x==y,name+' changed');checks[name]={'unchanged':True,'sha256':sha(x.encode())}
pa=(OLD/'parse-result.py').read_text();pb=(P/'parse-result.py').read_text();need(pb.replace('dn-fixed-limit','dl-fixed-limit').replace('Strict offline DN','Strict offline DL')==pa,'strict native receipt parser change beyond schema')
need(sb.count('read(fd,descriptor,(UIntPtr)18)')==1 and 'ValidateFdIdentity(openedFd,id)' in sb,'single advancing cached read / stat-only revalidation')
need('if(n.Value==0){ownClaim=true;claimFd=fd;}' in sb,'ownership follows successful claim only')
need('Need(ownClaim&&fd==claimFd&&fd==openedFd,"bulk requires own successful claim")' in sb,'bulk ownership guard')
print(json.dumps({'schema':'dn-claim-delta-verification-v1','target_operations':0,'parent_source_sha256':sha(a),'current_source_sha256':sha(b),'unchanged_controller_sections':checks,'strict_receipt_parser_schema_only_change':True,'cached_descriptor_reads':1,'owned_fd_stat_revalidation':True,'ownership_set_only_after_claim_zero':True,'bulk_requires_own_claim':True},indent=2))
