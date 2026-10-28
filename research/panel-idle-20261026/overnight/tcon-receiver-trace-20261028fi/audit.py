#!/usr/bin/env python3
"""Host-only finite receiver-boundary audit; never opens device/target paths."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import os
import stat
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
from elftools.elf.elffile import ELFFile

HERE = Path(__file__).resolve().parent
B = HERE.parent
TV = B.parents[1]
ANCHORS = [b'RHEA_M_TCON', b'TCON Image Info', b'Msgbox ISR In Ch']
checks = 0

def need(ok, label):
    global checks
    checks += 1
    if not ok:
        raise ValueError(label)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def root_path(domain, relative):
    need(domain in ['overnight', 'tv'], 'allowed pin domain')
    root = B if domain == 'overnight' else TV
    path = root / relative
    need(path.is_relative_to(root) and '..' not in Path(relative).parts,
         'bounded relative path')
    return path

def tree_scan(root):
    """No symlink following; regular files only, all errors fatal.

    Manifest bytes per regular file: UTF-8 relative path, NUL, decimal size,
    NUL, lowercase SHA256, LF; entries sorted by path. No OEM bytes emitted.
    """
    paths = []
    skipped_links = 0
    skipped_other = 0
    for current, dirs, files in os.walk(root, followlinks=False,
                                        onerror=lambda e: (_ for _ in ()).throw(e)):
        for name in list(dirs):
            path = Path(current) / name
            if path.is_symlink():
                dirs.remove(name)
                skipped_links += 1
        for name in files:
            path = Path(current) / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                skipped_links += 1
            elif stat.S_ISREG(mode):
                paths.append(path)
            else:
                skipped_other += 1
    digest = hashlib.sha256()
    total = 0
    matches = []
    overlap = max(map(len, ANCHORS)) - 1
    for path in sorted(paths, key=lambda p: p.relative_to(root).as_posix()):
        file_digest = hashlib.sha256()
        length = 0
        tail = b''
        found = {a: [] for a in ANCHORS}
        with path.open('rb') as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                file_digest.update(chunk)
                span = tail + chunk
                for anchor in ANCHORS:
                    start = 0
                    while True:
                        offset = span.find(anchor, start)
                        if offset < 0:
                            break
                        absolute = length - len(tail) + offset
                        if not found[anchor] or found[anchor][-1] != absolute:
                            found[anchor].append(absolute)
                        start = offset + 1
                length += len(chunk)
                tail = span[-overlap:]
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode() + b'\0' + str(length).encode() +
                      b'\0' + file_digest.hexdigest().encode() + b'\n')
        total += length
        for anchor, offsets in found.items():
            if offsets:
                matches.append({'relative_path': relative,
                                'anchor': anchor.decode(), 'offsets': offsets})
    return {'regular_files': len(paths), 'regular_bytes': total,
            'symlinks_skipped': skipped_links, 'other_entries_skipped': skipped_other,
            'manifest_sha256': digest.hexdigest(), 'exact_anchor_matches': matches}

def main():
    pins = json.loads((HERE / 'input-pins.json').read_text())
    data_by_id = {}
    for pin in pins['inputs']:
        data = root_path(pin['domain'], pin['path']).read_bytes()
        need(len(data) == pin['bytes'] and sha(data) == pin['sha256'],
             'input pin ' + pin['id'])
        data_by_id[pin['id']] = data
    corpus_results = []
    for pin in pins['corpora']:
        result = tree_scan(root_path(pin['domain'], pin['path']))
        need(result == pin['result'], 'finite corpus identity and scan ' + pin['id'])
        corpus_results.append({'id': pin['id'], **result})

    elf = ELFFile(BytesIO(data_by_id['sdp_tcon']))
    need(elf['e_machine'] == 'EM_AARCH64' and elf.little_endian, 'AArch64 source')
    md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
    def ins(section, offset, mnemonic, operands):
        data = elf.get_section_by_name(section).data()
        decoded = list(md.disasm(data[offset:offset+4], offset))
        need(len(decoded) == 1 and decoded[0].mnemonic == mnemonic and
             decoded[0].op_str == operands, section + '+' + hex(offset))
    def reloc(section, offset, name, target_section, target, rtype):
        rs = elf.get_section_by_name('.rela' + section)
        symtab = elf.get_section(rs['sh_link'])
        matches = [r for r in rs.iter_relocations() if r['r_offset'] == offset]
        need(len(matches) == 1, 'unique relocation ' + section + hex(offset))
        r = matches[0]
        symbol = symtab.get_symbol(r['r_info_sym'])
        actual_section = (elf.get_section(symbol['st_shndx']).name
                          if isinstance(symbol['st_shndx'], int) else None)
        need((symbol.name, actual_section, symbol['st_value'] + r['r_addend'],
              r['r_info_type']) == (name, target_section, target, rtype),
             'resolved relocation ' + section + hex(offset))

    # Resource row3's DMA slot is .data+0x2f8; its physical cells are separate.
    data = elf.get_section_by_name('.data').data()
    need(data[0x2b8:].split(b'\0', 1)[0] == b'samsung,tcon_info', 'row3 identity')
    need(0x2b8 + 64 == 0x2f8, 'row3 DMA slot')
    for offset, mnemonic, operands in [
        (0xc94,'orr','x20, x1, x20, lsl #32'),
        (0xca0,'str','x0, [x19, #0x390]'),
        (0xcac,'str','x0, [x19, #0x330]'),
        (0xcb0,'add','x1, x20, #0x20, lsl #12'),
        (0xcb8,'mov','x2, #0x40000'),(0xcc0,'str','x0, [x19, #0x368]'),
        (0xcc8,'add','x1, x20, #0xa0, lsl #12'),
        (0xcd0,'mov','x2, #0x20000'),(0xcd8,'str','x0, [x19, #0x378]'),
        (0xce0,'add','x1, x20, #0xc0, lsl #12'),
        (0xce8,'mov','x2, #0x30000'),(0xcf0,'str','x0, [x19, #0x370]'),
        (0x7594,'mov','w19, w1'),(0x75d4,'str','w19, [x2]'),
        (0x76a0,'ldr','w24, [x25]'),(0x76a4,'ldr','x23, [x0, #0x368]'),
        (0x7814,'ldr','x0, [x19, #0x360]'),(0x7824,'ldr','x0, [x19, #0x360]'),
        (0x7828,'mov','w1, #0'),(0x782c,'add','x0, x0, #4'),
        (0x7834,'ldr','x0, [x19, #0x360]'),(0x7838,'sub','x1, x20, x23'),
        (0x783c,'add','w1, w24, w1'),(0x7840,'add','x0, x0, #8'),
        (0x7848,'ldr','x0, [x19, #0x360]'),(0x784c,'mov','w1, w22'),
        (0x7850,'add','x0, x0, #0xc'),(0x7860,'ldr','x0, [x19, #0x360]'),
        (0x7864,'mov','w1, #1'),(0x7868,'lsl','w1, w1, w21'),
        (0x786c,'add','x0, x0, #0x40'),
        (0x7a48,'ldr','x20, [x19, #0x368]'),(0x7a58,'mov','x0, x20'),
        (0x7a60,'blr','x21'),(0x7a64,'mov','w3, w0'),
        (0x7a6c,'ldrh','w1, [x20, #8]'),(0x7a74,'mov','x2, x20'),
        (0xcdc4,'ldr','x0, [x20, #0x370]'),
        (0xce04,'ldr','x0, [x20, #0x370]'),(0xce08,'mov','x2, #0x30000'),
        (0xce48,'ldr','x2, [x20, #0x370]'),
        (0x2c20,'ldr','x1, [x1, #0x118]'),(0x2c28,'str','w1, [x0]'),
        (0x2c30,'mov','w0, #0x5678'),(0x2c34,'movk','w0, #0x1234, lsl #16'),
        (0x2c3c,'str','w0, [x1]'),(0x2ccc,'mov','x0, #0x654'),
        (0x2cd4,'movk','x0, #0x9d, lsl #16')]:
        ins('.text', offset, mnemonic, operands)
    for offset, mnemonic, operands in [
        (0x26c,'str','x0, [x19, #0x358]'),(0x2cc,'str','x0, [x19, #0x360]'),
        (0x77c,'ldr','x1, [x0]'),(0x788,'mov','x0, x19'),
        (0x78c,'add','w1, w1, #0x20, lsl #12')]:
        ins('.text.unlikely', offset, mnemonic, operands)
    for offset in [0xcbc, 0xcd4, 0xcec]:
        reloc('.text', offset, 'devm_ioremap_nocache', None, 0, 283)
    for offset in [0x7820, 0x7830, 0x7844, 0x7854, 0x7870]:
        reloc('.text', offset, 'ft_write', '.text', 0x4938, 283)
    reloc('.text', 0x7a78, 'sdp_tcon_send_to_msgbox', '.text', 0x7670, 283)
    reloc('.text', 0x75c4, '', '.data', 0xe7c, 275)
    reloc('.text', 0x769c, '', '.data', 0xe7c, 275)
    reloc('.text.unlikely', 0x76c, '', '.data', 0x2f8, 275)
    reloc('.text.unlikely', 0x77c, '', '.data', 0x2f8, 286)
    reloc('.text.unlikely', 0x790, 'sdp_tcon_msgbox_init', '.text', 0x7560, 283)
    for offset in [0x268, 0x2c8]:
        reloc('.text.unlikely', offset, 'devm_ioremap_resource', None, 0, 283)
    for offset in [0x298, 0x29c]:
        rs = elf.get_section_by_name('.rela.text.unlikely')
        r = next(r for r in rs.iter_relocations() if r['r_offset'] == offset)
        symbol = elf.get_section(rs['sh_link']).get_symbol(r['r_info_sym'])
        target = symbol['st_value'] + r['r_addend']
        need(elf.get_section(symbol['st_shndx']).data()[target:].split(b'\0',1)[0]
             == b'msgbox-tx', 'TX resource name ' + hex(offset))
    for offset, name in [(0xcdcc,'__memcpy_fromio'),(0xce10,'__memset_io')]:
        reloc('.text', offset, name, None, 0, 283)
    for offset, name, target in [(0xce1c,'fio_fopen',0x72b8),
        (0xce30,'fio_fseek',0x73f8),(0xce44,'fio_fseek',0x73f8),
        (0xce58,'fio_fread',0x73a8),(0xce60,'fio_fclose',0x7388)]:
        reloc('.text', offset, name, '.text', target, 283)
    ins('.text',0x4938,'dmb','oshst')
    ins('.text',0x493c,'str','w1, [x0]')

    # Scan limits are demonstrated by the known writer itself: constructed
    # constants need not have a raw little-endian address/magic literal.
    text = elf.get_section_by_name('.text').data()
    handoff = text[0x2af0:0x2e3c]
    need((0x9d0654).to_bytes(4,'little') not in handoff, 'known writer lacks raw address')
    need((0x12345678).to_bytes(4,'little') not in handoff, 'known writer lacks raw magic')
    tree = json.loads(data_by_id['candidate_dtb'])
    def walk(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child)
    nodes = [n for n in walk(tree) if n.get('path') == '/soc/sdp_tcon']
    need(len(nodes) == 1, 'candidate tcon node')
    props = {p['name']:p for p in nodes[0]['properties']}
    names = props['reg-names']['strings']
    cells = props['reg']['cells']
    resources = {name:cells[i*2:i*2+2] for i,name in enumerate(names)}
    need(resources['msgbox-tx'] == [0x9d0480,0x44], 'candidate TX MMIO resource')
    need(resources['msgbox-rx'] == [0x9d0400,0x44], 'candidate RX MMIO resource')

    examples=[]
    for dma in [0, 0xffffffff, 0x15fe00000, 0xabcdef0102030405]:
        for relative in [0, 4, 0x3fffc]:
            boot = dma & 0xffffffff
            mailbox = (dma + 0x20000) & 0xffffffff
            payload = (mailbox + relative) & 0xffffffff
            need(payload == (dma + 0x20000 + relative) % (1<<32), 'mailbox low32 model')
            need(payload == (boot + 0x20000 + relative) % (1<<32), 'common handoff arithmetic')
            examples.append({'dma':hex(dma),'buffer_relative':hex(relative),
                             'boot_low32':hex(boot),'mailbox_low32':hex(mailbox),
                             'message_pointer_low32':hex(payload)})
    prefix=data_by_id['retained_prefix']
    need(prefix.startswith(b'RHEA_M_TCON_FW_20250103_1715\n'), 'retained domain banner')
    need(b'TCON Image Info : F77ABU2D20\n' in prefix, 'distinct retained image-info field')
    need(b'Msgbox ISR In Ch : 2\n' in prefix, 'retained mailbox text anchor')
    small_scans=[]
    for id in ['seret','secos','secos_drv','ddr_init','kernel','selected_external']:
        blob=data_by_id[id]
        hits={anchor.decode():[i for i in range(len(blob)) if blob.startswith(anchor,i)]
              for anchor in ANCHORS if anchor in blob}
        need(hits == {}, 'bounded exact anchors ' + id)
        small_scans.append({'id':id,'bytes':len(blob),'exact_anchor_matches':hits})
    spans=[]
    for section,start,end in [('.text',0xc84,0xcfc),('.text',0x2af0,0x2e3c),
        ('.text.unlikely',0x228,0x2d8),('.text.unlikely',0x76c,0x794),
        ('.text',0x7560,0x75e8),('.text',0x7670,0x79dc),('.text',0x79e0,0x7b00),
        ('.text',0xcd80,0xceb4)]:
        spans.append({'domain':'sdp_tcon.ko:'+section,'start':hex(start),
                      'end_exclusive':hex(end),'sha256':sha(elf.get_section_by_name(section).data()[start:end])})
    result={'schema':'fi-tcon-receiver-boundary-v1','checks':checks,
        'source_spans':spans,'corpora':corpus_results,'bounded_other_scans':small_scans,
        'shared_info_layout':[{'resource_offset':hex(a),'bytes':hex(n),'device_pointer':hex(p)}
                              for a,n,p in [(0,0x20000,0x390),(0x20000,0x40000,0x368),
                                            (0xa0000,0x20000,0x378),(0xc0000,0x30000,0x370)]],
        'mailbox':{'probe_dma_load':'.text.unlikely+0x77c -> .data+0x2f8',
            'mailbox_dma_add':'.text.unlikely+0x78c low32(DMA+0x20000)',
            'saved_low32_dma':'.data+0xe7c',
            'send_function':'.text+0x7670',
            'pointer_write':'.text+0x7834..0x7844, TX+8',
            'length_write':'.text+0x7848..0x7854, TX+0xc',
            'trigger':'.text+0x7860..0x7870, TX+0x40, 1<<channel',
            'candidate_dtb_resources':resources,
            'arithmetic_examples':examples,
            'candidate_physical_equals_dma_proven':False},
        'retained_log':{'banner':'RHEA_M_TCON_FW_20250103_1715',
            'image_info_field':'F77ABU2D20','historical_not_current':True},
        'receiver_image_identified':False,'receiver_instruction_coordinates_identified':False,
        'base_plus_a0000_producer_identified':False,'external_image1_bridge_identified':False,
        'external_image1_proxy_excluded':False,'target_network_root_operations':0,
        'search_limit':'Exact-anchor results cover pinned regular-file roots/raw bodies only; compressed, encrypted, runtime-loaded and absent images remain unresolved.'}
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__ == '__main__':
    main()
