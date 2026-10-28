#!/bin/sh
set -eu
ulimit -c 0
FP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$FP_DIR"
mkdir -p host-environment/tmp
chmod 700 host-environment host-environment/tmp
export TMPDIR="$FP_DIR/host-environment/tmp" PYTHONDONTWRITEBYTECODE=1
python3 -B finalize.py
python3 -B verify-source.py > source-checks.normal.json
python3 -O -B verify-source.py > source-checks.optimized.json
python3 -B test-host.py > host-validation.normal.json
python3 -O -B test-host.py > host-validation.optimized.json
python3 -B finalize.py
