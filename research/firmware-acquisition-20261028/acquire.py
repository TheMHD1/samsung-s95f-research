#!/usr/bin/env python3
"""Exact official encrypted package acquisition; no target access or execution."""
from pathlib import Path
import datetime,hashlib,html,json,os,ssl,struct,time,urllib.request,urllib.parse,zipfile,zlib
P=Path(__file__).resolve().parent
OLD=Path('${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight')
META=json.loads((OLD/'samsung-official-firmware-archive-metadata.json').read_text())
URL=META['archive_url'];NAME='T-RSMFAKUC-0090_TB-RSWF4AKUC-0090.zip';SIZE=2439527748
CTX=ssl.create_default_context();START=time.monotonic();os.umask(0o077)
def require(ok,why):
 if not ok:raise ValueError(why)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name,obj):(P/name).write_text(json.dumps(obj,indent=2)+'\n')
class OfficialRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  parts=urllib.parse.urlsplit(newurl)
  require(parts.scheme=='https' and parts.hostname in {'org.downloadcenter.samsung.com','downloadcenter.samsung.com'},'redirect outside official HTTPS allowlist')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
OPENER=urllib.request.build_opener(OfficialRedirect(),urllib.request.HTTPSHandler(context=CTX))
def request(method):return OPENER.open(urllib.request.Request(URL,method=method,headers={'User-Agent':'Mozilla/5.0','Accept-Encoding':'identity','Cache-Control':'no-cache'}),timeout=30)
def response(r):return {'url':URL,'resolved_url':r.url,'status':r.status,'headers':dict(r.headers),'utc':now(),'tls_certificate_verification':True}
def sha_file(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def run():
 page=(P/'support-page.html').read_text();key='{"softwares"';at=page.find(key);require(at>=0,'support JSON absent')
 data,_=json.JSONDecoder().raw_decode(page[at:]);listed=[f for f in data['softwares'] if f['fileName']==NAME]
 require(len(listed)==1 and listed[0]['fileVersion']=='0090-1301.0' and listed[0]['downloadUrl']==URL,'official listing drift')
 save('official-listing.json',{'source_page':META['source_page'],'checked_utc':now(),'model':'QN77S95FAFXZC','listing':listed[0],'web_tool_reverified':True})
 with request('HEAD') as r:
  hd=response(r);save('head-response.json',hd)
  require(r.status==200 and int(r.headers['Content-Length'])==SIZE,'HEAD size/status drift')
  require(r.headers.get('ETag')==META['headers']['ETag'],'HEAD ETag drift')
 partial=P/(NAME+'.partial');require(not partial.exists() and not (P/NAME).exists(),'existing acquisition output')
 h=hashlib.sha256();count=0;last=0
 with request('GET') as r,partial.open('xb') as out:
  gd=response(r);save('get-response.json',gd)
  require(r.status==200 and int(r.headers['Content-Length'])==SIZE,'GET size/status drift')
  require(r.headers.get('ETag')==META['headers']['ETag'],'GET ETag drift')
  while True:
   require(time.monotonic()-START<1800,'overall download deadline')
   b=r.read(1024*1024)
   if not b:break
   count+=len(b);require(count<=SIZE,'excess download length');out.write(b);h.update(b)
   if count-last>=256*1024*1024:print(json.dumps({'stage':'download','bytes':count,'expected':SIZE,'elapsed_seconds':round(time.monotonic()-START,1)}),flush=True);last=count
  out.flush();os.fsync(out.fileno())
 require(count==SIZE and partial.stat().st_size==SIZE,'incomplete archive')
 digest=h.hexdigest();require(sha_file(partial)==digest,'post-write archive SHA256 mismatch')
 print(json.dumps({'stage':'length-and-sha-pass','bytes':count,'sha256':digest}),flush=True)
 expected=META['entries'];members=[];temporary=[]
 with zipfile.ZipFile(partial) as archive:
  entries=archive.infolist();require(len(entries)==len(expected) and len(set(x.filename for x in entries))==len(entries),'ZIP entry count/duplicates')
  for info,old in zip(entries,expected):
   require(info.filename==old['name'] and info.file_size==old['uncompressed_size'] and info.compress_size==old['compressed_size'] and info.CRC==int(old['crc32'],16) and info.compress_type==old['method'] and info.header_offset==old['local_header_offset'] and info.flag_bits==old['flags'],'ZIP directory drift')
   require(info.compress_type in (0,8) and not (info.flag_bits&1),'ZIP unsupported method/encryption')
   mh=hashlib.sha256();crc=0;n=0;prefix=bytearray();out=None
   if info.filename.endswith('/upgrade.msd'):
    target=P/(info.filename.split('/')[0]+'-upgrade.msd.partial');out=target.open('xb');temporary.append(target)
   try:
    with archive.open(info) as stream:
     while True:
      b=stream.read(4*1024*1024)
      if not b:break
      n+=len(b);require(n<=info.file_size,'ZIP decoded overrun');crc=zlib.crc32(b,crc);mh.update(b)
      if len(prefix)<65494:prefix.extend(b[:65494-len(prefix)])
      if out:out.write(b)
    if out:out.flush();os.fsync(out.fileno())
   finally:
    if out:out.close()
   require(n==info.file_size and crc==info.CRC,'ZIP decoded size/CRC mismatch')
   item={'name':info.filename,'flags':info.flag_bits,'method':info.compress_type,'compressed_size':info.compress_size,'uncompressed_size':n,'local_header_offset':info.header_offset,'crc32':f'{crc:08x}','sha256':mh.hexdigest(),'crc32_verified':True}
   if info.filename=='T-RSMFAKUC-0090/image/upgrade.msd':
    retained=(OLD/'samsung-official-T-RSMFAKUC-0090-msd-prefix.bin').read_bytes()
    require(bytes(prefix)==retained,'retained MSD prefix differs');item['retained_prefix_bytes_equal']=len(retained);item['retained_prefix_sha256']=hashlib.sha256(prefix).hexdigest()
   if info.filename.endswith('info.txt'):
    require(n<4096,'info size bound');(P/(info.filename.split('/')[0]+'-info.txt')).write_bytes(prefix)
   members.append(item);print(json.dumps({'stage':'zip-member-pass','name':info.filename,'bytes':n,'crc32':item['crc32']}),flush=True)
 # No final archive or MSD filename exists until all members pass CRC/size.
 os.replace(partial,P/NAME)
 for path in temporary:os.replace(path,path.with_suffix(''))
 save('acquisition-manifest.json',{'started_utc':hd['utc'],'completed_utc':now(),'model':'QN77S95FAFXZC','version':'0090-1301.0','source_page':META['source_page'],'original_url':URL,'resolved_url':gd['resolved_url'],'http_headers':gd['headers'],'expected_bytes':SIZE,'bytes':count,'sha256':digest,'post_write_sha256_verified':True,'tls_certificate_verification':True,'all_zip_members_crc32_verified':True,'members':members,'encrypted_payloads_only':True,'oem_signatures_verified':False,'tv_operations':0,'executed_downloaded_code':False,'archive_finalized_only_after_full_validation':True,'private_oem_binaries_not_for_publication':True})
 print(json.dumps({'stage':'complete','archive_sha256':digest,'elapsed_seconds':round(time.monotonic()-START,2)}),flush=True)
if __name__=='__main__':
 try:run()
 except Exception as e:
  save('acquisition-failure.json',{'utc':now(),'exception':type(e).__name__,'reason':str(e),'finalized':False,'tv_operations':0});raise
