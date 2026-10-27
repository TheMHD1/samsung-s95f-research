# Independent runtime/control review — mailbox record

This file is written by the parent from the independent reviewer's messages.
The reviewer remained read-only and did not create or edit this file, contact
the TV or run a network operation. Authored artifacts were corrected by their
authors/parent, then rechecked independently. This is an evidence record,
not a claim that every condition has an automated test or that a fix passed.

## Corrections before integration

* Family selection: Y23 requires PPI type0 **and** product year0x17; nonzero
  type forces legacy. Both EL and off-sensing selector descriptions now retain
  this conjunction. A pointer alone is not a live/running-object observation.
* Runtime recipe: global tuple G1 must bracket the object reads with G2;
  reading globals twice before later heap reads is insufficient. The parent
  followed G1→object fields twice→G2 for the daemon state sample.
* Base QD output: the `this+0x10` backend call is conditional on non-null,
  and the `this+0x0c` vendor leg requires inner word0==1. The vendor resolves
  to the inherited no-op slot. The report no longer calls both legs unconditional.
* RoseMQD second transport uses a mutable buffer reloaded after the first API,
  not necessarily the original candidate scalar. Its cache store precedes
  both calls; combined errors are ignored by the vsync caller.
* UI trace: the managed/native bridge must be resolved, not inferred from a
  method name. The tightened probe now hashes both assemblies and prints five
  bounded methods plus the exact P/Invoke module/entrypoint. The previous
  keyword output and curated highlights are not represented as generated IL.

## Independently checked runtime evidence

The120-byte daemon sample decodes correctly: bias0xb7c000, legacy selectors0,
EL pointer0x1182208/off pointer0x1182f78, both Y23 pointers null, local states0,
and child vptrs bias+128a28/128a90/128ab0. Power index1 agrees with subsequent
publiclcdon; public BurnIn returns0. Fresh maps match before/after. This
establishes local states, not VCONF request state, timer activity, hardware
maintenance, panel output, the earlier blackout or recovery.

The earlier child-vptr sample reused the bias/hash from a separate sample
about32seconds before; that provenance is retained. The new108-byte combined
sample freshly checks diskAVEhash/maps and the actual relocated function slot:

```text
bias f6b77000
backend vptr f711852c = bias+5a152c
slot f7118604 = vptr+d8
slot target f6d3d275 = bias+1c6275 (Thumb)
siDimLvl cache f7122958 = bias+5ab958 = 207
inner+a8 = inner+ac = 207
```

All identity/cache/duty pairs and maps match over uptime37195.51..56. The
single gate reads correctly decode byte+39=1, byte+5c=1, word+1b4=0,
controlffffffff, vendor gate89, AutoDim0 and outer-ready byte1. This places
the sampled early guards in a pass configuration, but is not an atomic
snapshot or proof of callback dispatch. Earlier callbacks can change/reload
control. Physical state is unobserved.

If invoked with the unchanged candidate, equal cache207 takes the skip branch.
This is steady-state cache suppression, **not an observed failed retry**.
The image's initial cache is-1, but runtime207 does not by itself prove
exclusive writer history, time of change or transport success.

## Static and IL checks

The final active-base/RoseMQD hash-gated verifier passes. The reviewer verified
the cache PC derivation, pre-I/O store, lack of rollback in the bounded body,
ORed statuses, ignored caller result and mutable post-API word.

The final menu probe was rerun independently against both exact hashes and
produced byte-identical174-line stdout, SHA-256
`c23bceb6b91dfe77ad4c410ed2e2783493e67f1b6d3395f0f4951d85be3456c7`.
The duration branch, button bindings, literal modes, toast argument, unchanged
managed/native forwarding and P/Invoke identity check out. It proves the
manual Pixel Refresh workflow, not the owner's automatic60s/10min prompt.

The reviewer parsed `runtime-qd-duty-cache-20261026T115305Z.json` and confirmed
its raw decoding and guards. No reviewed artifact establishes blackout
causality, a failed transport at onset, physical panel emission or a repair.
