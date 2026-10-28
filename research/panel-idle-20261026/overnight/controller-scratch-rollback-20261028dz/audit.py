#!/usr/bin/env python3
"""Read-only selected-package audit; no device, subprocess or network access."""
from pathlib import Path
import hashlib
import importlib.util
import json
import struct
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
ASSET = ROOT / 'overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'
EXPECTED = 'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0'
COUNT = 0


def need(ok, message):
    global COUNT
    COUNT += 1
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def growth(frontier, request, sp):
    """Image0 VA1afa success path, for source-qualified aligned arguments.

    This models the pool extension bounds, not malloc success or free memory.
    """
    if any(type(v) is not int for v in (frontier, request, sp)):
        raise ValueError('integer arguments required')
    if not (0x20018000 <= frontier < 0x20020000 and frontier % 8 == 0
            and 0 < request <= 0x10000 and request % 8 == 0
            and 0x20001000 <= sp <= 0x20020000 and sp % 8 == 0):
        raise ValueError('outside modeled aligned source domain')
    required_end = frontier + request
    ceiling = sp - 0x1000
    if required_end > ceiling:
        return None
    end = min(required_end + 0x1000,
              required_end + (ceiling - required_end) // 2)
    return (end + 7) & ~7


def build():
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
    data = ASSET.read_bytes()
    need(len(data) == 0x500000 and sha(data) == EXPECTED, 'package identity')
    provenance = json.loads((HERE / 'input-provenance.json').read_text())
    for item in provenance['inputs']:
        path = ROOT / item['path']
        need(not Path(item['path']).is_absolute() and '..' not in Path(item['path']).parts,
             'bounded input path')
        raw = path.read_bytes()
        need(len(raw) == item['bytes'] and sha(raw) == item['sha256'],
             'source input identity: ' + item['path'])
    decoder_path = ROOT / 'tcon-research/qd-rt-window-reset-output-reproduce.py'
    decoder_hash = 'fa6e59c24b5a2d91c917c908b4c60b078add9a8ca6815c24ec3e6d55cfe18d02'
    need(sha(decoder_path.read_bytes()) == decoder_hash, 'decoder source identity')
    spec = importlib.util.spec_from_file_location('pinned_scatter_decoder', decoder_path)
    decoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)
    cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)

    def word(image, va):
        return struct.unpack_from('<I', data, va + (0x200 if image == 0 else 0x40200))[0]

    snippets = []
    text = []
    for image, va, length, label in [
        (0, 0x284, 0x50, 'image0 runtime and explicit heap inputs'),
        (0, 0xc6c, 0xb0, 'image0 allocator globals and initialization'),
        (0, 0x378, 0xac, 'image0 allocation and free-list insertion/coalescing'),
        (0, 0x1ae4, 0x50, 'image0 SP-limited heap extension'),
        (0, 0x2f13c, 0x4c, 'image0 concrete 24-byte allocation caller'),
        (0, 0x344, 0x24, 'image0 reset entry and literals'),
        (0, 0x26758, 0x14, 'image0 first reset callee CPACR'),
        (1, 0x368, 0x24, 'image1 reset entry and literals'),
        (1, 0xdc00, 0x14, 'image1 first reset callee CPACR'),
        (1, 0x284, 0x3c, 'image1 runtime and stack initialization'),
        (1, 0x904, 0x10, 'image1 runtime-state getters'),
        (1, 0x1c268, 0x70, 'image1 startup callees string selection and FPSCR'),
        (1, 0x140, 0xb4, 'image1 scatter dispatcher and handlers'),
        (1, 0xbd58, 0x10, 'image1 unpacker stack frame'),
        (0, 0x2c598, 0x5c, 'AIRCR read is priority comparison, not reset'),
        (1, 0x96a, 8, 'raw 2001e000 word is instructions, not stack-limit literal'),
    ]:
        offset = va + (0x200 if image == 0 else 0x40200)
        raw = data[offset:offset + length]
        snippets.append(dict(image=image, va=hex(va), fileOffset=hex(offset),
                             bytes=length, sha256=sha(raw), label=label))
        text.append(f'IMAGE {image} VA {va:06x} file {offset:06x} bytes {length}: {label}')
        for ins in cs.disasm(raw, va):
            text.append(f'{ins.address:06x} {ins.mnemonic:10} {ins.op_str}')
        text.append('')

    maps = []
    for image, count in [(0, 12), (1, 9)]:
        bias = 0x200 if image == 0 else 0x40200
        start, end = word(image, 0x174) + 0x174, word(image, 0x178) + 0x174
        need(end - start == count * 16, 'scatter table length')
        rows = []
        for i in range(count):
            source, dest, size, handler = struct.unpack_from('<4I', data, bias + start + 16 * i)
            need(handler in (0x17c, 0x1d8) and size > 0, 'known scatter handler')
            if handler == 0x17c:
                out, source_end = decoder.unpack(data, bias + source, size)
                need(source_end <= len(data), 'source bounds')
                consumed = source_end - (bias + source)
            else:
                out, consumed = bytes(size), 0
            need(len(out) == size, 'exact scatter output length')
            need(not (dest < (0x40000 if image == 0 else 0x20000)), 'no low-code scatter destination')
            rows.append(dict(index=i, sourceVa=hex(source), destination=hex(dest),
                             endExclusive=hex(dest + size), bytes=size, handler=hex(handler),
                             sourceBytesConsumed=consumed, outputSha256=sha(out)))
        maps.append(dict(image=image, addressDomain=f'image{image}-CPU',
                         tableVa=hex(start), tableFileOffset=hex(bias+start),
                         tableSha256=sha(data[bias+start:bias+end]), rows=rows))

    need(word(0, 0x2b0) == 0x20018000, 'initial heap base')
    need(word(0, 0x2b4) == 0x20019000, 'initial heap end')
    need(word(0, 0x360) == 0x26759 and word(0, 0x364) == 0x141,
         'image0 reset callee and scatter')
    need(word(1, 0x384) == 0xdc01 and word(1, 0x388) == 0x141,
         'image1 reset callee and scatter')
    need(word(0, 0x2cc) == word(1, 0x2bc) == 0x20020000, 'initial stack tops')
    need(word(0, 0xc70) == 0x2001732c, 'image0 free-list global')
    need(word(0, 0x1b30) == 0x20000f48, 'image0 heap frontier global')
    need(word(1, 0x908) == 0x2000e15c, 'image1 runtime state')
    need(word(1, 0x910) == 0x2000e13c, 'image1 auxiliary runtime state')
    need(word(1, 0x96c) == 0x2001e000, 'negative literal example')
    need(word(0, 0x2c5f0) == 0xe000ed0c, 'AIRCR read literal')
    need(0x20000f4c + 0x16438 == 0x20017384, 'image0 BSS end')
    need(0x200004f8 + 0xdca4 == 0x2000e19c, 'image1 BSS end')
    need(0x20018000 - 0x20017384 == 3196 < 5952, 'image0 narrow unclassified gap too small')
    need(0x20010000 - 0x2000e19c == 7780 > 5952, 'image1 gap fits data numerically only')
    need(92 * 64 + 64 == 5952, 'DS data footprint')
    need(52 + 0xf1c == 3920, 'unpacker own stack footprint')
    need(4096 < 5952, 'initial image0 heap smaller than data pool')
    for sp in range(0x20019000, 0x20020001, 0x100):
        for request in (8, 16, 24, 4096, 5952, 5960, 8192, 65536):
            end = growth(0x20019000, request, sp)
            need(end is None or (end % 8 == 0 and
                 0x20019000 + request <= end <= sp - 0x1000), 'growth ceiling')
    need(growth(0x20019000, 5952, 0x20020000) is not None, 'large future allocator claim is possible')
    need(growth(0x20019000, 5952, 0x2001b000) is None, 'stack-dependent allocator refusal')
    for args in [(0, 8, 0x20020000), (0x20019000, 5953, 0x20020000),
                 (0x20019000, -8, 0x20020000), (True, 8, 0x20020000)]:
        try:
            growth(*args)
        except ValueError:
            need(True, 'out-of-domain model rejection')
        else:
            need(False, 'model accepted unqualified arguments')
    result = dict(schema='dz-source-memory-rollback-v1', packageSha256=EXPECTED,
                  targetOperations=0, ownedLoggerScratch=None, codeStorageKind='unqualified',
                  mode2OriginalCodeRestorationQualified=False,
                  sourceRanges=snippets, scatterMaps=maps,
                  image0Heap=dict(initialBase='0x20018000', initialEnd='0x20019000',
                                  dynamicCeiling='SP minus 0x1000; per-call, not fixed reservation',
                                  allocatorVa='0x378', freeVa='0x3d6', initVa='0xcb4', growVa='0x1afa'),
                  initialStackTops={'image0-CPU':'0x20020000','image1-CPU':'0x20020000'},
                  limitations=['Separate CPU address domains; equal numeric addresses are not shared ownership.',
                               'Scatter rows are startup writes, not complete runtime ownership maps.',
                               'No image1 allocator reservation established on examined startup path.',
                               'No receiver for OCL mailbox command 0x3f or boot-ROM/remap implementation recovered.'])
    return (json.dumps(result, indent=2) + '\n').encode(), ('\n'.join(text) + '\n').encode()


def main():
    evidence, disassembly = build()
    for name, content in [('source-audit.json', evidence), ('reviewed-disassembly.txt', disassembly)]:
        path = HERE / name
        if sys.argv[1:] == ['--record']:
            path.write_bytes(content)
        else:
            need(path.read_bytes() == content, 'frozen derived artifact: ' + name)
    print(json.dumps({'accepted':True, 'checks':COUNT, 'targetOperations':0,
                      'sourceAuditSha256':sha(evidence), 'disassemblySha256':sha(disassembly)}, sort_keys=True))


if __name__ == '__main__':
    main()
