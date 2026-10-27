# Independent H/K offline review

Reviewed read-only on 2026-10-27. No TV, root-agent, network, USB, I2C,
controller, UI, process, storage, firmware, or device operation was made. No
protected/high-bank, persistence, POFLG, return-guard, bypass, flashing, or
write path was explored.

Pinned inputs:

- `executing-code-diagnostic-route.md`:
  `d70b624599ef4aff3cfbe5759ce9ea257aa912f37d48a20b24eef35abc98c3ba`
- `executing-code-diagnostic-route.py`:
  `221c45c2229833671f98119d3c84feeded175c99b1d07dc69226c94ec78813aa`
- `../rtp-baseline-live-comparison-20261027k/README.md`:
  `8760f05d54ed4eabafa6806a1cdff11cc7190b5efcb7cebde8356e88f8d57e26`
- `../rtp-baseline-live-comparison-20261027k/compare-ap-exco.py`:
  `46088052536db446c9091f735bcc5638f0babb96b6be13b80e73cb16007a9bda`
- `../rtp-baseline-live-comparison-20261027k/comparison.json`:
  `ba5b8e159ba002001d82a8a47672d64e41b7f8fac3602c9046480b2aabdb416c`

## Findings

No P0/P1/P2/P3 finding was identified in this bounded scope.

## H: existing-route census

Normal and optimized runs emitted identical JSON with
`status=diagnostic_route_gap`, no candidate request, and zero target
operations. Critical instruction and call-path checks support the report's
limited conclusion:

- The console version leaf at linked VA `0x20430` writes bytes `03 03 04`
  to its local stack and returns numeric `0x040303`; it reads no executable
  memory and is a constant subsystem version, not active-image identity.
- The two HardFault vectors lead to exception-only register formatters and
  their handlers terminate in local infinite loops. A naturally captured PC
  could be evidence, but this is not an ordinary read diagnostic and the
  report proposes no fault trigger.
- Generic CRC helper `0x2e6c4` is directly used by the Mks header/payload
  validator for caller-supplied buffer regions. The separate configuration
  formatter is called at `0x176dc` after the loader requests `0x400` bytes
  from fixed source `0x04d00000`. Neither path selects or fingerprints
  executing image-1 text.
- The CDC result is correctly phrased as a bounded negative **direct-edge**
  census, not proof against indirect or unavailable mechanisms. Target
  `0x101` remains useful caller-addressed memory only after a source-qualified
  bus address; target `0x203` returns storage bytes. Neither is silently
  promoted into an address-free active-code identity route.

Accordingly, the supported result is only that no address-free running-code
fingerprint was recovered in the finite copied surfaces. It is not a global
claim about boot ROM, undocumented hardware, other builds, or factory tools.

## K: AP_EXCO baseline comparison

Normal and optimized comparison runs exactly reproduced `comparison.json`.
The retained selected package and recovered backup independently match over:

- AP_EXCO directory FILE `0x85e00..0x85fff`, SHA-256
  `dad4caf149769f0b363a11231267d73752802a3bd7484bd720562bbaa7be1cd8`;
- first payload FILE `0x182200`, `0x33a` bytes, SHA-256
  `c50e438b4882c04e62542fa718cda662b56c3ea0930e20d54944a949e2e3afbf`;
- second payload FILE `0x182600`, `0x1200` bytes, SHA-256
  `5000ce2a135b4b463505a32cf5b525916605b32c21a20de4bd91607d4b839761`.

The source arithmetic is correct. The mapped object's first region has
length `0x33a`, so object `+0x3d8` lies `0x9e` bytes into the second region:

```text
0x182600 + (0x3d8 - 0x33a) = 0x18269e
```

Selected and backup bytes are therefore `20` at object `+0x3d8` and `0` at
object `+0`. Independent instruction review of callback VA `0x3934` confirms
that it copies AP_EXCO `+0x3d8` to fixed context `+0x6c7` and AP_EXCO `+0`
to `+0x6c8`. The retained candidate bus bytes at those offsets are `1,3`.

That mismatch rules out the two copied AP_EXCO payloads as a direct bytewise
explanation for the saved `1,3` pair. It does **not** identify a runtime
writer, prove that either stored artifact was active, prove the candidate
bus/CPU alias universally, sample the live AP_EXCO object, or establish
event-time state. H likewise does not convert matching stored profile bytes,
versions, or CRCs into proof of code currently being executed.
