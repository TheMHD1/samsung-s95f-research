#!/usr/bin/env python3
# Run exact frozen author test source, relocating its disposable directory into review ownership.
import runpy,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
original=tempfile.TemporaryDirectory

def owned(*args,**kwargs):
 kwargs['dir']=str(HERE/'private')
 return original(*args,**kwargs)

tempfile.TemporaryDirectory=owned
runpy.run_path(str(HERE.parent/'test-runner.py'),run_name='__main__')
