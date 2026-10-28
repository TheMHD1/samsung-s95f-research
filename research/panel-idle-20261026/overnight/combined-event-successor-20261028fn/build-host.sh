#!/bin/sh
set -eu
ulimit -c 0
FN_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$FN_DIR"
mkdir -p host-environment/sdk-home host-environment/tmp host-environment/nuget
chmod 700 host-environment host-environment/sdk-home host-environment/tmp host-environment/nuget
export DOTNET_CLI_HOME="$FN_DIR/host-environment/sdk-home" TMPDIR="$FN_DIR/host-environment/tmp" NUGET_PACKAGES="$FN_DIR/host-environment/nuget" DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 DOTNET_NOLOGO=1
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet build CombinedEventSuccessor.csproj -c Release --configfile NuGet.Config -p:NuGetAudit=false
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/CombinedEventSuccessor.dll --self-test > native-tests.json
cat native-tests.json
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/CombinedEventSuccessor.dll --fixture > fixture.json
python3 -B finalize.py
python3 -B verify-source.py > source-checks.normal.json
python3 -O -B verify-source.py > source-checks.optimized.json
python3 -B qualify-context.py > context-qualification.normal.json
python3 -O -B qualify-context.py > context-qualification.optimized.json
python3 -B qualify-scan.py > scan-qualification.normal.json
python3 -O -B qualify-scan.py > scan-qualification.optimized.json
python3 -B finalize.py
python3 -B test-host.py > host-validation.normal.json
python3 -O -B test-host.py > host-validation.optimized.json
python3 -B test-key-exposure.py > key-exposure-tests.normal.json
python3 -O -B test-key-exposure.py > key-exposure-tests.optimized.json
python3 -B finalize.py
