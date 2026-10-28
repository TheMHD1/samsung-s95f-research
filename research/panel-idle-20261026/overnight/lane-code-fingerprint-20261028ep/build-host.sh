#!/bin/sh
set -eu
EP_TASK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$EP_TASK_DIR"
mkdir -p host-environment/sdk-home host-environment/tmp host-environment/nuget
chmod 700 host-environment host-environment/sdk-home host-environment/tmp host-environment/nuget
export DOTNET_CLI_HOME="$EP_TASK_DIR/host-environment/sdk-home"
export TMPDIR="$EP_TASK_DIR/host-environment/tmp"
export NUGET_PACKAGES="$EP_TASK_DIR/host-environment/nuget"
export DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 DOTNET_NOLOGO=1
EP_DOTNET=${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet
"$EP_DOTNET" build LaneCodeFingerprint.csproj -c Release --configfile NuGet.Config -p:NuGetAudit=false
"$EP_DOTNET" bin/Release/net6.0/LaneCodeFingerprint.dll --self-test
