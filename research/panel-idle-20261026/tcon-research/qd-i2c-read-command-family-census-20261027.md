# Selected-profile I2C response-family census

This is a new offline census of the receive/transmit protocol ingress in the
selected packaged QD controller profile.  It makes no TV, USB, UART, network,
I2C, controller, or firmware call.  It names no new command for use against a
device.

## Result

The finite, code-backed response families found at this ingress do not expose
an arbitrary controller-memory, configuration-logical-reader, saved-history,
or firmware-image read.  In particular, no decoded command maps a caller
value to image-0's fixed `0x4701xxxx` object space, image-1's `0x2001xxxx`
space, or the `0x637c` configuration reader.

The remaining parser mode, `F7`, has now also been bounded.  Its transmit
side exposes only three command values and its receive side is action/control
capable.  Therefore its transient `F7:40` response buffer is not a safe or
source-backed generic diagnostics channel.

## Input and coordinate rule

The sole firmware input is
`overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
5,242,880 bytes, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.

All locations below are **stored file offsets** unless labelled otherwise.
For image 0, `linked VA = file offset - 0x200`; absolute RAM/MMIO values are
not rebased.  Thus the F7 transmit handler stored at file `0x1f608` has
linked VA `0x1f408`.  This corrects the coordinate wording in the earlier F7
boundary note without changing its pinned byte evidence.

## Ingress and family census

The receive/parser state machine occupies stored file `0x12ac4..0x12dbe`
(SHA-256 `5b2cbcbac9d03ba3a1dd175568a5cbc8cb7e74a75264a17fd354833d1f4e9c85`).
It uses the first received byte to select one of four modes.  Its command and
selector/value assembly is protocol state, not an address decoder.

| first byte / mode | transmit response branch | finite response domain | acquisition result |
| --- | --- | --- | --- |
| `F3`, mode 0 | file `0x21824` / VA `0x21624` | `F3:00` bounded logical-selector getter; `F3:80` 35-entry selector table; `F3:01` fixed framing expression | No caller-selected memory address; no saved-RT route. |
| `D0`, mode 2 | file `0x21878` / VA `0x21678` | exactly `D000..D004`, each with bounds-checked byte index | Five fixed arrays, not a memory window. |
| `FE`, mode 3 | file `0x2212e` / VA `0x21f2e` | four known profile arrays and six other exact commands; unmatched values return zero | No raw-address route. |
| `F7`, mode 1 | file `0x1f608` / VA `0x1f408` | exactly `F700`, `F720`, `F740`; unmatched values/indexes return zero | No generic read; see below. |

The F3/D0/FE conclusions are retained cross-checks of the previously decoded
dispatchers rather than a claim that their getters are universally
side-effect-free.  In particular, `F3:80` selector `0x09` is known
read-to-clear and some selectors read MMIO.

## F7: exact bounded outcome

The F7 transmit body is stored `0x1f608..0x1f65c`, 84 bytes, SHA-256
`2ae7a0bb909b54b67268f938d7456961ceb7a60a908794ffe15bc767241f1d51`.
The code-backed result map is:

| command | accepted index | returned source | not a route to |
| --- | --- | --- | --- |
| `F700`, `F720` | `0` | byte RAM `0x20000cb9` | firmware checksum / image data |
| `F700`, `F720` | `1` | low byte, common-object halfword `+0x152` | saved RT history |
| `F740` | `0..30` | byte at `0x20015180 + index` | arbitrary RAM / MCU dump |

`0x20000cb9` is a four-byte command/value additive protocol sum, not a
profile hash.  The `F740` source is a 31-byte subset of a transient response
envelope.  Its immediate clear helper and packet-sum helper are respectively
stored `0x1eed4..0x1eee4` (SHA-256
`7276da33f6172e31b583e5e11610dcb89473997ab0cb5bc3722b1abfdde188dc`) and
`0x1efd4..0x1eff2` (SHA-256
`0f9c85389f2b5e0bed86756031ba6286b232bfac3e5c756d8971985557ca3e0d`).

The paired F7 receive/action dispatcher is stored `0x1eee4..0x1efc6`
(SHA-256 `bdf186399bea803b7ec43d700238ad147607d89e43f56233ba1bc3a9edb2917e`).
It handles `F700`, finite `F701..F716` action cases, and `F730` no-op.  The
action set writes internal state/response RAM and includes MMIO-range stores.
That makes an `F740` result dependent on a control-capable protocol path; it
is not a defensible passive read candidate.

## Explicitly missing edges

Static code reviewed here does not bind any I2C response family to:

* the config logical reader at stored file `0x657c` (linked VA `0x637c`);
* a saved history record or the RT offsets `+0x2466`, `+0x2484`, `+0x24aa`,
  or `+0x24ac` of the fixed image-0 object;
* the live RT-related `+0x240a` field;
* image-0 `0x47010000` or image-1 `0x20010000` as a caller-selected source;
  or
* a whole-image version/hash/export route.

This is a negative result over these recovered ingress dispatchers and their
immediate F7 response producers.  It does not prove an absent undocumented
service interface elsewhere, current-flash equality, or a relationship to
the display blackout.

## Reproduction

Run `qd-i2c-read-command-family-census-20261027-checker.py` offline.  It pins
the profile SHA-256, file slices, and corrected file-to-VA mapping, then emits
the finite census.  It performs no target operation.
