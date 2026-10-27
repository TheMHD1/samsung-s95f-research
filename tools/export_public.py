#!/usr/bin/env python3
"""Offline public export. Reads an explicitly supplied evidence root; never contacts a TV.

This is a reproducible release transform, not a credential scanner for arbitrary data.
Every input gets a disposition and SHA-256; exported bytes get a separate hash.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import stat

VERSION = '2026-10-27.6'
BUILD_PARTS = {'.git', '__pycache__', '.pytest_cache', 'node_modules', 'venv', 'bin', 'obj', 'dotnet10', 'sdk', 'framework', 'installer-data', 'installer-beta', 'installer-source', 'tizentube-source', 'untethered-source'}
BINARY_EXTS = {'.dll','.so','.ko','.exe','.pdb','.bin','.img','.elf','.range','.wgt','.zip','.tgz','.tar','.gz','.xz','.zst','.nupkg','.deb','.pdf','.png','.jpg','.jpeg','.rgba','.pyc','.dat','.db','.sqlite','.woff','.ttf','.a','.o','.pem','.p12','.pfx','.crt','.key'}
TEXT_EXTS = {'.md','.py','.sh','.cs','.csproj','.c','.h','.cjs','.js','.json','.jsonl','.txt','.disasm','.summary','.stdout','.stderr','.log','.trace','.dts','.dtsi','.xml','.yml','.yaml','.toml','.lock','.config','.intent','.svg','.patch','.diff','.csv','.tsv','.service','.socket','.rules','.conf','.props','.targets','.sln','.il'}
SOURCE_EXTS = {'.py','.sh','.cs','.csproj','.c','.h','.cjs','.js','.toml','.patch','.diff'}
MEDIA_TITLES = []  # Private labels are supplied out of tree at export time.
SECRET_KEY = re.compile(r'(?i)^(?:.*(?:password|passwd|credential|cookie|access.?token|auth.?token|client.?secret|session.?id|serial.?number|duid|mac.?address)|boot_?id|expected_?boot|token|secret|ssid|bssid)$')
PRIVATE_IPV4 = re.compile(r'(?<![\w.])(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(?![\w.])')
UUID = re.compile(r'(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b')
MAC = re.compile(r'(?i)(?<![\w:])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![\w:])')
LONG_ENCODED = re.compile(r'(?<![A-Za-z0-9+/=_-])(?:[A-Za-z0-9+/_-]{320,}={0,2}|[0-9a-fA-F]{512,})(?![A-Za-z0-9+/=_-])')
NAME_REPLACEMENTS = []  # Private filename aliases are supplied out of tree.

def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)+'\n')
def public_name(value: str) -> str:
    for old,new in NAME_REPLACEMENTS:
        value=re.sub(r'(?<![A-Za-z])'+re.escape(old)+r'(?![A-Za-z])',lambda match: new,value,flags=re.IGNORECASE)
    return value

def redactor(root: Path):
    secrets = []
    token = root/'private'/'s95f.token'
    if token.is_file():
        val=token.read_text().strip()
        if val: secrets.append(val)
    root_s=str(root)
    home=str(root.parent.parent.parent)
    def redact(text: str) -> str:
        text=text.replace(root_s,'${S95F_EVIDENCE_ROOT}')
        # Absolute local user paths carry no scientific identity.
        text=re.sub(r'(?<![A-Za-z0-9_])/home/[^/\s"\'<>`]+', '/home/researcher', text)
        text=public_name(text)
        for i,title in enumerate(MEDIA_TITLES): text=re.sub(re.escape(title),f'PROGRAM_{i+1:02}',text,flags=re.IGNORECASE)
        text=re.sub(r'(?i)\bS\d{2}E\d{2}(?:[–-]\d{2})?\b','EPISODE_REDACTED',text)
        text=re.sub(r'(?i)\b(?:Pilot|Americans|Conjuring)\b','PROGRAM_LABEL',text)
        text=PRIVATE_IPV4.sub(lambda m: '198.51.100.20' if m.group().endswith('.201') else '198.51.100.10', text)
        text=UUID.sub('00000000-0000-4000-8000-000000000000',text)
        text=MAC.sub('00:00:00:00:00:00',text)
        for value in secrets:
            text=text.replace(value,'REDACTED_AUTH_TOKEN')
        text=re.sub(r'(?i)([?&](?:token|auth|session|key)=)[^&\s"\'<>]+',r'\1REDACTED',text)
        text=re.sub(r'(?im)(authorization:\s*(?:bearer|basic)\s+)\S+',r'\1REDACTED',text)
        text=LONG_ENCODED.sub(lambda m: m.group() if re.fullmatch(r'[0-9a-fA-F]{1,511}',m.group()) else '[encoded-payload-omitted]',text)
        return text
    return redact

def disposition(rel: Path, data: bytes, upstream_roots: list[Path]):
    parts=rel.parts; low=rel.as_posix().lower(); suffix=rel.suffix.lower()
    if any(x in BUILD_PARTS for x in parts): return 'omit','dependency-build-cache'
    if rel.name.startswith('upstream-linux-') and suffix in {'.c','.h'}:return 'omit','upstream-source-referenced-not-vendored'
    if rel.name=='reserve-addresses.cjs': return 'omit','private-network-administration'
    if ('binaries' in parts and suffix in {'.xml','.txt','.json'}) or low.endswith('-tree.json'):return 'omit','mechanical-vendor-resource-or-discovery-index'
    if ('history-comparison' in low or 'two-week-controls' in low) and suffix=='.json':return 'omit','private-media-history'
    if parts[0] in {'private','devtools'} or 'root-access/persistent/' in low: return 'omit','private-access-state'
    if any(rel==x or x in rel.parents for x in upstream_roots): return 'omit','upstream-source-referenced-not-vendored'
    if any(x in low for x in ['repository-metadata.json','commit.json','topic.html','owner-photo','repair-board','repair-oc-board','repair-guide-board','duid-read','bell-reservations','applications.before','home-content.before','preferences.json','preferences.summary','after-home.json','after-home.summary','pull-csfs2.json','pull-csfs2.summary']): return 'omit','private-or-discovery-record'
    if rel.name in {'core','control.sock','daemon.lock'} or suffix in BINARY_EXTS or '.so.' in rel.name or data.startswith((b'\x7fELF',b'MZ',b'\x1f\x8b',b'PK\x03\x04')): return 'omit','binary-firmware-media-or-build-product'
    if '.full.disasm' in low or rel.name in {'sdp_drm.disasm','sdp_frc.disasm','sdp_tcon.disasm','rosem_frc.disasm'} or ('.il.txt' in low and len(data)>200_000): return 'omit','whole-library-mechanical-disassembly'
    if len(data)>8_000_000: return 'omit','bulk-acquisition-not-authored-analysis'
    if b'\0' in data: return 'omit','non-text-acquisition'
    if suffix not in TEXT_EXTS and rel.name not in {'Makefile','LICENSE','NOTICE','NOTICE.md','.gitignore','hosts.block','.python-version'}: return 'omit','unsupported-acquisition-or-runtime-format'
    try: text=data.decode('utf-8')
    except UnicodeDecodeError: return 'omit','non-utf8-acquisition'
    if suffix=='.json':
        try: obj=json.loads(text)
        except ValueError:return 'omit','invalid-json-acquisition'
        if isinstance(obj,dict) and any(x in obj for x in ['calls','commands','transport_stdout','transport_stderr','authenticated','root_persistence']):return 'extract','raw-transport-envelope'
    if suffix in {'.stdout','.txt','.trace','.summary','.log'} and any(x in text[:5000] for x in ['"authenticated":','"root_persistence":','"transport_stdout":','"calls":']): return 'omit','raw-transport-envelope'
    return 'export','authored-source-report-or-derived-evidence'

def scrub_json(obj, redact):
    if isinstance(obj,dict):
        result={}
        for k,v in obj.items():
            if SECRET_KEY.match(k) or k.lower() in {'userid','user_id','accountid','account_id','deviceid','device_id','title','series','seriesname','episode','season','lastplayeddate','last_played','last_played_utc','item_id','itemid','sessionid','session_id'}:result[redact(k)]='[private-identity-or-secret-omitted]'
            elif k in {'transport_stdout','transport_stderr'}:continue
            elif k in {'base64','data_base64','raw_base64','raw_b64','payload_base64','bytes_base64'}:result[k]='[encoded-payload-omitted]'
            else:result[redact(k)]=scrub_json(v,redact)
        return result
    if isinstance(obj,list):return [scrub_json(v,redact) for v in obj]
    if isinstance(obj,str):return redact(obj)
    return obj

def extract_observations(obj, redact):
    # Preserve scientific commands/results from the envelope, dropping transport,
    # host/session/authentication state, payload staging, and encoded byte copies.
    records=[]
    def visit(value):
        if isinstance(value,dict):
            if isinstance(value.get('stdout'),str) and isinstance(value.get('command'),str):
                command=value['command']; output=value['stdout']
                if not any(x in command for x in ['base64','b64decode','STAGED_CHUNK','PRIVATE_STAGE_CREATED','cat /proc/net','/csfs/','/dtv/','/home/owner','jellyfin','Jellyfin','X-Emby','sqlite3','/etc/passwd','/etc/shadow','ifconfig','ip addr']):
                    records.append({'command':redact(command),'exit_code':value.get('exit_code'),'timed_out':value.get('timed_out'),'stdout':redact(output),'stderr':redact(str(value.get('stderr','')))})
            for k,v in value.items():
                if k not in {'transport_stdout','transport_stderr','command','stdout','stderr'}:visit(v)
        elif isinstance(value,list):
            for v in value:visit(v)
    visit(obj)
    unique=[]; seen=set()
    for r in records:
        key=json.dumps(r,sort_keys=True)
        if key not in seen:unique.append(r);seen.add(key)
    return {'schema':'public-scientific-observations-v1','notice':'Derived extraction; authentication, transport envelopes and payload staging omitted. Original hash is in the disposition manifest. Device output is an observation, not proof of emitted light.','observations':unique}

def export(root: Path, dest: Path):
    root=root.resolve();dest=dest.resolve()
    if root==dest or root in dest.parents:raise ValueError('destination must be outside evidence root')
    out=dest/'research'
    if out.exists():shutil.rmtree(out)
    out.mkdir(parents=True)
    # Copied upstream checkouts are referenced. The modified local Unlicense
    # root-access source tree is retained WITH its original license and delta.
    upstream=[]
    for git in root.rglob('.git'):
        if git.parent.relative_to(root).as_posix()!='root-access/source':upstream.append(git.parent.relative_to(root))
    external=root/'research-20261027-external/sources'
    for f in external.rglob('*'):
        if f.is_dir() and ('--' in f.name or f.name in {'linux-5.4.261','tizen-docs','quiet-tizen','ovos-skill-my-samsungctl','samsungctl','TizenAmbilight','msddecrypt','firmware-mod-kit','vdfs4','vdfs-unpack','CMSIS_6','cmsis6','vdfs_unpack','firmware_mod_kit','tizenwled','q60t'}):upstream.append(f.relative_to(root))
    redact=redactor(root); rows=[]; totals=Counter(); topics=Counter(); changed=0
    files=sorted(f for f in root.rglob('*') if f.is_file() or f.is_symlink())
    for f in files:
        rel=f.relative_to(root); source_id=sha(rel.as_posix().encode())
        if f.is_symlink():
            rows.append({'source_id':source_id,'disposition':'omit','reason':'symlink-reference-not-dereferenced','bytes':0});totals['omit_files']+=1;totals['symlink_files']+=1;continue
        try:data=f.read_bytes()
        except (OSError,ValueError):
            rows.append({'source_id':source_id,'disposition':'omit','reason':'unreadable-runtime-object','bytes':0});continue
        action,reason=disposition(rel,data,upstream)
        row={'source_id':source_id,'bytes':len(data),'disposition':action,'reason':reason}
        if reason not in {'private-access-state','private-network-administration'}:row['source_sha256']=sha(data)
        else:row['hash_withheld']='credential or private access-state hash is not published'
        totals[action+'_files']+=1;totals[action+'_source_bytes']+=len(data)
        # Name only scientific/public records; withheld records use opaque IDs
        # so the manifest does not itself reveal media or private filenames.
        if action!='omit':
            name=public_name(rel.as_posix()); target=out/name
            text=data.decode('utf-8')
            if action=='extract':
                obj=extract_observations(json.loads(text),redact)
                if not obj['observations']:
                    row['disposition']='omit';row['reason']='transport-envelope-no-public-observations'
                    totals['extract_files']-=1;totals['omit_files']+=1
                    totals['extract_source_bytes']-=len(data);totals['omit_source_bytes']+=len(data)
                    rows.append(row);continue
                text=json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n'
            elif rel.suffix.lower()=='.json':text=json.dumps(scrub_json(json.loads(text),redact),indent=2,sort_keys=True,ensure_ascii=False)+'\n'
            else:text=redact(text)
            if 'vlog' in rel.name.lower() and rel.suffix in {'.txt','.log','.stdout'}:
                lines=text.splitlines(); selected=[line for line in lines if re.search(r'(?i)DRM|FRC|TCON|HDMI|QD_|qd_tcon|RT_PROTECT|i2c|usb|ERRDET|ocif|DPMS|AVMUTE|PrePD',line)]
                text='# Public scientific log extraction: unrelated application/account/network rows omitted.\n'+'\n'.join(selected)+'\n'
            if 'history-comparison' in name or 'two-week-controls' in name:
                text=re.sub(r'2026-\d{2}-\d{2}(?:[ T][0-9:–.]+(?: UTC|Z)?)?','[private-viewing-time]',text)
            encoded=text.encode();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(encoded)
            # No historic payload is made executable by the export.
            target.chmod(0o644)
            row.update(public_path='research/'+name,public_sha256=sha(encoded),public_bytes=len(encoded),redacted=(encoded!=data))
            topics[rel.parts[0]]+=1;changed+=encoded!=data;totals['public_bytes']+=len(encoded)
        rows.append(row)
    totals['regular_input_files']=len(rows)-totals['symlink_files']
    totals['total_input_entries']=len(rows)
    manifest={'schema':'s95f-public-dispositions-v1','exporter_version':VERSION,'scope':'All regular files and symlinks discovered under the retained Samsung research root; original private paths and withheld filenames are intentionally absent.','totals':dict(totals),'exported_by_original_workstream':dict(topics),'changed_exports':changed,'records':rows}
    dump(dest/'manifests/source-dispositions.json',manifest)
    dump(dest/'manifests/omissions.json',{'schema':'s95f-omissions-v1','counts_by_reason':dict(Counter(r['reason'] for r in rows if r['disposition']=='omit')),'records':[r for r in rows if r['disposition']=='omit']})
    dump(dest/'manifests/export-summary.json',{k:v for k,v in manifest.items() if k!='records'})
    print(json.dumps(manifest['totals'],indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--destination',type=Path,required=True)
    parser.add_argument('--private-redactions',type=Path,help='Optional private label/filename-alias JSON; never copied into the release')
    args=parser.parse_args()
    if args.private_redactions:
        config=json.loads(args.private_redactions.read_text());MEDIA_TITLES=config.get('labels',[]);NAME_REPLACEMENTS=config.get('names',[])
    export(args.source,args.destination)
