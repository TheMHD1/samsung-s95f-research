# Addendum: correction to the USB/AP_RTP reader review

Recorded 2026-10-27 UTC. This corrects, without overwriting, the earlier
independent reader review retained in this same work block.

## Correct branch interpretation

The earlier review reversed the ARM Thumb operand ordering for:

```text
63c2  cmp  r0,r7
63c4  bhi  63e4
```

For the reviewed logical address, `r0 = 0x0100` and `r7 = 0x000a`.
`cmp r0,r7` establishes unsigned-higher because `0x100 > 0x0a`; `bhi` is
therefore taken to `0x63e4`. That branch loads table `+0x04`
(`0x47012400`) and adds the low value, producing source address
**`0x4701240a`** for the count-one reader call.

The earlier review's fall-through calculation of `0x4700fc0a` is wrong: that
path is not selected for `low=0x000a`.

## Corrected scope

The earlier claimed arithmetic blocker is withdrawn. The narrow static claim
that logical `0x21000a`, count one, maps to the fixed image-0 address
`0x4701240a` is supported by the corrected branch evaluation.

This correction does not create a host command or live permission. The
existing limits remain: package bytes do not prove current controller
execution; the CDC-to-UART finding is a bounded negative; no command grammar,
transport, or invocation is established; and the image-1/image-0 producer or
alias question remains unresolved.

The prior review is intentionally preserved as historical evidence of the
mistake. No TV, USB, root, network, media, or controller action occurred.
