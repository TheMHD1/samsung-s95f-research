# AP_EXCO source capture: independent runtime review

Recorded 2026-10-27 UTC. This review inspected only the retained M artifacts
and the final pinned helper. It made no TV, root, USB, controller, network,
UI, reset, write, or target call and did not modify any earlier evidence.

## Verdict

The transport capture is accepted and complete, but its conditional pointer
interpretation is rejected exactly as designed.

- **P0/P1 runtime findings:** none.
- All three fixed reads completed with exact counts, the protocol returned to
  `ReadyForHeader`, release and close returned zero, and the private stage was
  verified absent.
- The required pointer at returned offset `0x0c` is not `0x4500ff14`; it is
  `0x450158a8`. Therefore the proposed pointer binding failed and the three
  sequential windows must not be treated as one AP_EXCO live tuple.
- The same raw pointer window contains `0x4500ff14` and `0x4501024e` at the
  neighboring bus words `0x470002c4` and `0x470002c8`. Those two local numeric
  matches do not prove a global `0x4700....` relocation, whole-bank alias,
  executing-image identity, or physical meaning.

## Reviewed identities

| artifact | SHA-256 |
| --- | --- |
| final helper manifest | `3222c56b1b80749123a2b360ebae9ffbf44779cf748061737774c93fc153fa51` |
| prior independent source review | `c56b76d402ed83330631dd85a6dc56dd72060531d6abfe3823aba210a4de1b77` |
| raw wrapper record | `e6986cb1cef2e78f14057a95c087e905db97ee22f22102001560e816d8c91f74` |
| wrapper result | `ffba3a63943e30fe689a1251237dfe18dcadff0c6eb5aec1022c3ac1eb20e901` |
| execute envelope | `e7d5be93636ab86bf12b284751bda295e4af5240192de01a91440c491ed8f98f` |
| native stdout | `6ab12b8146335a89152d5129f770756b5231f6117f8d608ed7ea2cd24c7301de` |
| native stderr | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The final manifest contains the source, wrapper, runtime, tests, and native
DLL identities reviewed before execution. The record pins that manifest, the
same wrapper and root adapter, boot ID
`00000000-0000-4000-8000-000000000000`, one native invocation, no retry, and
three accepted target read requests.

## Raw authenticated-envelope audit

`record.json` contains exactly 19 calls. For every call I independently
decoded the retained base64 transport stdout and verified that its parsed
JSON equals the saved `response` object. Every response has:

- `authenticated=true`, `uid=0`, and `euid=0`;
- exactly one command whose echoed text equals the requested command;
- transport exit and command exit zero;
- no host or remote timeout;
- empty transport and command stderr; and
- the pinned 45-second remote and 75-second host limits.

There is exactly one `--self-test` call and exactly one production
`--execute` call. The extracted self-test and execute-envelope files equal
the corresponding authenticated command stdout byte-for-byte. The execute
envelope pins native exit zero, stdout length 1,812 and SHA-256
`6ab12b81...`, empty stderr, exact five-file terminal inventory, and boot
uptime `122020.20`.

Native stdout contains one JSON object followed by exactly two recognized GC
rows. Its ten steps are exactly:

```text
open, claim,
pointer-header OUT 12, pointer-data IN 32,
source-base-header OUT 12, source-base-data IN 16,
source-tail-header OUT 12, source-tail-data IN 32,
release, close
```

Every step has `Errno=0` and no error. The three fixed headers represented by
the pinned helper are:

```text
01010000c002004720000000  -> target 0x101, 0x470002c0, 32
0101000014ff004510000000  -> target 0x101, 0x4500ff14, 16
01010000e002014520000000  -> target 0x101, 0x450102e0, 32
```

There is no memory-write or reset request. The evidence establishes only
these three read requests and local usbfs lifecycle operations; it is not a
general claim that no unrelated actor could alter memory concurrently.

## Exact returned bytes

### Pointer window

`pointer-window.bin` is 32 bytes, SHA-256
`7634f63e1eace3b6da5f287655f1b1ef3ebdb81b22909605a467c2472af43cd3`:

```text
bus address    LE32 value
0x470002c0     0x00000001
0x470002c4     0x4500ff14
0x470002c8     0x4501024e
0x470002cc     0x450158a8   <- reviewed anchor slot; mismatch
0x470002d0     0x450130b6
0x470002d4     0x450130f0
0x470002d8     0x4500f0e0
0x470002dc     0x0001b691
```

The gate expected `LE32(window[0x0c:0x10]) == 0x4500ff14`; actual is
`0x450158a8`. Native and wrapper both preserve the raw window, set
`PointerMatches=false`, `InterpretationAccepted=false`, and report
`pointer-anchor-mismatch`.

The values at offsets `+0x04/+0x08` numerically equal the selected AP_EXCO
first and second mapped destinations. This is positive local content at the
two stated bus words only. It does not establish that the selected startup
table shifted by two words, that bus `0x470002c4` is CPU slot `0x200002c4`,
or that other `0x4700....` addresses share the same mapping.

### Fixed source windows

`source-base-window.bin` is 16 all-zero bytes, SHA-256
`374708fff7719dd5979ec875d56cd2286f6d3cf7ec317a3b25632aab28ec37bb`.
Its monitored source byte at object `+0` is zero, matching the selected
package. The complete window does **not** equal the selected comparison
window `00000000000000000100000000000000`: selected offset `+8` is one,
while this late raw window has zero. Accordingly, the result field
`sequential_values_match_packaged_defaults=true` refers only to the two
monitored scalar bytes, not full-window equality.

`source-tail-window.bin` is 32 bytes, SHA-256
`f4eec86c76db591f12c003fc318c76418e9455c10f10ad2c40acf0b21010814b`:

```text
1300130013001300140014001400140015001500150016001600160016001700
```

It equals the selected comparison window byte-for-byte. Its offset `+0x0c`,
corresponding numerically to AP_EXCO object `+0x3d8`, is `0x14` (20).

Thus the sequential scalar pair is `0/20`, matching the selected package's
two monitored values and differing from the earlier saved context-mirror
pair `3/1`. Because the pointer anchor failed, the reads were sequential, and
the context mirror itself had only conditional source semantics, this numeric
comparison does not bind the values into one live AP_EXCO structure or show
which state changed first.

## Cleanup and limits

The native result is `Accepted=true`, `Released=true`, `Closed=true`, and
terminal `ReadyForHeader`. The final authenticated cleanup command verified
the exact five-file stage inventory and hashes before removal, then returned
`STAGE_ABSENT`; the record has `cleanup_required=false`.

The capture occurred long after the retained V6 onset and has no
contemporaneous physical-picture annotation. It proves neither event-time
state nor a panel-blackout transition. It also does not prove selected code
body identity, active configuration source, field semantics, a global bus
alias, or physical pixel/sensor meaning.
