#!/usr/bin/env python3
"""Offline correction for the exact QDF legacy mute-read command form."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct

HERE=Path(__file__).resolve().parent
DECODER=HERE/'decode-qd-trace.py'
QDF=HERE.parent/'binaries/qdf_tcon.ko'

def static_proof():
    data=QDF.read_bytes()
    if hashlib.sha256(data).hexdigest()!='97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63':
        raise ValueError('exact QDF input changed')
    if data[:6]!=b'\x7fELF\x02\x01': raise ValueError('ELF64 little endian')
    shoff=struct.unpack_from('<Q',data,40)[0]
    entsize,count,strindex=struct.unpack_from('<HHH',data,58)
    if entsize!=64: raise ValueError('section header size')
    headers=[struct.unpack_from('<IIQQQQIIQQ',data,shoff+i*64) for i in range(count)]
    sh=headers[strindex]; names=data[sh[4]:sh[4]+sh[5]]
    selected=[h for h in headers if names[h[0]:].split(b'\0',1)[0]==b'.text']
    if len(selected)!=1: raise ValueError('unique text section')
    sh=selected[0]; text=data[sh[4]:sh[4]+sh[5]]
    actual=struct.unpack_from('<6I',text,0xcf98)
    expected=(0x9100c3e1,0x52801fe2,0xd2802c80,0xb90033e2,0xf2de6000,0x97fff2f7)
    if actual!=expected: raise ValueError('bounded mute-read instructions changed')
    imm=actual[-1]&0x3ffffff
    if imm&(1<<25):imm-=1<<26
    target=0xcfac+4*imm
    if target!=0x9b88:raise ValueError('read helper target')
    command=((actual[2]>>5)&0xffff)|(((actual[4]>>5)&0xffff)<<32)
    if command!=0xf30000000164: raise ValueError('read command derivation')
    return dict(module_sha256=hashlib.sha256(data).hexdigest(),section='.text',
                instruction_start='0xcf98',read_call='0xcfac',read_helper='0x9b88',
                command_hex=f'{command:012x}',output_initial_word=255)

def readback(tx):
    if not (tx.get('structurally_complete') is True and tx.get('bus')==5 and
            tx.get('n')==2 and tx.get('ret')==2 and not tx.get('issues')):return None
    messages=tx.get('messages',[])
    if len(messages)!=2:return None
    a,b=messages
    if not (a.get('direction')=='write' and a.get('length')==6 and
            a.get('address')==b.get('address')==118 and a.get('write_hex')=='f30000000164'
            and b.get('direction')=='read' and b.get('length')==4
            and re.fullmatch('[0-9a-f]{8}',b.get('reply_hex',''))):return None
    return dict(time=tx['start_time'],end_time=tx['end_time'],task=tx['task'],pid=tx['pid'],
                command_hex=a['write_hex'],reply_hex=b['reply_hex'],
                returned_word=int(b['reply_hex'],16),
                interpretation='stock QDF mute-status read form; not measured light')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trace',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    proof=static_proof()
    if hashlib.sha256(DECODER.read_bytes()).hexdigest()!='cc69c38cb78c94b3e044dc546ce1d0d6328b0c2f5aace308499ead0baf375be3':
        raise ValueError('original decoder changed')
    s=importlib.util.spec_from_file_location('preserved_qd_decoder',DECODER);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    raw=a.trace.read_bytes(); original=m.decode(raw.decode('utf-8'),hashlib.sha256(raw).hexdigest())
    reads=[value for tx in original['transfers'] if (value:=readback(tx)) is not None]
    report=dict(static_proof=proof,trace_sha256=original['source_sha256'],
                ring_accounting_complete=original['ring_accounting_complete'],
                raw_parse_errors=original['parse_errors'],mute_readbacks=reads,
                original_decoder_unchanged=True,
                qualification='This corrects one command shape only. Does not accept the failed capture, identify physical onset, or establish emission/MCU health.')
    with a.out.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
