#!/usr/bin/env python3
"""Bounded, read-only source map. No firmware execution or binary extraction.

Reads retained files in place. stdout contains only source metadata/derived facts.
No runtime/TV adapters are imported. Capstone/pyelftools are existing host tools.
"""
import hashlib, io, json, os, re, struct, sys, zlib
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
B = HERE.parent
ROOT = B.parent
DB = B / 'firmware-platform-analysis-20261028db'
P = DB / 'private/pltf-extracted/tree/root'
Q = DB / 'private/prd-extracted/tree/root'
checks = 0
pins = []

def need(ok, message):
    global checks
    if not ok:
        raise ValueError(message)
    checks += 1

def sha(b):
    return hashlib.sha256(b).hexdigest()

def read(p, expected=None):
    need(p.is_file() and not p.is_symlink(), 'ordinary input file ' + p.name)
    b = p.read_bytes()
    need(expected is None or sha(b) == expected, 'input pin ' + p.name)
    pins.append({'path': str(p.relative_to(ROOT)), 'bytes': len(b), 'sha256': sha(b)})
    return b

def reverse_words(b):
    if len(b) % 4:
        raise ValueError('word view requires full words')
    return b''.join(b[i:i+4][::-1] for i in range(0, len(b), 4))

def checksum_source(b, initial=1):
    """Instruction-level arithmetic of .text1aaa0 for full groups of four.

    ldr little-endian word; consume bits24..31,16..23,8..15,0..7;
    update Adler accumulators modulo65521 after each byte. No trimming/padding.
    """
    if len(b) % 4:
        raise ValueError('source checks only full words')
    lo, hi = initial & 65535, initial >> 16
    for (word,) in struct.iter_unpack('<I', b):
        for shift in (24, 16, 8, 0):
            lo = (lo + ((word >> shift) & 255)) % 65521
            hi = (hi + lo) % 65521
    return lo | (hi << 16)

def census(root):
    """Filename-only inventory; no symlink traversal or candidate content scans."""
    rows = []
    def failed(error):
        raise error
    for base, dirs, names in os.walk(root, followlinks=False, onerror=failed):
        dirs[:] = sorted(d for d in dirs if not (Path(base)/d).is_symlink())
        for n in sorted(names):
            p = Path(base)/n
            rel = str(p.relative_to(root))
            if re.search(r'ocl(?![a-z])|micom|mcu|serdes', n, re.I):
                rows.append({'path': rel, 'kind': 'symlink' if p.is_symlink() else 'file',
                             'bytes': p.lstat().st_size})
    return sorted(rows, key=lambda x: x['path'])

def main():
    sys.path.insert(0, '/tmp/tcon-capstone')
    from capstone import Cs, CS_ARCH_ARM64, CS_ARCH_SPARC, CS_MODE_ARM, CS_MODE_BIG_ENDIAN
    from elftools.elf.elffile import ELFFile
    module_path = B/'serdes-ack-copy-20261026/sdp_ocl_jp.ko'
    module = read(module_path, 'e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c')
    e = ELFFile(io.BytesIO(module))
    need(e['e_machine'] == 'EM_AARCH64', 'sender module architecture')
    need(read(P/'usr/lib/modules/5.4.261/kernel/soc/sdp_ocl_jp.ko') == module,
         'extracted OCL module byte-identical to retained module')
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    sm = Cs(CS_ARCH_SPARC, CS_MODE_BIG_ENDIAN)
    rs = {}
    for section in ('.text', '.text.unlikely'):
        r = e.get_section_by_name('.rela'+section)
        sy = e.get_section(r['sh_link'])
        rs[section] = {}
        for x in r.iter_relocations():
            sym = sy.get_symbol(x['r_info_sym'])
            name = sym.name
            if not name and type(sym['st_shndx']) is int:
                name = e.get_section(sym['st_shndx']).name
            rs[section][x['r_offset']] = {'name': name, 'addend': x['r_addend']}
    def ins(section, at, mnemonic, operands):
        code = e.get_section_by_name(section).data()[at:at+4]
        xs = list(md.disasm(code, at))
        need(len(xs) == 1 and (xs[0].mnemonic, xs[0].op_str) == (mnemonic, operands),
             'source instruction ' + section + ':' + hex(at))
    def reloc(section, at, name, addend=0):
        need(rs[section][at] == {'name': name, 'addend': addend},
             'relocation ' + section + ':' + hex(at))
    for at, m, o in [
        (0x2b3c,'mov','w1, #0x3f'), (0x2b40,'mov','w2, #1'),
        (0x2b48,'add','x4, sp, #0x2f'), (0x2b4c,'mov','w3, #0'),
        (0x2b54,'strb','w0, [sp, #0x2f]'), (0x2b58,'mov','w0, w2'),
        (0x7ddc,'tbz','w0, #1, #0x8030'), (0x7df4,'cmp','w2, #4'),
        (0x7e18,'cbnz','w21, #0x7f94'), (0x7f94,'add','x28, sp, #0x73'),
        (0x7fa0,'ldrb','w2, [x24, x0]'), (0x7fac,'strb','w2, [x1, #5]'),
        (0x7fb4,'add','w0, w21, #5'), (0x7fb8,'strh','w0, [sp, #0x94]'),
        (0x7fbc,'b','#0x7e28'), (0x7e3c,'ldrh','w1, [x1, #2]'),
        (0x7e48,'lsr','w1, w1, #1'), (0x7e60,'bl','#0x7e60'),
        (0x7e68,'tbnz','w0, #0x1f, #0x7f60'), (0x7e94,'orr','w20, w20, w0'),
        (0x803c,'add','x0, sp, #0xb0'), (0x8040,'bl','#0x7b10'),
        (0x7b98,'mov','x0, x24'), (0x7b9c,'bl','#0x7b9c'),
        (0x6810,'ldr','w0, [x19]'), (0x6814,'cmp','w0, #1'),
        (0x6818,'b.eq','#0x684c'), (0x684c,'ldp','w0, w1, [x19, #4]'),
        (0x6850,'ldp','w2, w3, [x19, #0xc]'), (0x6854,'ldr','x4, [x19, #0x18]'),
        (0x6858,'bl','#0x62d8'), (0x6360,'strb','w2, [x1, #1]'),
        (0x6388,'ldrh','w3, [x3, #2]'), (0x6394,'lsr','w3, w3, #1'),
        (0x63a0,'bl','#0x63a0'), (0x63dc,'ldr','w0, [x20]'),
        (0x63e0,'tbz','w0, #1, #0x6534'), (0x6548,'strb','w26, [sp, #0x73]'),
        (0x654c,'str','w24, [sp, #0x74]'), (0x6558,'bl','#0x6558'),
        (0x1dab4,'mov','x4, #0xbff8'), (0x1dabc,'movk','x4, #0xd, lsl #16'),
        (0x1dac8,'mov','x2, #4'), (0x1dad4,'bl','#0x1b040'),
        (0x1db08,'mov','w26, #1'), (0x1db44,'bl','#0x1aaa0'),
        (0x1dbbc,'ldr','w0, [sp, #0x64]'), (0x1dbc0,'cmp','w26, w0'),
        (0x1e544,'mov','x4, #0xf08c'), (0x1e54c,'movk','x4, #0xb, lsl #16'),
        (0x1e554,'mov','x2, #0x15'), (0x1e5c4,'cmp','w0, #0xff'),
        (0x1e5c8,'b.eq','#0x1e5b4'),
        (0x1f6cc,'adrp','x20, #0x1f000'), (0x1f6d0,'adrp','x19, #0x1f000'),
        (0x1b288,'ldrh','w4, [sp, #0x48]'), (0x1b29c,'rev16','w4, w4'),
        (0x1b2b4,'strb','w8, [sp, #0x47]'), (0x1b2bc,'strb','w7, [sp, #0x4a]'),
    ]:
        ins('.text', at, m, o)
    for at, name in [(0x2b5c,'SDP_OCL_I2C_MBox_Write'), (0x7e60,'i2c_transfer'),
                     (0x7ed4,'i2c_transfer'), (0x63a0,'i2c_transfer'),
                     (0x6558,'i2c_transfer'), (0x7b9c,'wait_for_completion')]:
        reloc('.text', at, name)
    for at,m,o in [(0x68,'mov','w4, #0x10'), (0x88,'movk','w4, #0xf8, lsl #16'),
                   (0xb4,'stp','wzr, w4, [sp, #0x80]'),
                   (0xf0,'ldr','w0, [x0, #8]'), (0x310,'bl','#0x310'),
                   (0x314,'str','x0, [x19, #0x30]'), (0x3f0,'add','x1, sp, #0x70'),
                   (0x3f8,'str','x0, [x19, #0x38]')]:
        ins('.text.unlikely', at,m,o)
    reloc('.text.unlikely',0x310,'i2c_get_adapter')
    reloc('.text.unlikely',0x3f4,'i2c_new_device')
    reloc('.text',0x1f6cc,'.rodata.str1.8',0x5448)
    reloc('.text',0x1f6d0,'.rodata.str1.8',0x5488)
    reloc('.text',0x6368,'mBox_client')
    reloc('.text',0x636c,'mBox_adap')
    reloc('.text',0x1e574,'.data',0x2520)
    reloc('.text',0x1e578,'.rodata',0x1eb8)
    for at,m,o in [(0x1e584,'add','x1, x22, #0x678'),
                   (0x1e598,'add','x1, x22, #0x7b8'),
                   (0x1e5cc,'add','x1, x22, #0xb80'),
                   (0x1e5dc,'add','x1, x22, #0xcc0')]:
        ins('.text',at,m,o)
    strings = e.get_section_by_name('.rodata.str1.8').data()
    def cstr(at):
        return strings[at:strings.index(0,at)].decode('ascii')
    need(cstr(0x5448) == '/opt/usr/apps/appbinarymanager/default/empOCJPsubmicom.img', 'conditional override filename')
    need(cstr(0x5488) == '/etc/micom-binary/RMFMICOM_OCJP.bin', 'conditional stock filename')
    ro = e.get_section_by_name('.rodata').data()
    need(len(ro[0x2670:0x2670+968]) == 11*88, '11 source layout records')
    layouts = []
    for i in range(11):
        at=0x2670+i*88
        q=struct.unpack_from('<11Q',ro,at)
        layouts.append({'record':i,'sectionOffset':hex(at),'fileOffset':q[1],
                        'flashDestinationCandidate':q[2],'bytes':q[3],
                        'secondaryFileOffset':q[5],'secondaryBytes':q[7]})
    need((layouts[3]['fileOffset'],layouts[3]['bytes']) == (0xf000,0x30000), 'system candidate segment')
    need((layouts[5]['fileOffset'],layouts[5]['bytes'],layouts[5]['secondaryFileOffset'],layouts[5]['secondaryBytes'])
         == (0x3f000,0x60000,0x9f000,0xa000), 'split second candidate segment')
    need((layouts[7]['fileOffset'],layouts[7]['bytes']) == (0xa9000,0x6000), 'third candidate segment')
    version = struct.unpack_from('<5Q',ro,0x25a8)
    need(version[:3] == (0xf000,0x850,8), 'system candidate version descriptor')
    image = read(P/'etc/micom-binary/PMDMICOM_OCJP.bin','61754d8e0445ed1a73685af83cdcf3fea66971b1a622b04c3f614b8b63286aff')
    need(len(image) == 0xdc000, 'candidate exact length')
    need(read(P/'usr/lib/modules/5.4.261/kernel/soc/PMDMICOM_OCJP.bin') == image, 'candidate duplicate identity')
    fr = read(P/'etc/micom-binary/PMFMICOM_FRJP.bin','45f68e72fe62859431ffb9bcb918cd66895296602c7c28c6a6f031e3951dd349')
    need(read(P/'usr/lib/modules/5.4.261/kernel/soc/PMFMICOM_FRJP.bin') == fr, 'FRJP duplicate identity')
    need(image[0xbf08c:0xbf08c+21] == b'\xff'*21, 'new-layout selector bytes')
    view = reverse_words(image)
    calc = checksum_source(image[:0xdbff8])
    need(calc == zlib.adler32(view[:0xdbff8]), 'independent library checksum agreement')
    need(calc == struct.unpack_from('<I',image,0xdbff8)[0] == 0xce93f188, 'source-format checksum passes')
    need(checksum_source(b'\x00'*4) == zlib.adler32(b'\x00'*4), 'zero-word independent checksum')
    need(checksum_source(bytes(range(16))) == zlib.adler32(reverse_words(bytes(range(16)))), 'non-palindromic checksum fixture')
    for bad in (b'x',b'xxx',b'xxxxx'):
        for fn in (reverse_words,checksum_source):
            try: fn(bad)
            except ValueError: need(True,'partial-word rejection')
            else: need(False,'partial-word must reject')
    mutated = bytearray(image[:0xdbff8]);mutated[0x10040] ^= 1
    need(checksum_source(mutated) != calc, 'single-byte corruption changes checksum')
    # Per-instruction disassembly avoids stopping at inline data/tables. Addresses below
    # are FILE OFFSETS in a word-reversed view, never asserted runtime PCs.
    sparc=[]
    for at,m,o in [(0x10040,'ba','0x1006c'),(0x10044,'mov','0, %g3'),
                   (0x2c904,'save','%sp, -0x68, %sp'),(0x2c908,'ldub','[%i1+2], %i1'),
                   (0x2c910,'cmp','%g1, 0xc'),(0x2c914,'bgu','0x2c930'),
                   (0x2c924,'ld','[%o5+%g1], %o4'),(0x2c928,'jmp','%o4'),
                   (0x2bb80,'ldub','[%i0], %l0'),(0x2bb84,'cmp','%l0, 0x7e'),
                   (0x2bbc4,'cmp','%l0, 0x68'),(0x2bbec,'cmp','%l0, 0x3f'),
                   (0x2bbfc,'call','0x2b914')]:
        xs=list(sm.disasm(view[at:at+4],at))
        need(len(xs)==1 and (xs[0].mnemonic,xs[0].op_str)==(m,o),'candidate SPARC file instruction '+hex(at))
        sparc.append({'fileOffset':hex(at),'mnemonic':m,'operands':o})
    anchors=[]
    for text,at in [('get a interrupt from hdmi leon2',0x34a28),
                    ('APP_Mailbox_IPC_System_Read',0x3b918),
                    ('[HDMI 8051 Menu]',0xaae52)]:
        # Last anchor is visible without word-reversal, indicating multiple formats.
        data = image if text == '[HDMI 8051 Menu]' else view
        need(data[at:at+len(text)] == text.encode(), 'candidate text anchor '+hex(at))
        anchors.append({'fileOffset':hex(at),'view':'original'if data is image else 'reverse-each-4B',
                        'text':text})
    pltf,prd=census(P),census(Q)
    candidates = [x for x in pltf if 'micom-binary/' in x['path'] or x['path'].endswith('.ko')]
    need(not any(Path(x['path']).name == 'RMFMICOM_OCJP.bin' for x in pltf+prd), 'RMF basename unlocated in bounded extracted-root inventory')
    need(not (P/'opt/usr/apps/appbinarymanager/default/empOCJPsubmicom.img').exists(), 'override absent at exact extracted PLTF path')
    need(not (Q/'opt/usr/apps/appbinarymanager/default/empOCJPsubmicom.img').exists(), 'override absent at exact extracted PRD path')
    spans=[]
    for section,lo,hi,label in [
        ('.text',0x2b38,0x2b88,'reset sender'),
        ('.text',0x7d60,0x8248,'write frontend, conditional direct AHB versus queued mailbox'),
        ('.text',0x7b10,0x7c5c,'queue completion semantics'),
        ('.text',0x6758,0x6894,'message worker dispatches write helper'),
        ('.text',0x62d8,0x6758,'mailbox write framing and poll loop'),
        ('.text.unlikely',0x2c,0x488,'adapter/client initialization'),
        ('.text',0x1aaa0,0x1ab7c,'source checksum arithmetic'),
        ('.text',0x1b230,0x1b3cc,'LEON version byte reversal'),
        ('.text',0x1da60,0x1dd88,'fixed checksum read and streaming comparison'),
        ('.text',0x1e544,0x1e5ec,'layout selector and copied tables'),
        ('.text',0x1f420,0x1f710,'conditional board/product filename choice')]:
        s=e.get_section_by_name(section);data=s.data()[lo:hi]
        need(len(data)==hi-lo,'complete bounded source span')
        spans.append({'section':section,'sectionOffset':hex(lo),'fileOffset':s['sh_offset']+lo,
                      'bytes':len(data),'sha256':sha(data),'meaning':label})
    for filename in ('accepted-report.md','accepted-outcomes.json'):
        read(DB/filename)
    for directory in ('stock-mode2-reset-domain-20261028gz','rtp-fault-clear-paths-20261028gx'):
        read(B/directory/'README.md');read(B/directory/'source-inventory.json')
    result={'schema':'he-ocl-reset-receiver-map-v1','decision':'SOURCE_CANDIDATE_IDENTIFIED_RECEIVER_UNCLOSED',
        'checks':checks,'pins':pins,'sourceSpans':spans,'pltfFilenameInventory':pltf,
        'prdFilenameInventory':prd,'micomAndKernelCandidates':candidates,
        'sender':{'symbol':'sdp_ocl_reset_tcon_power','op':1,'command':63,'payloadBytes':1,
                  'argumentTruncatedToByte':True,'mailboxHeaderU32':hex(1 | 63<<8 | 1<<16),
                  'transportVariantLiveAttested':False,'adapterNumberLiveAttested':False,
                  'defaultMailboxAddressConditional':124,'sourceAddressHalvedForI2cTransfer':True},
        'loader':{'conditionalDefault':cstr(0x5488),'conditionalOverride':cstr(0x5448),
                  'namedPathsSelectedForReturnedSelector4InExaminedFunction':True,
                  'defaultBasenameLocatedInTwoExtractedRoots':False,
                  'appbinarymanagerOverrideLocatedAtExactExtractedPaths':False,
                  'PMDIsSelectedRuntimeFirmwareProven':False},
        'candidate':{'path':str((P/'etc/micom-binary/PMDMICOM_OCJP.bin').relative_to(ROOT)),
                     'bytes':len(image),'sha256':sha(image),'sourceFormatChecksumPass':True,
                     'checksum':'0xce93f188','checksumScopeEndExclusive':'0xdbff8',
                     'newLayoutSelector21BytesAllFF':True,'newLayoutRecords':layouts,
                     'versionDescriptor':{'fileBase':version[0],'offset':version[1],'bytes':version[2]},
                     'anchors':anchors,'sparcFileInstructions':sparc,
                     'encryptionRequiredForInspectedViews':False,
                     'cpuArchitectureIdentification':'SPARC/LEON code candidate plus distinct 8051-labelled component',
                     'fileToRuntimeAddressMapQualified':False,'incomingCommand3fHandlerIdentified':False,
                     'consoleQuestionMarkCaseIsResetReceiver':False},
        'limits':{'liveCalls':0,'oemExecutions':0,'binaryCopies':0,'resetDomainProven':False,
                  'sharedRootReinitializationProven':False,'exhaustiveReceiverAbsenceClaim':False}}
    return result

if __name__ == '__main__':
    print(json.dumps(main(),sort_keys=True,indent=2))
