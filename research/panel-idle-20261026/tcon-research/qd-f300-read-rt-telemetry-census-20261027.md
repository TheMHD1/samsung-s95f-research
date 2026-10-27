# F3:00 read census: fixed-root fields and RT boundary

Recorded 2026-10-27 UTC. This is a bounded offline follow-up to the earlier
301-position `F3:00` selector census. It reads only the retained selected
5 MiB profile. It made no TV, root, network, USB, UART, I2C, controller,
getter, setter, or firmware call and constructs no runnable command.

## Result

The finite `F3:00` read table contains **no direct getter for the known
AP_RTP live/history fields** and no direct transition to the generic logical
reader at linked VA `0x637c`. The three selector leaves that directly use the
fixed-root accessor `0x47010000` are now positively bound to three *other*
configuration rows:

| selector | linked leaf / stored FILE | exact returned source | configuration row | selected-package initial value |
| ---: | --- | --- | --- | ---: |
| `0xf4` | `0x21c9c` / `0x21e9c` | bit 0 of byte `0x470129da` | `AP_SBD`, first region `+0x02` | `0` |
| `0x144` | `0x21cf8` / `0x21ef8` | low 11 bits of halfword `0x47012748` | `AP_ZA`, first region `+0x248` | `0` |
| `0x1b4` | `0x21d9c` / `0x21f9c` | byte `0x47013826` | `AP_HUT`, first region `+0xaa` | `0` |

This is the useful new closure beyond the old selector count: the three
apparently nearby `0x4701xxxx` values are not anonymous RT inputs. The exact
21-row mapping table places them outside both AP_RTP destinations
`0x47012400..0x470124ff` and `0x47010000..0x470123ff`.

Two are also paired with ordinary `F3:00` write-table leaves: selector
`0xf4` stores the incoming low bit to the same AP_SBD field, and selector
`0x144` clamps its incoming value to `0x400` and stores the resulting
halfword to the same AP_ZA field. Selector `0xe0` can additionally set the
AP_SBD flag while changing another bounded AP_SBD selection. Selector
`0x1b4` reaches the common no-op/default write target. These writer facts
classify provenance; they are not recommendations to send those commands.

No source-backed F3:00 read candidate was found that would expose the RT bit
at root `+0x240a`, the saved fields at `+0x2466/+0x2484/+0x24aa/+0x24ac`,
or a newly recovered RTP scan/input discriminator. The correct conclusion is
a bounded negative for this dispatcher, not absence of such state elsewhere
and not a claim that the three non-RT fields lack other computed aliases.

## Inputs and corrected coordinate model

| input | SHA-256 |
| --- | --- |
| `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` (5,242,880 bytes) | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| prior finite-interface report `qd-profile-open-register-read-route.md` | `c50aee500fd8ff69000e0ae7c59dec72b4097062d350b2b93fdb19e8643ef27c` |
| positive AP_RTP loader report `qd-config-rtp-table-load.md` | `0da4998c58fa503ab8d934b9e250e57566908ef8a80f8d1dc7814aeedd34f29b` |
| independent loader review `qd-config-rtp-table-independent-review.md` | `4afe3ff9e2d87ef355999a47acf2bea14959bd711458c508d49d1826c6c4112f` |
| corrected generic-reader arithmetic erratum | `c5835ff06c1e068ecc3c985c1cae4b3f22841138174a5ca42226eec8005480d3` |

Image 0 begins at container FILE `0x200`; throughout this report,
`FILE = linked VA + 0x200`. The earlier open-register report's table shape
and bytes remain useful, but its statement that image-0 FILE offsets and
linked addresses coincide is superseded. For example, the dispatcher is
linked `0x21624` and stored FILE `0x21824`; the getter is linked `0x2174c`
and stored FILE `0x2194c`.

Current controller-flash equality with this selected packaged profile remains
unproved. Configuration bytes below are package initialization values, not
live reads.

## Finite dispatcher revalidation

The pinned dispatcher FILE `0x21824..0x21875` compares command `0xf300`, calls
linked getter `0x2174c`, and then calls linked helper `0x5924` with
`(command, selector, value)`.

Getter `0x2174c` accepts exactly:

* 189 aligned selector positions `0x24..0x314`, decoded by the relative
  branch table stored FILE `0x219b0..0x21ca3`; and
* 112 aligned positions `0x31c..0x4d8`, handled by the separately pinned
  bounded helper linked `0x21708` / FILE `0x21908`.

That is the same finite total of 301 positions reported earlier. The
reproduction independently decodes all 189 relative targets, obtains 161
distinct targets, checks the exact 29 selectors that share the zero-return
leaf, and verifies the second-range count. Neither linked `0x637c` nor any of
its three known direct callers (`0x11058`, `0x1148c`, `0x2a2f8`) is a branch
table target. Those caller addresses are linked VAs; their stored locations
are each `+0x200`.

The main getter acquires several unrelated object bases. Its fixed-root
accessor is linked `0xef94`, stored FILE `0xf194`, and consists of:

```text
ef94  ldr r0, [pc, #0]
ef96  bx  lr
ef98  .word 0x47010000
```

Manual CFG inspection of the hash-pinned getter identifies only the three
fixed-root leaves in the Result table. Other selector leaves with offsets in
the `0x25xx/0x26xx/0x27xx` numerical range are not automatically fields of
this root: many use the separate bases loaded by accessors such as linked
`0xef9c` (`0x2000d71c`). Numeric proximity is not an alias proof.

## Positive configuration-row binding

The 21-entry table at FILE `0x3ccbc`, stride `0x1c`, gives these exact rows:

| row | name | first destination / length | second destination / length |
| ---: | --- | --- | --- |
| 7 | `AP_ZA` | `0x47012500 / 0x270` | `0x2000f560 / 0x262` |
| 8 | `AP_SBD` | `0x470129d8 / 0x34` | `0x47012a0c / 0xd3c` |
| 14 | `AP_RTP` | `0x47012400 / 0x100` | `0x47010000 / 0x2400` |
| 17 | `AP_HUT` | `0x4701377c / 0x3e0` | `0x47013b5c / 0xc60` |

Therefore:

* `0x470129da = AP_SBD first + 0x02`;
* `0x47012748 = AP_ZA first + 0x248`; and
* `0x47013826 = AP_HUT first + 0xaa`.

The selected package directory independently has type-4 records for all
three. Their first payloads begin at FILE `0x172e00` (`AP_ZA`), `0x173600`
(`AP_SBD`), and `0x188a00` (`AP_HUT`). Their declared first lengths
`0x26e`, `0x34`, and `0x112` cover the respective field offsets. The exact
initial bytes at FILE `0x173048`, `0x173602`, and `0x188aaa` are all zero.
The loader's successful runtime execution and later mutation are not proved
by those packaged defaults.

The AP_RTP row ends at `0x470124ff` in its first destination and
`0x470123ff` in its second. None of the three F3:00 fields overlaps it. This
is address/table evidence, not a semantic expansion of `SBD`, `ZA`, or
`HUT`.

## Writers and read effects

The paired write table has these exact targets:

| selector | linked target | bounded effect relevant here |
| ---: | ---: | --- |
| `0xe0` | `0x2cd14` | calls linked `0x25c16`; for a bounded nonzero selection, that helper may set AP_SBD `+2` to one when its selected value changes |
| `0xf4` | `0x2cd26` | stores incoming bit 0 to AP_SBD `+2` |
| `0x144` | `0x2cdba` | clamps to `0x400`, stores halfword to AP_ZA `+0x248` |
| `0x1b4` | `0x2cf4c` | common no-op/default path; no paired F3:00 store to AP_HUT `+0xaa` recovered |

The three selected **read leaves** themselves contain loads/masks and no
stores. That does not make a controller transaction state-free. The parser
updates its command/selector/transmit state, and common post-getter helper
linked `0x5924` sums bytes of the command, selector, and returned value and
stores a checksum byte to RAM `0x200008e9`. No claim is made that all called
getters elsewhere in the 301-position API are side-effect-free.

The immediate-form access census and direct configuration loader establish
the sources above. They do not prove an exhaustive absence of every possible
computed pointer alias in the full firmware. No consumer edge from any of
these three leaves to the known RT producer, image-1 scan input, or generic
logical reader was recovered in this bounded dispatcher CFG.

## Reproduction

Run locally only:

```text
python3 qd-f300-read-rt-telemetry-census-20261027.py \
  ../overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin
```

The checker uses only Python's standard library. It verifies the whole-file
identity, corrected coordinate slices, all 189 first-range branch entries,
the 112-position second range, three fixed-root targets, 21-row configuration
mapping, selected directory records/default bytes, and paired write targets.
It neither emits nor accepts transport framing.

Pinned source slices include:

| stored FILE slice | bytes | SHA-256 |
| --- | ---: | --- |
| dispatcher `0x21824..0x21875` | 82 | `5f9a3da21a8aff22610a23c58b4e79bc20836d4111a456ccb393044616abacbe` |
| main getter `0x2194c..0x21fef` | 1,700 | `fc3bbd7a16650a34ce0105c0174f6e5099e8f0fc5722844649149016c1cdea07` |
| first branch table `0x219b0..0x21ca3` | 756 | `f5e7defc0e7189ddd0f4ce2c5a7b31b0124ea9248e003c895e3e8a54112485dc` |
| response bookkeeping `0x5b24..0x5b59` | 54 | `a8dc7f55717424be6f692640e86c7961f4e226936f9852ac4887d6d7a4286607` |
| configuration map `0x3ccbc..0x3cf07` | 588 | `669adda911a2e5bf5b053ab486f11c2611e115b284eeaec79c58e5876fbad287` |

## Limits

This report does not prove current-flash identity, live field values,
execution of the packaged loader, meaning of the three configuration names,
or physical panel behavior. It does not broaden the corrected generic-reader
route, which has separate caller and bounds gaps. It does not infer that an
unexposed RT field is absent, unchanged, or causally responsible for a black
panel. No read candidate or live experiment is proposed from this negative
dispatcher result.
