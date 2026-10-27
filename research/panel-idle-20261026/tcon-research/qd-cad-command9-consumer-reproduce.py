#!/usr/bin/env python3
"""Offline hash/landmark checker for qd-cad-command9-consumer.md.

This checker never opens a device and never executes target code.  It checks
the copied ELF bytes and selected AArch64 disassembly landmarks only; manual
control-flow review is still required.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "binaries"

MODULE_SHA256 = {
    "qdf_tcon.ko": "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63",
    "tztv_frc_tcon.ko": "aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd",
    "tztv_frc_tcon_api.ko": "3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6",
    "sdp_frc.ko": "05dea2eaad34a23def837fb86d2f7a4e99ef630066ad6fed18d0cf55ba37063d",
    "sdp_tcon.ko": "9b7c1cb8e2bb8d11e5465a41fa402e71bd8d15a5dabd6b3d76de98a7a42549ee",
    "rosem_frc.ko": "c646b45d8ab5028defca91b5f8188bf905b8d29f8927fae292be591c94cdbd34",
}

# All selected modules have .text at file offset 0x80.  readelf verification
# below prevents silently applying that fact to a different ELF layout.
FUNCTIONS = {
    "qdf_tcon.ko": {
        0x3F98: (492, "e8675eaf203e7ebafa4f7f2104447e260a8d9788d39a1f71150d0dafbdc88028"),
        0x9630: (980, "52d8be1c3a1963c4cdb7b182657600fb2c7809b360176def0b344e7d97c1e2d4"),
        0x12218: (2688, "6057aae74b1f8e4a4a3c9c248b4feeb7feaa3f587bd226624a34f8cc58973cd1"),
        0x13298: (720, "4618554a949d9cb72471e1eaf1e7ff16b2e906842ceb25a986e8343d4d1e1d47"),
    },
    "tztv_frc_tcon.ko": {
        0x2D78: (352, "d789b6d3e363fc4490bbefea796cde2dfae584daee61788bf36372a8237cb5fb"),
        0x3090: (216, "3fbed38cc476f58f8ba6a2d721d1e031d53a08872a42d1c0928fd409e76f1ad7"),
    },
    "sdp_frc.ko": {
        0x2258: (4656, "834fc29b621b5ad222de7181942859309fc3660020b7f63876c242eb9560f92e"),
        0x1C060: (76, "334ff21409898ed56a9a2db7a794046d5b9fc165ae818a12321daeb90eeddd52"),
        0x1C0E8: (104, "af7431c66247542b10aa07d6f76bba44783c9337dcc0a145ae050284bdeab389"),
    },
    "sdp_tcon.ko": {
        0x1160: (1300, "4b94bcaab937207f54ab0e47d4e273d7ba5243e1a2c4aeb47ca7a0ccd2b82c01"),
        0x1678: (752, "8b1a390d3d831437ee695ad6c86ae87f537530881c19e0d67e4abb3a775f46be"),
        0x79E0: (288, "bec410032d2440598bb8026d117c9828f2cde7eb291df0d9e537f27d72dc4870"),
        0xB350: (540, "b720dbf4f8754ed7c01e521b47cede3e70d6d90d31d244ce6b827fbd7a468efd"),
        0xCD80: (308, "adb3d71e163ce8725ec5cfb61ff15a2336994d6d8377cb80c888f73702253168"),
        0xDBF8: (612, "38236e4b9af0cc8db56db6b3e95dae737dcf565c9fb3c442a1e87fbb6a4f3cd4"),
    },
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True)


def disasm(name: str, start: int, stop: int) -> str:
    return run(
        "aarch64-linux-gnu-objdump",
        "-dr",
        "-j",
        ".text",
        f"--start-address={start:#x}",
        f"--stop-address={stop:#x}",
        str(BIN / name),
    )


def require(yes: bool, message: str) -> None:
    if not yes:
        raise AssertionError(message)


def main() -> None:
    blobs: dict[str, bytes] = {}
    for name, expected in MODULE_SHA256.items():
        data = (BIN / name).read_bytes()
        require(sha256(data) == expected, f"whole-file hash mismatch: {name}")
        blobs[name] = data

    for name, funcs in FUNCTIONS.items():
        sections = run("aarch64-linux-gnu-readelf", "-SW", str(BIN / name))
        m = re.search(r"\]\s+\.text\s+PROGBITS\s+0+\s+000080\s", sections)
        require(m is not None, f"unexpected .text layout: {name}")
        for address, (size, expected) in funcs.items():
            body = blobs[name][0x80 + address : 0x80 + address + size]
            require(len(body) == size, f"short function slice: {name}+{address:#x}")
            require(sha256(body) == expected, f"function hash mismatch: {name}+{address:#x}")

    qdf_se = disasm("qdf_tcon.ko", 0x3F98, 0x4184)
    require("mov\tw0, #0x9" in qdf_se, "SE helper no longer emits operation 9")
    require("tztv_frc_tcon_ext_cmd" in qdf_se, "SE helper callback relocation missing")

    qdf_cad = disasm("qdf_tcon.ko", 0x13298, 0x13568)
    require("bl\t12218 <m_tcon_flash_upgrade>" in qdf_cad, "CAD caller changed")
    qdf_direct = disasm("qdf_tcon.ko", 0x12218, 0x12C98)
    require("bl\t9630 <m_tcon_update_send_cmd>" in qdf_direct, "CAD update helper changed")
    qdf_nonse = disasm("qdf_tcon.ko", 0x9630, 0x9A04)
    require("tztv_tcon_ext_cmd" in qdf_nonse, "non-SE callback relocation missing")
    require("mov\tw0, #0x20" in qdf_nonse, "non-SE operation 32 landmark missing")

    bridge = disasm("tztv_frc_tcon.ko", 0x2D78, 0x2ED8)
    require("resolve_symbol" in bridge and "blr\tx3" in bridge, "FRC bridge changed")
    ordinary = disasm("tztv_frc_tcon.ko", 0x3090, 0x3168)
    require("resolve_symbol" in ordinary and "blr\tx3" in ordinary, "TCON bridge changed")
    require(b"sdp_display_ex_proc\x00" in blobs["tztv_frc_tcon.ko"], "SDP FRC endpoint name missing")
    require(b"tcon_ex_proc\x00" in blobs["tztv_frc_tcon.ko"], "ordinary TCON endpoint name missing")

    sf = disasm("sdp_frc.ko", 0x268C, 0x2710)
    require("mov\tx1, #0x200" in sf and "movk\tx1, #0x8036" in sf, "operation mask changed")
    require("bl\t1c060 <tcon_mediation_proc>" in sf, "operation dispatch changed")
    med = disasm("sdp_frc.ko", 0x1C060, 0x1C150)
    require(".bss+0x6c1c8" in med and "__symbol_get" in med, "mediation binding changed")
    require(b"sdp_tcon_ex_proc\x00" in blobs["sdp_frc.ko"], "SDP TCON endpoint name missing")

    st = disasm("sdp_tcon.ko", 0x1160, 0x13DC)
    require("cmp\tw1, #0x9" in st, "SDP operation-9 compare missing")
    require("bl\tdbf8 <tcon_update>" in st, "SDP update call missing")
    loader = disasm("sdp_tcon.ko", 0xCD80, 0xCEB4)
    for call in ("fio_fopen", "fio_fseek", "fio_fread", "fio_fclose"):
        require(call in loader, f"loader call missing: {call}")
    require("ldr\tx1, [x19, #8]" in loader, "pathname-pointer field changed")
    require("ldrh\tw2, [x19, #16]" in loader, "pathname-length field changed")

    pack = disasm("sdp_tcon.ko", 0xB350, 0xB56C)
    require("mov\tx2, #0x30000" in pack, "0x30000 payload copy changed")
    require("add\tx0, x19, #0x10" in pack, "payload destination offset changed")
    update = disasm("sdp_tcon.ko", 0xDBF8, 0xDE60)
    require("bl\tcd80 <sdp_tcon_load_update_image>" in update, "loader call missing")
    require("bl\t79e0 <__sdp_tcon_send_msgbox>" in update, "msgbox call missing")

    # Bounded literal census only.  It does not prove that no computed parser
    # can exist; it does prove that neither byte order appears verbatim here.
    for name, data in blobs.items():
        require(bytes.fromhex("5a5aa5a5") not in data, f"magic bytes newly present: {name}")
        require(bytes.fromhex("a5a55a5a") not in data, f"reversed magic newly present: {name}")

    print("PASS qd-cad-command9-consumer: hashes and selected landmarks match")


if __name__ == "__main__":
    main()
