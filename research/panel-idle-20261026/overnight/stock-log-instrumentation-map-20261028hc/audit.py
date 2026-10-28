#!/usr/bin/env python3
"""Bounded retained-source audit. Reads host files only; no target helper imports."""
import hashlib, importlib.util, io, json, re, sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent; B=HERE.parent; ROOT=B.parent
sys.path.insert(0,'/tmp/tcon-capstone')
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from stock_log import MARKERS, classify
checks=0; pins=[]
def need(v,why):
 global checks
 if not v:raise ValueError(why)
 checks+=1
def sha(b):return hashlib.sha256(b).hexdigest()
def read(rel,expected=None):
 p=ROOT/rel;b=p.read_bytes();need(not expected or sha(b)==expected,'input identity '+rel)
 pins.append(dict(path=rel,bytes=len(b),sha256=sha(b)));return b
def main():
 assets=[('QDF','binaries/qdf_tcon.ko','97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63'),
 ('FRC-TCON','binaries/tztv_frc_tcon.ko','aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd'),
 ('API','binaries/tztv_frc_tcon_api.ko','3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6'),
 ('SDP-FRC','binaries/sdp_frc.ko',None),
 ('OCL','overnight/serdes-ack-copy-20261026/sdp_ocl_jp.ko','e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c')]
 elf={}; observations=[]; formats=[]; early_calls=[]; marker_found=set(); md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
 for label,path,expected in assets:
  e=ELFFile(io.BytesIO(read(path,expected)));elf[label]=e
  names=[s.name for s in e.iter_sections()]
  sy=e.get_section_by_name('.symtab'); symbols=list(sy.iter_symbols())
  dynamic=[n for n in names if any(t in n.lower() for t in ['dyndbg','tracepoint','trace_events','ftrace_events'])]
  dynamic_symbols=[s.name for s in symbols if s.name.startswith(('__tracepoint_','__traceiter_','__trace_printk','__dynamic_pr_debug'))]
  need(not dynamic and not dynamic_symbols,'no matching instrumentation sections/symbols in bounded modules '+label)
  mi=e.get_section_by_name('.modinfo');params=[x.decode('ascii') for x in mi.data().split(b'\0') if x.startswith((b'parm=',b'parmtype='))]if mi else []
  need(params==(['parm=TIMESTAMP:20260701_1717']if label=='SDP-FRC'else []),'exact declared module parameter list '+label)
  debug=[dict(name=s.name,section=e.get_section(s['st_shndx']).name,offset=hex(s['st_value']),bytes=s['st_size'],type=s['st_info']['type']) for s in symbols if s.name in ['frc_tcon_debug_level','frc_debug_level','tcon_debug_level'] and isinstance(s['st_shndx'],int)]
  if label=='API':need(len(debug)==3 and all(s['section']=='.bss'and s['type']=='STT_OBJECT'for s in debug),'debug levels are objects, not module parameter ABI')
  observations.append(dict(asset=label,matchingDynamicInstrumentationSections=dynamic,matchingDynamicInstrumentationSymbols=dynamic_symbols,
    moduleParameters=params,debugLevelObjects=debug,importsTraceEarlyMessage=any(s.name=='trace_early_message'and s['st_shndx']=='SHN_UNDEF'for s in symbols)))
  for rel in e.iter_sections():
   if rel['sh_type']!='SHT_RELA':continue
   target=e.get_section(rel['sh_info'])
   if not target.name.startswith('.text'):continue
   st=e.get_section(rel['sh_link']); calls=[]; literals=[]
   for r in rel.iter_relocations():
    s=st.get_symbol(r['r_info_sym']); n=s.name
    if not n and isinstance(s['st_shndx'],int):n=e.get_section(s['st_shndx']).name
    if n=='printk':calls.append(r['r_offset'])
    if n=='trace_early_message':
     owners=[x for x in symbols if x['st_info']['type']=='STT_FUNC' and isinstance(x['st_shndx'],int) and e.get_section(x['st_shndx']).name==target.name and x['st_value']<=r['r_offset']<x['st_value']+x['st_size']]
     early_calls.append(dict(asset=label,section=target.name,call=hex(r['r_offset']),containingFunctions=[x.name for x in owners],instructionBytesSha256=sha(target.data()[r['r_offset']:r['r_offset']+4])))
    if not n.startswith('.rodata.str'):continue
    ro=e.get_section_by_name(n).data();a=r['r_addend'];end=ro.find(b'\0',a)
    need(0<=a<=end<len(ro),'bounded NUL-terminated source format')
    text=ro[a:end].decode('ascii',errors='strict')
    for marker,scope,fragment in MARKERS:
     if fragment in text and (not scope or scope in text):
      marker_found.add(marker); literals.append((r['r_offset'],n,a,text,marker))
   for at,section,offset,text,marker in literals:
    ins=next(md.disasm(target.data()[at:at+4],at))
    # Relocations are exact provenance. Nearby calls are candidates, NOT an inferred full CFG.
    candidates=[hex(x)for x in calls if at<=x<=at+128]
    formats.append(dict(marker=marker,asset=label,codeSection=target.name,literalRelocation=hex(at),instruction=ins.mnemonic+' '+ins.op_str,
      stringSection=section,stringOffset=hex(offset),format=text,formatSha256=sha(text.encode()),nearbyPrintkCalls=candidates,
      nearbyCallIsNotFullDataflowProof=True))
 need(marker_found=={x[0]for x in MARKERS},'all classifier marker fragments exist in retained exact source')
 q=elf['QDF'];code=q.get_section_by_name('.text').data()
 expected=[(0x118f4,'cbnz','w1, #0x11994'),(0x1192c,'bl','#0xb250'),(0x11930,'bl','#0x107e8'),(0x11934,'bl','#0xf6d8'),
  (0x11ce0,'bl','#0x11848'),(0x11cec,'bl','#0x11848'),(0x11cf0,'orr','w0, w19, w0')]
 for at,m,o in expected:
  i=next(md.disasm(code[at:at+4],at));need((i.mnemonic,i.op_str)==(m,o),'critical branch/call '+hex(at))
 spans=[]
 for lo,hi,meaning in [(0x11848,0x11b88,'ERR-skipped versus normal recovery tail; optional board callbacks'),(0x11c48,0x11d78,'mode2 off/on return aggregation'),(0xb250,0xb730,'status/access/display checks'),(0x107e8,0x10928,'frame-mode comparison and recovery request'),(0xf6d8,0xf910,'retained NPC register replay')]:
  blob=code[lo:hi];need(len(blob)==hi-lo,'full bounded span');spans.append(dict(asset='QDF',section='.text',start=hex(lo),endExclusive=hex(hi),sha256=sha(blob),meaning=meaning))
 gz=read('overnight/stock-mode2-reset-domain-20261028gz/README.md','a85104642a080c4f1425ada7b8d2c6593fc71be2d236238910b8b44b76d28a5b')
 read('overnight/stock-mode2-reset-domain-20261028gz/trace-continuation.md','4aaba29eb4d9440ca0bd6b823c50127c9d06e70a852cc1f92cd46e8e554118a7')
 live=read('overnight/hdmi-endpoint-trial-20261028gp/kernel-trace-capabilities/response.txt').decode()
 need('nop'in live and 'UNAVAILABLE'in live,'actual nop-only/filter-unavailable discovery retained')
 probe=read('overnight/hdmi-endpoint-trial-20261028gp/kernel-probe-capabilities/partial-response.txt').decode()
 for leaf in ['kprobe_events','dynamic_events','events/kprobes','kprobe_profile']:
  need('/sys/kernel/debug/tracing/'+leaf+'\nABSENT'in probe,'actual path absent '+leaf)
 read('overnight/hdmi-endpoint-trial-20261028gp/kernel-probe-capabilities/root.json')
 read('overnight/hdmi-endpoint-trial-20261028gp/kernel-probe-capabilities/refusal.json')
 read('overnight/autonomous-fault-harness-20261028dh/trace-formats.txt')
 eventsText=json.loads(read('overnight/kernel-observability.json'))['commands'][0]['stdout']
 events=sorted(set(re.findall(r'^([A-Za-z0-9_-]+:[A-Za-z0-9_-]+)$',eventsText,re.M)))
 selected=[e for e in events if e in ['gpio:gpio_direction','gpio:gpio_value','power:suspend_resume','power:device_pm_callback_start','power:device_pm_callback_end','raw_syscalls:sys_enter','raw_syscalls:sys_exit','irq:irq_handler_entry','irq:irq_handler_exit','early_trace:early_event']or e.startswith('i2c:')]
 need(all(x in events for x in ['gpio:gpio_direction','gpio:gpio_value','irq:irq_handler_entry','power:suspend_resume']),'historically advertised static event set')
 read('overnight/hdmi-endpoint-trial-20261028gp/dt-property-findings.md')
 read('overnight/early-trace-format.json','26d92050dcb1acdafda01a242d9d11f6be11e2debcfe39d70a84fcbfedff0559')
 hist=read('overnight/stock-rt-lifecycle-trial-20261027av/kernel-end.txt')
 projection=classify(hist)
 for marker in ['qdf-mode2-request','qdf-normal-tail-entered','qdf-init-status-result','qdf-access-success','qdf-display-status-result','qdf-register-replay-end','ocl-reset-return']:
  need(projection['markerCounts'].get(marker,0)>0,'historical actual positive marker '+marker)
 # Public/audit result contains hashes/locators and derived metadata, never raw kernel text/boot IDs.
 return dict(schema='s95f-stock-log-hc-source-v1',checks=checks,inputPins=pins,modules=observations,formats=formats,earlyTraceCalls=early_calls,sourceSpans=spans,
  historicallyAdvertisedSelectedEvents=selected,staticEventAvailabilityNotRequeried=True,
  currentFunctionGraphAvailable=False,currentKprobeInterfacesObservedAbsent=True,kprobeDiscoveryOriginallyRefused=True,
  historicalMode2Snapshot=dict(bytes=len(hist),sha256=sha(hist),markerCounts=projection['markerCounts']),
  liveOperations=0,networkOperations=0,dynamicDebugEnabled=False,
  limitations=['ELF instrumentation absence is bounded to selected names/sections in five retained modules',
   'symbol exports and historical event formats do not attest current event availability or live function binding',
   'no QDF-specific event was qualified; GPIO/IRQ/power/early_trace provide indirect context only',
   'printk markers attest printed reports, not physical GPIO state, instruction reload, shared fault clear, or optical recovery'])
if __name__=='__main__':print(json.dumps(main(),indent=2,sort_keys=True))
