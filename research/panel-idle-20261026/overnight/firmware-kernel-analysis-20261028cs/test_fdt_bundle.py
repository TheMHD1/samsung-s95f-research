import struct
import unittest
import fdt_bundle as f

def fixture():
    # Independent tiny FDT: root with one child and one u32 property.
    s=struct.pack('>I',1)+b'\0'*4
    s+=struct.pack('>I',1)+b'gpio\0'+b'\0'*3
    s+=struct.pack('>III',3,4,0)+struct.pack('>I',42)
    s+=struct.pack('>III',2,2,9)
    strings=b'phandle\0'
    return bytearray(struct.pack('>10I',0xd00dfeed,56+len(s)+len(strings),56,56+len(s),40,17,16,0,len(strings),len(s))+b'\0'*16+s+strings)

class Tests(unittest.TestCase):
    def test_offsets_and_values(self):
        d=fixture();t=f.parse(d,0);self.assertEqual([n['path'] for n in t['nodes']],['/','/gpio']);p=t['nodes'][1]['properties'][0]
        self.assertEqual(p['name'],'phandle');self.assertEqual(p['cells'],[42]);self.assertEqual(d[p['source_offset']:p['source_offset']+4],b'\0\0\0*')
    def test_nonzero_bundle_base(self):
        t=f.parse(b'x'*16+fixture(),16);self.assertEqual(t['bundle_offset'],16);self.assertEqual(t['nodes'][1]['path'],'/gpio')
    def test_truncation(self):
        with self.assertRaises(ValueError):f.parse(fixture()[:-1],0)
    def test_bad_structure_token(self):
        d=fixture();struct.pack_into('>I',d,56,5)
        with self.assertRaises(ValueError):f.parse(d,0)
    def test_property_outside_strings(self):
        d=fixture();struct.pack_into('>I',d,84,999999)
        with self.assertRaises(ValueError):f.parse(d,0)
    def test_blocks_overlap(self):
        d=fixture();struct.pack_into('>I',d,12,56)
        with self.assertRaises(ValueError):f.parse(d,0)
    def test_version(self):
        d=fixture();struct.pack_into('>I',d,20,18)
        with self.assertRaises(ValueError):f.parse(d,0)
    def test_pinned_bundle(self):
        data=f.SOURCE.read_bytes();self.assertEqual(f.hashlib.sha256(data).hexdigest(),f.SOURCE_SHA)
        trees=[f.parse(data,m.start()) for m in f.re.finditer(b'\xd0\x0d\xfe\xed',data)];self.assertEqual(len(trees),10)
        one=trees[1];chosen=next(n for n in one['nodes'] if n['path']=='/chosen');args=next(p for p in chosen['properties'] if p['name']=='bootargs')
        self.assertTrue(args['strings'][0].startswith('dtsversion=13781814_1_rosem-2.75G-oc '))
        node=next(n for n in one['nodes'] if n['path']=='/tztv_frc_tcon');err=next(p for p in node['properties'] if p['name']=='samsung,err_det');self.assertEqual(err['cells'],[54,5,0]);self.assertEqual(err['source_offset'],0x2421c)

if __name__=='__main__':unittest.main()
