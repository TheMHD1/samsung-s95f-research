#!/usr/bin/env python3
"""Execute frozen tests with only scratch destinations moved into owned reviews."""
import sys,types
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent.parent
name=sys.argv[1]
if name not in ['test-host.py','verify-source.py']:raise ValueError('fixed test only')
source=(P/name).read_text()
if name=='test-host.py':
 for old,new in [("P.joinpath('host-environment/tmp')", "P.joinpath('reviews/private')"),("dir=P/'host-environment/tmp'", "dir=P/'reviews/private'")]:
  if source.count(old)!=1:raise ValueError('exact scratch-only transformation')
  source=source.replace(old,new)
m=types.ModuleType('independent_author_test');m.__file__=str(P/name)
exec(compile(source,str(P/name),'exec'),m.__dict__)
