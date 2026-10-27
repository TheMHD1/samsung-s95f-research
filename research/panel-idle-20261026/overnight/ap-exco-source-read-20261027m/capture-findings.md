# Fixed source capture: accepted transport, rejected pointer binding

Recorded 2026-10-27 UTC. One invocation used reviewed build manifest
`3222c56b1b80749123a2b360ebae9ffbf44779cf748061737774c93fc153fa51`.
The capture completed on Linux boot `00000000-0000-4000-8000-000000000000`,
with terminal uptime `122020.20`. It contains 19 authenticated root calls,
one native execution, three exact header/read pairs, ReadyForHeader terminal
phase, successful release/close, and STAGE_ABSENT cleanup. Native self-tests
returned 47 passing cases. No configuration write, retry, reset, UI request,
flash or physical-picture observation occurred. Separate runtime review is
recorded in this directory.

## Unexpected pointer layout

The fixed 32-byte window returned these raw little-endian words:

| bus address | returned word |
| --- | --- |
| 470002c0 | 00000001 |
| 470002c4 | 4500ff14 |
| 470002c8 | 4501024e |
| 470002cc | 450158a8 |
| 470002d0 | 450130b6 |
| 470002d4 | 450130f0 |
| 470002d8 | 4500f0e0 |
| 470002dc | 0001b691 |

The selected packaged getter/startup predicted the AP_EXCO pointer at CPU
200002cc, conditionally observed through bus470002cc. The returned word there
is **450158a8**, not **4500ff14**. The wrapper therefore correctly reports
`transport_accepted=true`, `interpretation_accepted=false` and
`pointer-anchor-mismatch`. The expected first/second AP_EXCO addresses appear
at the neighboring c4/c8 words, but that is not permission to subtract eight
from every address or silently change this capture's acceptance rule.

The selected configuration row independently names AP_EXCO destinations
2000ff14/2001024e and AP_TED destinations200130b6/200130f0; its AP destination
is2000f0e0. Their +25000000 mappings match several raw neighboring words.
That makes the neighborhood worth an ordinary startup-layout trace, without
proving that they are the current getter's pointers. The word450158a8 was
not found inside either destination extent of the selected 21-row table.
No dynamic pointer was dereferenced, and no follow-up read was attempted.

## Fixed source bytes

The positively allocated fixed windows returned:

| window | raw result | SHA-256 |
| --- | --- | --- |
| 4500ff14 /16 | sixteen zero bytes | 374708fff7719dd5979ec875d56cd2286f6d3cf7ec317a3b25632aab28ec37bb |
| 450102e0 /32 | 1300130013001300140014001400140015001500150016001600160016001700 | f4eec86c76db591f12c003fc318c76418e9455c10f10ad2c40acf0b21010814b |

The pointer window SHA-256 is
`7634f63e1eace3b6da5f287655f1b1ef3ebdb81b22909605a467c2472af43cd3`.
At the proposed source byte positions, the numeric pair is20/0, matching the
two retained firmware defaults and differing from the earlier candidate
mirror pair1/3. This is a raw fixed-location comparison; the rejected pointer
binding means it does **not** establish that the running callback used those
locations at this acquisition, much less at V6.

The 32-byte tail window exactly matches the selected packaged window. The
16-byte base window does not: its offset8 is0 while the package has1. Thus
matching the two chosen bytes must not be described as complete source-window
or full-object equality. No field meaning is assigned to any byte.

## Consequence

This capture identifies a real inconsistency in the working runtime-layout
model. Plausible categories include a different active layout/body, wrong
local getter-slot interpretation, or another runtime writer. The raw words do
not select among these possibilities. Stored-image equality and matching
callbacks remain useful but cannot replace an executing-body/layout check.

Existing V6 fault and RTProtect observations are unchanged. The selected
package's numeric predicate remains a packaged-code fact; treating all its
absolute slot offsets as currently executing facts is not justified by this
new capture. No fault prevention or panel recovery has been established.

The next work is a finite offline comparison of ordinary startup pointer
stores/getters against this neighborhood. No new live diagnostic read is
scheduled merely by shifting a prior address.
