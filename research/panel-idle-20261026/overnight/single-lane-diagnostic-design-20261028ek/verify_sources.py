#!/usr/bin/env python3
"""Bounded static source/data qualification; emits design only, never target code."""
from pathlib import Path
import hashlib,json,struct,sys
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_MCLASS
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;B=D.parent;checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 checks+=1
 if not v:raise ValueError(s)
def j(p):return json.loads(p.read_text())
for f in j(D/'input-pins.json')['files']:
 b=Path(f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'pinned input')
package=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes();need(len(package)==5242880 and sha(package)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected exact package');image=package[0x40200:0x60200];cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_MCLASS)
for dirname in ('rtp-lane-gate-qualification-20261028ea','rtp-lane-table-writers-20261028ec','reference-refresh-control-20261028eg'):
 p=B/dirname
 for f in j(p/'source-inventory.json')['files']:
  raw=(p/f.get('path',f.get('name'))).read_bytes();need(len(raw)==f['bytes']and sha(raw)==f['sha256'],'source inventory '+dirname)
# Code portions start/end at boundaries recovered from the containing function;
# getter ends with data, not six invented instructions.
regions=[('root-getter',0x38fc,12,6,'6B code,2B alignment padding,4B literal at3904'),('root-save',0xbd6c,8,8,'BL38fc/MOVr5/root plus loop-index initializer'),('operating-mode-and-SB',0xbe0c,44,44,'ends before branch atbe38; whole instructions, no IT block'),('four-unrolled-local-gates',0xbeb4,228,228,'ends before loop advance atbf98; lane570 uses thirdsitebf22'),('gate-literal-pool',0xc030,32,0,'data-only adjunct:AA/AC/byte4cc/secondary base')]
function=list(cs.disasm(image[0xbd58:0xc026],0xbd58));boundaries={x.address for x in function}|{x.address+x.size for x in function}
windows=[]
for name,va,length,codebytes,note in regions:
 if codebytes:
  decoded=list(cs.disasm(image[va:va+codebytes],va));need(sum(x.size for x in decoded)==codebytes,'whole instructions '+name)
  need(not any(x.mnemonic.startswith('it')for x in decoded),'no within-range IT block '+name)
  if va!=0x38fc:need(va in boundaries and va+codebytes in boundaries,'containing-function boundaries '+name)
 else:decoded=[]
 windows.append({'name':name,'linkedVa':hex(va),'fileOffset':hex(va+0x40200),'busAddress':hex(0x46000000+va),'bytes':length,'expectedSha256':sha(image[va:va+length]),'readHeaderLittleEndianHex':struct.pack('<III',0x101,0x46000000+va,length).hex(),'codeBytes':codebytes,'scope':note,'instructions':[{'va':hex(x.address),'bytes':x.size,'mnemonic':x.mnemonic,'operands':x.op_str}for x in decoded]})
need(struct.unpack_from('<I',image,0x3904)[0]==0x200004e0,'getter points to mutable root pointer word')
refs=[]
for va,lit,want in [(0xbe16,0xc040,0x200004ac),(0xbe1e,0xc030,0x200004aa),(0xbe26,0xc044,0x200004cc),(0xbebe,0xc048,0x2000c95c)]:
 ins=next(cs.disasm(image[va:va+4],va,count=1));need(ins.mnemonic=='ldr','literal load');imm=int(ins.op_str.split('#')[1].split(']')[0],0);need(((va+4)&~3)+imm==lit and struct.unpack_from('<I',image,lit)[0]==want,'actual PC literal binding');refs.append({'instructionVa':hex(va),'literalVa':hex(lit),'selectedValue':hex(want)})
need(0x20010000+2*570==0x20010474 and 0x20010474+0x27000000==0x47010474,'fixed lane570 source/bus arithmetic')
need(0x2000c95c+570==0x2000cb96,'fixed secondary570')
need(sha(image[0xbeb4:0xbf98])=='044752267f71da1f8c28f8bca423972ac77ca099b1deb089e23ac42cde138d19','exact four-gate body')
# Only immutable already accepted ED/EE captures are used, not ongoing recovery evidence.
actual=[]
for relative in ('rtp-lane-gate-trial-20261028ed/table-read-01','lane-gate-onset-20261028ee/post-tables-01'):
 p=B/relative;r=j(p/'result.json');need(r['accepted']is True and r['headersSent']==16 and r['bulkTransfers']==32 and r['cleanup']=='STAGE_ABSENT','accepted tablecapture')
 byname={f['name']:f for f in r['rawFiles']}
 for name in ('primary-lane-gate.bin','secondary-lane-gate.bin','M.bin','C.bin','start-R.bin','end-R.bin'):
  b=(p/name).read_bytes();need(len(b)==byname[name]['bytes']and sha(b)==byname[name]['sha256'],'accepted rawbinding')
 primary=(p/'primary-lane-gate.bin').read_bytes();secondary=(p/'secondary-lane-gate.bin').read_bytes();m=(p/'M.bin').read_bytes();c=(p/'C.bin').read_bytes();rr=(p/'start-R.bin').read_bytes()
 need(primary==bytes(136)and secondary==bytes(68),'actual allzero tables');need(struct.unpack_from('<H',primary,4)[0]==0 and secondary[2]==0,'lane570 exact original')
 controls=[struct.unpack_from('<H',m,2)[0],struct.unpack_from('<H',rr,0x60)[0],struct.unpack_from('<H',rr,0x6e)[0]];need(controls==[0,0,0],'actual known writercontrols sampledzero')
 actual.append({'capture':relative,'resultSha256':sha((p/'result.json').read_bytes()),'primary570U16':0,'secondary570U8':0,'sampledKnownWriterControls':controls,'continuousWriterQuiescenceProven':False,'currentTargetIdentityEstablished':False})
source={'schema':'ek-single-lane-source-qualification-v1','selectedPackageSha256':sha(package),'fixedLane':570,'rootCpu':'0x20010000','primaryCpu':'0x20010474','primaryBus':'0x47010474','secondaryCpu':'0x2000cb96','aliasScope':'DW nonzero tag image1 codeVA<0x20000 +0x46000000,SRAM20000000..2001ffff +0x27000000; no alternativebankfallback','positiveFingerprintProposal':windows,'fourCodeWindowsBytes':292,'extraLiteralWindowBytes':32,'fingerprintPairs':5,'fingerprintBulks':10,'liveNewFingerprintsQualified':False,'targetOperations':0,'helperImplemented':False,'literalBindings':refs,'immutableZeroTableExamples':actual,'sourceLimits':['Local gate/body selected source; no active instruction fetch/physical mapping proof','Known source writer controls are snapshot guards,not complete writer exclusion','Primary upper15bits are stock publication data,never disposable','Existing EB full136B/68B data reads are reused; newaddress two-byte write requires independent native allowlist and receipt qualification']}
# Literal-only design schedule; this is not a runner or write helper.
reads=[('Rpre',0x47012400,256),('Mpre',0x470004a0,68),('Cpre',0x47000bc0,16),('Secondarypre',0x4700cb94,68),('Primarypre',0x47010470,136),('Rfresh',0x47012400,256),('Mfresh',0x470004a0,68),('Cfresh',0x47000bc0,16),('Secondaryfresh',0x4700cb94,68),('Primaryfresh',0x47010470,136),('Primaryreadback',0x47010470,136),('Rpost',0x47012400,256),('Mpost',0x470004a0,68),('Cpost',0x47000bc0,16),('Secondarypost',0x4700cb94,68),('Primarypost',0x47010470,136)]
readrows=[{'name':n,'busAddress':hex(a),'bytes':z,'headerLittleEndianHex':struct.pack('<III',0x101,a,z).hex()}for n,a,z in reads]
plan={'schema':'ek-fixed-single-lane-design-v1','designOnly':True,'helperImplemented':False,'targetOperations':0,'writesPerformed':0,'nativeLibraryBuildOrDeploy':False,'lane':570,'primaryBusAddress':'0x47010474','originalWordMustEqual':0,'installedWordMustEqual':1,'secondaryLane570MustEqual':0,'secondaryReadWindowLane570Offset':2,'primaryReadWindowLane570Offset':4,'primaryWindowBus':'0x47010470','primaryWindowBytes':136,'secondaryWindowBus':'0x4700cb94','secondaryWindowBytes':68,'fullPrimaryBaselineWordsMustEqual':[0]*68,'fullPrimaryInstalledWordsExpected':[1 if i==2 else 0 for i in range(68)],'fullSecondaryBytesMustEqual':[0]*68,'setHeaderLittleEndianHex':struct.pack('<III',0x102,0x47010474,2).hex(),'setPayloadHex':'0100','restoreHeaderLittleEndianHex':struct.pack('<III',0x102,0x47010474,2).hex(),'restorePayloadHex':'0000','writeHeaderIndexAfterReadPair':10,'readSchedule':readrows,'perSeparateAction':{'readPairs':16,'writeHeaderPayloadPairs':1,'headers':17,'bulkTransfers':34,'readInputBytes':sum(z for _,_,z in reads),'writePayloadBytes':2,'maximumDataPayloadBytes':256},'knownWriterControlsRequiredZero':['M+2 CPU4a2','R+0x60 root2460','R+0x6e root246e'],'extraConservativeAdmission':['M+36 refreshcounterzero','C7∈0/1 and M+34 selectorMirror==C7 at sampledtime','Same selector and coherent RT across each action pre/fresh; no root/geometry/dispatch drift','Full primary/secondary windows unchanged except the owned lane570 bit0'],'setRt':'coherent clean0/0/1','separateRestoreRt':'coherent clean0/0/1 OR fault1/4097/0, stable within restore action','allowedAcrossExposureChanges':['C7/selectorMirror coherent0or1','clean/faultRT','Mpublicationbound','rows,Nordinals,latches,temperature/history; recorded,not sourcewriter quiescence'],'strictFixedInvariants':['sameboot/USBnode/descriptors/interface/ownershiplineage','same root20010000/geometry2160,1920,2880/xbase0','AA0/AC2/Roperating4','known writercontrols0 throughout fresh observedguards','secondarylane5700','exact wholeprimaryword0(set)or1(restore),nohighbitchange'],'deadlineProposal':{'cooperativeTransactionBudgetSeconds':40,'perBulkTimeoutMs':2000,'minimumBeforeWriteReserveSeconds':32,'rootTimeoutSeconds':45,'hostTimeoutSeconds':75,'hardNativeProcessAlarmImplemented':False,'reserveCalculation':'writeOUT+payload4s;6post-readpairs24s;release/closemargin4s,conditionalon2sbulkdeadlinebeinghonored','durationNotGuaranteed':True},'ownershipRule':'onlyverifiedset/readback1receiptestablishesconditionalownership;separaterestore0mustguardfullword/sourcecontext;MODE2notrestore','ambiguousTransferPolicy':'Unknownhardstop;noheader/retry/reset/assumedrestore;retainwriteMayHaveChangedandreceiptforcentralreconciliation','readyForImplementation':False,'openQualification':['Fresh live positive code/literal fingerprints; new fixed-address two-byte write native allowlist','independent implementation,ABI,receipt/adversarialfailurebounds andfreshcaptureadmission','completewriterquiescence/ABAexclusion remainsunproved;USB readthenwriteisnotCAS','unknown-writephase recovery route preserving ownedbit remainsunqualified','causal tupleepoch/sameexposure/earlyexit effects and physicalmapping remainconditional']}
for name,report in [('source-qualification.json',source),('design.json',plan)]:
 out=json.dumps(report,indent=2,sort_keys=True)+'\n'
 if sys.argv[1:]==['--record']:(D/name).write_text(out)
 else:need((D/name).read_text()==out,'frozen design/source report')
print(json.dumps({'accepted':True,'checks':checks,'fingerprintProposalWindows':5,'targetOperations':0,'helperImplemented':False,'readyForImplementation':False}))
