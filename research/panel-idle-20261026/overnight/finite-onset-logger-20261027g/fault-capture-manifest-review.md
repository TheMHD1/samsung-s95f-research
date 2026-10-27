# Independent D7 fault-capture freeze review

## P0 — No integrity blocker found

The frozen manifest `fault-capture-evidence-manifest.json` has exact SHA-256
`3bda86db80ddc3a0d5d6b0127e2dbc0ce6c1dcc19b15af3ad7b919bd29d12fb6`.
Its declared schema is `s95f-d7-fault-capture-evidence-v1`, `frozen` is true,
and the declared inventory is exactly 194 files and 6,083,645 bytes.

An independent row-by-row read-only reconstruction passed:

- all 194 relative paths are contained under the D7 directory;
- every row resolves to an ordinary non-symlink regular file;
- every actual size and SHA-256 matches its manifest row;
- the row sizes sum exactly to 6,083,645 bytes;
- the 14 declared inventory roots contain exactly 148 files; and
- the 46 declared individual files supply the remaining 46 rows, with no
  missing, unexpected, duplicate, absolute, or `..` path.

The root counts are independently reproduced as:

```text
source-checkpoint-v6                 37
control-smoke-v3                      2
control-smoke-v3-receipt-recovery     3
control-smoke-v3-terminal             4
control-smoke-v3-terminal-complete   29
control-smoke-v3-validated            9
onset-v4 / onset-v5 / onset-v6       16 each
ui-prepared-onset-v4                  2
ui-for-you-onset-v4/v5/v6             4 each
ui-cleanup-onset-v6                   2
individual files                     46
```

The manifest correctly excludes itself, this later independent review, the
mutable README/current narrative, and future captures. Those exclusions are
consistent with its stated scope rather than omissions from a declared root.

## P1 — The 84-file parent freeze is unchanged and correctly pinned

The prior `runtime-evidence-manifest.json` remains byte-identical at SHA-256
`2d1d1427ea37c70e5b6ee37e301488027f6b2a0ff64f7d591884ca6faa252534`.
The new manifest's `prior_manifest_sha256` field is exactly that value.

The parent manifest independently passes the same reconstruction: 84 exact
regular non-symlink files, 4,515,096 bytes, ten complete inventory roots plus
15 individual files, and no missing or extra path. The new freeze and parent
freeze have no overlapping file row; they are complementary inventories tied
together by the parent-manifest hash, not competing descriptions of the same
files.

## P2 — Reviewed source identity is preserved in the freeze

The 37-file `source-checkpoint-v6` tree pins the exact logger and UI code used
by the captured runs. Material identities include:

- framing wrapper manifest
  `b1ffc0f91b614163e10e4132b9410c60116d22101b5666f1614ef471b4938780`;
- framing wrapper
  `489c4391db6622918befcf365b5952f08cd3f58f3989925b8b6d0fa51a1ab36f`;
- logger native manifest
  `316d92b64be47767cb8461d4cbde30b9446d901060b2de798da605d9f1c8131c`;
- logger native DLL
  `4870eed095247b8f5c86a58044e10e8c3682248b4c0465c49e5d4642cb8e54e9`;
- parent smoke wrapper
  `eeb852c8e1b9a0d2611abc17e853ad2ee834f4e42712b2810bf8309eda5e59ca`;
- UI sender manifest
  `79815f8e9d0a00f49de31f3e80a0e73ac549c4681097ef7f0453b518d3fb58ee`;
  and
- UI wrapper
  `985b97762e1379cc062b4b222873588566ad81f8e07043c46ac1a9f3fadc2b97`.

The frozen copy also includes the prior independently reviewed V3, V4, and
V5/V6 runtime audits at their exact manifest hashes. No audit file was
rewritten during this review.

## P3 — The three new static chains pass, with their limits intact

The frozen read-only verifiers were inspected for file operations and then
executed in normal and optimized Python modes. All six invocations passed and
made no write, subprocess, network, root, TV, USB, or controller operation.

### Normal/control chain

`rtp-normal-log-trace.py` SHA-256
`610e8fd523f110ac7a0dfe62b28be386289445afd92db80dc420981245049368`
pins the exact V3 56-byte delta and selected-package slices. Its instruction
and direct-call checks support the distinct status-halfword and `t`-byte
counter paths, including the bounded reset-to-zero candidate. It correctly
does not promote matching text to proof that the packaged body executed or to
a panel-fault meaning.

### V6 incident-record chain

`rtp-incident-record-format.py` SHA-256
`d6818a8abcfd42729144f04783c4377f66b2b8d8e07574526eceb6af2b5003f7`
pins the exact accepted outcome, all RT/ring artifact hashes, the 1,756-byte
delta, all 31 formatted rows, selected-package slices, fixed scalar sources,
four unsigned 12-bit packed lanes, absolute-difference arithmetic, and final
formatter argument order. It correctly classifies `x` as a logical packed
element index and leaves the physical/electrical meaning and units unassigned.

### Event-736 producer-to-host chain

`verify-rtp-act-736-trace.py` SHA-256
`e17da69bc7454b99822844d5be40af4a0ae1f2b40a2232d7a6b3867457240fbe`
pins the observed `0 -> 0x1001` fixed-window transition, exact two terminal
`rtp_act_736` lines, packaged `0x2e0` caller, common setter stores and two sink
calls, image-0 bit-zero consumer, selector-`0x10` store, selector-8 getter,
later same-boot status `0x10`, matching kernel row, and GPIO value one. Its
normal and optimized outputs are identical compact summaries.

This last verifier relies on the full SHA-256-pinned prior wire report for the
lower host serializer/reversal proof rather than re-decoding that entire path
itself. The report was independently read at its pinned hash
`6c532e2ad8a48041cf83ebddfa42af1282019d14169902b47e621f6a1c237f6e`;
it supplies the `F3 80 00 00 00 08 -> 00 00 00 10 -> host 0x10` path and its
image-identity caveat. Likewise, the event verifier checks the native step
count rather than replaying every transfer field; the frozen V5/V6 runtime
audit supplies that independent exact 16-step transport check. These are
layered coverage boundaries, not contradictions.

The static chains consistently preserve the decisive limit: callback
generation and matching runtime behavior do not prove immutable equality of
the complete executing controller image. They also do not prove UI causality,
physical emitted light, a blackout, an electrical meaning for RTP, or a safe
repair/bypass.
