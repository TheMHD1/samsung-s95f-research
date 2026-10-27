# Independent review: selected-profile RT selector to wire status

Recorded 2026-10-27 UTC. This was an offline, read-only review of retained
bytes. It made no TV, root, network, I2C, EEPROM, eMMC, GPIO, controller,
firmware-update, or display call.

## Scope and identities

Reviewed source report:

```text
qd-profile-rt-status-wire.md
SHA256 6c532e2ad8a48041cf83ebddfa42af1282019d14169902b47e621f6a1c237f6e
```

Independently decoded source:

```text
overnight/selected-qd-profile-copy-20261027b/
  F_RSM1_BN9659934B_COMMON.bin
size   5242880
SHA256 bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
```

The review was bounded to the image-0 producer/store, the `f380` selector-8
getter, the receive/transmit byte assembly, and the selector-`0x10` action.
It is not a whole-firmware writer census and does not establish that these
packaged bytes were the bytes running during the retained live sample.

## Independent result

No material error was found in the report's producer-to-wire claim for the
exact packaged image.

1. `0xb860` retains its input selector in `r5`, calls `0x14b10(r5)`, then
   calls `0x2b964(r5)`. Function `0x2b964` gets the common object through
   `0xe870`, loads its halfword `+0x10`, replaces all 16 bits with `BFI`, and
   stores the result back. For selector `0x10`, that halfword becomes
   `0x0010`.
2. Receive code `0x12b66..0x12b88` shifts and ORs the first two received
   bytes into the command halfword; `f3 80` becomes `0xf380`. Code
   `0x12ba4..0x12be0` shifts and ORs the following bytes into a word;
   `00 00 00 08` becomes selector `8`.
3. The `0xf380` branch at `0x21846..0x21860` passes that selector to
   `0x21ff8`. Its 35-byte `TBB` table begins at `0x22012`; entry 8 is
   `0x2a`, so `PC + 2*0x2a` reaches `0x22066`. That case calls the same
   common-object accessor `0xe870` and executes `LDRH r0,[r0,#0x10]`.
   The case has no store, clear, or acknowledgement.
4. Transmit code `0x12c92..0x12cc0` invokes the dispatcher at response index
   zero, retains the returned word, and selects bytes by shifts
   `24 - 8*(index & 3)`. Stored value `0x0010` is therefore emitted as
   `00 00 00 10`. Combined with the independently established host-side
   reversal, the host word is `0x00000010`.

The exact function hashes in the reviewed report also matched the retained
binary: `0x21824..0x21875` is
`5f9a3da21a8aff22610a23c58b4e79bc20836d4111a456ccb393044616abacbe`,
`0x21ff8..0x220e9` is
`7b7038d870a46b9f897a44d3368618a13a61025ed86a9c5c61b6dccddba23aa0`,
and `0x2b964..0x2b979` is
`3d538c104bca6958c66173c7d56a095ded57e9453134e78933ee6d0e26fffb03`.

## Action-path qualification

The selector-`0x10` path is not a passive logging path. Before the common
halfword store, `0x14b70..0x14b88` clears a halfword, calls `0x25d24(1)`,
writes `0x10` to an MMIO address, calls `0x9b68`, and calls `0xa230`.
Independent decoding confirms:

* `0x25d24(1)` contains further internal calls and two additional literal
  MMIO writes;
* `0x9b68` increments the low byte read from object `+0x24ac`, attempts a
  four-byte EEPROM-labelled write at address `0xe0`, waits, reads the four
  bytes back, and compares them, with up to ten attempts; and
* `0xa230` passes object `+0x1000`, length `0x1400`, and a fixed constant to
  a lower path whose retained literal names an eMMC write failure.

These facts support the report's warning that the producer entry itself is
active. They do not identify the MMIO blocks as panel rails, prove a reset or
power effect, or authorize invoking the path.

## Boundary of the conclusion

The static bytes establish an exact internal-selector-to-wire mapping for
this packaged image. They do not prove current flash equality, that the
accepted live `0x10` was produced by the EEPROM startup check rather than a
different selector-`0x10` caller, how long the common field remains stored,
or what physical condition initiated the selector. The next valid source
question is the upstream selector-`0x10` producer census; it is not another
status read or any controller action.
