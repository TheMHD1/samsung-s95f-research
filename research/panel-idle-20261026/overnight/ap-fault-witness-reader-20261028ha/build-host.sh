#!/bin/sh
set -eu
HA_TASK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$HA_TASK_DIR"
mkdir -p host-environment/sdk-home host-environment/tmp host-environment/nuget
chmod 700 host-environment host-environment/sdk-home host-environment/tmp host-environment/nuget
export DOTNET_CLI_HOME="$HA_TASK_DIR/host-environment/sdk-home"
export TMPDIR="$HA_TASK_DIR/host-environment/tmp"
export NUGET_PACKAGES="$HA_TASK_DIR/host-environment/nuget"
export DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 DOTNET_NOLOGO=1
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet build RecordCapture.csproj -c Release --configfile NuGet.Config -p:NuGetAudit=false
