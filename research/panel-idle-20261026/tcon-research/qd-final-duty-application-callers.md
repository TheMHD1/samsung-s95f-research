# Final consumers of the selected F3:0x128 scalar

Recorded 2026-10-27 UTC. This is a finite, offline-only continuation of
qd-final-duty-controller-consumers.md. It reads the selected profile file only;
it made no TV, root, network, media, I2C, controller, MMIO, or firmware action.

## Input and address convention

Input is the selected 5 MiB ordinary profile copy:
overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin
SHA-256 bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0

Image-0 executable linked VA equals FILE offset minus 0x200. RAM and MMIO
values below are not rebased. The selected copy is not established as a
readback of the executing controller.

## Recovered scalar and derived-field paths

The prior dispatch trace establishes the gated write of the low ten bits of
the received F3:0x128 scalar at root 0x2000d71c + 0xa6. The previously
identified calculations are confirmed with their immediate caller edges:

    VA 0x1356a -> VA 0x188a4
      -> VA 0x1a1f8
         read root +0xa6 and +0xa8
         -> write root +0x4fa and root +0x4fc

    VA 0x189ce -> VA 0x188d8
      -> read root +0xa6
      -> write root +0x68

0x188a4 copies root +0x62 to its caller buffer, obtains a float from 0x19898,
then calls 0x1a1f8. The direct 0x1356a call follows other routine work in its
enclosing body; no return value from 0x188a4 is turned there into an MMIO, I2C,
image-1, reset, or RT action in the bounded slice.

0x188d8 calculates a float from masked root +0xa6, root +0x2e, and its float
argument, then converts and writes root +0x68. Its direct caller 0x189ce
continues through floating-point routines. This is still a RAM
calculation/cache edge, not a recovered hardware-application edge.

## Final +0x4fc reader

The immediate-offset direct access census in image 0 finds the +0x4fc write at 0x1a3c2
and only two later reads, both in the same function:

    0x232da read root +0x4fc; call 0xcec4(value, 0); store result at
             another object returned by 0xf4f0, offset +0x82.
    0x23302 if that object's +0xbc equals 1, multiply root +0x4fc by its
             +0xbe, shift/extract, clamp between that object's +0x8a/+0x8c,
             then store the result at its +0xc0.

The function starts at 0x2324c. Its direct enclosing caller is at 0x233ce
inside the 0x23394 body. That call is gated: it is selected only when the
object returned by 0xf4f0 has +0x12 == 3, after earlier alternate branches
for its +0x3a bit and several root fields (+0x196, +0x19a, +0x19c).

0x2324c passes its returned selected value to 0x2353c; the reviewed 0x2353c
range performs table interpolation and stores in its own RAM object. No
instruction in the bounded +0x4fc reader/caller chain directly accesses an
absolute 0x4... MMIO location, bus transport, image-1 handoff, reset register,
or the RT field.

## Final +0x4fa reader

The immediate-offset direct access census finds the +0x4fa write at 0x1a3a2 and one
later read at 0x249ee. The latter is inside the function entered by the direct
call at 0x2475a:

    0x249ea if u16(object from 0xf1ec) != 0:
    0x249ee   load root +0x4fa
    0x249f2   compare it with that object's +0x18a
    0x249f8   if greater, inspect the object's +0x18c
    0x24a00/0x24a06 select local register sb as 1 or 0

The local flag then selects arithmetic and RAM counter/field updates in
0x24a14..0x24b6c. In particular, the direct +0x4fa value itself is not passed
to an MMIO write or a transport routine in this slice. The available call
chain also includes a startup/recurring dispatcher call at 0x39ad2 to a
nearby enclosing function, but static direct-call recovery does not prove that
this schedule ran during the owner's fault.

## Hardware boundary

The useful finite result is that the received scalar reaches three derived RAM
fields (+0x68, +0x4fa, +0x4fc), and that the final direct reads found for the
two later fields feed local policy/scaling and RAM stores. This narrows the
missing application edge to later indirect callbacks, unbounded callers,
runtime-populated tables, other controller state, or hardware paths outside
these direct consumers.

No brightness, nits, power, fault, panel-output, threshold, recovery, or
physical-display meaning follows from these calculations. No execution,
controller acceptance, field value, or fault-time ordering is established.

## Byte identity

All ranges are linked VA half-open intervals, followed by their corresponding
stored FILE range and SHA-256:

    VA 13510..135b0 FILE 13710..137b0 c4b380caa71c4731eb653af3dfe957241e5933dec5a8abb7d7ecc2323da395a0
    VA 188a4..18952 FILE 18aa4..18b52 de1b61fe85835c7835034018429070573de4222b93af09b061bdc021f8205b18
    VA 1a1f8..1a3d2 FILE 1a3f8..1a5d2 7069d7a48b79cdb63bda9ed2c4a844a375797558c3f6166286a5d9e05f253b7a
    VA 2324c..2338a FILE 2344c..2358a 7c7d1dd938cd7c715dda90f6a7887a422247a1483975ffee5a99454859897f16
    VA 23394..23432 FILE 23594..23632 6fe81de84256225d7d125f01a0d2b93a24c227c992d4f2ba9ec56aaf9d512a44
    VA 2353c..236c0 FILE 2373c..238c0 4ac22ef6ac1d9eb8cb53dc52096eb1a303e954e0bc333138377ab9926538fe6e
    VA 24974..24b6e FILE 24b74..24d6e 91407be09dd99bd2fd1df75260a62119926e3ed46495da344604e3eb6e24f823
    VA 39a90..39b0c FILE 39c90..39d0c 3cda403339afb3bcdbc0ad8fb665ed1cd703a2da5606a9780b2022e3d08affb6

A Capstone Thumb sweep of the first image was used to enumerate immediate
direct BL/BLX targets. It does not resolve computed branches, table callbacks,
exceptions, or runtime function pointers.

