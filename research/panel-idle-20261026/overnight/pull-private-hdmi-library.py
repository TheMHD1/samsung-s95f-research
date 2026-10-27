#!/usr/bin/env python3
"""Default-dry fixed 13-chunk copy of the discovered HDMI userspace library."""
from pathlib import Path
import hashlib
import importlib.util

HERE = Path(__file__).resolve().parent
SOURCE = HERE/'pull-serdes-modules.py'
if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != '62fa8107cb3a50b20949d59370fa5a4ed33d48c71153f11643e5b370f680ea11':
    raise ValueError('frozen bounded-copy utility changed')
spec = importlib.util.spec_from_file_location('fixed_hdmi_library_copy', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ALLOWLIST = {
    'hdmi-control': ('/usr/lib/libhdmi-control.so.0.1', 415124,
                     '067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410'),
}

if __name__ == '__main__':
    module.main()
