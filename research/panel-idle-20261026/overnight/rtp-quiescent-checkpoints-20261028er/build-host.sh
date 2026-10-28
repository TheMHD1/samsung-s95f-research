#!/bin/sh
# Host-only offline build and mock verification. Never loads root/TV transport.
set -eu
ER_TASK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$ER_TASK_DIR"
mkdir -p host-environment/sdk-home host-environment/tmp host-environment/nuget
chmod 700 host-environment host-environment/sdk-home host-environment/tmp host-environment/nuget
export DOTNET_CLI_HOME="$ER_TASK_DIR/host-environment/sdk-home"
export TMPDIR="$ER_TASK_DIR/host-environment/tmp"
export NUGET_PACKAGES="$ER_TASK_DIR/host-environment/nuget"
export DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 DOTNET_NOLOGO=1
ER_DOTNET=${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet
"$ER_DOTNET" build SynchronizedOnset.csproj -c Release --configfile NuGet.Config -p:NuGetAudit=false
python3 -B verify_source.py
"$ER_DOTNET" bin/Release/net6.0/QuiescentCheckpoints.dll --self-test
"$ER_DOTNET" bin/Release/net6.0/QuiescentCheckpoints.dll --key-self-test
"$ER_DOTNET" bin/Release/net6.0/QuiescentCheckpoints.dll --checkpoint-self-test
python3 -B finalize_host.py
python3 -B test-parse-result.py
python3 -O -B test-parse-result.py
python3 -B test-runner.py
python3 -O -B test-runner.py
python3 -O -B verify_source.py

python3 -B test-timing.py
python3 -O -B test-timing.py
python3 -B test-readiness.py
python3 -O -B test-readiness.py

python3 -B test-quiescent.py
python3 -O -B test-quiescent.py
