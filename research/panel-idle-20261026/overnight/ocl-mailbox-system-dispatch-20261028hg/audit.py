#!/usr/bin/env python3
"""Read-in-place SPARC source map and bounded actual-instruction oracle.

No target imports, no OEM execution, no image writes. Source PCs are linked PCs,
not evidence of live execution. All emitted firmware coordinates are metadata.
"""
import hashlib, importlib.util, io, json, struct, sys, zlib
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
B = HERE.parent
ROOT = B.parent
P = B/'firmware-platform-analysis-20261028db/private/pltf-extracted/tree/root'
checks = 0
pins = []
def need(v, why):
    global checks
    if not v:
        raise ValueError(why)
    checks += 1
def sha(b):
    return hashlib.sha256(b).hexdigest()
def read(p, expected=None):
    need(p.is_file() and not p.is_symlink(), 'ordinary source input '+p.name)
    b=p.read_bytes()
    need(expected is None or sha(b)==expected, 'source identity '+p.name)
    pins.append({'path':str(p.relative_to(ROOT)), 'bytes':len(b), 'sha256':sha(b)})
    return b
def header(component):
    """Pure legacy-header validation; retain sizes, never export payload."""
    if len(component)<64:
        raise ValueError('short header')
    magic,hcrc,timestamp,size,load,entry,dcrc=struct.unpack_from('>7I',component)
    if magic!=0x27051956 or size>len(component)-64:
        raise ValueError('magic/length')
    h=bytearray(component[:64]);h[4:8]=b'\0'*4
    if zlib.crc32(h)!=hcrc or zlib.crc32(component[64:64+size])!=dcrc:
        raise ValueError('header/data CRC')
    return {'magic':hex(magic),'headerCrc32':hex(hcrc),'timestamp':timestamp,
            'payloadBytes':size,'load':hex(load),'entry':hex(entry),'dataCrc32':hex(dcrc),
            'osId':component[28],'architectureId':component[29],
            'imageTypeId':component[30],'compressionId':component[31],
            'name':component[32:64].split(b'\0',1)[0].decode('ascii')}
def main():
    sys.path.insert(0,'/tmp/tcon-capstone')
    from capstone import Cs, CS_ARCH_SPARC, CS_MODE_BIG_ENDIAN
    from elftools.elf.elffile import ELFFile
    he=read(B/'ocl-reset-receiver-map-20261028he/audit.py',
            '03ddc30de36fc002ca1057fbbfdb989413b91f375149074480bbba23f6616f89')
    sp=importlib.util.spec_from_file_location('frozen_he',B/'ocl-reset-receiver-map-20261028he/audit.py')
    helper=importlib.util.module_from_spec(sp);sp.loader.exec_module(helper)
    read(B/'ocl-reset-receiver-map-20261028he/source-inventory.json',
         '55712bbc11905098ff7cdc3d3b0cd7b714a818b5490fa26361c5638d3e5cda34')
    image=read(P/'etc/micom-binary/PMDMICOM_OCJP.bin',
               '61754d8e0445ed1a73685af83cdcf3fea66971b1a622b04c3f614b8b63286aff')
    module=read(B/'serdes-ack-copy-20261026/sdp_ocl_jp.ko',
                'e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c')
    need(helper.checksum_source(image[:0xdbff8])==0xce93f188,'full-source checksum retained')
    view=helper.reverse_words(image)
    elf=ELFFile(io.BytesIO(module));ro=elf.get_section_by_name('.rodata').data()
    record=struct.unpack_from('<11Q',ro,0x2778)
    need((record[1],record[3])==(0xf000,0x30000),'source layout system component')
    h=header(view[0xf000:0x3f000])
    need(h=={'magic':'0x27051956','headerCrc32':'0x7afe4346','timestamp':0x65c33ddb,
             'payloadBytes':0x2cbe0,'load':'0xa0020000','entry':'0xa0020000',
             'dataCrc32':'0x5f82b60','osId':5,'architectureId':10,'imageTypeId':1,
             'compressionId':0,'name':'fw_sys.uimg'},'exact validated component header')
    payloadFile=0xf040
    payloadEnd=payloadFile+h['payloadBytes']
    textBase=int(h['load'],16)
    def linked_to_file(address):
        if type(address)is not int or not textBase<=address<textBase+h['payloadBytes']:
            raise ValueError('linked text address out of validated payload')
        return payloadFile+address-textBase
    def file_to_linked(offset):
        if type(offset)is not int or not payloadFile<=offset<payloadEnd:
            raise ValueError('file instruction outside validated payload')
        return textBase+offset-payloadFile
    md=Cs(CS_ARCH_SPARC,CS_MODE_BIG_ENDIAN)
    instructions={}
    def ins(at,m,o):
        need(payloadFile<=at and at+4<=payloadEnd and at%4==0,'whole instruction inside validated component')
        xs=list(md.disasm(view[at:at+4],at))
        need(len(xs)==1 and(xs[0].mnemonic,xs[0].op_str)==(m,o),'actual SPARC instruction '+hex(at))
        instructions[at]=(m,o)
    for at,m,o in [
      (0xf040,'ba','0x10650'),(0xf044,'nop',''),
      (0x2d000,'cmp','%i0, 1'),(0x2d004,'be','0x2d278'),
      (0x2d278,'call','0x148d0'),(0x2d280,'sethi','0x3f0c44, %g1'),
      (0x2d284,'andcc','%o0, 0xff, %g0'),(0x2d288,'bne','0x2d030'),
      (0x2d28c,'or','%g1, 0x20, %l1'),
      (0x2d030,'call','0x11740'),(0x2d034,'mov','%l1, %o0'),
      (0x2d038,'st','%o0, [%fp+-0xc]'),(0x2d03c,'ldub','[%fp+-9], %g1'),
      (0x2d040,'andcc','%g1, 0x80, %g0'),(0x2d04c,'be','0x2d21c'),
      (0x2d21c,'mov','%l1, %o0'),(0x2d220,'call','0x2cb18'),(0x2d224,'mov','%l2, %o1'),
      (0x11740,'ld','[%o0], %o0'),(0x11744,'retl',''),(0x11748,'nop',''),
      (0x2cb1c,'ldub','[%i1+1], %g1'),(0x2cb20,'cmp','%g1, 0x1c'),
      (0x2cc64,'call','0x11740'),(0x2cc68,'add','%o0, 4, %o0'),
      (0x2cc6c,'mov','4, %o5'),(0x2cc70,'sub','%o5, %l1, %o5'),
      (0x2cc74,'sll','%o5, 3, %o5'),(0x2cc78,'mov','-1, %g1'),
      (0x2cc7c,'srl','%g1, %o5, %g1'),(0x2cc84,'and','%o0, %g1, %o0'),
      (0x2cc88,'sethi','0x2a00bc, %o5'),(0x2cc8c,'or','%o5, 0x320, %o5'),
      (0x2cc90,'st','%o0, [%o5+%l0]'),
      (0x2ccc0,'ldub','[%i1+3], %g1'),(0x2ccc4,'and','%g1, 0x7f, %g1'),
      (0x2ccc8,'cmp','%g1, 0xa'),(0x2cccc,'bgu','0x2cce8'),
      (0x2ccd0,'sethi','0x2800f6, %o5'),(0x2ccd8,'or','%o5, 0x2ac, %o5'),
      (0x2ccdc,'ld','[%o5+%g1], %o4'),(0x2cce0,'jmp','%o4'),
      (0x2cd6c,'sethi','0x2a00bc, %i2'),(0x2cd70,'call','0x2f798'),
      (0x2cd74,'restore','%i2, 0x320, %o2'),
      (0x2f798,'save','%sp, -0xd8, %sp'),(0x2f79c,'ldub','[%i1+2], %o1'),
      (0x2f7a4,'add','%g1, -4, %g1'),(0x2f7a8,'cmp','%g1, 0x3b'),
      (0x2f7ac,'bgu','0x2f7c8'),(0x2f7b0,'sethi','0x280101, %o5'),
      (0x2f7b8,'or','%o5, 0x268, %o5'),(0x2f7bc,'ld','[%o5+%g1], %o4'),
      (0x2f7c0,'jmp','%o4'),
      (0x2f7e0,'ldub','[%i2+3], %g1'),(0x2f7e4,'cmp','%g1, 0'),
      (0x2f7e8,'bne','0x2f7f4'),(0x2f7ec,'mov','2, %o1'),
      (0x2f7f0,'mov','3, %o1'),(0x2f7f4,'call','0x177a4'),
      (0x2f7f8,'mov','0x14, %o0'),(0x2f7fc,'ba,a','0x30278'),
      (0x30278,'ret',''),(0x3027c,'restore',''),
      (0x177a4,'save','%sp, -0x78, %sp'),(0x177b4,'and','%i0, 0xff, %o2'),
      (0x177bc,'and','%i1, 0xff, %o3'),(0x177c0,'mov','0, %o0'),
      (0x177c4,'mov','0x40, %o1'),(0x177c8,'mov','0, %o4'),
      (0x177cc,'call','0x17088'),(0x177d0,'mov','0x40, %o5'),
      (0x1708c,'and','%i1, 0xff, %i1'),(0x17090,'and','%i3, 0xff, %o2'),
      (0x17094,'and','%i4, 0xff, %o3'),(0x17098,'and','%i2, 0xff, %o1'),
      (0x1709c,'call','0x1705c'),(0x170a0,'mov','%i1, %o0'),
      (0x170a8,'call','0x16e50'),(0x170b0,'call','0x16e60'),
      (0x1705c,'and','%o0, 0xff, %o0'),(0x17060,'sll','%o0, 8, %o0'),
      (0x17064,'and','%o1, 0xff, %o1'),(0x17068,'or','%o0, %o1, %o0'),
      (0x1706c,'sll','%o0, 8, %o0'),(0x17070,'and','%o2, 0xff, %o2'),
      (0x17074,'or','%o0, %o2, %o0'),(0x17078,'sll','%o0, 8, %o0'),
      (0x1707c,'and','%o3, 0xff, %o3'),(0x17084,'or','%o0, %o3, %o0'),
      (0x16e50,'sethi','0x3f0100, %g1'),(0x16e54,'st','%o0, [%g1]'),
      (0x170e8,'srl','%o1, 0x18, %g1'),(0x1710c,'srl','%o1, 0x18, %g1'),
      (0x17110,'cmp','%g1, 0xf1'),(0x17114,'bne','0x17178'),
      (0x17118,'srl','%o1, 0x10, %g1'),(0x17124,'cmp','%g1, %o5'),
      (0x2c930,'sethi','0x2a00ae, %i0'),(0x2c93c,'restore','%i0, 0xa8, %o0'),
      (0x2ca80,'sethi','0x2a00ae, %o0'),(0x2ca84,'or','%o0, 0x148, %o0'),
      (0x30280,'sethi','0x2a00b2, %o0'),(0x30284,'or','%o0, 0xf8, %o0'),
      (0x30330,'sethi','0x2a00b2, %o0'),(0x3033c,'or','%o0, 0x148, %o0'),
      (0x2bb80,'ldub','[%i0], %l0'),(0x2bbec,'cmp','%l0, 0x3f'),
      (0x2bbfc,'call','0x2b914')]:
        ins(at,m,o)
    # Three independent absolute code tables corroborate the header-derived map.
    tables=[]
    for base,n in [(0x2caec,11),(0x2cfd0,11),(0x2f6a8,60)]:
        entries=[]
        for i in range(n):
            ptr=struct.unpack_from('>I',view,base+4*i)[0]
            f=linked_to_file(ptr)
            need(file_to_linked(f)==ptr and f%4==0,'bounded absolute code-table entry')
            entries.append({'index':i,'linkedAddress':hex(ptr),'fileOffset':hex(f)})
        tables.append({'fileOffset':hex(base),'entries':entries})
    need(linked_to_file(0xa003daac)==0x2caec,'op dispatch table built by actual sethi/or')
    need(linked_to_file(0xa0040668)==0x2f6a8,'cmd dispatch table built by actual sethi/or')
    need(tables[0]['entries'][1]['fileOffset']=='0x2cd6c','op1 actual table entry')
    need(tables[2]['entries'][63-4]['fileOffset']=='0x2f7e0','cmd3f actual table entry')
    def op1_case(command):
        if type(command)is not int or not 0<=command<=255:
            raise ValueError('byte command domain')
        index=(command-4)&0xffffffff
        return None if index>59 else tables[2]['entries'][index]['fileOffset']
    defaultCases=0
    for command in range(256):
        case=op1_case(command)
        need((case is not None)==(4<=command<=63),'source unsigned table-bound model')
        defaultCases+=case is None
    need(defaultCases==196 and op1_case(63)=='0x2f7e0','default-bound and reset case')
    for invalid in (True,-1,256,'63'):
        try:op1_case(invalid)
        except ValueError:need(True,'invalid host model command rejected')
        else:need(False,'invalid host model command accepted')
    # Corroborated same-payload-offset data/string correspondence. This does not
    # assert an observed hardware alias, MMU configuration, or live RAM mapping.
    dataAnchors=[]
    for pointer,text in [(0xa802b8a8,'[ERROR]:   \n Audio Undefined Sub Write Cmd!(0x%x) \n'),
                         (0xa802b948,'[ERROR]:   \n CVBS Undefined Sub Read Cmd!(0x%x) \n'),
                         (0xa802c8f8,'[ERROR]:   \n Leon_Inter_COMM Undefined Sub Read Cmd!(0x%x) \n'),
                         (0xa802c948,'[ERROR]:   \n Leon_Inter_COMM Undefined Sub Write Cmd!(0x%x) \n'),
                         (0xa802c8d8,'APP_Mailbox_IPC_System_Read'),
                         (0xa8027198,'[ERROR]:   %s, STBC reply timeout!\n')]:
        f=payloadFile+pointer-0xa8000000
        need(payloadFile<=f and f+len(text)<payloadEnd,'data correspondence bounded')
        need(view[f:f+len(text)]==text.encode(),'data correspondence '+hex(pointer))
        dataAnchors.append({'linkedDataAddress':hex(pointer),'fileOffset':hex(f),'text':text})
    # Delayed-control-transfer oracle over exact, already checked instructions.
    def run_handler(payload):
        regs={'%g1':0,'%o0':0,'%o1':0};pc=0x2f7e0;eq=False;pending=None;trace=[]
        for _ in range(12):
            old=pending;pending=None
            m,o=instructions[pc];trace.append(pc)
            if m=='ldub': regs['%g1']=payload
            elif m=='cmp': eq=regs['%g1']==0
            elif m=='bne': pending=('branch',0x2f7f4 if not eq else pc+8)
            elif m=='mov':
                a,r=o.split(', ');regs[r]=int(a,0)
            elif m=='call': pending=('call',int(o,0))
            else: raise ValueError('unsupported oracle instruction')
            if old:
                if old[0]=='call':
                    return {'calleeFile':old[1],'arg0':regs['%o0'],'arg1':regs['%o1'],'trace':trace}
                pc=old[1]
            else: pc+=4
        raise ValueError('handler oracle bound')
    oracle=[]
    for payload in range(256):
        got=run_handler(payload)
        need((got['calleeFile'],got['arg0'],got['arg1'])==(0x177a4,20,2 if payload else 3),
             'actual handler delay-slot oracle '+str(payload))
        oracle.append({'payload':payload,'pin':20,'argument':got['arg1']})
    need(0x2f7f0 in run_handler(0)['trace'] and 0x2f7f0 not in run_handler(1)['trace'],
         'zero/nonzero branch path differs after unconditional delay slot')
    frame=0x00013f01
    octets=frame.to_bytes(4,'big')
    need((octets[1],octets[2],octets[3]&127)==(1,63,1),'source header fields after SPARC store')
    need(octets[3]&128==0,'write branch is selected by source bit7 test')
    need((0x3f0c44<<10)|0x20==0xfc311020,'same address as kernel AHB mailbox message register')
    need(0x3f0100<<10==0xfc040000,'downstream STBC command register')
    need((0x40<<24)|(20<<16)|(2<<8)==0x40140200,'nonzero secondary packed command')
    need((0x40<<24)|(20<<16)|(3<<8)==0x40140300,'zero secondary packed command')
    negative=0
    for bad in (b'',view[0xf000:0xf03f],image[0xf000:0x3f000]):
        try:header(bad)
        except(ValueError,UnicodeDecodeError): negative+=1
        else:need(False,'malformed component accepted')
    for at in (0,4,12,24,32,64,512):
        bad=bytearray(view[0xf000:0x3f000]);bad[at]^=1
        try:header(bad)
        except(ValueError,UnicodeDecodeError): negative+=1
        else:need(False,'corrupted component accepted')
    for bad in (-1,True,textBase-4,textBase+h['payloadBytes'],0xa8000000):
        try:linked_to_file(bad)
        except ValueError:negative+=1
        else:need(False,'unqualified code address accepted')
    need(negative==15,'focused malformed/transform/address negatives')
    hf=B/'menu-recovery-branch-trial-20261028hf/ocl-file-identity/response.txt'
    live=read(hf,'768cd19fbd0cc2ce4d45b276bede099ad1a4d33a16778ca24fd6ec15ae4cc7d3').decode()
    need(live.count('61754d8e0445ed1a73685af83cdcf3fea66971b1a622b04c3f614b8b63286aff')==2,
         'parent ordinary metadata matches both available PMD copies')
    need(live.count('NOT_REGULAR_OR_ABSENT')==2,'two expected unavailable named loader paths')
    need('e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c' in live,
         'parent installed JP module identity')
    spans=[]
    for lo,hi,meaning in [
      (0xf000,0xf040,'word-reversed component legacy header'),
      (0x2cffc,0x2d3d0,'incoming mailbox channels and read/write dispatch'),
      (0x2caec,0x2cde4,'write header/payload extraction and op table'),
      (0x2f6a8,0x2f800,'command table and real command3f branch'),
      (0x177a4,0x177dc,'secondary command40 wrapper'),
      (0x1705c,0x171c4,'command packing/write/ack validation'),
      (0x16e50,0x16ee0,'secondary mailbox write and queued-reply wait'),
      (0x2bb80,0x2bc20,'distinct console question-mark case')]:
        need(0<=lo<hi<=len(image),'complete bounded candidate span')
        spans.append({'fileOffset':hex(lo),'bytes':hi-lo,'originalSha256':sha(image[lo:hi]),
                      'wordReversedSha256':sha(view[lo:hi]),'meaning':meaning})
    result={'schema':'hg-ocl-candidate-system-dispatch-v1','decision':'CANDIDATE_HANDLER_TO_STBC_COMMAND_CLOSED',
      'checks':checks,'pins':pins,'header':h,'componentFileOffset':'0xf000',
      'payloadFileInterval':['0xf040',hex(payloadEnd)],'linkedTextBase':hex(textBase),
      'textTables':tables,'dataCorrespondenceAnchors':dataAnchors,'sourceSpans':spans,
      'instructionCount':len(instructions),'commandBoundCases':256,'defaultCommandCases':defaultCases,
      'actualInstructionOracleCases':len(oracle),
      'oracleCase0':oracle[0],'oracleCase1':oracle[1],'oracleAllNonzeroSame':True,
      'malformedCasesRejected':negative,'incoming':{'register':'0xfc311020','header':'0x00013f01',
       'op':1,'command':63,'bytes':1,'actualHandlerFile':'0x2f7e0','actualHandlerLinked':'0xa00407a0',
       'pinArgument':20,'nonzeroArgument':2,'zeroArgument':3},
      'outgoing':{'register':'0xfc040000','command':64,'nonzeroWord':'0x40140200',
       'zeroWord':'0x40140300','replyKindExpected':241,'replyCommandExpected':64,
       'returnCheckedBy3fHandler':False,'downstreamReceiverIdentified':False,
       'pinBoardNetIdentified':False,'mode2And3ElectricalMeaningQualified':False},
      'identity':{'acceptedExtractedCandidatePinned':True,'parentAvailableFileHashesMatch':True,
       'parentInstalledOclModuleHashMatches':True,'flashedMcuIdentityProven':False,
       'loaderRmfPmdEquivalenceProven':False},
      'limits':{'liveCalls':0,'networkCalls':0,'oemExecutions':0,'oemCopies':0,
       'linkedPcIsObservedRuntimePc':False,'liveRamAliasesQualified':False,
       'image0SharedRootResetProven':False,'physicalResetProven':False}}
    return result
if __name__=='__main__':
    print(json.dumps(main(),sort_keys=True,indent=2))
