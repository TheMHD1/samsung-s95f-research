"""Read-only reproduction of exact uImage CRC, byte identity and PREL32 checks."""
from pathlib import Path
import hashlib
import json
import struct
import zlib

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
SOURCE=Path('/home/researcher/.local/state/s95f-live-trials/swu-cn-01/uImage')
def need(ok,reason):
    if not ok:raise ValueError(reason)
def main():
    raw=SOURCE.read_bytes()
    need(len(raw)==11892528 and hashlib.sha256(raw).hexdigest()=='131aa441564f1bd1db019f5284c6f115e1e667e3a7a570407389633105209350','original source pin')
    h=struct.unpack('>7I4B32s',raw[:64]);need(h[0]==0x27051956 and h[3]==11786752,'uImage bounds')
    header=bytearray(raw[:64]);header[4:8]=b'\0'*4
    need(zlib.crc32(header)==h[1],'header CRC');image=raw[64:64+h[3]];need(zlib.crc32(image)==h[6],'data CRC')
    need(image==(BASE/'kernel-Image.bin').read_bytes(),'previous payload identity')
    need(raw[:64+h[3]]==(BASE/'kernel-uImage.bin').read_bytes(),'previous declared uImage identity')
    need(image==(HERE/'private/kernel-Image.bin').read_bytes(),'private extracted payload identity')
    need(raw[64+h[3]:]==(HERE/'private/appended.bin').read_bytes(),'private appended identity')
    index_bytes=(BASE/'kernel-export-index.json').read_bytes()
    need(hashlib.sha256(index_bytes).hexdigest()=='6d3ffe0edfd2ab92fc4439ffe35371db4c3f2ad8a99cf5b2b20ae2ef4eb937ac','index pin')
    rows=json.loads(index_bytes)['exports'];need(len(rows)==9379,'index count')
    for row in rows:
        p=int(row['entry_file_offset'],16);target,name,ns=struct.unpack_from('<iii',image,p);namep=p+4+name;end=image.index(b'\0',namep)
        need(hex(p+target)==row['target_image_offset'] and image[namep:end].decode()==row['name'] and ns==0,'export record')
    print(json.dumps({'header_crc_valid':True,'data_crc_valid':True,'previous_declared_uimage_equal':True,'export_records_revalidated':len(rows),'target_operations':0}))
if __name__=='__main__':main()
