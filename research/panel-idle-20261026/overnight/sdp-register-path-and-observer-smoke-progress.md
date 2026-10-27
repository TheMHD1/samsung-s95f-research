# SDP register-path follow-up and combined-observer smoke

Recorded 2026-10-26T19:03:42.643262+00:00. The previous goal turn made concrete progress by persisting the independently reviewed monitor/FRC analysis and current navigation. This phase adds a reviewed downstream code path and actual passive instrumentation evidence. The owner-authorized diagnostic/fix goal remains incomplete: no incident cause, physical recovery/prevention, untethered root, or permanent repair has been established.

## New static result

The [extension-to-SDP register-path report](../tcon-research/frc-extension-and-sdp-register-path.md) traces the dimming envelope beyond the former unresolved extension boundary. Compiled chip initialization selects code14 and therefore the SDP symbol name. Same-file constructor/callback relationships resolve coordinator and FRC-device indirections to operation2 decoding, its static ACL, and a register write wrapper. Under allowed access the final implementation is a barrier plus store to the mapped base plus selector. A separate dummy access table exists; upstream bypass and ignored acceptance results remain explicit caveats. None of this is incident execution evidence.

This means Linux I2C traffic alone does not cover the identified memory-mapped implementation. There is no new raw MMIO read/write or control probe. Both offline verifiers passed under parent execution and independent read-only review; all final claims were checked against exact copied ELFs. The reviewed exact bytes are:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| frc-extension-and-sdp-register-path.md | 9773 | `eb20c468e9b313b1b7c5b308f984eca2c6f259c1fff57263f9d86f74f0c37a4a` |
| frc-extension-bridge-reproduce.py | 6871 | `7e2b78b20f350535954d3864e0bfe138398dfc7f2f7ab4290aa965aab63a92ed` |
| frc-extension-bridge.disasm | 5250 | `30be87f55fcb3654c628d890b617e7f0376786bee5e9cf89f71741857de1929b` |
| sdp-frc-register-write-reproduce.py | 6727 | `6b997fb5b9951922e367b5bd8a99ff6ee8c06be101d661e510d0278e23fd96a0` |
| sdp-frc-register-write.disasm | 51900 | `9ca73b783cf175149a9d1f821ea957cd3c5b06fe6b52aa951e22aebf715ee41f` |

## Instrumentation: local failure preserved, then rejected passive run

The first archived observer revision49f4e5c passed53 offline tests and initial review but its actual public execution entrypoint recursed before staging or any network call. The local [failure record](branch-smoke-20261026t1900.onset/preflight-failure.json) documents this. A second analogous validator dispatch bug was found by inspection. Previous execution clearance was withdrawn; its archive was preserved. No TV state was created by that attempt.

The corrected revisioncf70750 captured immutable references to the frozen functions and added actual patched-orchestration regression coverage with transport forbidden. It passed55 tests and independent re-review, then was [archived](observed-branch-onset-reviewed-cf70750/archive.json) before one finite5-second passive, zero-annotation smoke. The complete [run record](branch-smoke-20261026t1901.onset/record.json) has accepted=false, technical_capture_complete=false and diagnostic_eligible=false.

The collector actually ran and retained22 monitor rows and5 Q branch rows. Q start-to-end spans were0.44,0.45,0.44,0.46,0.44seconds; process identity tuples were stable in those rows. These counts/spans are forensic observations from a **rejected** capture, not an accepted completeness or capacity result. The current physical picture was unobserved and no visible-to-black transition was annotated. No panel-health or absence claim is supported.

The strict stderr gate rejected five `--: line2: $1: unbound variable` warnings. The tool did not ignore them. Parent inspection points to an empty/departed-process result in hardened shell process parsing, but independent failure review and source correction remain underway at this document's recording time. Do not count this revision as a validated live capture tool, and do not weaken acceptance to make these artifacts pass.

The tool quiesced once, salvaged the partial raw sidecars with hashes, and completed cleanup. The persisted quiesce response exits0 with QUIESCED and empty stderr; cleanup exits0 with `0` then CLEAN and empty stderr. record.json marks both quiesce_verified and cleanup_verified true. The host process is terminal (exit1); there is no running experiment from this smoke. No reboot, key, picture/power setting, service restart or raw register control was issued by it.

## Remaining work

Fix and independently review the disappearing-process parser failure offline, preserving all rejected evidence and reviewed archives. Before any further live instrumentation run, archive exact corrected bytes. A successful short passive smoke could validate target execution and cleanup only; it cannot establish sustained full-window capacity or physical behavior. The decisive observed Apps-to-black onset still requires owner-confirmed physical annotations aligned to state and traffic. Further offline work can audit register-access gate writers, mapped-base initialization and the monitor's electrical/error history without claiming the damaged hardware is repaired.

The preceding31-file snapshot was reverified unchanged: SHA2563b784160b3ba9566c93270d01d1099000347253789f5f02664601ee9b6d429ac. New phase artifacts here have not yet been published in a snapshot manifest.

## Independent rejected-run audit supplement

The independent reader confirmed the following from the unchanged1901 partial artifacts:

- The immediate rejection is exactly five nonempty-stderr warnings from the process parser. `set -- $(p4 ...)` masked the command-substitution failure and a later positional-parameter read could fail under nounset when a process disappeared. This is a collector lifecycle/parser issue, not evidence of a TV panel fault.
- A separate dd inventory defect would also reject the run: actual191 operations =39 static +26 per Q row times5 +22 monitor reads. The draft validator expected45 static. Correcting the expected count must follow actual generated read inventory, not relaxing error handling.
- A third independent strict trace failure remains: AVOC TID1011 entered ioctl62733.646733 (fd0x21, request0xc010643a), CAPTURE_START was emitted at62733.650478, and the ioctl returned0 at62733.651341. The frozen rule rejects a call crossing the start marker. The partial capture must remain rejected even after parser/dd corrections.
- Metadata and Q sample checks pass on read-only continuation:22M/5Q, actual Q spans0.44–0.46seconds, final row completes62738.09 before trace_end62738.68. Trace retained/written counts are9750/9750 and all three markers are present. These partial checks do not change accepted=false.
- Quiesce and cleanup exit0 with empty stderr. Their checks cover named owned process groups and private artifacts, with tracing_on0 and the named trace/output/stage/expiry objects absent. This is bounded cleanup evidence, not a claim that every unrelated process on the TV is absent.

The implementation agent has prepared an offline parser and inventory correction with additional nested-shell/dead-PID regression coverage; independent exact-byte review is pending at this supplement. No second target smoke has been launched. The crossing-start rule is unchanged. Future acquisition architecture may need a separately reviewed pre-roll/boundary-accounting design; no change is made here simply to accept rejected data.

## Mapped-base origin: additional static evidence and a limit

Parent and a read-only agent followed `sdp_frc_resource_init` in the same copied SDP ELF. At.text1dfc/1e04 it materializes the `frc-reg` name; at1e08 it sets resource type0x200 (IORESOURCE_MEM), at1e10 calls platform_get_resource_byname, at1e2c calls devm_ioremap_resource, and at1e30 stores its return to instance+0x138. Resource-missing and mapping-error paths exist. Thus the base used by wrap_write has a concrete resource/mapping initializer. No current mapping or successful probe was read.

The unchanged retained display-devicetree.tar is102400B, SHA256`2be5e7807f99bbab655ceb265e3226a88095d1280bde154cb1040600990c9955`. Parent independently read member soc/sdp_frc/reg-names (8B `frc-reg\0`) and soc/sdp_frc/reg (8B hex`00b900000005f000`). The two BE32 words are0x00b90000 and0x0005f000. **This scoped archive lacks root/soc address-cells, size-cells and ranges properties.** It does not independently prove inherited cell widths or bus-to-CPU translation. An initial agent physical-address interpretation was corrected after parent challenge; do not present these words or their sum with a selector as a verified CPU physical address. A future finite passive metadata capture can close this specific gap. No raw register/memory access was attempted.

The exact five stderr messages have also now been attributed by independent review to the outer vlog lifecycle: one final while-vg check, one subsequent if-vg check, and three EXIT/stopv checks after that PID exits. The Q child had no such stderr. This supports the disappearing-process parser correction without changing the rejected capture classification.

## Corrected observer: final offline review and archive

The final correction is now independently reviewed and archived at [reviewed3aa5c94](observed-branch-onset-reviewed-3aa5c94/archive.json). Exact source38281B SHA256`3aa5c9480c8a643e14be5c6aeac62202f918d16cd9100a5b0c4ff14a5e2785ca`; tests31687B SHA256`ec4186840e22206efceab6a3fbea994e41ad586ab3068c6b51b83ad1d9411089`; design6791B SHA256`330260e0523513f72a5d2a1de2be63c002265155f0bc84797b51714153e08998`. Independent57/57 tests pass, including exact nested /bin/sh execution with unredirected empty stderr, dead/disappearing PID handling under set-e/+e, public orchestration dispatch/restoration, and actual retained artifact replay. Generated5/10/85/90-second shell syntax was checked.

The replay test pins the raw record and all salvaged sidecar/transport sizes and hashes, and asserts the original Q DATA identity before replacing exactly its two hash sections **in a synthetic in-memory metadata fixture**. This normalization tests compatibility with the corrected sampler; it is not an acquired raw metadata change, does not prove the new sampler ran, and does not change the original rejection. The original trace crossing is still required to reject. The corrected source has **not** run on the TV. No second live smoke or repair experiment was performed.
