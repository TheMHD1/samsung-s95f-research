# Consumers of controller `F3:0x128` staged field

## Scope

This offline continuation of [qd-f300-write-payload-dispatch.md](qd-f300-write-payload-dispatch.md)
follows coherent accesses through root getter `0xef9c -> 0x2000d71c`. The
prior report proves a gated store of the received scalar's low ten bits at
root `+0xa6` (`0x2000d7c2`) in the selected profile. This report does not
treat arbitrary raw immediates as the same object.

Input SHA-256 is `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Image-0 linked addresses use file bias `+0x200`. No live action occurred.

## Confirmed consumers

### Floating calculation and RAM cache

Linked `0x188d8..0x18950` calls `0xef9c`, reads root `+0xa6`, masks it to ten
bits, and divides it by a literal float. It combines the result with its float
input and root `+0x2e`, then stores a converted result at root `+0x68` and
returns a float:

```text
188e2  bl       ef9c
188f0  ldrh.w   r0,[r4,#0xa6]
188f4  ubfx     r0,r0,#0,#0xa
...     floating-point min/multiply/conversions ...
18944  strh.w   r0,[r4,#0x68]
18950  pop      {r4,pc}
```

This is a calculation and RAM cache update, not a recovered hardware write.

### Derived controller values

Function linked `0x1a1f8..0x1a3d0` also calls `0xef9c`. At `0x1a364` it reads
the same ten-bit field, multiplies it by root `+0xa8`, applies floating-point
arithmetic, then caches converted results at `+0x4fa` and `+0x4fc`:

```text
1a364  ldrh.w   r0,[r4,#0xa6]
1a368  ubfx     r0,r0,#0,#0xa
1a36c  ldrh.w   r1,[r4,#0xa8]
1a370  muls     r0,r1,r0
...     FP arithmetic ...
1a3a2  strh.w   r0,[r4,#0x4fa]
1a3c2  strh.w   r0,[r4,#0x4fc]
```

A bounded later reader at `0x249ee` compares root `+0x4fa` to a distinct
object's `+0x18a` threshold and conditionally sets a local policy flag.
Another reader at `0x232da` uses root `+0x4fc` in scaling/clamping before
storing to other RAM fields. Neither recovered slice makes an MMIO, I2C,
secondary-core, reset, or RT-error call.

## Boundary

The static path now established is:

```text
received F3:0x128 scalar
  -> gated low-10-bit root +0xa6 store
  -> internal floating/threshold calculations
  -> derived RAM fields +0x68, +0x4fa, +0x4fc
```

It does not reach a drive/program/MMIO transfer, image-1 handoff, or image-0
RT field `0x4701240a`. Function callers and runtime gates were not recovered,
so this does not establish that every staged update applies. Separate profile
configuration loading is not treated as a causal payload edge. No brightness,
fault, threshold, or recovery semantics are assigned.
