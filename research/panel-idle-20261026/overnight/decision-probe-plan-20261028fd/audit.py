#!/usr/bin/env python3
"""Offline ELF/DT/source audit and fixed-size read-bound model. No target adapter."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import sys
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM64, CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_THUMB, CS_MODE_MCLASS
from capstone.arm64_const import ARM64_OP_MEM, ARM64_REG_SP, ARM64_REG_X21

HERE = Path(__file__).resolve().parent
B = HERE.parent
checks = 0

def need(ok, label):
    global checks
    checks += 1
    if not ok:
        raise ValueError(label)

def sha(b): return hashlib.sha256(b).hexdigest()

def load_elf(relative):
    raw = (B / relative).read_bytes()
    elf = ELFFile(BytesIO(raw))
    need(elf['e_machine'] == 'EM_AARCH64' and elf.little_endian, 'AArch64 module')
    return elf

def reloc(elf, section, offset):
    rs = elf.get_section_by_name(section)
    tab = elf.get_section(rs['sh_link'])
    found = [r for r in rs.iter_relocations() if r['r_offset'] == offset]
    need(len(found) == 1, f'unique relocation {section}:{offset:x}')
    r = found[0]
    s = tab.get_symbol(r['r_info_sym'])
    target = elf.get_section(s['st_shndx']).name if isinstance(s['st_shndx'], int) else None
    return s.name, target, r['r_addend'], r['r_info_type']

def ins(elf, address, mnemonic, operands=None):
    data = elf.get_section_by_name('.text').data()
    d = list(Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN).disasm(data[address:address+4], address))
    need(len(d) == 1 and d[0].mnemonic == mnemonic, f'instruction {address:x}')
    if operands is not None: need(d[0].op_str == operands, f'operands {address:x}')

def bounded_copy_model(advertised, position, requested=4096):
    """Model only audited .61cc..62a8 branch domain, not a file reader."""
    need(type(advertised) is int and 0 <= advertised <= 65535, 'u16 length domain')
    need(type(position) is int and type(requested) is int, 'integer arguments')
    if position < 0: return 'EINVAL', 0
    total = advertised + 1
    if position > 0x3ffff or position >= total: return 'EOF', 0
    if total <= 4095: return 'DATA', total
    remaining = total - position
    if remaining <= 4095: return 'DATA', remaining
    if requested > 0x7fffffff: return 'BUG_PATH', 0
    return 'DATA', requested

def main():
    pins = json.loads((HERE / 'input-pins.json').read_text())
    for row in pins['inputs']:
        raw = (B / row['path']).read_bytes()
        need(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'input pin ' + row['path'])
    modules = 'firmware-platform-analysis-20261028db/private/pltf-extracted/tree/root/lib/modules/5.4.261/kernel/'
    logger = load_elf(modules + 'logger.ko')
    tcon = load_elf(modules + 'soc/sdp_tcon.ko')
    need(reloc(logger, '.rela.data', 0x480)[1:3] == ('.text', 0x5e50), 'g_vlog_ops slot0')
    need(reloc(logger, '.rela.text', 0x6848)[0] == 'vlog_set_ops', 'stock registration')
    need(reloc(logger, '.rela.text', 0x66bc)[1:3] == ('.data', 0x418), 'ops base')
    ins(logger, 0x6844, 'add', 'x0, x22, #0x68')
    need(reloc(tcon, '.rela.rodata', 0x1670)[1:3] == ('.text', 0x61b0), 'debugfs read binding')
    need(reloc(tcon, '.rela.rodata', 0x16d0)[0] == 'simple_open', 'no custom open callback')
    need(reloc(tcon, '.rela.text', 0x71b0)[0] == 'debugfs_create_file', 'file creation')
    strings = tcon.get_section_by_name('.rodata.str1.8').data()
    need(strings[0x2b68:].split(b'\0',1)[0] == b'tcon_micom_log', 'debugfs file name')
    need(strings[0x2a98:].split(b'\0',1)[0] == b'tcon', 'debugfs directory name')
    need(strings[0x428:].split(b'\0',1)[0] == b'sdp_mmap', 'memory node')
    need(tcon.get_section_by_name('.data').data()[0x2b8:0x2c9] == b'samsung,tcon_info', 'memory property name')
    for addr, name, operands in [
        (0x9a0,'add','x2, x23, #0x34'),(0xa4c,'add','x23, x23, #0x48'),
        (0xc84,'ldr','w1, [x24, #0x2f0]'),(0xc8c,'ldr','w20, [x24, #0x2ec]'),
        (0xc94,'orr','x20, x1, x20, lsl #32'),(0xcc8,'add','x1, x20, #0xa0, lsl #12'),
        (0xcd0,'mov','x2, #0x20000'),(0xcd8,'str','x0, [x19, #0x378]'),
        (0x61c8,'ldr','x23, [x0, #0x378]'),(0x61cc,'ldrh','w20, [x23]'),
        (0x61d0,'tbnz','x19, #0x3f, #0x6330'),(0x6200,'cmp','x19, x0'),
        (0x620c,'cmp','x20, x19'),(0x6214,'cmp','w20, #0xfff'),
        (0x621c,'mov','x24, x20'),(0x6280,'sub','x20, x20, x19'),
        (0x6294,'mov','x20, x25'),(0x62f0,'mov','x2, x24'),
        (0x625c,'str','x19, [x21]'),(0x6f48,'mov','w1, #0'),
        (0x6f44,'mov','x2, #0x3ff00'),(0xfdc,'strh','w2, [x1, #2]'),
        (0x278,'ldr','w0, [x0, #0x4cc]'),(0x280,'mov','w0, #0')]:
        ins(tcon,addr,name,operands)
    for addr,name in [(0xcd4,'devm_ioremap_nocache'),(0x61f4,'tcon_rpm_dev_tryuse'),
                      (0x62f8,'__arch_copy_to_user'),(0x6260,'tcon_rpm_dev_disuse'),
                      (0x6f50,'__memset_io')]:
        need(reloc(tcon,'.rela.text',addr)[0] == name, f'call {addr:x}')
    # Complete bounded read function: classify every decoded store destination.
    decoder = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
    decoder.detail = True
    body = tcon.get_section_by_name('.text').data()[0x61b0:0x634c]
    read_stores = []
    for i in decoder.disasm(body, 0x61b0):
        if i.mnemonic.startswith('st'):
            mem = [o.mem for o in i.operands if o.type == ARM64_OP_MEM]
            need(len(mem) == 1, 'store destination known')
            m = mem[0]
            need(m.base == ARM64_REG_SP or (i.address == 0x625c and m.base == ARM64_REG_X21 and m.disp == 0), 'no shared-buffer store in read body')
            read_stores.append(hex(i.address))
    ins(tcon, 0x62ec, 'add', 'x1, x19, #4')
    ins(tcon, 0x62fc, 'nop')
    ins(tcon, 0x6300, 'b', '#0x6258')
    # Existing kernel export body closes simple_open without assuming live VAs.
    image = (B/'kernel-Image.bin').read_bytes()
    exports = json.loads((B/'kernel-export-index.json').read_text())['exports']
    opened = [r for r in exports if r['name'] == 'simple_open']
    need(len(opened) == 1 and opened[0]['target_image_offset'] == '0x1b6b60', 'simple_open Image binding')
    opened_body = list(decoder.disasm(image[0x1b6b60:0x1b6b74],0x1b6b60))
    need([(i.mnemonic,i.op_str) for i in opened_body] == [('ldr','x0, [x0, #0x240]'),('cbz','x0, #0x1b6b6c'),('str','x0, [x1, #0xc8]'),('mov','w0, #0'),('ret','')], 'simple_open private-data-only body')
    # Kernel-side owner closure must not turn module section offsets into live VAs.
    dt = json.loads((B/'firmware-kernel-analysis-20261028cs/private/dtb-01.json').read_text())
    def walk(x):
        if isinstance(x,dict):
            yield x
            for v in x.values(): yield from walk(v)
        elif isinstance(x,list):
            for v in x: yield from walk(v)
    props=[x for x in walk(dt) if x.get('name')=='samsung,tcon_info' and 'cells' in x]
    need(len(props)==1 and props[0]['cells']==[1,0x5fe00000,0x100000], 'candidate DTB memory')
    base=(props[0]['cells'][0]<<32)|props[0]['cells'][1]
    need(base+0xa0000==0x15fea0000, 'candidate log buffer physical address')
    # Negative semantic case and exhaustive first-read bound; no target reads.
    need(bounded_copy_model(100,0,16)==('DATA',101), 'small request can be over-copied')
    need(bounded_copy_model(65535,-1)==('EINVAL',0), 'negative offset')
    need(bounded_copy_model(65535,0x40000)==('EOF',0), 'offset bound')
    need(bounded_copy_model(65535,0,0x80000000)==('BUG_PATH',0), 'oversized count not allowed')
    max_copy=0
    for advertised in range(65536):
        status,n=bounded_copy_model(advertised,0)
        need(status=='DATA' and 0<n<=4096, 'fixed first-read allocation bound')
        max_copy=max(max_copy,n)
    for advertised in [0,1,4093,4094,4095,4096,8191,65535]:
        for pos in [0,1,4094,4095,4096,advertised,advertised+1,65536]:
            status,n=bounded_copy_model(advertised,pos)
            need(n<=4096, 'positive-offset allocation bound')
            if status=='DATA': need(pos+4+n<=0x20000,'mapped source extent bound')
    spans={}
    for name,elf,ranges in [('logger',logger,[(0x66b0,0x6910),(0x5e50,0x5fc0)]),
                            ('sdp_tcon',tcon,[(0x920,0xa58),(0xc84,0xce0),(0x270,0x288),(0xdf8,0x1018),(0x61b0,0x634c),(0x6f38,0x6f74),(0x718c,0x71b8)])]:
        data=elf.get_section_by_name('.text').data()
        for a,z in ranges: spans[f'{name}:.text:{a:x}..{z:x}']={'bytes':z-a,'sha256':sha(data[a:z])}
    spans['kernel:Image:1b6b60..1b6b74']={'bytes':20,'sha256':sha(image[0x1b6b60:0x1b6b74])}
    asset=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
    for a,z in [(0x2024,0x203e),(0xbd58,0xbd60),(0xc5d0,0xc5d8),(0xc1e0,0xc212)]:
        spans[f'selected-image1:VA:{a:x}..{z:x}']={'file_offset':a+0x40200,'bytes':z-a,'sha256':sha(asset[a+0x40200:z+0x40200])}
    result={'schema':'fd-source-probe-audit-v1','checks':checks,'source_spans':spans,
       'vlog_owner':{'module':'logger.ko','registration_text_offset':0x6848,'callback_text_offset':0x5e50,'ops_data_offset':0x480,'live_pointer_proven':False},
       'debugfs_candidate':{'source_path':'tcon/tcon_micom_log','read_text_offset':0x61b0,'map_bytes':0x20000,'candidate_physical_base':hex(base+0xa0000),'live_node_or_producer_proven':False,'external_rtp_bridge_proven':False,'fresh_open_offset':0,'exact_requested_and_allocated_bytes':4096,'maximum_modeled_first_copy':max_copy,'max_calls':1,'complete_log_proven':False,'payload_starts_after_header_bytes':4,'copy_to_user_residual_checked':False,'bounded_read_body_has_no_shared_buffer_store':True,'read_store_sites':read_stores},
       'bounded_export_census':{'scope':'9379 retained namespace-zero exports, not all symbols or live configuration','register_kprobe_present':any(r['name']=='register_kprobe' for r in exports),'register_ftrace_function_present':any(r['name']=='register_ftrace_function' for r in exports),'tracepoint_probe_register_present':any(r['name']=='tracepoint_probe_register' for r in exports)},
       'target_calls':0,'network_calls':0,'controller_writes':0,'instruction_hooks_generated':False}
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__': main()
