#!/bin/sh
set -eu
ulimit -c 0
GG_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$GG_DIR"
mkdir -p host-environment/sdk-home host-environment/tmp host-environment/nuget
chmod 700 host-environment host-environment/sdk-home host-environment/tmp host-environment/nuget
export DOTNET_CLI_HOME="$GG_DIR/host-environment/sdk-home" TMPDIR="$GG_DIR/host-environment/tmp" NUGET_PACKAGES="$GG_DIR/host-environment/nuget" DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 DOTNET_NOLOGO=1 PYTHONDONTWRITEBYTECODE=1
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet build CombinedEvent200.csproj -c Release --configfile NuGet.Config -p:NuGetAudit=false
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/CombinedEvent200.dll --self-test > native-tests.json
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/CombinedEvent200.dll --fixture > fixture.json
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/CombinedEvent200.dll --branch-fixtures > branch-fixtures.json
python3 -B finalize.py --sources-only
python3 -B verify-source.py > source-validation.normal.json
python3 -B -O verify-source.py > source-validation.optimized.json
python3 -B test-host.py > host-validation.normal.json
python3 -B -O test-host.py > host-validation.optimized.json
python3 -B test-key-exposure.py > key-validation.normal.json
python3 -B -O test-key-exposure.py > key-validation.optimized.json
cmp source-validation.normal.json source-validation.optimized.json
cmp host-validation.normal.json host-validation.optimized.json
cmp key-validation.normal.json key-validation.optimized.json
python3 -B finalize.py
