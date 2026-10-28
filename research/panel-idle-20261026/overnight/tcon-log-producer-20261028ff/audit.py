#!/usr/bin/env python3
"""Finite, host-only source audit of the TCON-info boot-register handoff."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
from elftools.elf.elffile import ELFFile
HERE=Path(__file__).resolve().parent
B=HERE.parent
checks=0

def need(ok,label):
    global checks
    checks+=1
    if not ok: raise ValueError(label)

def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    pins=json.loads((HERE/'input-pins.json').read_text())
    for p in pins['inputs']:
        data=(B/p['path']).read_bytes()
        need(len(data)==p['bytes'] and sha(data)==p['sha256'],'pin '+p['path'])
    module=B/'firmware-platform-analysis-20261028db/private/pltf-extracted/tree/root/lib/modules/5.4.261/kernel/soc/sdp_tcon.ko'
    elf=ELFFile(BytesIO(module.read_bytes()))
    need(elf['e_machine']=='EM_AARCH64' and elf.little_endian,'module architecture')
    text=elf.get_section_by_name('.text').data()
    data=elf.get_section_by_name('.data').data()
    md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
    def ins(a,m,ops):
        decoded=list(md.disasm(text[a:a+4],a))
        need(len(decoded)==1 and decoded[0].mnemonic==m and decoded[0].op_str==ops,'instruction '+hex(a))
    def relocation(section,offset):
        rs=elf.get_section_by_name(section)
        sym=elf.get_section(rs['sh_link'])
        matches=[r for r in rs.iter_relocations() if r['r_offset']==offset]
        need(len(matches)==1,'relocation '+hex(offset))
        r=matches[0];s=sym.get_symbol(r['r_info_sym'])
        target=elf.get_section(s['st_shndx']).name if isinstance(s['st_shndx'],int) else None
        return s.name,target,s['st_value']+r['r_addend'],r['r_info_type']
    def call(a,name,target):
        r=relocation('.rela.text',a)
        need(r[0]==name and r[2]==target and r[3]==283,'call '+hex(a))
    rows=[]
    for index in range(4):
        off=0x1e0+index*0x48
        name=data[off:].split(b'\0',1)[0].decode('ascii')
        rows.append({'index':index,'data_offset':off,'name':name,'physical_high_cell':off+52,'physical_low_cell':off+56,'bytes_cell':off+60,'dma_slot':off+64})
    need([r['name'] for r in rows]==['samsung,tcon-y','samsung,tcon-c','samsung,demura','samsung,tcon_info'],'resource row identities')
    need(relocation('.rela.text',0x970)[1:3]==('.data',0),'parser table base')
    for a,m,ops in [
      (0x97c,'add','x23, x24, #0x1e0'),(0x9a0,'add','x2, x23, #0x34'),
      (0x9b0,'mov','x3, #3'),(0xa4c,'add','x23, x23, #0x48'),
      (0x9c0,'ldp','w1, w0, [x23, #0x34]'),(0x9cc,'orr','x1, x0, x1, lsl #32'),
      (0xa08,'str','x4, [x23, #0x40]'),(0xa58,'add','x0, x24, #0x1e0'),
      (0xa5c,'str','x0, [x19, #0x3a8]'),
      (0xc84,'ldr','w1, [x24, #0x2f0]'),(0xc8c,'ldr','w20, [x24, #0x2ec]'),
      (0xc94,'orr','x20, x1, x20, lsl #32'),(0xcc8,'add','x1, x20, #0xa0, lsl #12'),
      (0xcd0,'mov','x2, #0x20000'),(0xcd8,'str','x0, [x19, #0x378]'),
      (0x2b0c,'mov','x21, x0'),(0x2b30,'add','x23, x21, #0x508'),
      (0x2bac,'mov','w20, #1'),(0x2bf0,'cmp','x0, #0'),
      (0x2bf4,'ccmp','w20, #0, #4, ne'),(0x2bf8,'b.eq','#0x2c40'),(0x2bfc,'dmb','oshst'),
      (0x2c00,'ldr','x1, [x21, #0x3a8]'),(0x2c04,'ldr','x0, [x19, #0x68]'),
      (0x2c08,'ldr','x1, [x1, #0xd0]'),(0x2c0c,'add','x0, x0, #4'),(0x2c10,'str','w1, [x0]'),
      (0x2c14,'dmb','oshst'),(0x2c18,'ldr','x1, [x21, #0x3a8]'),
      (0x2c1c,'ldr','x0, [x19, #0x68]'),(0x2c20,'ldr','x1, [x1, #0x118]'),
      (0x2c24,'add','x0, x0, #8'),(0x2c28,'str','w1, [x0]'),
      (0x2c2c,'dmb','oshst'),(0x2c30,'mov','w0, #0x5678'),
      (0x2c34,'movk','w0, #0x1234, lsl #16'),(0x2c38,'ldr','x1, [x19, #0x68]'),
      (0x2c3c,'str','w0, [x1]'),(0x2c98,'mov','w20, #0'),
      (0x2ccc,'mov','x0, #0x654'),(0x2cd0,'mov','x1, #0x10'),
      (0x2cd4,'movk','x0, #0x9d, lsl #16'),(0x2ce0,'str','x0, [x19, #0x68]'),
      (0x4938,'dmb','oshst'),(0x493c,'str','w1, [x0]'),
      (0x61c8,'ldr','x23, [x0, #0x378]'),(0x61cc,'ldrh','w20, [x23]')]:
        ins(a,m,ops)
    need(relocation('.rela.text',0x9b4)[0]=='of_property_read_variable_u32_array','DT parser call')
    need(relocation('.rela.text',0xcd4)[0]=='devm_ioremap_nocache','log map call')
    need(relocation('.rela.text',0x2cd8)[0]=='__ioremap','boot register mapping')
    call(0x2bb4,'sdp_tcon_dev_POWER_ON',0x4d88)
    need(relocation('.rela.text',0x4dc8)[0]=='sdp_set_clkrst_mux','clock/reset call')
    need(relocation('.rela.text',0x4e04)[0]=='sdp_set_clkrst_mux','clock/reset second table')
    call(0x2ef4,'tcon_ctrl_tcon_micom',0x2af0)
    call(0x2f70,'tcon_ctrl_tcon_micom',0x2af0)
    need(2*0x48+64==0xd0 and 3*0x48+64==0x118,'handoff slots resolve to row2/row3 DMA')
    # Explicitly model the actual 32-bit store, without equating DMA to physical.
    def handoff(dma2,dma3):
        need(type(dma2) is int and type(dma3) is int and 0<=dma2<1<<64 and 0<=dma3<1<<64,'DMA model domain')
        return {'0x9d0658':dma2&0xffffffff,'0x9d065c':dma3&0xffffffff,'0x9d0654':0x12345678}
    cases=[(0,0),(0xffffffff,0x100000000),(0x15fc00000,0x15fe00000),(0xffffffffffffffff,0xabcdef0102030405)]
    for a,b in cases:
        mapped=handoff(a,b)
        need(mapped['0x9d065c']==b%(1<<32),'low32 handoff')
        need(mapped['0x9d0658']==a%(1<<32),'independent row2')
    need(handoff(0,0x15fe00000)['0x9d065c']!=0x15fe00000,'no full64-bit handoff inference')
    tree=json.loads((B/'firmware-kernel-analysis-20261028cs/private/dtb-01.json').read_text())
    def walk(x):
        if isinstance(x,dict):
            yield x
            for v in x.values(): yield from walk(v)
        elif isinstance(x,list):
            for v in x: yield from walk(v)
    prop=[x for x in walk(tree) if x.get('name')=='samsung,tcon_info' and 'cells' in x]
    need(len(prop)==1 and prop[0]['cells']==[1,0x5fe00000,0x100000],'candidate DTB resource')
    need(0x15fe00000+0xa0000==0x15fea0000,'candidate DTB physical mapping arithmetic')
    ranges=[(0x920,0xa58),(0xc84,0xce0),(0x2af0,0x2e3c),(0x2e40,0x2fd0),(0x4d88,0x4e20),(0x4938,0x4944),(0xdf8,0x1018),(0x61b0,0x634c)]
    spans=[{'domain':'sdp_tcon.ko:.text','start':a,'end_exclusive':z,'sha256':sha(text[a:z])} for a,z in ranges]
    result={'schema':'ff-log-producer-source-audit-v1','checks':checks,'resource_rows':rows,'source_spans':spans,
      'handoff':{'function_text':0x2af0,'clock_reset_function_text':0x4d88,'destination_physical_registers':[0x9d0658,0x9d065c,0x9d0654],'value_source':'low32 of resource DMA slots2/3, then magic0x12345678','conditional_on_non_skip_path':True,'physical_equals_dma_proven':False,'actual_runtime_execution_proven':False},
      'log_map':{'resource_index':3,'physical_offset':0xa0000,'bytes':0x20000,'stored_device_offset':0x378},
      'firmware_instruction_producer_identified':False,'internal_boot_control_handoff_identified':True,'external_controller_proxy_excluded':False,'target_network_root_calls':0}
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
