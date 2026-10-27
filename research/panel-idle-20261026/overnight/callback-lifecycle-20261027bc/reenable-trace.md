# Descriptor-8 callback lifecycle and bounded re-enable edge

Recorded 2026-10-27 UTC. This is an offline selected-package trace only. It
made no TV, root, network, USB, controller, register, UI, power, reset,
instrumentation, build, patch, or firmware request.

## Result

The selected image contains a positive ordinary handoff path that re-enables the IRQ
saved as descriptor 8. Descriptor 8's own installed callback conditionally
disables its saved IRQ on its bit-3-one work branch and clears its pending bit
at completion. A distinct descriptor-`0x1c` callback, configured and enabled
by selected startup code, contains a conditional branch that clears
descriptor 8 pending and writes its enable bit. No execution schedule is
established.

This is **not a demonstrated post-fault recovery**. The fault teardown
disables descriptor `0x1c` first and descriptor 8 later. The source edge
therefore proves an ordinary callback-to-callback handoff only; after that
teardown there is no demonstrated normal dispatch route into it. An already
active callback or a separately established owner re-enable remains possible;
neither is observed here. Live execution, gate values, IRQ state, and any
physical panel effect are also unobserved.

## Source identity and coordinates

The selected profile
`selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` is
5,242,880 bytes with SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
For image 0, stored `FILE = linked VA + 0x200`.

The authoritative starting BA report
`mute-request-consumer-20261027ba/staged-consumer.md` has SHA-256
`7e3b2a3b25360f022af1399b166afb9413bef698ca1bf579e2f36d0d929ee7a2`.
It established the descriptor lookup, descriptor-8 registration, and fault
teardown. This follow-up checks their ordinary counterpart and handoff edge.

## Registration and startup caller

The complete enclosing registration body is linked
`0x1e47c..0x1eb35`, SHA-256
`318d15a1c1cb53a00219e72b355f297ca210e4e141c4b64ea5b6db97b6d6eadf`.
A finite halfword-aligned direct-`BL` census finds one direct caller:
startup callsite `0x39b8e`. The containing startup slice
`0x39b60..0x39baf` has SHA-256
`1d588034fe1142f5a5cf29e460295cb9eb8ff55525f0df6ae1b7d94c1ace2a22`.
This is a positive startup edge, not proof of live completion.

At `0x1e702..0x1e70c`, the registration body passes index 8 to claim helper
`0x13aa8`, preserves its return in `r5`, and calls descriptor lookup
`0x38c24`. At `0x1e712` it stores the returned descriptor pointer through
literal CPU `0x20000884`; at `0x1e796..0x1e79c` it installs Thumb callback
`0x132c1` at descriptor `+8`.

The claim helper returns the input index after setting descriptor byte `+0xc`
to one, but returns `0xff` when already claimed (or for an invalid high
index). The enclosing registration does not test `r5` against `0xff` before
the lookup. Thus all subsequent descriptor-8 conclusions are conditional on
the successful fresh claim represented by `r5 == 8`; this is an explicit
failure boundary, not a live result.

The same registration body configures descriptor `0x1c` at
`0x1e7aa..0x1e806`, installs Thumb callback `0x13465`, clears that
descriptor's pending bit through `0x1b024`, and enables its IRQ through
`0x1b16e`. This supplies a positive ordinary dispatch route for the distinct
callback that contains descriptor 8's ordinary handoff edge.

The previously reviewed [AA invocation trace](../ordinary-invocation-20261027aa/invocation-findings.md)
supplies the packaged descriptor-28 / IRQ59 / vector-wrapper `0x26989`
identity for this dispatch infrastructure. The present verifier pins its
callback installation and startup enable, not a fresh live vector read.

## Descriptor-8 callback: local disable and completion

The complete descriptor-8 callback is linked `0x132c0..0x13345`, SHA-256
`2e472ef163d2a285a67628abaef6195cdc824f781654e471f4e9659eb51e7a25`.
It has no direct `BL` callers in the nominal image; its positive route is the
installed callback pointer above. The separately reviewed vector/descriptor
work identifies the dispatch wrapper, but this report does not use that to
claim a live invocation.

At `0x132ca..0x132d4`, the callback extracts bit 3 from the word reached
through its input descriptor. Zero skips the disable and larger work branch,
joining the completion path at `0x1333c`. On the bit-3-one branch,
`0x132e2..0x132ee` loads CPU `0x20000884`, dereferences the saved descriptor,
loads signed IRQ byte `+4`, and calls `0x1b0b8`. That helper
writes the indexed bit through base `0xe000e180`, the NVIC ICER-class
clear-enable register family. At callback completion, `0x1333c..0x13340`
loads its input descriptor IRQ and calls `0x1b024`, whose fixed base is
`0xe000e280`, the NVIC ICPR-class clear-pending family. Within this complete
callback body there is no ISER-class re-enable call.

These are software requests to standard register families. They do not prove
the live IRQ value, ordering against an observed blackout, or hardware
acceptance.

## Positive ordinary counterpart: descriptor-0x1c callback enables descriptor 8

The complete installed descriptor-`0x1c` callback is linked
`0x13464..0x13759`, SHA-256
`ceb2219987046cb185913963cda6583abc9822e845ddbfdab30053f50c735d5f`.
Like descriptor 8's callback, it has no direct `BL` callers in the nominal
image and is reached positively through its registration slot.

The handoff branch is guarded by all of the following source conditions:

1. At `0x134ac..0x134b6`, bit 3 of the word reached through the callback's
   input descriptor must be one; zero branches around the larger body.
2. Two separate loads of the byte at CPU `0x2000087c`, at
   `0x134c2..0x134c6` and `0x134ee..0x134f2`, must each observe nonzero.
   Either zero arm sets `0x2000087c` to one and returns early. The two loads
   must not be collapsed into one stable observation: the field can in
   principle change between them and other writers were not globally
   excluded.
3. At `0x1351e..0x13522`, the saved descriptor-8 pointer loaded through CPU
   `0x20000884` must be nonzero; zero branches around the handoff actions.

After the second nonzero observation, `0x134fc..0x13500` separately clears
CPU byte `0x2000087e`; it does **not** clear the `0x2000087c` gate byte. When
the remaining gates reach the positive branch, the callback updates a bit in
the register reached through descriptor 8, then:

* `0x1353a..0x13542` loads descriptor-8 IRQ `+4` and calls `0x1b024`, the
  ICPR-class pending-clear helper; and
* `0x13546..0x1354e` reloads the same IRQ and calls `0x1b16e`, whose exact
  indexed write resolves to base `0xe000e100`, the NVIC ISER-class enable
  family.

This is the bounded positive ordinary enable edge. It is in a different
callback from descriptor 8's own disable/clear lifecycle. Its presence alone
does not establish a post-fault route to executing that owner callback.

## Relationship to fault teardown

The BA fault-teardown body `0x96d8..0x9745` first looks up descriptor `0x1c`
at `0x96e4..0x96e6`, loads its signed IRQ byte `+4`, and calls ICER-class
helper `0x1b0e8` at `0x96f0`. It later looks up descriptor 8 and calls the
same helper on its IRQ at `0x9724..0x9730`. `0x1b0e8` is byte-identical in
its complete 24-byte body to `0x1b0b8` and uses the same `0xe000e180` base.

Consequently the ordinary descriptor-`0x1c` handoff cannot be labeled a
post-fault recovery edge: its owner is itself disabled earlier in the same
teardown. A post-fault interpretation needs a separately proved way to make
descriptor `0x1c` dispatchable again. This finite trace neither finds nor
rules out such a path. It also does not establish global absence of other
enable or disable paths.

## Bounded conclusion

The positive source lifecycle is:

```text
startup 0x39b8e
  -> registration 0x1e47c
     -> claim/save descriptor 8; install callback 0x132c1
     -> install and enable descriptor 0x1c callback 0x13465

descriptor 8 callback 0x132c0
  -> if descriptor word bit3=1: ICER-class disable of saved descriptor-8 IRQ, then work
  -> if bit3=0: skip disable/work
  -> ICPR-class pending clear

descriptor 0x1c callback 0x13464 [ordinary dispatch; bit3, two 087c reads, saved-pointer gates]
  -> separately clear CPU 2000087e
  -> ICPR-class clear of descriptor-8 IRQ
  -> ISER-class enable of descriptor-8 IRQ

fault teardown 0x96d8
  -> ICER-class disable of descriptor-0x1c owner
  -> later ICER-class disable of descriptor 8
```

This selected-code ordinary handoff does not weaken a post-fault
disabled-owner explanation by itself. It demonstrates how descriptor 8 is
enabled during ordinary callback flow, while leaving the post-fault restart
of descriptor `0x1c` unresolved. It does not prove callback dispatch, another
state transition, or hardware behavior after the teardown.
No protection bypass, return guard, high-bank, storage, POFLG, bootloader, or
patch branch was followed or proposed.

## Reproduction

Run locally only:

```text
python3 reenable-reproduce.py
python3 -O reenable-reproduce.py
```

The standard-library verifier pins the package and BA identities, complete
function slices, registration/callback pointers, finite direct-call census,
exact branch gates, saved-pointer references, and the ICER/ICPR/ISER helper
edges. It performs zero target operations.
