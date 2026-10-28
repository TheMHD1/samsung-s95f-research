#!/usr/bin/env python3
"""Replay one frozen author's zero-target suite with all temporary files in reviews/."""
import hashlib,json,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parent;P=R.parent
if len(sys.argv)!=2 or sys.argv[1]not in ['source','host']:raise ValueError('source or host suite required')
raw=(P/'source-inventory.json').read_bytes()
if hashlib.sha256(raw).hexdigest()!='f0098a4ccd58e1662a9f37e4a7f8d2f38fc1eea72eb4f6950c20c4b6e28f0f2c':raise ValueError('author freeze')
for row in json.loads(raw)['files']:
 data=(P/row['path']).read_bytes()
 if len(data)!=row['bytes']or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('author inventory '+row['path'])
original=tempfile.TemporaryDirectory
def review_temporary_directory(*args,**kwargs):
 kwargs['dir']=R/'tmp';return original(*args,**kwargs)
tempfile.TemporaryDirectory=review_temporary_directory
try:
 path=P/('verify-source.py'if sys.argv[1]=='source'else'test-host.py')
 exec(compile(path.read_bytes(),str(path),'exec'),{'__file__':str(path),'__name__':'ga_frozen_suite_replay'})
finally:tempfile.TemporaryDirectory=original
