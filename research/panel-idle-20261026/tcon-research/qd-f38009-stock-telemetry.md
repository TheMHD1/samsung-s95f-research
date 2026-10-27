# `F3:80:...:09` stock telemetry / consumption audit

Recorded 2026-10-27 UTC. This is an offline examination of already-retained
controller-image bytes and logs. It made no TV, root, network, media,
controller, I2C, or display call, and does not propose a new target query.

## Result

`F3 80 00 00 00 09` is a **stock, periodic `sp-kpi` read** on this TV, not a
diagnostic packet invented for this investigation. The retained duty log has
eight `sp-kpi` reads roughly 60 seconds apart, all returning zero. In the
selected packaged QD image, selector `09` returns a seven-bit composite word.
One of its sources is the halfword at RAM `0x2000f808`; if that halfword is
nonzero, the getter sets returned bit `0x20` **and then writes that halfword to
zero**. Thus this selector is read-to-clear for that source.

That gives a concrete observability limit: after an ordinary `sp-kpi` poll,
a later zero does *not* show that the `0x2000f808` latch was never nonzero.
A nonzero returned bit `0x20` would show that it was nonzero at that specific
read. It would not, by itself, label the event, locate a panel fault, or prove
that it caused a blackout.

The bounded static path has no direct call to the recovered EEPROM RT check,
RT action, EEPROM helper, or common-error entry. No writer of
`0x2000f808` was positively recovered in this bounded pass, so its producer
and semantic name remain unknown. In particular, it must not be relabelled as
an RT counter, error subtype, or the source of the observed status `0x10`.

## Exact stock evidence

Input `overnight/sleep-investigation-20261027a/duty-log.stdout`, SHA-256
`d43184307091d67d93992a4dd72188ff3331d2a7fd258534c2161c7e1bd5c1c6`, contains
these kernel rows (kernel uptime seconds):

| Uptime | Task | Command | Returned value |
| ---: | --- | --- | ---: |
| 92735.855734 | `sp-kpi` | `0xF38000000009` | 0 |
| 92795.859431 | `sp-kpi` | `0xF38000000009` | 0 |
| 92855.864595 | `sp-kpi` | `0xF38000000009` | 0 |
| 92915.868916 | `sp-kpi` | `0xF38000000009` | 0 |
| 92975.875009 | `sp-kpi` | `0xF38000000009` | 0 |
| 93035.882580 | `sp-kpi` | `0xF38000000009` | 0 |
| 93095.886725 | `sp-kpi` | `0xF38000000009` | 0 |
| 93155.894093 | `sp-kpi` | `0xF38000000009` | 0 |
| 93215.917166 | `sp-kpi` | `0xF38000000009` | 0 |

The first seven intervals are approximately 60 seconds (the final interval is
shorter in this retained ring excerpt). This proves periodic host-side use and
the logged values, not what the selected package calls the field.

An independent retained PROGRAM_A kernel extraction also contains a stock
`sp-kpi` row at uptime `87574.612711`, command `0xF38000000009`, value `0`.
Its source is
`overnight/hdmi-blackout-20261027a/ugoos-PROGRAM_A-query-kernel-offline.txt`,
SHA-256 `2d19ceaa3f25add9b87dbb468b5dc745f6aecf4a6938f6bd674f8df432a3250e`.
That extraction is a later kernel-ring capture, not an event-aligned reply
captured by the PROGRAM_A playback collector.

## Packaged getter mechanics (corrected coordinates)

The selected package is
`overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
5,242,880 bytes, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
All addresses below use the corrected image-0 convention: `file = linked VA +
0x200`; they do not establish equality with the controller's current flash.

`F3:80` reaches the bounded selector table at linked VA `0x21df8` (file
`0x21ff8`), 242 bytes, SHA-256
`7b7038d870a46b9f897a44d3368618a13a61025ed86a9c5c61b6dccddba23aa0`.
Its `09` case calls linked VA `0xfe6c` (file `0x1006c`), 316 bytes, SHA-256
`24f30bf63c8dbfd8fbeb0a8410d07057215b126b5125b91bf0c375615e971b0c`.
The latter has these material instructions:

```text
VA 0xfe7c  BL    0xf4f0             ; returns literal 0x2000f7c2
VA 0xfe80  MOV   r8,r0
...
VA 0xff66  LDRH  r0,[r8,#0x46]      ; RAM 0x2000f808
VA 0xff6a  CBZ   r0,0xff76
VA 0xff6c  ORR   r4,r4,#0x20
VA 0xff70  MOVS  r0,#0
VA 0xff72  STRH  r0,[r8,#0x46]      ; clear after reporting bit 0x20
```

The complete result is held in `r4` and serialized by the established F3:80
four-byte path as `00 00 00 xx`. The static conditions for the other bits are
comparisons/threshold tests in this same function:

| Result bit | Direct source class in the getter |
| ---: | --- |
| `0x01`, `0x02`, `0x08`, `0x10` | halfword comparisons against package thresholds / accessor-returned object fields |
| `0x04` | four sampled word-vs-range tests (each can set the same bit) |
| `0x20` | nonzero RAM halfword `0x2000f808`, then destructive clear |
| `0x40` | three byte range tests from the object returned by VA `0xea84` |

This table describes code behavior only; no vendor names or physical units are
available for those operands. `0x20` is the sole persistent store in the
selector body. The four temporary stack words used by the `0x04` tests are not
state writes.

## RT/error-handler boundary and writer result

The resolved selector-table case calls only the composite getter above. Its
bounded callee graph does not call the corrected linked RT check `0x97e8`, RT
action `0x9968`, EEPROM helper `0x9748`, or common-error routine `0xb660`.
The getter also does not load the previously recovered RT EEPROM fields.
That is a direct-path exclusion for this exact image, not evidence that a
future or unrelated producer cannot correlate with an RT event.

The getter's accessor literal identifies the cleared field precisely as
`0x2000f7c2 + 0x46 = 0x2000f808`. A bounded literal-reference pass found no
unambiguous code writer that can be attributed to that field; nearby raw
literal/table data must not be decoded as instructions. Therefore the only
proved writer here is the getter's clear at VA `0xff72`. No clear-on-read
behavior is asserted for any other bit or for selector `08`.

## Playback-record check and limits

The retained PROGRAM_LABEL (`ugoos-movie`), PROGRAM_B, and PROGRAM_A
onset collectors are all marked `accepted: false` / not diagnostic-eligible
because their AVOC-map validation changed. Their `trace` and `vlog-after`
sidecars contain no exact `QDFTcon_ReadOneCommand ... F38000000009` record.
They therefore contain no event-aligned selector-09 request/reply to decode.
This is not an absence claim: the collectors were not a complete controller
transaction recorder.

PROGRAM_04 black-state kernel extraction is separately limited to its
requested dmesg window and does not expose a selector-09 row. The program_b retained
root responses expose the requested ring-read commands and one `ERR DET
Status:0x10` row, but no `F380...09` reply. Neither fact can recover the
pre-poll value of the read-to-clear field.

Accordingly, the documented automatic stock polling is a confounder for
retrospective interpretation of selector `09`; it does not establish a causal
connection to RT/error handling or the persistent-black symptom.
