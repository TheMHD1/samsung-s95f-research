#!/usr/bin/env python3
"""Offline host build/test only; no real plaintext, TV, root or network runner."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
DOTNET=Path('${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet')
PUBLIC=HERE.parent/'swu-public-key-20261028cc/itemsPublicRSAKey.txt'
PUBLIC_SHA='ebf12ab9d4ef069e1a6030b8c3b117894746637715270f7e3d37d3cd737f71a3'


def need(ok,why):
    if not ok:raise ValueError(why)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    public=PUBLIC.read_bytes();need(len(public)==426 and sha(public)==PUBLIC_SHA,'public anchor file')
    source=(HERE/'HeaderAuthentication.cs').read_text()
    for forbidden in ('System.IO','Console.','DllImport','Process.','System.Net','File.','Directory.','ITeec','TEEC_'):
        need(forbidden not in source,'pure library source boundary')
    command=[str(DOTNET),'build',str(HERE/'HostTests.csproj'),'-c','Release','--nologo','--configfile',str(HERE/'NuGet.Config')]
    build=subprocess.run(command,cwd=HERE,capture_output=True,text=True,timeout=45)
    (HERE/'build.log').write_text(build.stdout+build.stderr)
    need(build.returncode==0,'offline host build')
    run=subprocess.run([str(DOTNET),str(HERE/'bin/Release/net6.0/HostTests.dll'),str(HERE/'fixtures'),str(PUBLIC)],
                       cwd=HERE,capture_output=True,text=True,timeout=20)
    (HERE/'host-tests.log').write_text(run.stdout+run.stderr)
    need(run.returncode==0 and run.stderr=='','host fixture tests')
    result=json.loads(run.stdout)
    need(result['target_operations']==0 and result['actual_plaintext_used'] is False and
         result['full_schema_validated'] is False and result['metadata_published'] is False,'narrow test claims')
    result.update({'librarySourceSha256':sha((HERE/'HeaderAuthentication.cs').read_bytes()),
                   'libraryDllSha256':sha((HERE/'bin/Release/net6.0/HeaderAuthentication.dll').read_bytes()),
                   'fixtureManifestSha256':sha((HERE/'fixtures/manifest.json').read_bytes()),
                   'actualPublicPemSha256':PUBLIC_SHA,'pureSourceBoundaryChecked':True,
                   'portableIlBuild':True,'targetCryptoProviderQualified':False})
    (HERE/'host-verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
