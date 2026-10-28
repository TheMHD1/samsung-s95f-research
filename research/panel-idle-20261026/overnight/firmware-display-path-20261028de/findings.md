# Display-path static evidence after complete firmware extraction

The authenticated package contains the exact AVE and six display-driver bytes already retained from the running system. This closes package identity and exposes the packaged NPC resource used by the QD backend. It does not reveal a different firmware version, establish a physical fault, or resolve the packed RTP sample producer.

DE performed host-only reads and static decoding. No TV/root/network operation, OEM executable, display action, GPIO request, debug enable, module load, or memory write ran. Private disassembly/catalog evidence stays under `private/`; public artifacts contain source identities, structural metadata and bounded address evidence.

## Identity and scope

`PRD:/usr/lib/libave.so.0.1` is 6,657,066 bytes, SHA256 `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`, byte identical to the retained live-library copy. The six module matches and complete extraction results remain frozen in DB's `accepted-report.md`/`accepted-outcomes.json`; DE does not rerun extraction. Existing monitor/kernel analyses of these same bytes remain valid prior evidence, rather than new discoveries.

`PRD:/usr/fwupdate/controls/libtconfw.so` SHA256 `32b8b7005a239e2cbfe0327f2ef829c2571b2138300583d07a7c3af1a1696df4` is a firmware-update plugin. Its seven AVE entry points resolve to AVE functions in this exact package. The TCON-specific update branch calls `ave_tcon_api_do_update` at0x284200, buffer variant at0x28437a, and all-update-done at0x2853dc. These become character-device ioctls, not a recovered packed-RTP producer. Alternate dimming virtual branches are separate; this task does not execute an updater or assign undocumented enum meanings.

All AVE addresses below are ELF link VAs; for this library's relevant text they equal file offsets. They require a checked current load bias before use as process addresses. Module numbers are section offsets. BSS symbols have no initialized-file offsets. The runtime backend object/vptr was not measured by DE.

## Actual upstream content path

| Edge | Exact anchor | Qualification |
|---|---|---|
| QDDimming vsync -> scene construction | call0x17b56e to0x1795d0 | Real PLT-resolved edge, feature gates still apply |
| scene construction -> QD scene backend | indirect call0x1797a0, vtable offset0x70; relocation0x5a159c ->0x1c6370 | Requires active RoseMQD backend vptr; static table binding is exact |
| scene construction -> NPC selection | indirect call0x179836, vtable offset0x154; relocation0x5a1680 ->0x1c72dc | Same runtime-vptr qualification |
| QD backend construction -> NPC JSON load | constructor call0x1c85d2 ->0x1c7f3c | Resource opened through0x1c8018 |
| NPC selection -> controller writes | call0x1c73de, loop0x1c73aa..73e6 | Exactly16 sends on changed selected index, followed by `set_npc_lut`0x1c73ee |
| final duty -> controller/FRC |0x1c62b4 sends F3:0x128;0x1c62c4 writes FRC0x42b48 | Distinct from power-control/reset |

`QDDimming::t_vSyncCallBack` also calls screen-saver construction at0x17b580. The existing `content-static-power-path.md` distinguishes that route from Deviced DPMS/off-sensing and monitor-originated power recovery; it must not be collapsed into a single “screensaver turns the panel off” claim.

The scene backend reads request byte offsets0x24/0x25 as gates. A changed request word at+0x60, named by the local symbol `siPreScreenProtectedApp` and log label `ScreenProtect`, is written to FRC0x42618 through0x1c63fe. Further scene fields produce FRC writes0x40e70/0x41ec4/0x47028 at0x1c6454/65a8/6624. These are actual control writes, not proposed diagnostics. A direct `sdp_write_register` call at0x1c664a writes0x76385c based on an input-derived selector. Register-address metadata does not establish electrical meaning or authorize replay.

## Exact packaged NPC resource

The loader references `/prd/usr/bin/ave/pq/LUT_NPC_Point.json` at literal0x53f7b8, opened at0x1c8018. The extracted26192-byte file has SHA256 `e13048126ad19d6890ef8c862abacc682645de4bf8131f9f97a05dc3baef3ce3`, version0.03 and three compensation groups. Each status table has16 address/value entries. The parser reads `infoTBL/status/value/addr`, converts command addresses with `strtoull` at0x1c82de and values with `strtoul` at0x1c834e, then stores the backend command tables. The original table remains private.

`DimmingBackendRoseMQD::t_SetNpcLut` uses picture-mode comparisons and request flags/brightness inputs to choose a table. It stores the selected index in backend state+0x2e40 and AVE shared memory+0x9a1c. Its change log names compensation ratio, selected NPC LUT, HDR, `isMovie`, picture mode, peak brightness and factory flag. Exact field/source mappings and gates are in `evidence.json` and [capture-recommendation.md](capture-recommendation.md).

This gives a useful mechanism shared by Home composition and HDMI content: source/picture classification and content-processing state can select different controller commands. It does not show that one selection causes blackout. A complete explanation must handle failing fullscreen PROGRAM_LABEL/PROGRAM_B, the working player-Home composition, and working Cars3/PROGRAM_A/PROGRAM_09 controls. A Home-tab policy alone does not cover those controls; a “dark scene” label alone also fails to identify the hardware statistic or transition.

## Fault, blanking and GPIO boundary

The exact stock monitor remains the earlier mapped body0x2695fc. It can call the power wrapper with0 at0x26977a and2 at0x269ae0/269b26; the wrapper0x25c2e0 submits request0xc010749f word0=0x29(decimal41), word1=argument. The terminal zero branch stores `qd_tcon_off=1` at0x269786. The existing retry-predicate and runtime-map reports establish why a later latched1 does not prove a fresh power action. DE independently rechecked the PIC arithmetic for statebase0x5bfc20, ERR counter0x5bfc5c and latch0x5bfc78 against the packaged bytes.

Operation0x1d reads the separate raw ERR_DET path;0x1f reads decoded controller status, whose bit4 is logged as RT Protect. Neither interpretation makes a screenshot a light measurement. The QD state block/counters are historical userspace bookkeeping and can be sampled only under refreshed process identity/maps if the coordinator already has that passive logger. They do not replace the controller capture.

The exact packaged provider relocations reconfirm:

| Provider body (`tztv_frc_tcon.ko:.text`) | Read call | Direct mutations |
|---|---|---|
| PMIC0x1730 |0x17f0 `gpiod_get_raw_value_cansleep` | DT cache, `gpio_request`, direction input, free |
| ERR0x1af0 |0x1bb0 | Same |
| VDD0x1c30 |0x1cf0 | Same |
| generic get0x0fc0 |0x101c | `gpio_request`/free, despite no direction-input call in this body |
| generic get2 0x1128 |0x11f8 | request/direction input/free |

`ave_get_gpio`0x2b1018 explicitly exports, changes direction, reads and unexports. `system_read_gpio`0x2adce0 accepts a narrow system-request allowlist (0x80044901/03/62 and0x80044965 production mode), not an arbitrary fault pin number. No new passive direct-GPIO route is qualified. Reusing those “getters” would violate the present no-line-request/direction-change capture design.

CS's exact candidate DTB maps ERRgpio15.5, PMICgpio15.1, VDDgpio15.6, syncgpio15.7; current DH chip metadata supplies global125/121/126/127. TCON_ON/ELVDD/AC are micom bank3 lines5/7/1, observed global429/431/425. GPIO debug ownership metadata is not the physical line value. The candidate base DTB matches the runtime selector but has known bootloader-patched boot arguments, so full live-FDT identity remains unproved. No connector pin/voltage or asserted polarity is inferred.

## Logging and the remaining bridge

The coordinator subsequently qualified the exact filtered reader: 1,631 retained bytes, two `E/AVE QD_TCON_OFF=1` monitor rows, exit0, no root-output truncation and no producer change. Physical light was unobserved. Preserve the nonzero driver diagnostic `not_complete:4`; the stale latch messages do not establish a fresh action. Start with the finite, existing VLOG reader in [capture-recommendation.md](capture-recommendation.md), preserving its own time/size/exit evidence. Normal NPC-change and ScreenProtect-change messages are already in the producer bodies; no global/per-frame debug switch is needed to catch a real transition. A quiet window cannot prove absence of a transition outside retained history, an enabled producer, a selected backend, or a physical picture. Current tracefs lacks kprobe/uprobe control files and has only `nop` as an available tracer; event availability does not create function probes. GPIO event capture, if later technically qualified in a private trace instance, would observe only actual stock get/set calls and cannot force a new sample when the stale monitor latch skips its getter. Preserve the preexisting global trace configuration.

DF independently establishes the image1 C+7 cross-core source: the remote image0 AP_EXCO context+0x3d8 is written from AP_EXCO data byte+0xe6 bit0 OR uint16+0x2fc. The later FRC extension audit already closes the conditional stock path through chip14→SDP callback initialization, operation2, ACL and register-access indirection to a barrier/store. The instance register-base identity and propagation into those AP_EXCO fields remain unclosed; this is not an intrinsically unresolved callback. `frc-extension-and-sdp-register-path.md` supersedes the earlier first-callback gap. A bounded ASCII-label scan of AVE plus the six exact modules found no AP_EXCO/AP_RTP/PrePD/EXCO labels; this is a naming search result, not proof of unreachable code. The explicit unknown graph edge prevents a false root-cause bridge.

The next useful source closure is the controller field/transport writer matching those FRC addresses to AP_EXCO inputs, coordinated with DF. The next useful observation is an existing-log time bracket across source/content transitions paired with the already-qualified controller record and independent physical observation when available. No protection disable, table rewrite, guessed register fix, reset loop or firmware patch follows from the current evidence. A candidate fix must first explain the failing and working controls and the exact producer operand.

## Reproduction

`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/tcon-capstone python3 verify_evidence.py` passes854 exact-source/function-extent/relocation/graph checks, also under `python3 -O`. The inspector resolves ARM PLT entries by decoding their GOT target and matching the relocation, including the compact libdlog PLT layout; it does not infer entry names from ordinal spacing. Linear disassembly includes literal pools and is explicitly marked candidate evidence; selected graph edges were manually checked in their function bodies. No call-candidate count is presented as runtime execution coverage.
