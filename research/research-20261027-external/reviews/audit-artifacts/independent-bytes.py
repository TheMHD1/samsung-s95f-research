#!/usr/bin/env python3
"""Independent local byte spotchecks. Does not import or run source verifiers."""
from pathlib import Path
import hashlib
import json
import struct
import subprocess
import zlib

ROOT = Path('${S95F_EVIDENCE_ROOT}')
OUT = ROOT / 'research-20261027-external/reviews/audit-artifacts'
OLD = ROOT / 'panel-idle-20261026/overnight'

def sha(b):
    return hashlib.sha256(b).hexdigest()

image = (OLD / 'kernel-Image.bin').read_bytes()
container = (OLD / 'kernel-uImage.bin').read_bytes()
fields = struct.unpack('>7I4B32s', container[:64])
header = bytearray(container[:64])
header[4:8] = b'\0' * 4
kernel = {
    'image_sha256': sha(image), 'uimage_sha256': sha(container),
    'image_bytes': len(image), 'container_bytes': len(container),
    'payload_is_original_uimage_suffix': image == container[64:],
    'uimage_magic': hex(fields[0]), 'uimage_size_field': fields[3],
    'uimage_header_crc_matches': zlib.crc32(header) == fields[1],
    'uimage_payload_crc_matches': zlib.crc32(container[64:]) == fields[6],
    'arm64_image_header_magic_at_0x38': image[0x38:0x3c].hex(),
    'IKCFG_ST_count': image.count(b'IKCFG_ST'),
    'syscall_rows': []
}
link = 0xffffffc010080000
for abi, table, nums in [('native', 0x7f07e0, [241, 280]), ('compat', 0x7f5028, [364, 386])]:
    for nr in nums:
        entry = table + nr * 8
        pointer = int.from_bytes(image[entry:entry+8], 'little')
        offset = pointer - link
        insn = int.from_bytes(image[offset:offset+4], 'little')
        # Decode move-wide-immediate encoding rather than accepting a byte label.
        imm16, hw, rd = (insn >> 5) & 0xffff, (insn >> 21) & 3, insn & 31
        movn64 = (insn & 0xff800000) == 0x92800000
        value = (~(imm16 << (16 * hw))) & ((1 << 64) - 1)
        signed = value - (1 << 64) if value >> 63 else value
        kernel['syscall_rows'].append({
            'abi': abi, 'number': nr, 'entry_offset': hex(entry),
            'pointer': hex(pointer), 'handler_offset': hex(offset),
            'bytes': image[offset:offset+8].hex(), 'is_MOVN_64': movn64,
            'destination': rd, 'decoded_signed_value': signed,
            'followed_by_RET_x30': image[offset+4:offset+8] == bytes.fromhex('c0035fd6')})
kernel['extra_numbering_anchor_offsets'] = {}
for name, n, c in [('read',63,3), ('close',57,6), ('getuid32',174,199), ('getppid',173,64)]:
    a = int.from_bytes(image[0x7f07e0+n*8:0x7f07e0+n*8+8], 'little')
    b = int.from_bytes(image[0x7f5028+c*8:0x7f5028+c*8+8], 'little')
    kernel['extra_numbering_anchor_offsets'][name] = {'native':hex(a-link), 'compat':hex(b-link),'same_handler':a==b}
(OUT/'independent-kernel.json').write_text(json.dumps(kernel, indent=2)+'\n')

for name, args in [('fresh-dispatch.disasm', ['-b','binary','-m','aarch64','-D','--start-address=0x18ec8','--stop-address=0x190f0',str(OLD/'kernel-Image.bin')]), ('fresh-stubs.disasm',['-b','binary','-m','aarch64','-D','--start-address=0x52388','--stop-address=0x52438',str(OLD/'kernel-Image.bin')])]:
    result = subprocess.run(['aarch64-linux-gnu-objdump',*args],check=True,capture_output=True,text=True)
    (OUT/name).write_text(result.stdout)
result = subprocess.run(['aarch64-linux-gnu-objdump','-b','binary','-m','aarch64','-D','--start-address=0','--stop-address=0x20000',str(OLD/'kernel-Image.bin')],check=True,capture_output=True,text=True)
callers = [line for line in result.stdout.splitlines() if '\tbl\t0x19040' in line or '\tbl\t0x190d0' in line]
(OUT/'fresh-entry-callers.txt').write_text('\n'.join(callers)+'\n')

prefix = (OLD/'samsung-official-T-RSMFAKUC-0090-msd-prefix.bin').read_bytes()
# Read individual little-endian words directly; no parser/verifier import.
def le(start, size):
    return int.from_bytes(prefix[start:start+size], 'little')
count = le(18,4)
rows = []
for i in range(count):
    p = 22 + i*20
    rows.append({'id':le(p,4), 'offset':le(p+4,8), 'length':le(p+12,8)})
p = 22 + count*20
header_count = le(p,4)
p += 4
h_offset, h_size, n_size = le(p,8), le(p+8,4), le(p+12,1)
label = prefix[p+13:p+13+n_size].decode('ascii')
descriptor_end = p+13+n_size
msd = {
    'prefix_sha256':sha(prefix), 'prefix_bytes':len(prefix),
    'magic':prefix[:6].decode('ascii'), 'count':count, 'rows':rows,
    'header_count':header_count, 'header_label':label, 'descriptor_end':descriptor_end,
    'header_offset':h_offset,'header_size':h_size,'header_end':h_offset+h_size,
    'header_marker_at_offset_plus_8':prefix[h_offset+8:h_offset+16].decode('ascii'),
    'encrypted_metadata_bytes_present':len(prefix[h_offset:h_offset+h_size]) == h_size,
    'descriptor_header_adjacent': descriptor_end == h_offset,
    'header_payload_adjacent': h_offset+h_size == rows[0]['offset'],
    'all_payloads_contiguous':all(a['offset']+a['length']==b['offset'] for a,b in zip(rows,rows[1:])),
    'last_payload_end':rows[-1]['offset']+rows[-1]['length']}
eu = json.loads((ROOT/'research-20261027-external/sources/hardware-firmware/tizenwled/tools/firmware/manifests/T-RSMFDEUC-0090-1296.8.json').read_text())
msd['eu_size_deltas'] = [e['size']-r['length'] for e,r in zip(eu['sections'],rows)]
# Recover the original ZIP central-directory record from the retained tail.
tail = (OLD/'samsung-official-firmware-archive.tail').read_bytes()
central = []
pos = 0
while True:
    pos = tail.find(b'PK\x01\x02',pos)
    if pos < 0:
        break
    filename_size = int.from_bytes(tail[pos+28:pos+30],'little')
    extra_size = int.from_bytes(tail[pos+30:pos+32],'little')
    comment_size = int.from_bytes(tail[pos+32:pos+34],'little')
    name = tail[pos+46:pos+46+filename_size].decode('utf-8')
    central.append({'name':name,'compressed_size':int.from_bytes(tail[pos+20:pos+24],'little'),
                    'uncompressed_size':int.from_bytes(tail[pos+24:pos+28],'little'),
                    'crc32_declared_not_verified':hex(int.from_bytes(tail[pos+16:pos+20],'little'))})
    pos += 46+filename_size+extra_size+comment_size
msd['zip_msd_record'] = next(e for e in central if e['name']=='T-RSMFAKUC-0090/image/upgrade.msd')
msd['directory_end_equals_original_zip_record'] = msd['last_payload_end']==msd['zip_msd_record']['uncompressed_size']
zip_prefix = (OLD/'samsung-official-T-RSMFAKUC-0090-msd-prefix.range').read_bytes()
name_size, extra_size = struct.unpack_from('<HH',zip_prefix,26)
inflate = zlib.decompressobj(-15)
decoded = inflate.decompress(zip_prefix[30+name_size+extra_size:])
msd['reinflate_original_retained_zip_range_matches_prefix'] = decoded == prefix
msd['whole_zip_entry_crc_verified'] = False
(OUT/'independent-msd.json').write_text(json.dumps(msd,indent=2)+'\n')

module = ROOT/'panel-idle-20261026/binaries/qdf_tcon.ko'
meta = subprocess.run(['readelf','-h','-n','-S','-W',str(module)],check=True,capture_output=True,text=True).stdout
meta += subprocess.run(['readelf','-p','.modinfo','-x','.gnu_debuglink',str(module)],check=True,capture_output=True,text=True).stdout
(OUT/'fresh-qdf-readelf.txt').write_text('SHA256 '+sha(module.read_bytes())+'\n'+meta)
print(json.dumps({'kernel':kernel,'msd':msd,'entry_callers':callers},indent=2))
