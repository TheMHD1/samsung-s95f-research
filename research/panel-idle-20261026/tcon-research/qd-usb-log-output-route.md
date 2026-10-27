# QD image-0 diagnostic-output routes: USB CDC versus UART

Recorded 2026-10-27 UTC. This is bounded offline analysis of retained bytes
and retained read-only USB metadata. It made no TV, root, network, USB open,
USB control transfer, endpoint read/write, driver bind, UART, controller, or
firmware call.

## Result

The selected image contains a complete static route from its custom formatter
at `0x2b334` to the CDC data-IN endpoint numbered **`0x81`**:

```text
0x2b334 format -> 0x2b36e byte loop -> 0x2b2a0 enqueue
  -> USBSerial state output ring at 0x2026142c+0x28
  -> 0x29b50/0x29cfc transmit service
  -> endpoint state+0x0c = 0x81, at most 0x40 bytes per submission
```

That route still does not establish a reliable no-DTR, no-write acquisition
path, but the reason is more precise than a blanket DTR gate. When the
transmit service is idle and bytes are queued, `0x29b50` can submit its first
chunk **without testing** the CDC control-line bit at state `+0x4a`. That bit
does control the already-active/cancel/timeout path, and an IN completion calls
the same transition helper with value one. The proved host setter is CDC
`SET_CONTROL_LINE_STATE` (`bRequest=0x22`), whose bit zero drives that state.
A zero-to-one transition clears the output ring's read/write and in-flight
bookkeeping, discarding queued text. Therefore static code neither requires a
host DTR write for the first idle submission nor promises stable backlog
delivery when the state changes. Sending the request would be a USB control
transfer and local state change, even though it is not a vendor command or
bulk-OUT payload.

More importantly for the RT fault, the recovered common error path does **not**
use this USB ring. `0xb860` formats its error text through `0x39594` into a
separate `0xc00`-byte RAM circular log at `0x20205000`; `0x39604` drains that
log to MMIO base `0x40150000` through the UART-like byte writer `0x3acf6`.
The direct calls to USB formatter `0x2b334` cover `RDY\n` and USB/TCDATA
diagnostics, not the common RT error strings. Thus endpoint `0x81` is not a
source-backed way to recover the already-recorded RT error detail.

The existing cached USB descriptors are an exact identity candidate for the
packaged USB personality, but current execution and host binding remain
unproved. At the retained sample, all three `7-1` interface driver links were
absent. A receive-only attempt with no DTR/control request has neither a proved
active producer nor a proved preserved backlog.

## Inputs and address convention

| retained input | size | SHA-256 |
| --- | ---: | --- |
| `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` | 5,242,880 | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| `overnight/qd-usb-interface-metadata-20261027a/client.stdout` | 3,162 | `065113d8f9d133570a72a4c086e2fdbff26567c9f8c082612f794f7414430530` |
| `qd-usb-console-binding.md` | 6,043 | `e08fe2db2d98df6e4b36bc25f43847f68c703da29e8092e579612b5183e49404` |
| `qd-usb-cdc-control-requests.md` | 5,005 | `909a30915e2bf7ffa6ec5aeac02a1b65efc8fde636f0db333ef99e16a9d4a99b` |
| `ssb-transport-driver-binding.md` | 10,997 | `c35361bce02aae2946b5b0f4e22cab80af20c348c63a4cafd9267f3cfb05bbe7` |

Image-0 addresses below are Thumb linked addresses equal to stored offsets in
the first `0x40000` bytes. The selected file-to-runtime profile match is strong
and separately documented, but it does not prove that every packaged image-0
byte equals the firmware currently executing in the controller.

## Exact USBSerial instance and output ring

Initializer `0x22324..0x2238f` operates on the fixed state object
`0x2026142c` and writes:

| state field | initialized value | use recovered below |
| ---: | ---: | --- |
| `+0x0c` | `0x81` | bulk data IN endpoint |
| `+0x0d` | `0x01` | bulk data OUT endpoint |
| `+0x0e` | `0x83` | interrupt IN endpoint |
| `+0x14` / `+0x18` | allocated pointer / `0x101` | receive-side storage/capacity |
| `+0x28` / `+0x2c` | allocated pointer / `0x7f` | formatter output ring/capacity |
| `+0x5c` | Thumb pointer `0x2b071` | shared class-request callback |
| `+0x60` | `0x22394` | exact string `USBSerial` |

It passes this exact state pointer to `0x286b4`; that routine stores it in the
registration node at `+0x18`. The CDC class and transfer routines below load
their state back from that node field. This closes the state-instance edge
left open by the earlier descriptor-only and control-request reports.

`0x2b334..0x2b361` formats into a `0x100`-byte bounded stack destination and
calls `0x2b36e`. The latter walks the resulting NUL-terminated bytes and calls
`0x2b362`, which calls `0x2b2a0` for each byte. `0x2b2a0` writes into
`[0x2026142c+0x28]`, advances index `+0x30` modulo capacity `+0x2c`, and uses
index `+0x34` as the consumer boundary. The ordinary one-slot-empty ring
calculation in `0x2b23c` makes the `0x7f`-byte allocation capable of retaining
at most `0x7e` queued bytes at once.

When full, `0x2b2a0` invokes `0x2b2f8`. That helper refuses to wait when
`PRIMASK` is set, and otherwise distinguishes exception/thread conditions
before its scheduling helper. The enqueue returns `-1` if it cannot obtain
space and `1` after a write; `0x2b362` discards that return. Therefore this is
not a lossless log: depending on context and service progress, output can wait
or be dropped. Static code does not supply a timestamp, record boundary, or
sequence number for this ring.

## DTR/session state, endpoint submission, and lifetime

The CDC request dispatcher and request-number meanings are independently
bounded in `qd-usb-cdc-control-requests.md`. The exact instance binding above
adds these consequences:

1. `0x29a58` handles `bRequest=0x22`. It stores the low `wValue` byte at state
   `+0x58`, masks bit zero, and calls `0x29734`.
2. `0x29734` compares the new bit with state `+0x4a`. On a rising transition it
   zeros `+0x30`, `+0x34`, `+0x38`, `+0x3c`, and byte `+0x49`, calls
   `0x29bf2`, then stores the new bit at `+0x4a`. The cleared `+0x30/+0x34`
   are the producer/consumer indexes used by the formatter ring. Pre-DTR text
   is consequently discarded.
3. Transmit service `0x29b50` uses the `+0x28/+0x2c/+0x30/+0x34` ring. Its
   idle branch does not test `+0x4a`: when bytes are available, it sets the
   active byte `+0x49`, clamps the chunk to `0x40`, records it at `+0x3c`, and
   calls the endpoint submit helper with endpoint byte `+0x0c`, i.e. `0x81`.
   Only the already-active branch reads `+0x4a`; zero there cancels/zeros the
   IN state and clears ring bookkeeping, while nonzero enters timeout logic.
4. Completion routine `0x2976a` accepts the configured IN endpoint and first
   invokes `0x29734(...,1)`. If that is not a state transition, it advances the
   consumer index by the completed `+0x3c` count modulo `+0x2c` and can submit
   another chunk. If it is a zero-to-one transition, the helper has already
   cleared those fields. `0x29cfc` primes the companion receive side and is not
   evidence that host OUT data is needed for each IN chunk.

The exact `0x40` submission bound agrees with the cached endpoint-`0x81`
maximum packet size of 64 bytes. Static agreement does not prove that the
packaged image is running or that a host interface is currently bound.

The shared callback is no longer wholly unresolved for this instance:
initializer `0x22358` stores `0x2b071`, so the common tail of class requests
invokes code at `0x2b070`. That code reads a pointer from the registration
object at `+0x0c` and rewrites bits 0..1 of its register at `+0x800` from the
request code. The controller-register semantics were not recovered. This is
another reason not to label line-coding or DTR setup as a passive read.

The output allocation is retained by the fixed global state. No deallocation
was recovered in this bounded init/service trace, but that is not proof of
process-lifetime retention. Transfer-service scheduling/installation and its
time base were not fully recovered. A busy transfer has local timeout logic,
but its units and host-visible behavior are not assigned here.

## The RT/common-error print is a distinct UART route

The EEPROM RT-protection checker enters the common error routine at `0xb860`
with selector `0x10` and an error-source string. The common routine calls
`0x39594` with `System Emergence!!` and `Entry -> %s err_src[%s]` formatting
sites after applying the error selector. This is the relevant error-print
path; it does not call `0x2b334`.

`0x39594..0x395eb` formats into local storage, then for every output byte:

* reduces a monotonic counter at RAM `0x20000e5c` modulo `0xc00`;
* writes the byte at `0x20205000 + index`; and
* increments that counter.

`0x39604..0x396a1` is the recovered drain. It consumes this ring (and a second
buffer rooted at `0x20200000`) and calls `0x3acf6` with fixed MMIO base
`0x40150000`. `0x3acf6` checks status at base `+0x24`, writes bytes to
base `+0x2c`, and emits carriage return before line feed. These accesses are
UART-shaped MMIO behavior, not USB endpoint or SSB bulk submission. The
selected common-error CFG can call the drain in its continuing fallback loop;
there are also other direct calls to the drain elsewhere in image 0. This
proves a firmware-local UART output route, not that the UART is externally
wired, enabled, or recoverable from the host.

The direct-call census for `0x2b334` found four syntactic `BL` sites:
`0x2170c`, `0x2a572`, `0x2a5c2`, and `0x2a5d2`. The first formats the exact
literal `RDY\n` under additional live-RT/readiness gates; the latter sites are
USB statistics and `TCDATA` displays. This census does not exclude an indirect
call, but it supplies no direct RT common-error-to-USB edge. A coincident
`RDY\n` is not an error-history record and must not be treated as proof of the
RT cause, recovery, or physical panel state.

## CDC, UART, and vendor bulk must remain separate

The retained descriptor sample recorded:

| interface | class | endpoints | bounded interpretation |
| ---: | --- | --- | --- |
| `7-1:1.0` | CDC control `02/02/01` | interrupt IN `0x83` | class requests including line state |
| `7-1:1.1` | CDC data `0a/00/00` | bulk OUT `0x01`, bulk IN `0x81` | statically matches the formatter-ring route |
| `7-1:1.2` | vendor `ff/00/00` | bulk IN `0x82`, bulk OUT `0x02` | separate SSB/update transport candidate |

The Linux-side SSB implementation and its runtime-PM/open/write risks are
documented separately. Its `0x82/0x02` vendor interface is not the
`0x81/0x01` USBSerial data interface and is not evidence of a diagnostic log
stream. Conversely, the common-error RAM/UART ring does not become CDC data
merely because the same composite USB identity is present.

At boot ID `00000000-0000-4000-8000-000000000000`, uptime
`83382.46..83382.52`, metadata showed exact device `04e8:2001`, manufacturer
`Samsung`, product `STL1 CDC and Bulk`, but every child-interface driver link
was absent. `/dev/ttyUSB0` existed without a retained parent mapping; it must
not be assigned to this USB device.

## Acquisition-readiness conclusion

No technically grounded no-DTR/no-write log acquisition follows:

* the idle service can submit one chunk without checking DTR, but the static
  evidence does not prove that service is scheduled in the current runtime or
  promise continuation/backlog behavior across completion;
* explicitly establishing DTR would be a USB control write and invokes a
  resolved register callback in addition to changing local transfer state;
* a zero-to-one edge deliberately drops queued formatter bytes;
* the RT/common-error strings use the separate UART ring rather than the
  endpoint-`0x81` ring;
* the retained host sample had no bound interface driver; and
* packaged-image execution, current DTR, transfer-service scheduling, UART
  wiring, and retention of any old bytes are unproved.

The local idle service can emit newly produced `0x2b334` bytes on IN endpoint
`0x81` without first checking DTR and without a per-packet vendor command or
CDC bulk-OUT payload. That narrow static fact is not a current-runtime or
backlog-delivery proof and does not expose the RT error ring.
The smallest remaining technical evidence for a future USB-console study
would be an independently safe current interface-binding/session observation
and a non-fault test message produced after the session is established; it
would still not recover earlier RT detail. No such action was attempted here.

## Selected exact function hashes

Hashes are over half-open stored-byte intervals in the selected asset.

| function/interval | bytes | SHA-256 |
| --- | ---: | --- |
| USBSerial init `0x22324..0x22390` | 108 | `ac0cbbee3f3088afe88c4541c0136a60778cfcfa4d8461c4720247ecb117a8b6` |
| ring free count `0x2b23c..0x2b26c` | 48 | `5107005ebb46afd38c687d72601013e75f6a7dd4f4492769408736a7e08a1d28` |
| ring enqueue `0x2b2a0..0x2b2f4` | 84 | `84f27ce53fe9532c7d073e3380d0409c2485f806ddd7e78d3e44be3c42350f12` |
| formatter `0x2b334..0x2b362` | 46 | `b6ac186cc334dafe57a71260a354b0453ba00fda54a7d74009481c5538324700` |
| byte loop `0x2b362..0x2b384` | 34 | `944e2afe7573a333dabb50179dbb11499e71c6f65bfb4e95492092d5ad9875cd` |
| DTR transition `0x29734..0x2976a` | 54 | `5cd48ca0bee9bf9a4c72e3fbdfd31d274a3cd7a9f79044e99d26809a2f7fc273` |
| IN completion `0x2976a..0x2980a` | 160 | `9a3b45734c0e9c6e6d95526ccd552d4f929e1e62dd19b8eeecbb7fd4829ae2b4` |
| transmit service `0x29b50..0x29bf2` | 162 | `c821d5ac3508aa89059a6618d4ef12709de8bc09bfe3de7d79e356b37abe7fc5` |
| companion prime `0x29cfc..0x29da2` | 166 | `95f2b8b66c1a603d4d7b0d7868e5c387f0788086efc88be823b516408c725959` |
| error-ring formatter `0x39594..0x395ec` | 88 | `a239deae60e46c486aaf5b99d7e4943b4614f0ce26b9f43cab36a21ad0415a3f` |
| UART drain `0x39604..0x396a2` | 158 | `417e7c69a8422b140e7e59f680fdbb3b89e685de7716a9b2e7b38defd0ad2752` |
| UART byte writer `0x3acf6..0x3ad32` | 60 | `46e32bfc5419150349edad08242d08dff7b41765d83d379b04a5e58a1365ad87` |
| common error `0xb860..0xb8fa` | 154 | `40e434612828833aa7b433798a352a99c766cbb47351d2cb42ba364a868d2c6a` |

## Limits

This is a static packaged-image route, not a live transport capture. It does
not prove current firmware equality, current USB configuration, host binding,
DTR state, scheduling frequency, successful transfers, UART accessibility, or
the presence/absence of any particular log text at the incident. It provides
no panel-light, Apps, audio, recovery, cause, or repair conclusion.
