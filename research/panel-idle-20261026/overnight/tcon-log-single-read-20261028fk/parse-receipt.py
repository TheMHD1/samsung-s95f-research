#!/usr/bin/env python3
"""Offline FK receipt verifier. Does not open the debugfs node or call an adapter."""
import base64,hashlib,json,pathlib,sys
def need(v,m):
 if not v:raise ValueError(m)
def pairs(items):
 d={}
 for k,v in items:need(k not in d,'duplicate field');d[k]=v
 return d
def integer(v):return type(v)is int
FIELDS=set('schema accepted executed path requestedCount allocatedBytes initializedFillByte bufferPinnedBeforeOpen bufferPrefaultedBeforeOpen openAttempted readAttempted closeAttempted openResult openErrno readResult readErrno closeResult closeErrno nativeClock bracketsUs clockFailureMask exceptionMask rawAllocationBase64 rawAllocationSha256 returnedPrefixBytes returnedPrefixSha256 readCallsMaximum retries writesToDriver completeLogProven externalRtpProducerProven copyCompletionAttested loadedModuleBytesAttested producerAtomicityProven timeoutOrRollbackGuaranteed physicalPictureObserved'.split())
LIMITS='completeLogProven externalRtpProducerProven copyCompletionAttested loadedModuleBytesAttested producerAtomicityProven timeoutOrRollbackGuaranteed physicalPictureObserved'.split()
def parse(raw):
 need(type(raw)is bytes and len(raw)<=16384,'private receipt extent')
 v=json.loads(raw.decode('utf8'),object_pairs_hook=pairs,parse_constant=lambda c:(_ for _ in ()).throw(ValueError(c)))
 need(type(v)is dict and set(v)==FIELDS,'exact receipt fields')
 need(v['schema']=='fk-single-read-v1' and v['path']=='/sys/kernel/debug/tcon/tcon_micom_log' and v['nativeClock']=='Stopwatch-monotonic-us','fixed source/clock')
 for k,n in [('requestedCount',4096),('allocatedBytes',4096),('initializedFillByte',165),('readCallsMaximum',1),('retries',0),('writesToDriver',0)]:need(integer(v[k])and v[k]==n,'fixed '+k)
 for k in ['executed','bufferPinnedBeforeOpen','bufferPrefaultedBeforeOpen']:need(v[k]is True,'buffer/attempt declaration '+k)
 for k in LIMITS:need(v[k]is False,'unproved '+k)
 for k in ['accepted','openAttempted','readAttempted','closeAttempted']:need(type(v[k])is bool,'typed lifecycle '+k)
 for k in ['openResult','readResult','closeResult','openErrno','readErrno','closeErrno','returnedPrefixBytes','clockFailureMask','exceptionMask']:need(integer(v[k]),'typed '+k)
 for k in ['openErrno','readErrno','closeErrno']:need(0<=v[k]<=4095,'errno bound')
 need(0<=v['clockFailureMask']<=63 and 0<=v['exceptionMask']<=31,'failure mask bound')
 need(type(v['bracketsUs'])is list and len(v['bracketsUs'])==6 and all(integer(t)and t>=-1 for t in v['bracketsUs']),'clock brackets')
 b=base64.b64decode(v['rawAllocationBase64'],validate=True)
 need(len(b)==4096 and base64.b64encode(b).decode()==v['rawAllocationBase64']and hashlib.sha256(b).hexdigest()==v['rawAllocationSha256'],'full initialized allocation hash')
 n=v['readResult'];prefix=n if 0<=n<=4096 else 0
 need(v['returnedPrefixBytes']==prefix,'returned prefix count')
 need(v['returnedPrefixSha256']==(hashlib.sha256(b[:n]).hexdigest()if 0<=n<=4096 else None),'returned prefix hash')
 if v['readAttempted']:need(v['openAttempted']and 0<=v['openResult']<=2147483647 and v['closeAttempted'],'one acquired FD read and close attempt')
 if v['closeAttempted']:need(v['openAttempted']and 0<=v['openResult']<=2147483647,'close acquired FD')
 if not v['readAttempted']:need(v['readResult']==-1 and v['readErrno']==0 and b==bytes([165])*4096,'not-attempted read marker and initialized allocation')
 t=v['bracketsUs'];ordered=all(0<=x<=y for x,y in zip(t,t[1:]))
 derived=v['openAttempted']and v['openResult']>=0 and v['openErrno']==0 and v['readAttempted']and 0<=n<=4096 and v['readErrno']==0 and v['closeAttempted']and v['closeResult']==0 and v['closeErrno']==0 and v['clockFailureMask']==v['exceptionMask']==0 and ordered
 need(v['accepted']is derived,'acceptance recomputation')
 return v,{'schema':'fk-offline-interpretation-v1','accepted':derived,'returnedBytes':prefix,'receiptSha256':hashlib.sha256(raw).hexdigest(),'completeLogProven':False,'copyCompletionAttested':False,'externalRtpProducerProven':False,'rawBytesPrivate':True}
if __name__=='__main__':
 with pathlib.Path(sys.argv[1]).open('rb')as f:b=f.read(16385)
 print(json.dumps(parse(b)[1],sort_keys=True))
