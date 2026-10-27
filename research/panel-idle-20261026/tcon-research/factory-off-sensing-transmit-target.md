# UID `0x506e` factory setter: transmit target audit

Subsequent evidence: the [44-byte live diagnosis-backend capture](../overnight/factory-backend-runtime.md)
now binds the running wrapper's actual table+0x3c and method GOT to the paired
implementation below. This closes that specific live-pointer gap described
in the original pass. It still does not execute the factory route or prove
the VE guard outcome, a storage write, reload, persistence or physical repair.

This is a bounded, offline trace of the copied factory definition and
`TIFSDaemon`. It performs no FactoryService request, does not write storage,
and sends no panel/TCON command.

## Item identity and dispatch selector

`FactoryIndexFile_Part1.dat` record at `0x8bc0` is:

```text
(UID 20590 / 0x506e, 0, 6, 0, 5, 2, 1, offset 6240 / 0x1860)
```

The serialized item node starts at `0x6919c` (not at its UID field). The
`Factory_Part1.dat` record carries UID `0x506e` at node `+0x40`, label
`Offsensing TEST Period`, and key
`db/factory/FC_STORE_LEVEL_EER_B/OFFSENSING_TEST_PERIOD`. Its driver-module
selector is **16** at node `+0x44`; the `0x10` at file offset `0x691e0` is
not the `5` in the separate index tuple. In copied
`libfactory-interface-ATSC.so`, the construction path copies 0x164 bytes from
the serialized record at `0x43998982–0x4399898c`, preserving `+0x44` for the
node used by the setter. The construction loop subsequently writes its loop
index at `0x43998a26`, so this evidence is a bounded selector-preservation
claim—not a claim that every constructed byte remains unchanged. The generic
transmit routine's own log layout confirms that node `+0x44` is
`uiDriverModule`.

## Exact `SetDecimalValue(200802, value)` outcome

In copied `TIFSDaemon` SHA-256
`d2ebc1d11be46b4a189ec87666b68b73ae58d6f5a3c10da901c80e1125620c11`,
`FCControl::SetDecimalValue` resolves the key to the factory node and calls:

```text
0x107838  FCControlItemExecution::TransmitAItemToChip(node, value, &skipSaving)
```

`TransmitAItemToChip` at Thumb `0xc5e8c` reads `node+0x44` and uses a 28-entry
`TBH` dispatcher at `0xc5ef8`. Selector **16** resolves to `0xc5f34`, not the
unsupported selector-5 arm. It makes two PPI calls with UID `0x506e` and the
requested value:

```text
0xc5f3e  ppi_video_system_diagnosis_set_factory_item(uid, value, &status)
0xc5f6a  ppi_ve_set_factory_item(uid, value, 1, &status)
```

The copied `libvideoenhance.so.0` resolves the second PPI symbol at Thumb
`0x46f3cc34`. It validates its VE backend object, then tail-calls that object's
function pointer at `backend + 0x354` while preserving the four arguments.
The backend loader's paired static evidence loads `/prd/usr/lib/libave.so`; the
copied `libave.so.0.1` supplies a matching backend table. The initialized
static backend table's
`+0x354` slot is
`impl_set_factory_item` at `0x2a71d0`; its PLT/GOT edge `0x90c2c / 0x5a629c`
targets `VideoEnhancerImpl::set_factory_item` at `0x29fa34`, which in turn
uses PLT/GOT `0x8e1c0 / 0x5a5478` for `ave_api_set_factory_item` at
`0x27353c`.

That AVE routine does **not** unconditionally call both downstream APIs. Its
shared-memory/check guard can return `-1` at `0x273664` before dispatch. For
UID `0x4e39` it bypasses the FRC call, but UID `0x506e` does not take that
special branch. On UID `0x506e`'s non-error route, AVE calls
`ave_frc_api_set_factory_item` through GOT `0x5a423c` and
`ave_tcon_api_set_factory_item` through GOT `0x5a61d8`. This is a concrete,
guarded route into AVE's FRC and TCON factory-item APIs, though their
downstream UID handling can still reject the request. It is not proof that a
TCON command succeeded.

The copied handler bodies resolve this UID one level further. The FRC handler
falls through to `ave_frc_api_ep_set_factory_item` at `0x242a4e`; its endpoint
only accepts UID window `0x1be6..0x1c04`, so `0x506e` branches at `0x26cb16`
to its zero-return path without an endpoint setter. The TCON handler has no
matching range: `0x506e` lies below its next `0x5084..0x509a` interval and
returns through `0x263e2c` with zero, without a lower TCON call. Thus the AVE
FRC/TCON portion is a successful no-op for UID `0x506e`; the earlier,
unresolved video-system-diagnosis PPI call can still alter the shared status.

The first `ppi_video_system_diagnosis_set_factory_item` import has GOT slot
`0x165924`. A same-process read-only GOT capture resolves it to
`0x47590fd9` in copied `libvideo-misc.so.0.1.0` (SHA-256
`fcd5faa76492151512544fd29783d33b9f63c91a863909cc0c53ba598ff9e5dd`). Its
wrapper statically forwards UID/value/status through backend function-table
slot `+0x3c`. The runtime capture proves the wrapper address and that the
implementation ELF was mapped, but does not capture the live `+0x3c` pointer.
That library's paired static loader evidence loads the acquired, runtime-mapped
`/prd/usr/lib/libvideo-ft-control-impl-sec.so.0.1.0` (SHA-256
`2a2d24ed21babd5a7f67e6bd7aa3447cb9a7316fb0234ae4e0e1a93e77650b8d`).
Its backend table `+0x3c` is `video_system_diagnosis_set_factory_item_impl`,
which dispatches to `VideoSystemDiagnosisSecImpl::setFactoryItem` at ARM
`0xaa54`. Accordingly, the downstream pairing is static conditional evidence,
not a captured live backend-table dereference.

That concrete method has cases for a small set of IDs (`0x83`, `0x9b`,
`0x434`, `0x64d`, `0x4f02..0x4f04`); UID `0x506e` matches none and returns
`-95` at `0xabf4`. Crucially, its default path does not dereference or write
the incoming Boolean out-parameter. The return is overwritten by logging
between the diagnosis call and the next check: `0xc5f72` compares the **VE**
call's return, not the diagnosis `-95`.

The following is a manually reviewed paired static control/dataflow, beyond
the checker landmarks: `SetDecimalValue` initializes the caller
skip byte to zero at `0x107822/0x107824`; `TransmitAItemToChip` copies it into
`r7` (`0xc5e96`) and initializes local integer status `[sp+0x20]` to zero
(`0xc5ee8`). The diagnosis default leaves that status untouched. AVE's UID
`0x506e` FRC/TCON no-op route returns zero; the VE check at `0xc5f72` takes
`0xc6174 → 0xc6160 → 0xc6172 → 0xc6018`, which copies integer zero back as
skip byte zero at `0xc6028` and returns zero at `0xc5fec`. The setter's
`eor/and/cbnz` predicate then reaches `0x107890`, the `SetFactoryUID` storage
call. Thus, conditional on the paired backend/non-error route, the static
result is a **reached conditional-storage path with skip=false**, not a
skipped-storage result. This still does not prove a live write, persistence,
or safe effect.

Back in `SetDecimalValue`, a zero return plus `skipSaving == false` selects the
factory-storage branch:

```text
0x107890..0x10789a  FCStorageBaseCommon::SetFactoryUID(node.uid, value, -40)
```

The destination is the `SetFactoryUID` PLT relocation at GOT `0x165ad0`.
Because both PPI calls receive the status/skip-saving pointer, they can mutate
that flag; static code here does not prove that it remains false for UID
`0x506e`. Storage is therefore **conditional**, not guaranteed.
Consequently, the earlier no-op conclusion is withdrawn: this item reaches two
real PPI dispatches before factory storage. A FactoryService success reply
still cannot prove a TCON command or that the running `deviced` process has
observed the new stored value.

## Relation to the device-side read

Separately, copied `deviced` reads UID `0x506e` in
`OledDevice::OffSensingDisabledInFactoryMenu`: `factory_get_data` must return
1 and its integer must equal 6 to produce true. Whether an already running
daemon reloads a later stored value, or reads it only at a lifecycle point, is
not established by this trace.

The copied ELF inventory has one named implementation of the `value == 6`
predicate, in `deviced`; `TIFSDaemon` uses UID data through generic nodes.
This does not prove no unacquired component reads the key, nor that the
factory storage library cannot notify observers.

## Safety result

`SetDecimalValue(200802, 6)` reaches PPI dispatches; under the manually
reviewed paired backend/non-error route, the diagnosis return is discarded and
the status flow reaches the factory-storage call. This is static evidence for
the copied/runtime-mapped binary set, not proof of a live write or a safe
workaround. No write is recommended.

## Reproduction

```sh
python3 tcon-research/factory-off-sensing-transmit-target-reproduce.py
```

The script hash-gates the copied inputs and verifies selected landmarks:
serialized-node selector, module-16 dispatcher target, PPI calls, VE-to-AVE
forwarding, AVE FRC/TCON calls, setter storage branch, and storage relocation.
The complete ignored-return/out-status/CFG conclusion is a manual paired-path
review, not an automatic checker proof. It performs no device action.
