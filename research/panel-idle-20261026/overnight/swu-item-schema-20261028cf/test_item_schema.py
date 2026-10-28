import unittest,struct
from item_schema import *
def u(n,w=4):return n.to_bytes(w,'little')
def desc(tag,b=b'',mandatory=1):
 body=u(tag)+u(mandatory,1)+b;return u(len(body))+body
def children(*ds):return u(len(ds))+b''.join(b'\x00' if d is None else b'\x01'+d for d in ds)
def tree(*ds):return MAGIC+children(*ds)
def item(n=1001,size=48,ds=()):return desc(1,u(n)+b'\x03'+u(32,8)+u(size,8)+u(4,2)+b'test'+children(*ds))
class Tests(unittest.TestCase):
 def test_nested(self):
  b=tree(desc(2,u(7)+children(item(ds=[desc(7,children(desc(14,b'\x08'+b'synthetic'+u(48,8)),desc(18,u(0x12345678))))]))))
  # Deliberate 9-byte salt with length8 is malformed; exact consumption matters.
  with self.assertRaises(SchemaError):parse_ouit(b)
  b=tree(desc(2,u(7)+children(item(ds=[desc(7,children(desc(14,b'\x08'+b'saltsalt'+u(48,8)),desc(18,u(0x12345678))))]))))
  t=parse_ouit(b);self.assertEqual(items(t)[0]['item_id'],1001);self.assertEqual(t['descriptor_count'],5);self.assertTrue(t['wire_schema_complete']);self.assertFalse(t['full_schema_validated'])
 def test_leaf_layouts(self):
  ds=[desc(10,b'\x03abc'),desc(11,b'\x00'),desc(61,b'\x01X'),desc(21,b'\x01A\x01B'),desc(35,b'\x00\x00'),desc(16,u(2)+u(2,2)+b'xy'),desc(19,u(5)),desc(57,u(3)+u(55,8)),desc(62,u(2)+u(1,2)+u(2,2)+u(3,2)+u(4,2)),desc(58,children(None))]
  t=parse_ouit(tree(*ds));self.assertTrue(t['wire_schema_complete']);self.assertEqual(t['descriptor_count'],10);self.assertEqual(t['roots'][5]['public_key_id'],2);self.assertEqual(t['roots'][5]['signature_bytes'],b'xy')
 def test_optional_unknown(self):
  t=parse_ouit(tree(desc(999,b'xyz',0)));self.assertFalse(t['wire_schema_complete']);self.assertEqual(len(t['unsupported_descriptors']),1)
 def test_remaining_layouts(self):
  ds=[desc(25,b'\x01A\x01B'+b'\xff\xff\x00\x80'),desc(53,b'\x01X'+u(2)+b'YZ'+u(1,2)+u(2,2)),desc(55,u(17,8)+children(None,desc(18,u(3)))),desc(56,u(18,8)+u(19)+b'\x01W'+children()),desc(59,b'\x01A'+u(1,2)+b'B'+b'\x01C'),desc(60,b'\x00'+u(0)+u(1,2)+u(2,2)+u(3))]
  t=parse_ouit(tree(*ds));self.assertTrue(t['wire_schema_complete']);self.assertFalse(t['full_schema_validated']);self.assertFalse(t['metadata_published']);self.assertEqual(t['roots'][0]['field_50_i16'],-1);self.assertEqual(t['roots'][0]['field_54_i16'],-32768)
  for d in ds:
   for i in range(len(d)):
    with self.assertRaises(SchemaError):parse_ouit(tree(d[:i]))
   with self.assertRaises(SchemaError):parse_ouit(tree(u(len(d)-3)+d[4:]+b'X'))
 def test_reconcile(self):
  t=parse_ouit(tree(item()));r=reconcile_numeric_directory(t,[{'id':1001,'offset':4290,'length':48}])[0];self.assertEqual(r['clear_offset'],4290);self.assertTrue(r['clear_length_equals_processed_size']);self.assertFalse(r['clear_length_equals_original_size'])
  self.assertFalse(reconcile_numeric_directory(t,[{'id':1001,'offset':0,'length':47}])[0]['clear_length_equals_processed_size'])
 def test_bad_reconcile(self):
  for d in [[{'id':1002,'offset':0,'length':48}],[{'id':1001,'offset':0,'length':True}],[{'id':1001,'offset':-1,'length':48}],[{'id':1001,'offset':0,'length':48}]*2]:
   with self.assertRaises(SchemaError):reconcile_numeric_directory(parse_ouit(tree(item())),d)
  with self.assertRaises(SchemaError):reconcile_numeric_directory(parse_ouit(tree(item(),item())),[])
 def test_truncations(self):
  b=tree(item(ds=[desc(14,b'\x08saltsalt'+u(48,8))]))
  for i in range(len(b)):
   with self.assertRaises(SchemaError):parse_ouit(b[:i])
 def test_malformed(self):
  cases=[b'X'*len(MAGIC)+u(0),MAGIC+u(0xffffffff),tree(desc(999,b'x')),tree(desc(18,u(1),2)),tree(desc(18,u(1))+b'x'),tree(u(4)+u(18)),tree(desc(18,u(1)))+b'x',tree(desc(14,b'\xffx')),tree(desc(62,u(0xffffffff))),tree(desc(1,u(1)+b'\0'+u(0,8)*2+u(0xffff,2))) ]
  for b in cases:
   with self.assertRaises(SchemaError):parse_ouit(b)
 def test_depth(self):
  d=desc(18,u(0))
  for _ in range(18):d=desc(7,children(d))
  with self.assertRaises(SchemaError):parse_ouit(tree(d))
 def test_nodes(self):
  with self.assertRaises(SchemaError):parse_ouit(tree(desc(7,children(desc(18,u(0)),desc(18,u(0))))),max_nodes=2)
 def test_limits(self):
  import array
  for b in (b'X'*65537,memoryview(array.array('I',[0]*16385)),object()):
   with self.assertRaises(SchemaError):parse_ouit(b)
  for kw in ({'max_depth':True},{'max_nodes':0},{'max_depth':65},{'max_nodes':4097}):
   with self.assertRaises(SchemaError):parse_ouit(tree(),**kw)
if __name__=='__main__':unittest.main()
