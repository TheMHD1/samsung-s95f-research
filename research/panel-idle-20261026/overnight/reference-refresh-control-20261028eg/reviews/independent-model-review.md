# Independent EG source/model review

**PASS for the bounded selected-source model and retained-field logging proposal; no blocking correctness finding.** This review does not qualify a live hook, code/table write, actual historical copy sequence, runtime execution frequency or a prevention fix. Only new review artifacts were written. There were no TV, root-transport, network or OEM execution operations.

Reviewed frozen inventory SHA-256: `972fa87454ff935b42c1c5d3e1d380a2a64baa5893313809b7e7d8765696d8fe` (all seven entries match). Model SHA-256: `25676e8d0d06404e909097ec1ac17faaff22ee558fd56e9679e799c4e464bc28`. Source audit SHA-256: `be0481dcd3f122122132c8b64e33d32c961a433f800fb5d1df71e7ee6cc74ce3`. Input provenance SHA-256: `4338f3fee1794f7efb1adcadd1f4ad308c422464ec80f0681de5c0b52f44babb`.

## Source and branch findings

The selected 5,242,880-byte package is SHA-256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. Image1 file offset is VA+0x40200. All reported instruction/literal anchors and complete range hashes match its exact bytes. Independent supplementary checks cover the mirror reload, counter reloads, pointer reloads, copy argument loads and dispatcher bypass targets, rather than checking only the parent anchor subset.

- Getter 0x38f4 loads CPU0x20000500. Adding context offset0x6c7 gives CPU0x20000bc7, the captured C+7. There is no extra pointer dereference in that getter.
- In 0xc27c..0xc2a2, the initial byte selector is compared with the u16 at CPU0x200004c2. Equality bypasses rearming. On inequality, another byte load is stored to that halfword, then the stored mirror is reloaded and tested: nonzero seeds CPU0x200004c4 to1, zero seeds it to0. The model's stable-selector assumption correctly reduces these operations to `synchronize`. Nonzero selector values other than1 are handled correctly; a halfword mirror above255 cannot equal a stable byte selector.
- Caller 0x4446 is gated by a separate byte loaded at0x4440. The audit does not establish how often this caller runs. The rest of c250 has other behavior outside the modeled synchronization block; the model does not represent the entire function.
- Dispatcher0xb812 publishes the returned A pointer at CPU0x20000494; 0xb81e publishes B at CPU0x20000498. It reloads B and checks header byte+1 at0xb824 before calling0x1c12c. A nonzero refresh counter after that call sends 0xb830 to0xb878, which branches to the dispatcher epilogue. This bypasses ordinary comparison while the counter remains nonzero.
- 0x1c12c returns early for a zero counter or zero C+7. Header row is read as a u16 at actual B+6. Row0 takes the top path first; otherwise equality with `(u32 height)-1` takes bottom. The calls supply B+8, size0xb60 (2912 bytes), and fixed top/bottom destinations CPU0x20015000/CPU0x20015f10 to the selected copy routine0x70c. This is copy-call intent, not proof of atomic copy completion in a live invocation.
- Counter increments are stored by STRH and then reloaded by LDRH before the compare against2. Thus65535 increments to stored0. The final BLE is a signed condition, but its input is a zero-extended halfword in0..65535, so `counter > 2` is the correct model over the entire admitted range. A counter initially greater than2 can be cleared even on a nonboundary call, provided the entry guards admit it.
- Height is loaded as a halfword and decremented in a 32-bit register. Height0 gives0xffffffff, which no u16 row can equal; it does not turn row65535 into bottom. At height1, row0 still takes top precedence. The model implements both cases correctly.

Starting from seeded1, two qualifying events reach2 and then3, which is cleared. The bounded code has no state marking a specific top or bottom destination as already refreshed. Top/top, bottom/bottom, top/bottom and bottom/top are all admitted under stable modeled inputs. Consequently, **two boundary events do not guarantee distinct buffers or one refresh of each buffer**. Conversely, this permitted path does not establish that real producer scheduling supplied repeated boundaries, that either buffer was stale, or that any fault was caused by refresh order.

## Raw-input provenance and observations

All36 entries in `input-provenance.json` were independently rehashed: the selected package, five accepted DP results and30 corresponding M/C/P windows. Every retained window is present in its exact accepted result's raw-file list with matching declared length and SHA-256. The provenance manifest covers precisely the selected package and all files consumed by the audit; there are no extra unpinned audit inputs in that set. All ten reported M/C/P field decodes agree with the original bytes.

The parent audit itself pins the selected package and checks raw-window hashes against each saved result; it does not directly enforce the separate input-provenance manifest or a hardcoded result-file hash. That is a verification composition issue, not an observed integrity failure: the frozen source inventory pins the provenance manifest, and this independent review explicitly verifies every manifest file, every result hash and every result-to-window relationship. Running `audit.py` alone is therefore a source/row consistency check, not a substitute for this provenance verification.

All ten retained boundary samples have refresh counter0 and trainer control4a2=0 at their sampled times. Those two endpoint samples per trial discard intermediate sequence history. They do not prove the trainer never ran, that the refresh counter stayed0, that both buffers were refreshed, or that the corresponding dynamic B pointer identifies a historical header. M+34 and M+36 correctly map to CPU4c2 and CPU4c4; P+4/P+8 correctly map to CPU494/CPU498. The M and P windows are separate sequential reads.

## Limits carried forward

The pure model assumes stable inputs within each modeled block. Actual source rereads selector, mirror, counter and B pointer, including reloading B before copy; it provides no snapshot/locking proof against interrupts or another writer. The model is not an interrupt, DMA, scheduler, copy-atomicity or physical-input model. The ten halfword-aligned literal references are a syntactic bounded scan, not a complete reachable writer census or exclusion of computed/cross-core writes. The selected c250/1c12c bodies were not among the four small live code fingerprints.

Retaining extra fields from existing DP reads is a source-directed observability improvement. It adds no ability to observe the actual B header row/flag at a historical call, every boundary event or the producer's physical acquisition. A250ms sample can miss the full sequence. The proposed54-byte checkpoint requires its own shorter-observation receipt bound and implementation review; this source review does not approve EH's implementation or any target deployment.

## Verification

The frozen audit passes107checks in both normal and optimized Python. The six model unit tests pass in both modes. `reviews/independent-checks.py` passes11,559checks in each mode: all source/inventory/input relationships, supplementary source dominance/reload anchors, all256selector byte values across mirror/counter edge cases, and source-derived boundary/guard/height/counter truth tables including signed-compare and u16-wrap edges. No test uses Python assertions that disappear under `-O`.

Commands use `PYTHONDONTWRITEBYTECODE=1`; source checks additionally set `PYTHONPATH=/tmp/tcon-capstone`. Results and exact source pins are recorded in `reviews/independent-validation.json`. No frozen source was changed, and no additional functional tests are required absent a source change or new finding.
