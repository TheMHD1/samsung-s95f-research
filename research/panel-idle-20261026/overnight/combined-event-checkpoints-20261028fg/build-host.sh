#!/bin/sh
set -eu
ulimit -c 0
FG_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$FG_DIR"
mkdir -p host-environment/sdk-home host-environment/tmp host-environment/nuget
chmod 700 host-environment host-environment/sdk-home host-environment/tmp host-environment/nuget
export DOTNET_CLI_HOME="$FG_DIR/host-environment/sdk-home" TMPDIR="$FG_DIR/host-environment/tmp" NUGET_PACKAGES="$FG_DIR/host-environment/nuget" DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 DOTNET_NOLOGO=1
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet build CombinedEventCheckpoints.csproj -c Release --configfile NuGet.Config -p:NuGetAudit=false
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/CombinedEventCheckpoints.dll --self-test > native-tests.json
cat native-tests.json
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/CombinedEventCheckpoints.dll --fixture > fixture.json
python3 -B verify-source.py
python3 -B finalize.py
python3 -B test-host.py
python3 -O -B verify-source.py
python3 -O -B test-host.py
python3 -B test-key-exposure.py
python3 -O -B test-key-exposure.py
