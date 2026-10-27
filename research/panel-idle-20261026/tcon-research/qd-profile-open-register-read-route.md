# Selected-profile open-register read route and RT-state boundary

Recorded 2026-10-27 UTC. This report is a bounded offline analysis of the
selected packaged QD firmware and copied QDF host module. It made no TV,
root, network, controller, I2C, EEPROM, MMIO, getter, or display call and
changed no prior evidence.

## Result

The normal host burst reader and the controller's open-register handlers do
**not** expose a generic read window into the image-0 object's fixed
`0x4701xxxx` address space.

There are three distinct interfaces that must not be conflated:

1. controller command `0xf300` takes a 32-bit **logical selector** and
   dispatches it through a finite table/range mapper;
2. controller command `0xf380` takes a logical selector from the separately
   reviewed 35-entry getter table; and
3. QDF `m_i2c_burst_read` sends a two-byte device register address. In the
   packaged controller, the observed `0xfe63`, `0xfe64`, `0xfea3`, and
   `0xfea4` addresses are handled by a finite `FE` dispatcher and return bytes
   from four fixed arrays.

None is a raw-address operation. The `0xf300` getter accepts only aligned
logical selectors in two bounded ranges ending at `0x4d8`; its decoded cases
do not load image-0 object offsets `+0x240a`, `+0x2466`, `+0x2484`, `+0x24aa`,
or `+0x24ac`. The `FE` dispatcher recognizes a small exact command set and
returns zero for other values. The adjacent `D000..D004` one-command handler
likewise selects five bounded byte arrays rather than arbitrary memory.

Consequently, the fixed image-0 accessor value `0x47010000` does not make the
RT live/history fields available through the ordinary QDF burst-reader or
open-register paths. In particular, truncating an object address to 16 bits
does not select that object: the two bytes are first interpreted as a
protocol command, and an unrecognized command reaches a zero-return path.

This closes the source-bound acquisition question negatively for these
interfaces. It does not prove that no other controller debug/service
interface can read the fields. No new query is proposed.

## Exact inputs

| Input | SHA-256 |
| --- | --- |
| `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` (5,242,880 bytes) | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| `binaries/qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` |
| `qd-profile-rt-status-wire.md` | `6c532e2ad8a48041cf83ebddfa42af1282019d14169902b47e621f6a1c237f6e` |
| `qd-profile-readonly-rt-state-selectors.md` | `cde271e73dc03bafb950862df9ec3fe1a0323463c770b236cb5aa087bf5a4de8` |
| `qd-runtime-profile-log-fields.md` | `a339e02422f6be0a6979a7030a91b34d7ba5ee0c7483e81f94cbbddf03f2c323` |

The first embedded Thumb image is linked at zero, so image-0 code addresses
and file offsets coincide. Current controller-flash equality remains
unproved.

## Fixed image-0 object base

Accessor `0xf194..0xf19b` is eight bytes, SHA-256
`ac0f29fcf915e5ca06f49bce9cf9cf8e41fb1b01d5b7905895ac28d9d03cc131`:

```text
0xf194  LDR r0,[pc,#0]
0xf196  BX  lr
0xf198  .word 0x47010000
```

Thus a direct load at object offset `+0x240a` addresses `0x4701240a`, and the
saved RT fields established in earlier work occupy `0x47012466`,
`0x47012484`, `0x470124aa`, and `0x470124ac` in this packaged image's address
model. That arithmetic proves the internal source addresses only. It does not
make them protocol addresses.

## Low-level parser separates command, selector, and data

The controller state machine is `0x12ac4..0x12dbd`, 762 bytes, SHA-256
`5b2cbcbac9d03ba3a1dd175568a5cbc8cb7e74a75264a17fd354833d1f4e9c85`.
It assembles the first two received bytes, most-significant byte first, into
the command halfword at RAM `0x200008c8`.

The first byte selects one of four parser modes:

| First byte | Mode | transmit dispatcher |
| ---: | ---: | --- |
| `f3` (and unrecognized first bytes) | 0 | `0x21824` open-register dispatcher |
| `f7` | 1 | `0x1f608` |
| `d0` | 2 | `0x21878` one-command open-register dispatcher |
| `fe` | 3 | `0x2212e` finite `FE` dispatcher |

For mode 0, bytes 2 through 5 are shifted into the 32-bit selector word at
RAM `0x200008cc`. If transmission starts after those six bytes, the transmit
path calls `0x21824(command, selector)` and serializes its 32-bit return word
most-significant byte first.

The receive path is different once four data bytes follow the selector. It
accumulates the data word at `0x20000904` and, on each complete four-byte
word, calls `0x2c7f4(command, selector, data)`. That is a setter/action
boundary, not a read. This report does not decode or recommend that path.

The parser necessarily updates its command, selector, byte-count, and
transmit-index RAM while handling a read. These protocol-state writes are not
writes to the RT object fields, but they mean “read” is not synonymous with
“no controller state changes whatsoever.”

## `F3:00` is a finite logical-selector API

The open-register dispatcher `0x21824..0x21875` is 82 bytes, SHA-256
`5f9a3da21a8aff22610a23c58b4e79bc20836d4111a456ccb393044616abacbe`.
Its `0xf300` branch passes the 32-bit selector to `0x2194c`, then passes the
command, selector, and returned value to `0x5b24` before returning the word.

Getter `0x2194c..0x21fef` is 1,700 bytes, SHA-256
`fc3bbd7a16650a34ce0105c0174f6e5099e8f0fc5722844649149016c1cdea07`.
It is not `base + selector`:

* aligned selectors `0x24..0x314` use a 189-entry relative branch table;
* aligned selectors `0x31c..0x4d8` use helper `0x21908`; and
* values outside those ranges, including unaligned values, return zero.

Helper `0x21908..0x21949` is 66 bytes, SHA-256
`2c1cbc82be26278fcbc637e1287f9d89514d3d3468bf48e0b0140d39b1d90748`.
It maps the second range into bounded halfword tables rooted at the separate
object returned by accessor `0xf19c`. It does not use the `0x47010000` base.

Together the two ranges contain 301 aligned logical selector positions.
Their distinct targets and selector-specific leaf getters were decoded. The
only direct uses of the `0xf194` result retained in `r8` by the main getter
load packaged-object offsets `+0x29da`, `+0x2748`, and `+0x3826`. Other leaf
getters use bounded fields primarily in the `+0x25xx`, `+0x26xx`, `+0x27xx`,
`+0x29xx`, and `+0x37xx` regions or separate objects. None reads
`+0x240a`, `+0x2466`, `+0x2484`, `+0x24aa`, or `+0x24ac`.

The common post-getter helper `0x5b24..0x5b59` is 54 bytes, SHA-256
`a8dc7f55717424be6f692640e86c7961f4e226936f9852ac4887d6d7a4286607`.
It computes a byte sum over command, selector, and value and stores that sum
in RAM. Therefore even an `F3:00` getter has a controller bookkeeping write.
Moreover, the large logical-selector table includes computed getters and
hardware-derived state whose read effects are not globally proven. It is not
a generic side-effect-free memory reader.

### `F3:01` is not a memory window

The adjacent `0xf301` case calls `0x218f8..0x21903` (12 bytes, SHA-256
`8f11ecd58ca0d1bdf0c58837b73de9365eb268ef25b8e8102bd9f878384a6869`).
That function ignores its selector argument, reads one byte at RAM
`0x200008e9`, shifts it left eight, adds four, and returns the result. It does
not dereference a caller-selected address.

## `D0:00..04` is five bounded arrays

The one-command open-register dispatcher `0x21878..0x218f1` is 122 bytes,
SHA-256
`09a4c7e01bb146e2f7d33d78c59f99da83595b9d73fac3c6bc0388f786923349`.
It recognizes only commands `0xd000..0xd004`:

* `d000`: at most 16 bytes from `common_object+0x220`;
* `d001`: at most 8 bytes from `common_object+0x230`;
* `d002`: at most 8 bytes from `common_object+0x238`;
* `d003`: at most 32 bytes from `common_object+0x240`; and
* `d004`: at most 32 bytes from RAM `0x200008a0`.

The second argument is a checked byte index, not an address. Unknown commands
or out-of-range indices return zero. None of these regions overlaps the saved
RT fields.

## QDF burst reads enter the finite `FE` dispatcher

Copied QDF function `m_i2c_burst_read`, module `.text+0x2220`, is 552 bytes
(body SHA-256
`52d7ff7612691300319f56a939abd6930c5565467e61a9b304e4143c89b20fce`).
It:

1. masks the caller address to 16 bits;
2. reverses those 16 bits so the two-byte device prefix is sent high-byte
   first;
3. checks QDF state/provider gates;
4. calls the registered `tztv_i2c_read_common` pointer with bus 5, address
   `0x76`, two prefix bytes, caller length, and caller output buffer; and
5. retries the provider call once after a nonzero return.

The ordinary profile formatter's four calls use addresses `0xfea4`,
`0xfea3`, `0xfe64`, and `0xfe63`, with lengths 9, 9, 16, and 16. On the
packaged controller these first bytes select parser mode 3. The transmit path
passes the command and successive zero-based byte indices to dispatcher
`0x2212e..0x221c5`, 152 bytes, SHA-256
`fc1635b96eeda65f2976cf9ba4fea0ed7b40391cc18827040685b5a5ff712f53`.

The exact profile cases are:

| command | valid byte indices | packaged source |
| ---: | ---: | --- |
| `fe63` | `0..15` | RAM `0x200153e6` |
| `fe64` | `0..15` | RAM `0x200153d6` |
| `fea3` | `0..8` | RAM `0x200153cd` |
| `fea4` | `0..8` | RAM `0x200153c4` |

Each helper checks the index and returns zero outside its bound. The same
dispatcher has only six other exact command cases (`fec0`, `fec4`, `fed2`,
`fed4`, `fed6`, and `fed8`); every other 16-bit command returns zero. Some of
those other cases call computed getters, so this finite dispatcher should not
be generalized as wholly side-effect-free.

The QDF helper is an actual device transaction, not a process-memory read.
Its provider and the controller parser may have transport/bookkeeping effects;
the copied sources do not prove arbitrary device reads harmless. For the four
profile cases, however, the controller-side value bodies are checked array
loads and contain no store to their source arrays.

## Why the RT fields are not reachable here

The internal object address and all three read APIs use different namespaces:

| value | namespace | source interpretation |
| --- | --- | --- |
| `0x470124ac` | image-0 memory address | fixed base `0x47010000` plus RT saved-count offset |
| `0x24ac` | potential `F3:00` logical selector | outside the getter's maximum `0x4d8`, so returns zero |
| low 16-bit device prefix | parser command halfword | interpreted by first-byte mode and exact command dispatch, not as object address |

The same reasoning applies to `+0x240a`, `+0x2466`, `+0x2484`, and `+0x24aa`.
No decoded case translates any of those values to the corresponding
`0x4701xxxx` location.

## Conclusion and limits

The normal interfaces prove several useful bounded reads, but no saved-RT
acquisition path:

* `F3:80` selector 8 returns the current common error-selector field;
* `F3:00` exposes a finite logical register table, not arbitrary memory;
* `F3:01` returns one fixed framing/status expression;
* `D000..D004` expose five bounded byte arrays; and
* QDF burst reads reach a finite `FE` command table, including the four
  runtime profile strings.

None returns the RT EEPROM signature, gate, threshold, or saved count. A
direct-memory experiment, arbitrary register guess, EEPROM access, or
data-bearing open-register write would be a different and insufficiently
bounded interface, and none is constructed here.

The result is conditional on the packaged image. It does not establish
current-flash identity, prove that the RT fields held any particular values
during the owner's incident, identify an electrical cause, or establish a
safe recovery action. Absence of a route in these handlers is not evidence
that RT history was absent.
