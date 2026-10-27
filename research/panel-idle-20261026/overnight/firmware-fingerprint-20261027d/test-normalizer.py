#!/usr/bin/env python3
"""Offline compatibility checks, including the actual Samsung newline failure."""
import base64
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('adapter',HERE/'run-backup-with-normalizer.py')
adapter=importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)

def main():
    for data in (b'abc',bytes(range(256))*96):
        compact=base64.b64encode(data).decode()
        wrapped='\n'.join(compact[i:i+76] for i in range(0,len(compact),76))+'\n\n'
        adapter.need(adapter.canonicalize(wrapped)==compact+'\n','valid canonicalization')
    rejected=0
    for bad in ('YWJj\r\n','YR==\n','YWJj!\n','A\n','A'*34001):
        try:
            adapter.canonicalize(bad)
        except ValueError:
            rejected+=1
        else:
            raise ValueError('accepted invalid base64')
    record=json.loads((HERE/'boundary-probe/record.json').read_text())
    call=record['calls'][-1]
    adapter.need(adapter.is_fetch(call['command']),'actual file-fetch command shape')
    raw=call['response']['commands'][0]['stdout']
    adapter.need(raw.count('\n')==2 and adapter.canonicalize(raw).count('\n')==1,'actual Samsung framing correction')
    report=dict(valid_wrapped_cases=2,invalid_cases_rejected=rejected,actual_failed_fetch_reproduced=True,target_operations=0)
    (HERE/'normalizer-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':
    main()
