"""Strict bounded offline FDT bundle reader. OEM tree copies stay private."""
from pathlib import Path
import hashlib
import json
import os
import re
import struct

SOURCE = Path('${S95F_EVIDENCE_ROOT}/firmware-extracted-20261028/dtb.bin')
SOURCE_SHA = '5021c20fba8b6b04303faf5b02a8132071e94b6e834498878b895bf9e0a00396'
HERE = Path(__file__).resolve().parent

def need(ok, reason):
    if not ok: raise ValueError(reason)

def parse(data, base):
    need(base+40<=len(data), 'header bounds')
    h=struct.unpack_from('>10I', data, base)
    magic,size,st,ss,rs,version,last,boot,strings_size,structure_size=h
    need(magic==0xd00dfeed and 40<=size<=262144 and base+size<=len(data), 'extent')
    need(version==17 and last<=17 and rs>=40 and rs+16<=size, 'version/reserve')
    need(st%4==0 and st>=40 and ss>=40 and st+structure_size<=size and ss+strings_size<=size, 'block bounds')
    need(st+structure_size<=ss or ss+strings_size<=st, 'block overlap')
    reserve=rs
    while True:
        need(reserve+16<=size,'reserve end');address,length=struct.unpack_from('>QQ',data,base+reserve);reserve+=16
        if not address and not length:break
    strings=data[base+ss:base+ss+strings_size]
    p=st;end=st+structure_size;stack=[];nodes=[];ended=False
    while p<end:
        need(p+4<=end,'token bounds');token=struct.unpack_from('>I',data,base+p)[0];p+=4
        if token==1:
            terminator=data.find(b'\0',base+p,base+end);need(terminator>=0,'node name')
            raw=data[base+p:terminator];need(len(raw)<=255 and b'/' not in raw,'node name bound')
            name=raw.decode('ascii');p=(terminator-base+4)&~3
            need(len(stack)<128 and len(nodes)<4096,'tree bound')
            path=('/'+'/'.join([n['name'] for n in stack[1:]]+[name])) if stack else '/'
            node={'name':name,'path':path,'properties':[]};nodes.append(node);stack.append(node)
        elif token==2:
            need(bool(stack),'unmatched node end');stack.pop()
        elif token==3:
            need(stack and p+8<=end,'property header');length,nameoff=struct.unpack_from('>II',data,base+p);p+=8
            need(length<=65536 and p+length<=end and nameoff<len(strings),'property bounds')
            z=strings.find(b'\0',nameoff);need(z>=0 and z-nameoff<=255,'property name')
            name=strings[nameoff:z].decode('ascii');need(not any(x['name']==name for x in stack[-1]['properties']),'duplicate property')
            value=data[base+p:base+p+length]
            prop={'name':name,'source_offset':base+p,'length':length,'hex':value.hex()}
            if value and value[-1]==0 and all(32<=x<127 or x==0 for x in value):prop['strings']=[x.decode('ascii') for x in value[:-1].split(b'\0')]
            if length%4==0:prop['cells']=list(struct.unpack('>'+str(length//4)+'I',value))
            stack[-1]['properties'].append(prop);p=(p+length+3)&~3
        elif token==4:pass
        elif token==9:
            need(not stack,'unclosed nodes');ended=True;break
        else:raise ValueError('unknown structure token')
    need(ended and nodes and nodes[0]['path']=='/','tree completeness')
    return {'bundle_offset':base,'total_size':size,'sha256':hashlib.sha256(data[base:base+size]).hexdigest(),'nodes':nodes}

def main():
    data=SOURCE.read_bytes();need(hashlib.sha256(data).hexdigest()==SOURCE_SHA,'source pin')
    private=HERE/'private';need(private.stat().st_mode & 0o777==0o700,'private mode')
    trees=[]
    for match in re.finditer(b'\xd0\x0d\xfe\xed',data):trees.append(parse(data,match.start()))
    need(len(trees)==10,'exact tree count')
    for i,tree in enumerate(trees):
        for name,content in [(f'dtb-{i:02}.bin',data[tree['bundle_offset']:tree['bundle_offset']+tree['total_size']]),(f'dtb-{i:02}.json',(json.dumps(tree,indent=2)+'\n').encode())]:
            fd=os.open(private/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'wb') as f:f.write(content)
    print(json.dumps({'trees':len(trees),'source_pin_valid':True,'target_operations':0}))

if __name__=='__main__':main()
