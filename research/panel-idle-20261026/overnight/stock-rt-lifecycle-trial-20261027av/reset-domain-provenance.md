# MODE2 reset-domain provenance for the mapped RT object

Recorded 2026-10-27 UTC. This is a bounded offline source/evidence audit. It
made no TV, root, network, USB, I2C, GPIO, reset, firmware, controller, or
native-helper call. It neither requests another lifecycle nor proposes a
patch.

## Result

There is **no positive source-backed edge proving that stock MODE2 resets the
image-1 CPU or the CPU `0x20010000` RT object observed conditionally through
bus `0x47010000`**. MODE2 positively reaches an OCL mailbox request and one
retained run positively caused the Samsung USB function to disappear and
re-enumerate. The receiver and reset-domain implementation behind that OCL
request remain missing.

The selected package separately proves coherent reset/startup paths for both
embedded images. It does not prove that MODE2 invokes image 1's reset vector,
releases that core, or clears its RT object. In fact, image 1's own reset
scatter initializes the pointer slot `0x200004e0 = 0x20010000` but does **not**
write the pointed-to `0x20010000` object. Therefore even a genuine image-1
core restart would not, from the recovered scatter path alone, imply that the
fault fields at CPU `0x20012400..0x200124ff` were cleared.

The delayed post-MODE2 observation must consequently be interpreted as a
late state sample, not a reset-domain test:

- if the RT tuple is still faulted, the retained evidence cannot distinguish
  no reset, a core restart that retained this object, or a clear followed by
  re-fault before the sample;
- if the tuple is clear, that proves a sampled state change, but does not by
  itself attribute the change to a full image-1 reset rather than an ordinary
  initializer/writer; and
- USB re-enumeration alone proves neither case.

## What MODE2 positively reaches

The copied QDF path maps operation 2 to its stock off then on sequence. On the
relevant platform branch it calls dynamically bound
`sdp_ocl_reset_tcon_power(1)` on the off side and
`sdp_ocl_reset_tcon_power(0)` on the on side. The copied provider sends OCL
mailbox command `0x3f` with the one-byte value.

The retained historical run records this bounded chronology:

| uptime | retained event | supported conclusion |
| ---: | --- | --- |
| `94420.503051` | OCL `Write [01 3f 01 01 00]` | command `0x3f`, value 1 requested |
| `94420.641740..94420.649049` | USB path `7-1` disconnect | host observed the USB device disappear |
| `94421.655057` | OCL `Write [01 3f 00 01 00]` | command `0x3f`, value 0 requested |
| `94422.123180` | new high-speed USB device at `7-1` | a fresh host enumeration began |
| `94422.271427..94422.271451` | `04e8:2001`, revision `2.50`, `STL1 CDC and Bulk`, serial `0x12345678` | the reappearing function presented the same detailed identity |

This closes the QDF caller, OCL provider, request bytes, and host-visible USB
lifecycle. It does not close the OCL command-`0x3f` receiver. No retained body
shows which processor, clocks, reset lines, RAM banks, PHY, or shared power
domain that receiver controls. Callback return zero is not an electrical or
memory-reset measurement.

The selected/current-generation image-0 source also has a coherent USB
startup path: ordinary startup calls the vendor initializer, the USB class
configuration callback initializes the vendor state, and its descriptors
match the retained Samsung composite identity. This makes the host USB event
consistent with an image-0 USB-function restart. It does not turn the event
into evidence that image 1 reset with it.

## The two packaged reset paths are independent

For the selected 5 MiB package, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`,
the corrected mappings are:

```text
image 0 linked VA = FILE - 0x00200
image 1 linked VA = FILE - 0x40200
```

Both components contain their own Cortex-M vector and coherent reset/scatter
startup:

| component | vector FILE | reset Thumb pointer / body FILE | relevant packaged reset effect |
| --- | ---: | ---: | --- |
| image 0 | `0x00200` | `0x345` / `0x00544` | scatter row 9 expands `0x47bc` zero bytes at bus `0x47010000`, covering `0x47012400` |
| image 1 | `0x40200` | `0x369` / `0x40568` | scatter writes local RAM ranges, including a decoded pointer `0x200004e0 = 0x20010000` |

The image-0 zero-fill is a packaged cold-start baseline, not proof that MODE2
ran image 0's reset vector or scatter routine. If it did run and its
`0x47010000` destination is the same physical view later sampled as RT state,
it would provide a possible clear-before-refault mechanism. The delayed
sample cannot establish that execution or observe the transient.

Image 1's nine scatter destinations are:

```text
0x20000000  0x20015000  0x20015f10  0x2020a000  0x20253000
0x20209000  0x20209800  0x20269000  0x200004f8 (zero fill)
```

The final zero fill is `0x200004f8..0x2000e19b`. The context object begins at
`0x20010000`, after that range and before the next scatter destination
`0x20015000`. No image-1 scatter record covers it. Image-1 application entry
retrieves this pre-existing root and its first visible direct root operation
is a read-modify-write of `root+0x2406`, not a whole-object clear.

The existing bounded cross-image audits recovered no executable image-0 path
that consumes the stored image-1 component at FILE `0x40000`, installs its
entry point, releases a secondary core, programs VTOR for it, or maps its RT
object as part of MODE2. That is a bounded negative over the recovered
reset/scatter/direct-startup mechanisms, not a whole-firmware absence claim.

## Generation compatibility of the three delayed RT fields

The selected package identifies `241230A`, while the recovered-current stored
package identifies `241205A` in its differing first-image/header material.
That generation difference does **not** introduce a byte-layout disagreement
for the retained image-1 candidate: FILE `0x40000..0x7ffff` is byte-identical
across both complete 5 MiB files. The common 256 KiB slot SHA-256 is:

```text
56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf
```

This equality covers the image-1 vector, reset/scatter tables, root getter,
event predicate, and the complete common setter VA `0xc1e0..0xc211`. The
setter's 50 bytes are identical with SHA-256
`f8a6285dd94b333ee0ff8fbe7c599410c0befae4f5b7a4e32679607d2b4883d`
and make the three response offsets explicit relative to root
`0x20010000` / bus window `0x47010000`:

| delayed `R` response offset | setter field | exact event store |
| ---: | ---: | ---: |
| `+0x00` | root `+0x2400` | halfword `1` (the retained stop/event flag) |
| `+0x0a` | root `+0x240a` | halfword `0x1001` (the retained fault field) |
| `+0x0e` | root `+0x240e` | halfword `0` (the retained ordinary gate) |

The accepted V6 transition independently changed exactly these fields from
`0 / 0 / 1` to `1 / 0x1001 / 0`, matching those stores. Therefore the
`241230A` versus recovered-stored `241205A` distinction, by itself, does not
make the meanings or offsets of these three image-1 fields differ. A delayed
raw comparison is layout-compatible with **either of these two retained
image-1 slots**, provided it is still the same rooted `0x47012400` view.

This is not proof that MODE2 selected either stored source, that the active
core's entire executable equals the slot, or that no third/unretained source
exists. The current first-image generations differ substantially, and MODE2's
boot-source/reset-selection behavior remains unknown. Thus the raw
`+0/+0x0a/+0x0e` tuple has strong two-package layout support, while its active
generation, mapped-root continuity, and reset chronology remain conditional.

## What the live mapping evidence does and does not add

The image-1 mapper implements, for CPU addresses in
`0x20000000..0x201fffff`, a non-A branch `bus = CPU + 0x27000000`. A retained
read at bus `0x470004e0` returned the exact reset-derived root word
`0x20010000` with plausible neighboring state. This is the positive local
anchor supporting the conditional interpretation:

```text
CPU 0x20010000 -> bus 0x47010000
CPU 0x20012400 -> bus 0x47012400
```

The live core-tag register itself was not sampled. The anchor and later RT
reads strongly support this mapped volatile view; they do not identify the
MODE2 reset domain, prove a core was reset, or show when any field changed.

There is also dual packaged provenance for the same bus range: image 0 has a
reset scatter destination and AP_RTP configuration destinations at
`0x47010000/0x47012400`, while image 1 reaches the range through a conditional
CPU-to-bus mapper. Bus-address equality therefore must not be used as a reset
ownership proof.

## Exact missing link

The first missing proof is one of these positive edges:

1. the actual OCL command-`0x3f` receiver, showing that its observed 1/0 path
   asserts and releases the image-1 core/reset domain and defining whether
   SRAM `0x20010000` is retained or cleared; or
2. a source-backed image-0/boot component edge that starts image 1 across the
   MODE2 lifecycle and specifies the relevant RAM-reset behavior.

A USB disconnect/re-enumeration, a successful image-0 vendor configuration,
a stable device serial, or a delayed RT value supplies neither edge. A reset
vector and scatter table describe what occurs **if that image starts**; they
do not prove MODE2 starts it.

## Evidence pins

| retained artifact | SHA-256 |
| --- | --- |
| `tcon-research/qd-full-reset-versus-mode2.md` | `82e44c95ed0c49482a023cbbf6973e571e76ace4ceb57ccea506535bbbdda904` |
| `sleep-investigation-20261027a/reset-coupled-usb-identity-provenance.md` | `7b8f86f4f1a685e011002d7d960c6712af31f8b28072a2511b6f843c80a2c45a` |
| `tcon-research/qd-image1-context-initialization.md` | `e885c17d2d1092fd82d761ed4c7b1cd1627bcfa921bfba8027b515918da39c66` |
| `tcon-research/qd-rt-window-reset-output-20261027.md` | `879cdf0652a2eb762dd307b10e4bf47bdb581b05098517a7b3b54e5042ab377a` |
| `tcon-research/qd-rt-window-alias-evidence-20261027.md` | `fe3b4a7a868759dd19b4baccaf95a55202bdd78324a615e34a11ccb8672ccc22` |
| `executing-image-identity-20261027e/reverse-engineering-map.md` | `c1c8942916a2b1ba4e9b95479a932bd5a0b83efb39ae01b20f96debc18590798` |
| `finite-onset-logger-20261027g/rtp-mode-ram-read-qualification.md` | `7983f13205ccd88a13ad7f02cfd04e75988c4ac2085ac488fab08e65cf0284e7` |
| `firmware-fingerprint-20261027d/backup-runtime-audit.json` | `8ce3a8f42a372822d6d91cde1e2736fafdbf55886ebc236c1ffac38c01ba01b5` |
| `finite-onset-logger-20261027g/rtp-act-736-trace.md` | `9f14ed08477b252ceb62a4af8386bdacd222a3948c17c1f089323e398b815f16` |
| `stock-lifecycle-followup-20261027au/vendor-ready-boundary.md` | `f7352c2d26f9b61bed84409146dc45df998a4f4514c8c3884eefe22557273d8a` |

The present conclusion is deliberately finite: MODE2 proves a reset-coupled
USB lifecycle, while inclusion of the mapped image-1 RT object in that reset
domain and its clear/retention behavior remain unknown.
