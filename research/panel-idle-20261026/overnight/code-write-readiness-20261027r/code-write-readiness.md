# Selector-1 code-write diagnostic readiness

Recorded 2026-10-27 UTC. This is a finite offline analysis of retained local
bytes. It performed no TV, network, USB, device-node, target-memory, reset,
process-control, UI, or write operation. It built no target helper.

## Decision

**A code checkpoint/write is not qualified.** The earliest missing proof is a
positive classification of the selector-1 mapped code view as mutable backing,
or an explicit permission/configuration edge showing that writes to the view
are accepted. Nothing in the bounded reset, first reset callee, scatter, or
ordinary launch path supplies that edge.

The retained read result is useful but narrower: exact target-`0x101` reads at
`0x46001e60`, `0x460038c0`, and `0x4601bb60` matched three nonadjacent ranges
of selected/current stored image 1. That proves the returned mapped-view bytes
at acquisition. A readable mapped view is not thereby writable, backed by RAM,
or executable from RAM. The reads were sequential, not atomic, and their
retained result explicitly leaves both current execution and whole-image
identity unproved.

## Exact bounded startup evidence

Selected package SHA-256 is
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`;
recovered current storage SHA-256 is
`f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562`.
Their complete stored image-1 slot, FILE `0x40000..0x7ffff`, is byte-identical,
SHA-256
`56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf`.

The vector at FILE `0x40200` contains initial SP `0x20020000` and Thumb reset
word `0x369`. In the reset body at linked VA `0x368`, two literal loads resolve
to `0xdc01` and `0x141`: a call through the first word and a branch to the
scatter dispatcher through the second. This is a coherent linked startup path;
it does not identify the backing type of the external `0x4600....` view.

The first reset callee is pinned at linked VA `0xdc00..0xdc13`, SHA-256
`720dd0735e0becce7d432e13f0eeb3f5f0d5b9aba240d5b0eaddca5ef557ed89`.
It reads, changes, and writes through one raw literal address,
`0xe000ed88`, then returns. No symbol evidence here establishes that this
callee is named `SystemInit`, so this report calls it only the *first reset
callee*. The raw register is also deliberately left unnamed: assigning its
semantics is unnecessary, and this lone operation gives no positive backing,
write-permission, or RAM-execution edge for `0x46000000..0x4601ffff`.

The scatter dispatcher at linked VA `0x140..0x1f3` has SHA-256
`cf4020e3cdb1b314345608c30d00c1efa1e0ad4cf87bf8e54aa92f568fcb6330`.
Its exact nine records are:

| source linked VA | destination | output length | handler |
| ---: | ---: | ---: | ---: |
| `0x1d860` | `0x20000000` | `0x4f8` | `0x17c` |
| `0x1d95c` | `0x20015000` | `0xb50` | `0x17c` |
| `0x1d974` | `0x20015f10` | `0xb50` | `0x17c` |
| `0x1d98c` | `0x2020a000` | `0x2d30` | `0x17c` |
| `0x1d9e8` | `0x20253000` | `0x223c` | `0x17c` |
| `0x1da30` | `0x20209000` | `0x6c0` | `0x17c` |
| `0x1da40` | `0x20209800` | `0x6c0` | `0x17c` |
| `0x1da50` | `0x20269000` | `0x4890` | `0x17c` |
| `0x1d95c` | `0x200004f8` | `0xdca4` | `0x1d8` (zero-fill) |

Every destination is a data/RAM range. No record targets linked code VA
`0..0x3ffff`, the selector-0 mapped code view
`0x44000000..0x4403ffff`, or the selector-1 mapped code view
`0x46000000..0x4601ffff`. Thus ordinary scatter initializes data state; it
does not show code copied into writable backing.

The ordinary application-launch slice at VA `0x2ac`, context slice at VA
`0x1ba0c`, and selector mapper at VA `0x1bb74` are also byte-pinned by the
verifier. The mapper positively explains the selector-1 address translation
for linked VAs below `0x20000`. It does not declare the mapped region's memory
type, write behavior, or execution permission.

## Qualification matrix

| Question | Result | Evidence boundary |
| --- | --- | --- |
| Does target `0x101` return readable bytes for three selector-1 mapped windows? | yes | retained exact reads and hashes |
| Do those bytes match selected/current stored image 1 at those windows? | yes | three nonadjacent exact comparisons |
| Does ordinary scatter copy/decompress code into the selector-1 mapped view? | no positive row | all nine destinations are listed above |
| Is the view positively classified as mutable RAM/code RAM? | **unproved** | no backing declaration in the bounded startup path |
| Is write acceptance or a write protocol for this view proved? | **unproved** | read target `0x101` gives no such edge |
| Is RAM execution permission for the view proved? | **unproved** | no permission configuration is established here |
| Is a core PC proved to execute from this view? | **unproved** | matching code bytes are not a PC observation |
| Is rollback/recovery proved? | **unproved and not investigated** | prerequisite write/backing proof is absent |

The “no positive row” finding is bounded to the exact ordinary startup
mechanisms above. It is not a whole-SoC claim: boot-ROM behavior, computed or
indirect register setup, undocumented hardware mapping, and later-loaded code
remain outside the retained positive evidence.

## Why work stops here

A diagnostic write would cross a security and recoverability boundary before
the first prerequisite is met. In particular:

- successful reads do not qualify target `0x102` writes;
- matching mapped bytes do not prove mutable backing or current execution;
- the known `0x4500....`/`0x4700....` data aliases do not classify a
  `0x4600....` code mapping; and
- without positive backing/write semantics, a write-and-restore experiment
  has no proven restore path.

Therefore this task does not propose a write address, payload, probe, patch,
permission change, or helper. It also does not inspect flash/storage banks,
bootloader behavior, persistence, POFLG, protection, return guards, or other
excluded branches.

## Reproduction

The standard-library verifier uses explicit exceptions rather than Python
`assert`. Run it normally and with assertions disabled:

```sh
python3 verify-code-write-readiness.py
python3 -O verify-code-write-readiness.py
```

It pins both whole retained files, their complete image-1 slot equality, the
frozen N manifest and result, all three captured windows, exact vector/reset
bytes, the first reset callee and raw address, scatter dispatcher/table and
all nine rows, ordinary launch/context slices, and the selector mapper. Its
compact JSON ends with `status=qualification_gap`,
`write_probe_qualified=false`, and `target_operations=0`.

No external documentation was needed because this report does not assign a
name or permission meaning to the raw system address.
