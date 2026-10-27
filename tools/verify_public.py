#!/usr/bin/env python3
"""Verify the public release offline; never execute retained device tooling."""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

PATTERNS = {
    'private-ipv4': re.compile(r'(?<![\w.])(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(?![\w.])'),
    'private-absolute-home': re.compile(r'(?<![A-Za-z0-9_])/home/(?!researcher\b)[^/\s"\']+'),
    'github-token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b'),
    'jwt': re.compile(r'\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\b'),
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'encoded-payload': re.compile(r'(?<![A-Za-z0-9+/])[A-Za-z0-9+/_-]{512,}={0,2}(?![A-Za-z0-9+/])'),
}

def verify(root: Path):
    manifest=json.loads((root/'manifests/source-dispositions.json').read_text())
    errors=[];seen=set();counts=Counter();syntax=[]
    for row in manifest['records']:
        counts[row['disposition']]+=1
        if 'public_path' not in row:
            if row.get('reason')=='private-access-state' and 'source_sha256' in row:errors.append({'kind':'credential-hash','source_id':row['source_id']})
            continue
        rel=row['public_path'];p=root/rel
        if rel in seen:errors.append({'kind':'path-collision','path':rel})
        seen.add(rel)
        if not p.is_file() or p.is_symlink():errors.append({'kind':'missing-or-symlink','path':rel});continue
        data=p.read_bytes()
        if hashlib.sha256(data).hexdigest()!=row['public_sha256']:errors.append({'kind':'hash-mismatch','path':rel})
        if len(data)!=row['public_bytes']:errors.append({'kind':'size-mismatch','path':rel})
        if p.stat().st_mode & 0o111:errors.append({'kind':'executable-archive-artifact','path':rel})
        text=data.decode('utf-8')
        for label,pattern in PATTERNS.items():
            match=pattern.search(text)
            if match:errors.append({'kind':label,'path':rel,'line':text.count('\n',0,match.start())+1})
        if p.suffix=='.json':
            try:json.loads(text)
            except ValueError:errors.append({'kind':'invalid-json','path':rel})
        if p.suffix=='.py':
            try:ast.parse(text,filename=rel)
            except SyntaxError as e:syntax.append({'path':rel,'line':e.lineno,'error':e.msg})
    for p in (root/'research').rglob('*'):
        if p.is_symlink():errors.append({'kind':'symlink','path':str(p.relative_to(root))})
        elif p.is_file() and str(p.relative_to(root)) not in seen:errors.append({'kind':'unmanifested','path':str(p.relative_to(root))})
    return {'schema':'s95f-public-verification-v1','scope':'Offline hash, privacy-pattern, file-type and syntax inspection; no target activity. Pattern scanning is supplemented by human review and is not a proof that arbitrary secrets cannot exist.','verified_public_files':len(seen),'dispositions':dict(counts),'errors':errors,'historical_python_syntax_findings':syntax}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--report',type=Path)
    args=ap.parse_args();result=verify(args.root.resolve())
    if args.report:args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(bool(result['errors']))
