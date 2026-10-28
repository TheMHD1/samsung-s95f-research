#!/usr/bin/env python3
"""Build portable IL and an x64 dummy library, then verify on this host only."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
DOTNET=Path('${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet')
OUT=ROOT/'bin/Release/net6.0'


def run(argv,expected=0):
    result=subprocess.run([str(x) for x in argv],cwd=ROOT,capture_output=True,text=True,timeout=45)
    if result.returncode!=expected:
        raise RuntimeError(f'host command failed: {argv[0]} exit={result.returncode}\n'+result.stdout+result.stderr)
    return result


def main():
    build=run([DOTNET,'build','-c','Release','--nologo'])
    (ROOT/'build.log').write_text(build.stdout+build.stderr)
    native=run(['cc','-std=c11','-Wall','-Wextra','-Werror','-Wpedantic','-fPIC','-shared','-Wl,--version-script=host_mock.map','host_mock.c','-o',OUT/'host_mock.so'])
    run(['cc','-std=c11','-Wall','-Wextra','-Werror','-Wpedantic','-fPIC','-shared','-Wl,--version-script=host_owner_mock.map','host_owner_mock.c','-o',OUT/'host_owner_mock.so'])
    test=run([DOTNET,OUT/'SwuMetadataAdapter.dll','--self-test'])
    (ROOT/'host-test.log').write_text(test.stdout+test.stderr)
    guard=run([DOTNET,OUT/'SwuMetadataAdapter.dll'],64)
    (ROOT/'host-guard.log').write_text(guard.stdout+guard.stderr)
    result={'host_only':True,'native_arm_cross_build':False,'portable_il_build':True,
            'target_libraries_loaded':False,'real_tee_calls':0,'mock_dynamic_exports':7,'canonical_preload_aborting_exports_resolved':8,'owner_negative_cases':7,'owner_alias_policy_cases':9,'aborting_exports_invoked':0,
            'default_x64_exit':guard.returncode,'host_test_exit':test.returncode,
            'assembly_sha256':hashlib.sha256((OUT/'SwuMetadataAdapter.dll').read_bytes()).hexdigest()}
    if '--deadline' in sys.argv[1:]:
        start=time.monotonic()
        deadline=run([DOTNET,OUT/'SwuMetadataAdapter.dll','--self-test-deadline'],-14)
        result['deadline']={'expected_signal':14,'exit':deadline.returncode,'elapsed_seconds':round(time.monotonic()-start,3),'stdout':deadline.stdout,'stderr':deadline.stderr,'pass':True}
        (ROOT/'deadline-test.json').write_text(json.dumps(result['deadline']|{'host_only':True,'assembly_sha256':result['assembly_sha256']},indent=2)+'\n')
    (ROOT/'host-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
