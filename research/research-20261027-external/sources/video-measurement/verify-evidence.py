#!/usr/bin/env python3
# Checks retained static evidence only. No target/native-library invocation.
import pathlib,hashlib,json,sys,re
HERE=pathlib.Path(__file__).resolve().parent
for filename in ['target-binary-pins.json','kernel-binary-pins.json']:
 for row in json.loads((HERE/filename).read_text()):
  assert hashlib.sha256(pathlib.Path(row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
slots=json.loads((HERE/'backend-slot-resolution.json').read_text())
assert [r['got_relocation_symbol'] for r in slots]==['impl_get_rgb_measure_condition','impl_set_rgb_measure_position','impl_get_rgb_measure_pixel']
t=(HERE/'libave.so.0.1.rgb.disasm.txt').read_text()
for line in ['002466e8','002466f4','002466fc','0024675e','0024678e','00246790','002464a4','002464b6']:
 assert line in t,line
assert re.search(r'0024678e\s+\w+\s+b\s+#0x2466f0',t)
assert re.search(r'002466f4\s+\w+\s+strd\s+r0, r1, \[r4\]',t)
assert re.search(r'002466fc\s+\w+\s+strd\s+r2, r3, \[r4, #8\]',t)
for request_low in ['#0x6672','#0x6673','#0x6674']:
 assert request_low in t
k=(HERE/'rosem_frc.ko.rgb.disasm.txt').read_text()
for n in ['m_rosem_get_rgb_measure_conditon','RosemFrc_GetRgbMeasureInfo','RosemFrc_SetRgbMeasurePostion','tztv_frc_tcon_ext_cmd','#0x400']:
 assert n in k,n
print('PASS: pinned inputs, exact backend slots, 16-byte caller copies including negative-return path, ioctl request low words, kernel dedicated command edge')
