#!/bin/sh
set -eu
ulimit -c 0
FM_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$FM_DIR"
mkdir -p host-environment/sdk-home host-environment/tmp host-environment/nuget
chmod 700 host-environment host-environment/sdk-home host-environment/tmp host-environment/nuget
export DOTNET_CLI_HOME="$FM_DIR/host-environment/sdk-home" TMPDIR="$FM_DIR/host-environment/tmp" NUGET_PACKAGES="$FM_DIR/host-environment/nuget" DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 DOTNET_NOLOGO=1
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet build LoggerGateReconciliation.csproj -c Release --configfile NuGet.Config -p:NuGetAudit=false
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/LoggerGateReconciliation.dll --self-test > native-tests.json
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/LoggerGateReconciliation.dll > dry.json
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/LoggerGateReconciliation.dll --fixture > fixture.json
python3 -B finalize.py
python3 -B parse-result.py fixture.json > parsed-fixture.json
python3 -B verify-host.py > host-validation.normal.json
python3 -O -B verify-host.py > host-validation.optimized.json
python3 -B finalize.py
