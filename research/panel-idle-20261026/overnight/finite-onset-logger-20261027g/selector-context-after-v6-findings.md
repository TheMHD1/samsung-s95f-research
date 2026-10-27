# Later selector capture: nonzero alternate byte and NORMAL-compatible mode

The one reviewed selector acquisition completed on the same Linux boot.
It returned exactly 68 bytes from `0x470004a0` followed by 16 from
`0x47000bc0`, released/closed the interface, finished `ReadyForHeader`, and
removed its exact private stage. All 19 authenticated calls are retained in
`selector-context-after-v6/`. No flag, memory setting, firmware, UI or power
state was changed. A host output-poll tool call was aborted before dispatch;
the original native invocation was not retried. The already completed local
record/result establish its successful terminal outcome.

Terminal uptime was `119358.55`, about 3,451.10 seconds after V6 ended and
1,524.30 seconds after the earlier score-window read. These are separate
sampling epochs. The two selector reads themselves were sequential.

## Actual bus values

| Bus field | Value | Interpretation boundary |
| --- | ---: | --- |
| `0x470004e0`, u32 | `0x20010000` | same-response expected root anchor |
| `0x470004aa`, u16 | 0 | conditional image-1 `aa` selector |
| `0x470004ac`, u16 | 2 | conditional image-1 `ac` selector |
| `0x470004a0`, u16 | 396 | conditional scan/status counter |
| `0x470004c2`, u16 | 1 | conditional alternate-byte numeric mirror |
| `0x470004c4`, u16 | 0 | separate mirror-control field; preserve its zero |
| `0x470004d8`, byte | 0 | conditional ordinary scan-enable argument |
| `0x47000bc0/c2/c4`, u16 | 2160 / 1920 / 2880 | exact match to three startup constants |
| `0x47000bc7`, byte | 1 | alternate-byte candidate, nonzero |
| `0x47000bc8`, byte | 3 | neighboring callback-byte candidate |

The complete second window is:

```text
70 08 80 07 40 0b 5c 01 03 00 00 00 00 00 00 00
```

This is considerably stronger layout corroboration than a single nonzero
byte: the first three halfwords match separately traced initialization
stores, and byte `+7` agrees numerically with the first window's mirror.
The same-response root anchors the first window's conditional CPU model.
The helper deliberately retains the second window as candidate bus bytes;
this report does not turn those correlations into proof of the live core
tag, every RAM alias, or whole executing firmware identity.

The candidate source-byte pair `1,3` differs from the selected profile's
conditional `20,0` defaults. Its live state must therefore be measured rather
than assumed from that profile. The observation does not identify why it
differs, a named user setting, or which configuration/persistence mechanism
provided it.

## What it narrows

If the copied ordinary tail were reached with `aa=0, ac=2`, it would choose
mode 1: only equality to 1 selects either special mode. A nonzero alternate
byte then selects `R+0x24c4`, whose earlier bus-window value was 40. The
earlier shared non-mode-6 score latch was 44. That makes **mode 1 / alternate
limit 40 / retained score 44** a concrete, numerically consistent hypothesis
for further testing, also consistent with the captured NORMAL rows.

It is not an event-time reconstruction. The selector and score samples are
about 25 minutes apart; mode fields can transition after a scan, the
alternate-byte mirror updates separately from the ordinary scan gate, and
the score stores are not tagged with an event ID. The ordinary scan argument
in this sample is zero, so this is not a claim that a mode-1 comparison was
executing when sampled. See `rtp-post-fault-ordinary-gating.md`.

The `+0x4c4=0` value also must not be silently replaced with a Boolean 1 just
because `+0x4c2=1`. The source routine sets Boolean state when refreshing the
numeric mirror, but the subsequent ordinary function `0x1c12c` increments
the companion and clears it after it exceeds 2. When the selector still
equals the numeric mirror, `0xc250` skips both assignments. Thus mirror1
and companion0 are compatible with ordinary execution; this field is not a
continuously maintained Boolean. The exact writer/read paths are documented
in `rtp-selector-consistency-after-v6.md` and its verifier. The raw zero is
preserved.

The candidate byte `+6=0x5c` also matches a distinct startup handshake: the
code writes `0x5c` to an AP_EXCO request field and polls fixed-context
`+0x6c6` for equality. Its actual producer is not recovered by the bounded
direct-store census. Together with the three startup constants and numeric
mirror, this supplies several independent layout consistencies while
retaining the alias/time caveats.

## Artifacts and next observation

The exact source/build manifest is
`4d3e0ac655aff8eac8d1d2f3835d96597f74d5c45c751e67323ea36805663446`.
Mode-window SHA256 is
`c58a20a4147d7b09bfe560456cb65bfce1462fdc5aefcfc50b80e3f5927765c9`;
candidate-window SHA256 is
`2efca8a0f734277a3df0351751a2ec11d33d20423983381f5068299289fc308a`.
`decode-selector-context-after-v6.py` reproduces every halfword/byte and
conditional selector classification offline. Its JSON is
`selector-context-after-v6-decoded.json`; the independent runtime review is
separate from the source review.

The decisive future event record remains the actual selected mode, the
threshold source/value loaded for that call, and its accumulator/low-half
score immediately before the taken comparison edge. That observation would
distinguish the 44-versus-40 hypothesis from a special-mode event or a
selector/configuration change between samples. No physical recovery,
blackout prevention, permanent-root change, protection bypass or flash has
been demonstrated by this capture.
