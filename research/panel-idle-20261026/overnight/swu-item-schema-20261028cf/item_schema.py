"""Pure host bounded OUIT wire parser from pinned SWUCoreTV serializers.
No IO, crypto, target bindings, key selection, or execution of decoded data.
Bytes (salts/signatures/string bytes) stay in the returned in-memory tree.
Structural parsing is not authentication or firmware applicability validation.
"""
MAGIC=b'Tizen Software Upgrade Tree Binary Format ver. 1.9\x00'
NAMES={1:'OUUpgradeItemDesc',2:'OUGroupDesc',7:'OUDataProcessingDesc',10:'OUPartitionVersionDesc',11:'OUSWFileVersionDesc',14:'OUAESEncryptionDesc',16:'OURSAValidationDesc',18:'OUCRC32ValidationDesc',19:'OUGroupInfoDesc',21:'OUFirmwareVersionDesc',25:'OUSWImageVersionDesc',35:'OUMetadataDesc',53:'OUBDiffPatchDesc',55:'OUSecureDowngradeDesc',56:'OUWildcardInfoDesc',57:'OUXZCompressionDesc',58:'OUOSUpgradeDesc',59:'OUPostponeDesc',60:'OUMultiBDiffPatchDesc',61:'OUSWDeviceTypeDesc',62:'OUOSUpgradeBaseVersionDesc'}
class SchemaError(ValueError):pass
class Cursor:
 def __init__(self,data,base=0):self.data=memoryview(data).cast('B');self.pos=0;self.base=base
 @property
 def left(self):return len(self.data)-self.pos
 def take(self,n):
  if n<0 or n>self.left:raise SchemaError('truncated field at '+hex(self.base+self.pos))
  p=self.pos;self.pos+=n;return bytes(self.data[p:p+n])
 def num(self,n):return int.from_bytes(self.take(n),'little')
 def boolean(self):
  x=self.num(1)
  if x not in (0,1):raise SchemaError('noncanonical boolean')
  return bool(x)
 def string8(self):return self.take(self.num(1))
 def string16(self):return self.take(self.num(2))
 def string32(self):return self.take(self.num(4))
 def signed16(self):return int.from_bytes(self.take(2),'little',signed=True)
 def done(self):
  if self.left:raise SchemaError('descriptor/tree trailing bytes at '+hex(self.base+self.pos))
class Parser:
 def __init__(self,max_depth=16,max_nodes=1024):
  if type(max_depth) is not int or type(max_nodes) is not int or not 1<=max_depth<=64 or not 1<=max_nodes<=4096:raise SchemaError('invalid parser limits')
  self.max_depth=max_depth;self.max_nodes=max_nodes;self.nodes=0;self.unsupported=[]
 def children(self,c,depth):
  n=c.num(4)
  # Each entry consumes at least its one-byte presence flag.
  if n>c.left or n>self.max_nodes-self.nodes:raise SchemaError('child count bound')
  return [self.descriptor(c,depth+1) if c.boolean() else None for _ in range(n)]
 def descriptor(self,parent,depth):
  if depth>self.max_depth:raise SchemaError('nesting depth bound')
  self.nodes+=1
  if self.nodes>self.max_nodes:raise SchemaError('descriptor count bound')
  framing_offset=parent.base+parent.pos;length=parent.num(4)
  if length<5:raise SchemaError('descriptor shorter than tag+mandatory')
  start=parent.base+parent.pos;c=Cursor(parent.take(length),start);tag=c.num(4);mandatory=c.boolean()
  if tag not in NAMES and mandatory:raise SchemaError('unknown mandatory descriptor')
  d={'framing_offset':framing_offset,'body_offset':start,'body_length':length,'tag':tag,'type':NAMES.get(tag,'unknown_optional'),'mandatory':mandatory}
  if tag==1:
   d.update(item_id=c.num(4),item_type_raw=c.num(1),original_size=c.num(8),processed_size=c.num(8),optional_string_bytes=c.string16());d['children']=self.children(c,depth)
  elif tag==2:
   d['group_id']=c.num(4);d['children']=self.children(c,depth)
  elif tag in (7,58):d['children']=self.children(c,depth)
  elif tag in (10,11,61):d['string_bytes']=c.string8()
  elif tag in (21,35):d['first_string_bytes']=c.string8();d['second_string_bytes']=c.string8()
  elif tag==25:
   d.update(first_string_bytes=c.string8(),optional_string_bytes=c.string8(),field_50_i16=c.signed16(),field_54_i16=c.signed16())
  elif tag in (53,60):
   d.update(string_bytes=c.string8(),vector_bytes=c.string32(),field_40_i16=c.signed16(),field_44_i16=c.signed16())
   if tag==60:d['field_48_u32']=c.num(4)
  elif tag in (55,56):
   # The OEM converts this wire u64 through 376718/3768f4. Preserve raw bits.
   d['field_1c_wire_u64']=c.num(8)
   if tag==56:d.update(field_20_u32=c.num(4),string_bytes=c.string8())
   d['children']=self.children(c,depth)
  elif tag==59:
   d.update(first_string_bytes=c.string8(),optional_string_bytes=c.string16(),third_string_bytes=c.string8())
  elif tag==14:d['salt_bytes']=c.string8();d['processed_size']=c.num(8)
  elif tag==16:d['public_key_id']=c.num(4);d['signature_bytes']=c.string16()
  elif tag==18:d['crc32']=c.num(4)
  elif tag==19:d['group_id']=c.num(4)
  elif tag==57:d['field_1c_u32']=c.num(4);d['processed_size']=c.num(8)
  elif tag==62:
   n=c.num(4)
   if n>c.left//4:raise SchemaError('base-version pair count bound')
   d['version_pairs_raw']=[(c.num(2),c.num(2)) for _ in range(n)]
  else:
   self.unsupported.append({'tag':tag,'body_offset':start,'body_length':length,'mandatory':mandatory});d['opaque_remaining_bytes']=c.take(c.left)
  c.done();return d
 def tree(self,data):
  if not isinstance(data,(bytes,bytearray,memoryview)):raise SchemaError('input type/size bound')
  if (data.nbytes if isinstance(data,memoryview) else len(data))>65536:raise SchemaError('input type/size bound')
  c=Cursor(data)
  if c.take(len(MAGIC))!=MAGIC:raise SchemaError('OUIT magic')
  roots=self.children(c,0);c.done()
  return {'roots':roots,'descriptor_count':self.nodes,'unsupported_descriptors':self.unsupported,'wire_schema_complete':not self.unsupported,'full_schema_validated':False,'signature_authenticity_validated':False,'payload_validation_performed':False,'metadata_published':False}
def parse_ouit(data,*,max_depth=16,max_nodes=1024):return Parser(max_depth,max_nodes).tree(data)
def items(tree):
 """Walk numeric item descriptors without executing/interpreting item targets."""
 result=[]
 def walk(d):
  if d is None:return
  if d['tag']==1:result.append(d)
  for child in d.get('children',[]):walk(child)
 for root in tree['roots']:walk(root)
 return result

def reconcile_numeric_directory(tree,directory):
 """Compare numeric item IDs and lengths to caller-supplied clear records.
 Offset is a clear directory field, never guessed from an OUIT item size.
 Size equalities are observations; they do not assert which processing stage
 the clear length represents. No directory extent/overlap check is implied.
 No authentication or applicability flag is promoted by this comparison.
 """
 if not isinstance(directory,(list,tuple)) or len(directory)>1024:raise SchemaError('clear directory count/type bound')
 for r in directory:
  if not isinstance(r,dict):raise SchemaError('clear record type')
  for k in ('id','offset','length'):
   if type(r.get(k)) is not int or r[k]<0 or r[k]>0xffffffffffffffff:raise SchemaError('clear numeric field invalid')
 parsed=items(tree);ids=[d['item_id'] for d in parsed];clear_ids=[d['id'] for d in directory]
 if len(ids)!=len(set(ids)) or len(clear_ids)!=len(set(clear_ids)):raise SchemaError('duplicate numeric item ID')
 if set(ids)!=set(clear_ids):raise SchemaError('item ID set differs from clear directory')
 index={d['id']:d for d in directory};out=[]
 for d in parsed:
  record=index[d['item_id']]
  out.append({'id':d['item_id'],'clear_offset':record['offset'],'clear_length':record['length'],'original_size':d['original_size'],'processed_size':d['processed_size'],'clear_length_equals_original_size':record['length']==d['original_size'],'clear_length_equals_processed_size':record['length']==d['processed_size']})
 return out
