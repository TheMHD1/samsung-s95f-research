# Selected-profile RT status: internal selector to `F3 80 ... 08` wire reply

Recorded 2026-10-27 UTC. This is a bounded offline trace through the already
retained selected QD profile. It made no TV, root, network, I2C, EEPROM, eMMC,
controller, GPIO, firmware-update, or display call and modified no prior
evidence.

## Result

The selected packaged firmware contains a complete static path from the
EEPROM-labelled RT-protection check to the controller reply for the exact host
query `F3 80 00 00 00 08`:

```text
EEPROM RT check 0x99e8
  -> common error entry 0xb860(selector = 0x10)
  -> selector store 0x2b964: common_object halfword +0x10 = 0x0010

controller receives: F3 80 00 00 00 08
  -> command = 0xf380, selector = 8
  -> 0x21824 dispatch
  -> 0x21ff8 selector table, case 8
  -> load common_object halfword +0x10
  -> controller reply bytes: 00 00 00 10
```

This closes the missing **packaged-firmware producer-to-wire edge**. The
shared `0x10` is no longer merely a numerical/string correlation: the same
field written by the RT error entry is the field returned by selector 8 of
the `0xf380` open-register command.

The claim remains conditional on image identity. The retained selected asset
has exact SHA256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`,
but no current controller-flash readback proves that this packaged image was
the image executing during the accepted host `0x10` sample. The static path
also does not identify the electrical source of RT protection or prove that
the EEPROM branch caused the owner's black picture.

## Inputs and address convention

The input is
`overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
5,242,880 bytes. Its first embedded Thumb image is linked at address zero, so
all image-0 file offsets and linked code addresses in this report coincide.
All multibyte instruction/data values below are little-endian unless the I2C
wire-byte order is explicitly described.

The preceding content report is `qd-selected-profile-content.md`, SHA256
`e2dcdd78576032d2a250d388cbc55f40950f961238ce426bd5c9b961a4a40beb`.
The exact host ABI/transport proof is `qd-error-status-read-abi.md`, SHA256
`3812ca30cd846e0aee4e85da0716577c781939972d1836eeca41624b2ef0e3d1`.
That report proves that the QDF path sends fixed command
`F3 80 00 00 00 08`, reads four bytes, reverses those bytes into the
little-endian output word, and has separate skip/debug-override conditions.

## Symbol-label limit

The image contains the exact strings:

```text
0x3cbb4 I2C_TCON_Handler
0x3cbc5 I2C_OpenRegister_Handler
0x3cbde I2C_OneCmd_OpenRegister_Handler
```

The flat binary does not carry a recovered address-bearing symbol table.
Accordingly, the names below are functional labels, not claims of formal
symbol resolution: `0x12ac4` is the unique recovered low-level TCON I2C state
machine, `0x21824` is the open-register dispatcher for `f300/f380/f301`, and
`0x21878` is the adjacent D000..D004 one-command dispatcher. The byte-level
path and hashes do not depend on those labels.

## Exact packet parsing

### Command and selector assembly

Function `0x12ac4..0x12dbd` (762 bytes, SHA256
`5b2cbcbac9d03ba3a1dd175568a5cbc8cb7e74a75264a17fd354833d1f4e9c85`)
is a hardware-event state machine. Its current bus byte is read from the
peripheral object at `+0x28`.

For the receive path:

* `0x12b66..0x12b88` handles byte counts below two. It shifts the existing
  halfword at RAM `0x200008c8` left by eight, then ORs the new byte. Thus input
  bytes `f3 80` produce command halfword `0xf380`.
* `0x12ba4..0x12be2` handles the following bytes. It shifts the word at RAM
  `0x200008cc` left by eight, then ORs the new byte. Thus input bytes
  `00 00 00 08` produce selector word `0x00000008`.
* `0x12a9a..0x12ac0` independently classifies first byte `0xf3` as parser mode
  zero. Nearby cases classify `f7`, `d0`, and `fe`; they are not used to infer
  the `f380` response.

This is big-endian byte assembly. There is no appeal to the textual command
literal to establish the arguments: the shift/OR instructions themselves map
the six exact wire bytes to `(command=0xf380, selector=8)`.

### Open-register dispatch and case 8

Function `0x21824..0x21875` (82 bytes, SHA256
`5f9a3da21a8aff22610a23c58b4e79bc20836d4111a456ccb393044616abacbe`)
compares its first argument with `0xf300`, `0xf380`, and `0xf301`. The
`0xf380` branch at `0x21846..0x21860`:

1. passes its second argument unchanged to `0x21ff8`;
2. retains the returned 32-bit value;
3. calls `0x5b24(command, selector, value)`; and
4. returns the value unchanged.

The selector function `0x21ff8..0x220e9` (242 bytes, SHA256
`7b7038d870a46b9f897a44d3368618a13a61025ed86a9c5c61b6dccddba23aa0`)
rejects selectors `>= 0x23` and uses a 35-byte Thumb `TBB` table at `0x22012`.
Table entry 8 is byte `0x2a`, which branches to `0x22066`. That case executes:

```text
0x22066  BL    0xe870       ; get common object
0x2206a  LDRH  r0,[r0,#0x10]
0x2206c  B     common return
```

`LDRH` zero-extends the exact 16-bit field; selector 8 performs no store,
clear, acknowledgement, or call other than the common-object accessor. In
this packaged firmware, this controller-side read is therefore non-clearing.
That does not prove a different/current flash image has identical semantics.

Function `0x5b24..0x5b59` (54 bytes, SHA256
`a8dc7f55717424be6f692640e86c7961f4e226936f9852ac4887d6d7a4286607`)
sums the four bytes of each of command, selector, and value modulo 256 and
stores the result in a RAM byte. It does not modify the value returned by the
dispatcher.

### Reply byte order

On the transmit path, `0x12c92..0x12cc0` calls
`0x21824(command, selector)` once at response-byte index zero, stores the
returned word at RAM `0x20000900`, then emits successive bytes by shifting it
right by `24 - 8*(index & 3)`. Thus a field value `0x0010` is serialized as:

```text
index 0  00
index 1  00
index 2  00
index 3  10
```

The host QDF path's already-proved four-byte reversal converts controller wire
bytes `00 00 00 10` into output word `0x00000010`. This establishes exact
byte order across both sides without assuming native endianness at the wire.

## Exact internal producer

The EEPROM-labelled check at `0x99e8` calls common error entry `0xb860` with
`r0=0x10` on either of its two gated RT-protection conditions. The check and
its four-byte EEPROM input were established in the preceding content report.

Common entry `0xb860..0xb8f9` (154 bytes, SHA256
`40e434612828833aa7b433798a352a99c766cbb47351d2cb42ba364a868d2c6a`)
retains the selector in `r5`. It calls selector-specific action `0x14b10`,
then calls setter `0x2b964` with the same retained selector.

Setter `0x2b964..0x2b979` (22 bytes, SHA256
`3d538c104bca6958c66173c7d56a095ded57e9453134e78933ee6d0e26fffb03`)
gets the same common object at `0xe870`, loads halfword `+0x10`, uses `BFI` to
replace all 16 low bits with the selector, and stores the halfword back. It is
an overwrite, not a bitwise OR. With selector `0x10`, the exact field later
read by `f380` selector 8 becomes `0x0010`.

The recovered path proves the common field is a current stored selector value
at those instructions. It does not, by itself, prove how long the value
persists, enumerate every writer/clearer, or prove that it survives reset.
Calling it an immutable latch would therefore be too strong.

## What the selector-`0x10` action actually does

Selector dispatcher `0x14b10..0x14bbb` (172 bytes, SHA256
`5fcc7bea9301c9aa6b815a92fff05ac97769daf64e9eccbe1bac23f5667e3d18`)
has a dedicated `selector == 0x10` branch at `0x14b70..0x14b88`. Before the
common field is written, that branch:

1. clears a halfword at `second_object + 8`;
2. calls `0x25d24(1)`;
3. writes literal `0x10` to MMIO address `0x4013400c`;
4. calls `0x9b68`; and
5. calls `0xa230`.

`0x25d24(1)` calls three other internal functions, then writes `0x80` to
MMIO `0x40132010` and `4` to MMIO `0x40131010`. The register-block meanings
were not recovered, so these writes are not named as rail, panel, or reset
controls.

Function `0x9b68..0x9bfd` (150 bytes, SHA256
`72248d0305a3138c222077fd941bb1d0cad525ba6ccb1928e58998048c4252fc`)
is not merely a RAM-latch update. It increments the byte sourced from object
`+0x24ac` (wrapping values above `0xfe` to zero), places the new value in
bytes 2 and 3 of the four-byte buffer at RAM `0x20000c50`, and makes up to ten
attempts to:

* call `0x9990(address=0xe0, length=4, buffer=0x20000c50)`;
* wait `0x2710` through `0x1de90`;
* read four bytes back through `0x9948`; and
* compare every read byte with the write buffer.

The adjacent failure literal is `RT-P EERPOM Write Verify Fail` (spelling as
stored). Together with the earlier EEPROM-labelled read and exact
write/readback CFG, this establishes a persistent EEPROM counter update and
verification attempt. This report does not expose it as an operation to run.

Function `0xa230..0xa24f` (32 bytes, SHA256
`9fed5ee762170e40ec3c6a44c2f0312739be0dc93fd775d9a3117602433d6108`)
passes object region `+0x1000`, length `0x1400`, and constant
`0x464b2a00` to core `0xa0e4`. That core reaches lower transfer function
`0x16d70`; its exact error literal is `EMMC Write Fail [USB BUSY]`. This is
evidence of an eMMC-write attempt for a 0x1400-byte region, not evidence of a
physical panel-rail reset.

Consequently, the selector branch is more active than a volatile status
latch: it changes RAM state, writes three MMIO locations, updates and verifies
an EEPROM counter, and invokes an eMMC-write path before the common selector
store. Static code does **not** establish what the MMIO blocks control or that
any of these operations turns a physical rail off/on. The later common-error
path also contains generic emergency handling shared by other selectors; it
is not uniquely attributed to RT protection here.

## Proven and unproven conclusions

Proven for the exact packaged image:

* `F3 80 00 00 00 08` is parsed as command `0xf380`, selector 8.
* Selector 8 returns the same common-object halfword `+0x10` written by the
  common error selector setter.
* RT-protection entry with selector `0x10` therefore produces reply bytes
  `00 00 00 10` if that stored selector remains current at query time.
* The selector-8 read itself does not clear the controller field.
* The `0x10` action includes persistent EEPROM/eMMC activity and exact MMIO
  writes; it is not merely a diagnostic log.

Not proven:

* that these packaged bytes equal the controller image running during the
  accepted sample, or that the selected profile was installed unchanged;
* that the accepted host `0x10` originated specifically from the startup
  EEPROM check rather than another caller of the common error entry with the
  same selector;
* whether the stored selector is current, latched until another writer,
  restored, or cleared elsewhere over the full firmware lifetime;
* the hardware meanings of `0x4013400c`, `0x40132010`, and `0x40131010`, or
  any physical-rail/reset effect;
* the units/meaning of the EEPROM history/count bytes, the initiating physical
  fault, or causality for visible-black behavior.

No controller command, EEPROM/eMMC operation, patch, threshold change, or
recovery action is proposed. The next source-only question is writer/clearer
and MMIO-block identity, not another invocation of the already-proved status
read.
