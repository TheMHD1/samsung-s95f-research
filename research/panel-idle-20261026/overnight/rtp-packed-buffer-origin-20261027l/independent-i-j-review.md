# Independent review of I/J ordinary-source traces

Recorded 2026-10-27 UTC. Read-only offline review; no target, network, root,
USB, controller, UI, reset, or write operation was made. Reviewed inputs:

- I report `rtp-scan-input-origin.md` SHA-256
  `84ead8cd06b5b0136c7ee05b651094fb43c7387b7f26262f1fd25a4ab74499f2`
  and verifier SHA-256
  `09ea55f6096de5aa1332f571137471053d3ca043e1de58e3342af9d165d7824b`.
- J report `rtp-alternate-runtime-origin.md` SHA-256
  `22d10703aa26e54dc2a68ed383103b110aa2fff30f3ff7373986a518862b822f`
  and verifier SHA-256
  `d2b7420fdcde306420f1f7784cd5b435620e75cb4f706225065c7af3db7e33f1`.

## P2 — I overstates the naming gap at `0x58601408`

I's numeric/dataflow results are supported: `x` is the four-lane software
ordinal; `y` and `RGB` are copied scalars, not incremented by that packed
loop; the callback refresh reads them from low fields at `0x58601414` and
`0x5860140c`; the later `+0x2452/+0x2454` gate does not filter the earlier
detail emission; and neither `y=2159` nor `x=570..631` proves physical panel
coordinates.

However, describing `0x58601408` only as an unnamed or wholly unresolved
memory-mapped block is too strong. The selected package's exact record at
file `0x83c00` is named `EXCO_PAR2_S0`, has metadata address word
`0x58601400` at record offset `+0x24`, and refresh literal `0x58601408` is
exactly that word plus eight. The bounded conclusion should therefore be:

> `y`/`RGB` descend from fields in an `EXCO_PAR2_S0`-associated address
> block; the individual field names, physical producer, units, and
> panel-coordinate transform remain unresolved.

This correction does not promote the fields to display pixels or sensing
values and does not change I's lane counts or physical-coordinate limits.

No P0/P1 issue was found in I's ordinary numeric chain or J's bounded writer
chain. J correctly keeps capability separate from invocation: selected
writer `0x733c` has only the `bin`/`param` direct callers, logical
`0x1b049e` correctly accounts for the `0x400` second-region prefix gap,
selector-zero uses the AP_EXCO halfword hook, and the retained `1/3` mirror
is not promoted to a live AP_EXCO-object read or a named host setting. Both
verifiers emitted byte-identical results under normal Python and `python -O`.
