# Independent review: QD generic one-command read ABI

Reviewed 2026-10-27 UTC, using retained local ELF/module bytes only. No TV,
root, network, controller, bus, capture, ioctl, or command action occurred.

## Reviewed revision

| artifact | SHA-256 |
| --- | --- |
| ABI report | `52b1be2e269edc353ffa3f290305067c3c720a3ae000526e08f59d2bbe412172` |
| `libave.so.0.1` | `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` |
| `tztv_frc_tcon.ko` | `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd` |
| `tztv_frc_tcon_api.ko` | `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6` |
| `qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` |

## Independent findings

**Operation 19, not 18.** The ARM32 `ave_tcon_api_read_onecommand` body uses
the 16-byte `0xc010749f` envelope with word0 `19`, retains the initial word1,
and copies word1 to the caller only after a nonnegative ioctl result. The
adjacent send wrapper uses word0 `18` and an input scalar pointer without this
copyback. Treating operation 18 as a read would be a material ABI error; the
reviewed report correctly does not do so.

**Exact command split.** ARM32 passes the low 32 bits in `r0` and high 32
bits in `r1`; the wrapper stores high16 into word2 and low32 into word3. For
the narrow candidate, that is:

```text
word2 = 0x0000f300
word3 = 0x00000128
reconstructed command = 0x0000f30000000128
```

This is selector hexadecimal `0x128`, not decimal 128 / `0x80`. The API
operation-19 case loads the slot at `+0x3a8`; operation 18 instead loads
`+0x3a0`. The initializer's paired store places `QDFTcon_SendOneCommand` and
`QDFTcon_ReadOneCommand` in exactly those slots. The corrected report's
callback-binding claim is supported by these table offsets and relocations;
it is static intended binding, not a live pointer observation.

**Wire direction and size.** The read callback reaches `m_read_cmd`, which
forms two high command bytes plus the low word in big-endian byte order. For
the above split command the six write bytes are exactly:

```text
f3 00 00 00 01 28
```

The recovered lower routes both request a four-byte response. This is a
write-then-read protocol transaction, not a passive memory inspection. The
report correctly preserves the risks that a selector may have controller-side
semantics and that a nominally successful ioctl can leave the sentinel
unchanged if a dispatch path is absent or suppressed.

## Gates and preflight limits

The report's relevant static gates are appropriately retained: absent API
slot, suspend state, command-skip state, non-ready TCON state, and lower
transport failures can all prevent a new response. The two exact-command
exceptions cited in the report do not match `0x0000f30000000128`. A changed
word1 sentinel would demonstrate only that the kernel supplied a four-byte
output; it would not establish selector meaning, current firmware equality,
or physical panel effect.

The code block in the report is useful as an offline layout cross-check and
uses the correct corrected command. Because it uses Python `assert`, its
individual checks are not `-O` enforcement. That is not a contradiction of
the report: its normal/optimized reproducibility statement applies to the
separately retained `qd-onecommand-buffer-reproduce.py` verifier, not to this
illustrative block. Any future executable evidence tool should use explicit
runtime checks rather than relying on assertions.

## Verdict

**CLEAR for the bounded static ABI conclusion.** The report correctly
distinguishes operation 19 from operation 18, correctly encodes selector
`0x128`, proves the static callback table pairing, and correctly describes a
six-byte request followed by a four-byte read response. It does not overstate
this as a harmless, live, or ready-to-run operation.

No helper has been prepared or recommended by this review. In particular,
current callback installation, controller firmware identity, return freshness,
selector behavior, and controller-side state effects remain prerequisites for
any separate decision; this review authorizes none.
