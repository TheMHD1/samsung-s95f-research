#!/usr/bin/env python3
"""Single fixed ordinary-file copy using the frozen research copier."""
import hashlib
import importlib.util
from pathlib import Path

ROOT = Path('${S95F_EVIDENCE_ROOT}')
SOURCE = ROOT / 'research-20261027-external/tools/acquire-swu-files.py'
# The parent is checked against the frozen research checkpoint before import.
import json
CHECKPOINT = SOURCE.parents[1] / 'phase-checkpoint.json'
expected = next(e['sha256'] for e in json.loads(CHECKPOINT.read_text())['files']
                if e['path'] == 'tools/acquire-swu-files.py')
if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != expected:
    raise RuntimeError('Frozen copier changed')
spec = importlib.util.spec_from_file_location('frozen_file_copier', SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.execute(Path(__file__).resolve().parent / 'vconf-copy', [
    ('/usr/lib/libvconf.so.0.3.1', 57272,
     '007a02e106ee38d0319084c458f048c556dcf618112cc1114e3e47cb8d226619')])
