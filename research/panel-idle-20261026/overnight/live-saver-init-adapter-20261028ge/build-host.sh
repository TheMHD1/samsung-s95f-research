#!/bin/sh
set -eu
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1
python3 -B finalize.py --sources-only
python3 -B verify-source.py > source-validation.normal.json
python3 -B -O verify-source.py > source-validation.optimized.json
python3 -B test-host.py > host-validation.normal.json
python3 -B -O test-host.py > host-validation.optimized.json
cmp source-validation.normal.json source-validation.optimized.json
cmp host-validation.normal.json host-validation.optimized.json
python3 -B finalize.py
