#!/usr/bin/env python3
"""Default-dry fixed copies of the two identified HDMI implementation libraries."""
from pathlib import Path
import hashlib
import importlib.util

HERE = Path(__file__).resolve().parent
SOURCE = HERE/'pull-serdes-modules.py'
if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != '62fa8107cb3a50b20949d59370fa5a4ed33d48c71153f11643e5b370f680ea11':
    raise ValueError('frozen bounded-copy utility changed')
spec = importlib.util.spec_from_file_location('fixed_hdmi_backends_copy', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ALLOWLIST = {
    'hdmi-input-impl': ('/prd/usr/lib/libhdmi-input-control-impl-sec.so.0.1', 29650,
                        '5f822a6f297e1d24a65ad8dd4363a1dcf43b7d15f405fa7799ddf20f01410126'),
    'hdmi-control-impl': ('/prd/usr/lib/libhdmi-control-impl-sec.so.0.1', 75882,
                          '5eaef7e92eac9468bf41073ccece56a64a70339c3056c3ca2b62391171f4d2a1'),
}

if __name__ == '__main__':
    module.main()
