"""Build an offline evidence graph from authored reports; never load OEM code."""
from pathlib import Path
import hashlib,json,copy
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
B='panel-idle-20261026/overnight/'
REPORTS={
 'cb':B+'onset-trial-20261028cb/findings.md',
 'operand':B+'onset-trial-20261028cb/operand-analysis/operand-findings.md',
 'write':B+'onset-trial-20261028cb/operand-analysis/prevention-experiment-readiness.md',
 'bw':B+'full-confirmation-20261027bw/findings.md',
 'overlay':B+'ugoos-overlay-paired-control-20261027.md',
 'controls':B+'owner-control-clarifications-20261027.md',
 'causal':B+'diagnostic-causal-map-20261027.md',
 'cs':B+'firmware-kernel-analysis-20261028cs/report.md',
 'cf':B+'swu-item-schema-20261028cf/schema-call-map.md',
 'da':B+'swu-platform-controller-20261028da/phase-report.md',
 'cz':B+'firmware-extraction-workbench-20261028cz/phase-report.md',
 'incident':B+'incident-separation-20261027z/incident-comparison.md',
 'ordinary':B+'ordinary-fault-model-20261027.md',
 'capture8':B+'firmware-rtp-producer-20261028df/capture/README-wrapper.md',
}
CONTRIBUTIONS={
 'de':('firmware-display-path-20261028de','c6b75d288ef9925058a2213e818125281a78226a7f92ff2663848860143caa2b','findings.md'),
 'df':('firmware-rtp-producer-20261028df','75c53eb65c654c135c9b94fbcd67ff3ea409f9d472a6557a3a63ab9c15e4db41','README.md'),
}
def pinned_ref(path,**attrs):
 raw=(ROOT/path).read_bytes()
 return dict(path=path,sha256=hashlib.sha256(raw).hexdigest(),hash_semantics='original_retained_report_bytes',**attrs)
def merge_contributions(nodes,edges):
 """Normalize two frozen author graphs without executing graph attributes.

 Raw OEM and private prototype refs become authored report provenance. Public
 asset identities/offset anchors survive as metadata; source_refs always point
 to bounded authored evidence. Original graph bytes remain hash pinned.
 """
 manifests=[];kindmap={'file':'asset','tool':'evidence','unknown':'gap','logger':'interface','mechanism':'interface','resource':'asset','cross-core firmware boundary':'interface'}
 for owner,(directory,expected,report) in CONTRIBUTIONS.items():
  path=B+directory+'/evidence-graph.json';raw=(ROOT/path).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('frozen contribution changed: '+owner)
  original=json.loads(raw);graphref=pinned_ref(path);reportref=pinned_ref(B+directory+'/'+report)
  manifests.append(dict(owner=owner,**graphref,nodes=len(original['nodes']),edges=len(original['edges']),normalization='Kinds normalized; confidence labels removed; OEM/private source refs replaced with graph/report provenance; public asset identity anchors retained.'))
  assets={}
  for index,source in enumerate(original['nodes']):
   item=copy.deepcopy(source);item.pop('confidence',None);item['kind']=kindmap.get(item['kind'],item['kind'])
   item['source_refs']=[dict(graphref,locator='/nodes/'+str(index)),reportref]
   anchors=[]
   for ref in source.get('source_refs',[]):
    p=ref['path']
    if p.startswith(('PRD:','PLTF:')) or p.endswith('.bin'):
     # Logical target names are artifact identities, never host input paths.
     anchor={k:v for k,v in ref.items() if k not in ('path','sha256')}
     anchor.update(object_name=p.split('/')[-1],object_sha256=ref['sha256'],identity_scope='packaged/retained asset; not executing-image attestation')
     anchors.append(anchor)
     if owner=='de':assets.setdefault((p,ref['sha256']),[]).append(item['id'])
   if anchors:item['asset_anchors']=anchors
   if owner=='df' and item['id']=='df.logger':item['limitations'].append('Initial frozen host-only prototype; separate later capture/ contains deployable eight-window candidate.')
   if item['kind']=='observation':item.setdefault('observation_class','owner_report' if item['id']=='df.negative' else 'native_capture')
   nodes.append(item)
  for index,source in enumerate(original['edges']):
   item=copy.deepcopy(source);item.pop('confidence',None)
   locators='; '.join(ref.get('locator','') for ref in source.get('evidence_refs',[]))
   item['evidence_refs']=[dict(graphref,locator='/edges/'+str(index)+(('; '+locators) if locators else '')),dict(reportref,locator='Frozen contribution findings and qualification')]
   if item['evidence_type']=='observed':item.setdefault('observation_class','native_capture')
   edges.append(item)
  for asset_index,((logical,digest),members) in enumerate(sorted(assets.items())):
   assetid='de.asset.'+str(asset_index+1)
   nodes.append(dict(id=assetid,kind='asset',label=logical,source_refs=[graphref,reportref],identity=dict(sha256=digest,scope='exact packaged/retained asset'),limitations=['OEM bytes withheld; live current mapping/backend identity separately qualified.']))
   for member in members:
    edges.append(dict(id=assetid+'.contains.'+str(len(edges)),**{'from':assetid,'to':member},relation='contains_static_anchor',evidence_type='static',evidence_refs=[dict(graphref,locator='node source_refs exact artifact hash/offset')],limitations=[]))
 return manifests
def build():
 refs={k:dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),hash_semantics='original_retained_report_bytes') for k,p in REPORTS.items()}
 nodes=[];edges=[]
 def node(i,kind,label,report,**attrs):
  nodes.append(dict(id=i,kind=kind,label=label,source_refs=[refs[report]],limitations=attrs.pop('limitations',[]),**attrs))
 def edge(a,b,relation,typ,report,locator,obs=None,**attrs):
  e=dict(id='edge.'+str(len(edges)+1),**{'from':a,'to':b},relation=relation,evidence_type=typ,evidence_refs=[dict(refs[report],locator=locator)],limitations=attrs.pop('limitations',[]),**attrs)
  if obs:e['observation_class']=obs
  edges.append(e)
 node('asset.main_firmware','asset','Exact main 0090-1301.0 package; nine validated originals','cz',availability='OEM bytes withheld')
 node('asset.kernel','asset','Extracted ARM64 Linux5.4.261 stored kernel','cs',availability='OEM bytes withheld',identity_scope='Matches earlier stored boot-slot declared kernel; executing text unqualified')
 node('asset.dtb_bundle','asset','Ten bounded FDTs','cs',availability='OEM bytes withheld')
 node('asset.board_candidate','asset','Tree1: runtime dtsversion candidate','cs',limitations=['Bootargs differ: boot patching observed; not complete live-tree proof'])
 node('asset.qd.selected','asset','Selected F_RSM1_BN9659934B_COMMON profile','operand',availability='OEM bytes withheld',identity=dict(sha256='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0',scope='distributed selected asset; not whole running executable identity'))
 node('function.rtp_predicate','function','Mode-selected history/aggregate comparison','operand',address='0x1e68',address_domain='selected-image1 Thumb VA',file_offset='0x42068',limitations=['File offset=VA+0x40200; running-code/alias assumption explicit'])
 node('function.fault_setter','function','Common stop/fault/gate setter','operand',address='0xc1e0',address_domain='selected-image1 Thumb VA',file_offset='0x4c3e0')
 node('state.mode1','state','CB selected mode1; alternate finite limit40','operand',attributes={'flags_aa':0,'flags_ac':2,'alternate_selector':1,'normal_limit':200,'alternate_limit':40})
 node('state.clean','state','RT tuple stop0 / fault0 / ordinaryGate1','cb')
 node('state.fault','state','RT tuple stop1 / fault0x1001 / ordinaryGate0','cb')
 node('observation.cb_operands','observation','CB score0→38→44; action bucket0→3→7','operand',observation_class='native_capture',limitations=['Post M/C/H/L follow first fault R; not atomic event operands'])
 node('observation.cb_bracket','observation','250294us conservative clean/fault R bracket','cb',observation_class='native_capture',attributes={'outer_start_us':167671010145,'outer_end_us':167671260439},limitations=['Conditional reply freshness; not physical-light timestamp or compositor/key causality'])
 node('observation.cb_dark','observation','Owner reports panel went dark after onset capture','cb',observation_class='owner_report',limitations=['No exact native physical timestamp'])
 node('observation.cb_recovery','observation','Owner reports Apps visible after separate stockMODE2','cb',observation_class='owner_report')
 node('observation.cb_rejected_recovery','observation','Recovery wrapper rejected proc-exit race; native rc0/ioctl0/close0, cleanup confirmed','cb',observation_class='native_capture',limitations=['Physical recovery does not rehabilitate rejected wrapper'])
 node('action.menu_sequence','action','Apps header → Up Up → Left → cachedLive','cb',execution_owner='parent coordinator only',limitations=['CB synchronized recorder itself sent one Left only; header preparation was separate; cached page is not light'])
 node('action.apps_mode2','action','Normal Right→Apps, then one unchanged stockoperation41/mode2','cb',execution_owner='parent coordinator only',limitations=['Separate phase/identity/public-state guards; no automatic retry or post-reset key'])
 node('observation.bw_recovery','observation','BW operational ForYou→Apps+MODE2: owner visible, kernelstatus0','bw',observation_class='owner_report',limitations=['Kernel status and physical report separate; not raw MCU RT tuple'])
 node('interface.root_windows','interface','R/M/C/H/L fixed controller windows','operand',address_domain='captured controller bus',attributes={'R':'0x47012400/256','M':'0x470004a0/68','C':'0x47000bc0/16','H':'0x4700d0e0/96','L':'0x47010f00/64'})
 node('interface.count_window','interface','Fixed36B IDs/current-count capture candidate','capture8',address='0x4700ba28',address_domain='controller bus',status='source-qualified and independently host-reviewed; target outcome not asserted by this snapshot',limitations=['First new device reply requires exact36-byte validation; complete live-image identity remains unproved'])
 node('interface.pointer_window','interface','Fixed16B A/B pointer capture candidate','capture8',address='0x47000490',address_domain='controller bus',status='source-qualified and independently host-reviewed; not executed by DG')
 node('interface.packed_ring','interface','Three-slot RTP ring','operand',address='0x20253002',address_domain='selected-image1 CPU data',attributes={'stride':'0xb68'},limitations=['Physical producer/units unresolved'])
 node('interface.aperture','interface','Descriptor-selected0x60000000 aperture copies','operand',address='0x60000000',address_domain='selected-image1 address space; physical semantics unknown')
 node('interface.prepd_image0','interface','Separate unresolved PrePD source0x584109a4','operand',address='0x584109a4',address_domain='image0 source domain',limitations=['No proved dataflow bridge to image1 RTP'])
 node('gap.producer','gap','Physical/dataflow producer and units remain unresolved','operand')
 node('gap.running_identity','gap','Whole executing image and bus/CPU alias not proved','operand')
 node('gap.electrical','gap','Software latch→electrical suppression→emitted light edge unresolved','causal')
 node('hypothesis.rtp736','hypothesis','CB path consistent with event736 mode1 aggregate crossing','operand',limitations=['CB did not log event736 itself; competing transient/indirect/different-code writers not excluded'])
 node('hypothesis.format_only','hypothesis','A codec/HDR/framerate label alone explains failures','controls',status='weakened by controls')
 node('hypothesis.mute_only','hypothesis','CLEAR_AVMUTE or QD_TCON_OFF alone explains black','causal',status='weakened by visible counterexamples')
 node('case.native_sparse','case','Sparse Live/ForYou persistent black while audio continues','overlay',observation_class='owner_report')
 node('case.hdmi_fail_A','case','HDMI failureA fullscreen; same playback behind UgoosHome can remain visible after restart','ordinary',observation_class='owner_report',limitations=['Same playback is not bit-identical final HDMI composition; exact historical HDMI format unknown'])
 node('case.hdmi_fail_B','case','HDMI failureB fullscreen; same-playback Home control','ordinary',observation_class='owner_report',limitations=['Private titles intentionally replaced with stable case IDs'])
 node('case.working_movies','case','Owner-confirmed working movie/series controls across formats','controls',observation_class='owner_report',limitations=['Server played flags are not physical proof; no contemporaneous HDMI mode for every title'])
 node('case.visible_apps','case','Populated Apps/screensaver visible control','overlay',observation_class='owner_report')
 node('case.rare_av_pause','case','Rare brief recovering picture loss, sometimes audio pause','incident',observation_class='owner_report',limitations=['Separate uncaptured symptom group; not automatically same persistent fault'])
 node('interface.errdet','interface','ERR_DET candidate gpio15 line5','cs',address_domain='candidate DT GPIO controller/line; not global Linux GPIO number',limitations=['Raw flags not proved electrical assertion polarity; getter may request/direction/read/free'])
 node('interface.pmic','interface','PMIC/VDD/sync candidate bank15 inputs','cs',limitations=['Static wiring candidate, no current levels'])
 node('interface.micom','interface','Micom control/messagebox distinct from TCON mailbox','cs',limitations=['Block identity not external OLED-controller protocol identity; version getter actively transacts'])
 node('hypothesis.limit200','hypothesis','Deferred finite40→200 RAM comparison experiment','write',status='not implemented; technical qualification incomplete',limitations=['Couples record-ID bound; electrical safety and score>200 possible; no arbitrary write or proved reset restoration'])
 node('hypothesis.screenshot_light','hypothesis','Nonblack compositor screenshot proves emitted light','incident',status='falsified in B0/B1 context')
 node('observation.screenshot_counterexample','observation','Nonblack Apps compositor capture while owner confirms panel black throughout B0/B1','incident',observation_class='owner_report',limitations=['Host composition and emitted light are separate; no electrical measurement'])
 node('negative.bucket_clear','configuration','Action bucket+0x2486 is accumulated output, not comparator enable','operand')
 edge('asset.main_firmware','asset.kernel','contains_validated_section','observed','cz','Observed results','host_validation')
 edge('asset.main_firmware','asset.dtb_bundle','contains_validated_section','observed','cz','Observed results','host_validation')
 edge('asset.dtb_bundle','asset.board_candidate','matches_runtime_dtsversion_candidate','static','cs','Board selection and exact DTB scope')
 edge('asset.board_candidate','interface.errdet','maps_property','static','cs','Candidate board TCON GPIO bindings')
 edge('asset.board_candidate','interface.pmic','maps_properties','static','cs','Candidate board TCON GPIO bindings')
 edge('asset.board_candidate','interface.micom','distinguishes_resource_domains','static','cs','MMIO and MCU/logging distinctions')
 edge('asset.qd.selected','function.rtp_predicate','contains','static','operand','Exact active comparison')
 edge('asset.qd.selected','function.fault_setter','contains','static','operand','Common setter0xc1e0')
 edge('function.rtp_predicate','state.mode1','selects_comparison','static','operand','ac=2 therefore ordinary mode1')
 edge('function.rtp_predicate','function.fault_setter','calls_on_low16_score_gt_limit','static','operand','cmp r7,fp; ble clean; event736 edge')
 edge('function.fault_setter','state.fault','writes_tuple','static','operand','root+0x2400/0x240a/0x240e')
 edge('state.clean','state.fault','sampled_transition','observed','cb','final clean R and first fault R','native_capture')
 edge('interface.root_windows','observation.cb_operands','carries_sequential_samples','observed','operand','Observed values','native_capture')
 edge('observation.cb_operands','hypothesis.rtp736','supports_under_running_source_assumptions','inferred','operand','3→7 bucket and44>40')
 edge('observation.cb_bracket','state.fault','brackets_software_transition','observed','cb','250294us','native_capture')
 edge('state.fault','observation.cb_dark','cooccurs_in_trial_context','observed','cb','owner then reported panel went dark','owner_report')
 edge('state.fault','gap.electrical','does_not_close','unknown','cb','no exact physical timestamp')
 edge('action.menu_sequence','state.fault','precedes_sampled_fault','observed','cb','one Left, five clean cycles, cycle6fault','native_capture',limitations=['No key causality claim'])
 edge('action.apps_mode2','observation.cb_recovery','precedes_reported_visibility','observed','cb','panel is back on on apps','owner_report')
 edge('observation.cb_recovery','observation.cb_rejected_recovery','does_not_rehabilitate','observed','cb','top-level accepted=false','native_capture')
 edge('action.apps_mode2','observation.bw_recovery','has_operational_prior_control','observed','bw','one operation41/mode2, no post-reset key','owner_report')
 edge('interface.aperture','interface.packed_ring','supplies_descriptor_selected_copies','static','operand','packed-buffer provenance')
 edge('interface.packed_ring','function.rtp_predicate','feeds_packed_lane_count_chain','static','operand','What contributes to score')
 edge('interface.prepd_image0','interface.packed_ring','unproven_bridge','unknown','operand','must not be identified as this RTP source')
 edge('interface.aperture','gap.producer','leaves_physical_source_unknown','unknown','operand','physical meaning aperture still unproved')
 edge('interface.count_window','hypothesis.rtp736','would_discriminate_count_vs_ID_saturation','inferred','operand','smallest missing count window')
 edge('interface.pointer_window','gap.producer','would_narrow_selected_input_branch','inferred','operand','A/B pointers494/498')
 edge('asset.qd.selected','gap.running_identity','does_not_establish_executing_identity','unknown','operand','full live executable hash/alias proof absent')
 for case in ['case.hdmi_fail_A','case.hdmi_fail_B']:
  edge(case,'case.native_sparse','shares_persistent_black_phenotype_not_proved_mechanism','inferred','causal','not confined to empty Home pages')
  edge(case,'hypothesis.format_only','paired_home_control_weakens','inferred','ordinary','Owner-observed problem: same playing content behind UgoosHome')
 edge('case.working_movies','hypothesis.format_only','negative_case','observed','controls','working controls span formats','owner_report')
 edge('case.visible_apps','hypothesis.mute_only','weakens_as_marker','observed','causal','CLEAR_AVMUTE visible menu and QD_TCON_OFF good+black','native_capture',limitations=['CLEAR_AVMUTE raw trace rejected; owner timing uncalibrated; adjacent QD_TCON_OFF sample is not an exact electrical event counterexample'])
 edge('case.rare_av_pause','case.native_sparse','must_remain_distinct','unknown','incident','separate incidents')
 edge('observation.screenshot_counterexample','hypothesis.screenshot_light','negative_case','observed','incident','compositor-to-light equivalence directly falsified','owner_report')
 edge('negative.bucket_clear','hypothesis.limit200','rejects_bucket_as_equivalent_prevention','static','write','bucket is OR history; clearing does not prevent comparator')
 edge('hypothesis.limit200','gap.electrical','does_not_establish_safety_or_rootcause','unknown','write','electrical safety not proved')
 contributions=merge_contributions(nodes,edges)
 addendum=pinned_ref(B+'firmware-rtp-producer-20261028df/cross-core-slg-addendum.md')
 refs['slg']=addendum
 node('df.slg_data','configuration','Image0 AP_EXCO data+0xe6 bit0 OR uint16+0x2fc','slg',address='0x2000ff14',address_domain='selected-image0 CPU data',limitations=['Upstream writers and physical meaning unresolved; whole liveimage0 identity unproved'])
 node('df.slg_writer','function','Image0 derives SLG boolean into remote AP_EXCO context','slg',address='0x2fb44',file_offset='0x2fd44',address_domain='selected-image0 Thumb VA',attributes={'write_range':'0x2fb60..0x2fb76','expression':'context[0x3d8] = ((data.u8(0xe6)&1) | data.u16(0x2fc)) != 0'})
 node('df.slg_context','state','Image0 context+0x3d8 / image1 remote alias0x45015c80','slg',address='0x20015c80',address_domain='selected-image0 CPU data',attributes={'image1_remote_alias':'0x45015c80','resource_context':'0x200158a8'},limitations=['SLG short source label only; no expansion or electrical effect inferred'])
 node('df.capture8','evidence','Separately frozen eight-window executable candidate','capture8',limitations=['Initial df.logger graph node is a different earlier host-only prototype; independent integration review in DG/reviews; target outcome not asserted here'])
 edge('df.slg_data','df.slg_writer','supplies_boolean_operands','static','slg','data+e6 bit0 OR u16+2fc')
 edge('df.slg_writer','df.slg_context','writes_boolean','static','slg','image0VA2fb60..2fb76; file=VA+0x200')
 edge('df.slg_context','df.contextflag','remote_resource_alias_then_mirror_to_C_plus7','static','slg','mode0 SRAM+0x25000000; image1 resolver; context+3d8')
 edge('df.contextflag','state.mode1','selects_alternate_limit_and_fixed_A_branch','static','slg','C+7 derived from AP_EXCO SLG')
 edge('de:ap-exco','df.slg_context','names_same_cross_core_boundary','static','slg','DF resolves AP_EXCO selected directory to context; Linux upstream field writer unclosed')
 edge('de:_ZN21DimmingBackendRoseMQD17t_SetQdSeneDetectEP22BackendQdSceneDetect_t','df.slg_data','unproved_register_to_field_bridge','unknown','slg','FRC writes are distinct source facts; propagation to AP_EXCO data+e6/+2fc not established')
 edge('df.package','asset.qd.selected','same_distributed_asset_identity','static','slg','bad60bca selected official factory package identity')
 edge('df.contextflag','hypothesis.rtp736','narrows_selector_source_not_physical_producer','inferred','slg','positive cross-core source bridge; exact live writer timing still absent')
 edge('df.capture8','interface.count_window','implements_fixed_exact_length_read','static','capture8','Cycle R/M/C/P/N/H/L/R; fixed N address and36-byte length')
 edge('df.capture8','interface.pointer_window','implements_fixed_exact_length_read','static','capture8','P fixed16-byte request; no pointer dereference')
 for case in ['case.hdmi_fail_A','case.hdmi_fail_B','case.working_movies']:
  edge(case,'de:content-route','constrains_candidate_explanation','inferred','controls','Failing and working content/composition controls must all be explained')
 return dict(schema='s95f-evidence-graph-v1',scope='Offline graph; evidence classes are provenance, not probability. No executable instructions or private values.',hash_semantics='Source refs pin original retained report bytes; redacted public bytes may differ. OEM identity pins identify assets, not running code.',nodes=nodes,edges=edges,contributions=contributions)
if __name__=='__main__':
 from validate_graph import validate
 graph=build();validate(graph,ROOT);(HERE/'graph.json').write_text(json.dumps(graph,indent=2)+'\n');print('DG_GRAPH nodes='+str(len(graph['nodes']))+' edges='+str(len(graph['edges']))+' target_calls=0')
