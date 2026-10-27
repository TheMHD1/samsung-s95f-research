# Selected controller profile: positive AP_RTP load binding

Recorded 2026-10-27 UTC. This offline result follows the actual corrected
image0 code pointers, a21-row configuration table, the selected package's
AP_RTP directory entry and its two payloads. No TV/network/firmware/register/
EEPROM/GPIO/USB action was performed. Existing reports remain historical.

## What changed

The earlier RT-parameter provenance review had not recovered a binding from
AP_RTP to the fixed RT field window. That missing-loader conclusion is now
narrowly superseded: the packaged startup path does contain such a binding.
On successful type4 reads, the selected record's first payload supplies the
RT field block at0x47012400 and its second supplies0x47010000..0x470123ff.
This identifies initialization provenance, not the fault trigger or a fix.

## Pinned source and address convention

`../overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
5MiB, SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Image0 executable VA = FILE offset minus0x200. Absolute RAM addresses are
unchanged. All code offsets below use FILE explicitly. Runtime image equality
and successful execution of this packaged path on this TV remain unproved.

## The real mapping table

At FILE0x3ccbc (VA0x3cabc) there are21 rows of seven32-bit words, stride0x1c.
The loader and generic reader load that exact VA from FILE0x6570/0x660c.
Each row is consumed as a name pointer, first physical destination/length,
second physical destination/length, and two logical prefixes. Row14 at
FILE0x3ce44 is:

| field | value |
| --- | --- |
| name VA | 0x3de8c -> stored0x3e08c, AP_RTP |
| first destination / maximum | 0x47012400 / 0x100 |
| second destination / maximum | 0x47010000 / 0x2400 |
| first / second logical prefix | 0x210000 / 0x210400 |

The logical prefixes are not raw file offsets. Reading the package at raw
0x210000 and finding zeros is not evidence that the initialized RT block is
empty. The metadata supplies separate source offsets relative to a selected
configuration base.

## Directory and source payloads

The selected package's configuration header is FILE0x80000; its count is57
and directory records start at0x80200 with stride0x200. AP_RTP is record47,
at FILE0x86000. Relevant fields decoded by the actual loader are:

| record offset | value / use |
| --- | --- |
| +0x20 | type4: MCU-copy branch |
| +0x24 | logical0x210000 |
| +0x28 / +0x2c | first present1 / source0x103800 |
| +0x6c / +0xac | first destination offset0 / length0x100 |
| +0xf0 / +0xf4 | second present1 / source0x103a00 |
| +0x134 / +0x174 | logical second offset0x400 / length0x2400 |

For this package's configuration base0x80000, successful loader arithmetic is:

| packaged source | size | fixed physical destination |
| --- | --- | --- |
| FILE0x183800 =0x80000+0x103800 | 0x100 | 0x47012400 |
| FILE0x183a00 =0x80000+0x103a00 | 0x2400 | 0x47010000 |

The loader does NOT add metadata+0x134 to the second physical destination.
Its first destination includes metadata+0x6c; its second uses table+0xc
directly. The0x400 gap belongs to the logical address layout, reflected by
0x210400-0x210000. Confusing those layouts would misplace the RT fields.

## Executable path and bounds

Startup FILE0x39c5e calls FILE0x7674, which reaches the type4 enumerator
FILE0x7744 through FILE0x7692. The alternate enumerator FILE0x77b8 also
reaches the same loader. Both use directory reader FILE0x70e4 with selected
base+0x200+index*0x200. FILE0x7780 and0x77f4 call loader FILE0x6390 when
the directory type is4; type7 follows a different IP-copy path.

The loader compares each record's name with the21 table names. For a match,
it reads source bytes through FILE0x9dd4, in bounded chunks up to0x2000,
with a three-failure counter. Only a successful read reaches the memcpy.
The first copy at FILE0x6442..0x6458 uses table+4 plus metadata+0x6c,
and min(table first length, metadata first length). The second at
FILE0x6516..0x6528 uses table+0xc and the analogous second length minimum.
Persistent failures enter common error handling with selector0x400. This
is an executable successful-path binding, not proof that live storage reads
succeeded or that the runtime configuration was not changed later.

## Concrete default RT fields

The first payload maps to object offsets0x2400..0x24ff, so the previously
identified image0 RT fields have the following selected-package defaults:

| object offset | fixed address | payload offset | default |
| --- | --- | --- | --- |
| +0x240a | 0x4701240a | +0x0a | low byte0; halfword0 |
| +0x2466 | 0x47012466 | +0x66 | halfword0 |
| +0x2484 | 0x47012484 | +0x84 | halfword0 |
| +0x24aa | 0x470124aa | +0xaa | byte100 |
| +0x24ac | 0x470124ac | +0xac | halfword0 |

Other packaged fields include mode+0x2410=4, +0x2450=20,
+0x2452=2157, +0x2454=2160 and +0x24b4=1. These are raw initial values;
the code-specific units and their relation to damaged pixels remain unknown.
The history threshold byte100 is not a physical voltage/current limit and
is not a justified tuning target. A zero initial RT flag does not explain
when, why or by whom it becomes set during the live failure.

The image1 startup context base is separately proved as0x20010000. The
matching object layout strengthens the shared-window lead, but this report
does not prove the hardware alias between its0x2001 region and image0's
0x4701 window, nor that image1 was running during the incident.

## Generic reader boundary

FILE0x657c translates logical high16 prefixes with the same table and copies
from first or second physical RAM into a caller buffer. For logical0x21000a,
the first-region arithmetic resolves to0x4701240a. That is static address
arithmetic, not a completed read from the TV.

The recovered reader does not provide adequate general second-region,
logical-gap or count bounds. Its only recovered direct callers are debug/
parameter/TCDATA paths at FILE0x11258,0x1168c and0x2a4f8. No binding to the
established host I2C dispatch is proved. Thus it is a lead for a narrowly
bounded diagnostic route, not a command ready to send. No candidate logical
read or config write was issued.

## Verification and relationship to prior findings

The reproduction script checks the whole source hash, table and metadata
schema, exact instructions at the copy/dispatch sites, and source arithmetic.
It records source slices and parameter bytes in the companion JSON. Normal
and optimized Python runs produced identical output. The independent review
[qd-config-rtp-table-independent-review.md](qd-config-rtp-table-independent-review.md)
separately confirms the binding, startup reachability and destination-offset
nuance. It preserves the current-flash/runtime/protocol gaps.

This result supersedes the missing AP_RTP initializer portion of
[qd-rt-parameter-load-provenance.md](qd-rt-parameter-load-provenance.md).
It does not supersede the relative RT-to-status path, physical observations,
status/pin comparison, or the unresolved hardware producer. No configuration
was changed, no protection bypass was prepared, and no repair is claimed.

Reproduce offline:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/qd-config-rtp-table-reproduce.py
```
