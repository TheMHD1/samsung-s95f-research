#!/usr/bin/env python3
"""Default-dry, fixed 19-chunk passive copy of discovered sdp_ocl_jp.ko only."""
from pathlib import Path
import hashlib
import importlib.util

HERE = Path(__file__).resolve().parent
SOURCE = HERE/'pull-serdes-modules.py'
if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != '62fa8107cb3a50b20949d59370fa5a4ed33d48c71153f11643e5b370f680ea11':
    raise ValueError('frozen copy utility changed')
spec = importlib.util.spec_from_file_location('frozen_serdes_module_copy', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ALLOWLIST = {
    'ack': ('/lib/modules/5.4.261/kernel/soc/sdp_ocl_jp.ko', 594110,
            'e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c'),
}

if __name__ == '__main__':
    module.main()
