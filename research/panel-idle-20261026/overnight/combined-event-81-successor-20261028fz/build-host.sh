#!/bin/sh
set -eu
ulimit -c 0
FZ_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$FZ_DIR"
mkdir -p host-environment/sdk-home host-environment/tmp host-environment/nuget
chmod 700 host-environment host-environment/sdk-home host-environment/tmp host-environment/nuget
export DOTNET_CLI_HOME="$FZ_DIR/host-environment/sdk-home" TMPDIR="$FZ_DIR/host-environment/tmp" NUGET_PACKAGES="$FZ_DIR/host-environment/nuget" DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 DOTNET_NOLOGO=1 PYTHONDONTWRITEBYTECODE=1
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet build CombinedEvent81Successor.csproj -c Release --configfile NuGet.Config -p:NuGetAudit=false
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/CombinedEvent81Successor.dll --self-test > native-tests.json
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/CombinedEvent81Successor.dll --fixture > fixture.json
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/CombinedEvent81Successor.dll --time-fixture > time-fixture.json
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/CombinedEvent81Successor.dll --partial-fixture > partial-fixture.json
python3 -B finalize.py
python3 -B verify-source.py > source-checks.normal.json
python3 -B -O verify-source.py > source-checks.optimized.json
python3 -B test-host.py > host-validation.normal.json
python3 -B -O test-host.py > host-validation.optimized.json
python3 -B test-key-exposure.py > key-exposure.normal.json
python3 -B -O test-key-exposure.py > key-exposure.optimized.json
python3 -B finalize.py
