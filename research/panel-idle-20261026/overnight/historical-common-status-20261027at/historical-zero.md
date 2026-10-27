# Historical raw common-status zero

## Answer

Yes, with explicit conditions: the retained E read supplies the missing
**raw-controller temporal premise** that the earlier stock-status-zero claim
did not have.  It proves that a successful target-`0x101` read returned zero
at bus window `0x4500f0c0 + 0x30` during Linux uptime
`106924.06..106924.58`.

Associating that bus halfword with common status CPU `0x2000f0f0` is
conditional on the qualified `+0x25000000` mapping branch being the live
mapping at that time.  Extending the zero as a lower temporal bound for the
later `0x10` additionally requires the same controller instance, without an
intervening controller restart or image/mapping replacement.  The records
establish the same **Linux** boot, not uninterrupted controller lifetime.

Those conditions establish only the raw-zero lower premise.  **If a later
`0x10` is additionally proved to reflect that same controller field**, it
cannot be unchanged stale contents from before the E zero: some later write,
copy, or reinitialization is required.  The retained host query does not by
itself supply that extra proof because it records
`controller_transaction_proved=false`.  The corpus therefore has no verified
raw-zero-to-raw-`0x10` transition.  It also does not identify when within the
roughly 2.5-hour gap a change occurred, prove it occurred during V6, or
identify one writer or cause.

## Exact retained transaction

The retained directory is
`executing-image-identity-20261027e/common-error-guard-read-once`:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `record.json` | 170,623 | `cf9f5fab4186562e1c953e9cdf888b06ff324d4d0ca6545cdb5b8fb3d0def26d` |
| `returned-block.bin` | 64 | `309cd7686044d75384b26fd389eef73add04f6a4651339151a0535fce3c4d3aa` |
| `stdout.txt` | 884 | `33f19e6df97bdab9ae29712786bc0d14f67bd8484092e90f7a48e4868ad329d0` |

The saved record has exactly 16 root calls.  Every call has transport exit 0,
no host timeout, an authenticated response with UID/EUID 0, exactly one
command with exit 0/no timeout/empty stderr, and a base64 transport envelope
that decodes exactly to the stored response.  The one active call is bracketed
by host UTC `2026-10-27T07:15:11.671040Z..07:15:12.342009Z`.

The build manifest has SHA-256
`db25f3b8dccd5d95705a097a987784a7fc902d7d18a78a348794de91a0840aa4`
and fixes this header:

```text
target   0x101
address  0x4500f0c0
length   64
header   01010000c0f0004540000000
```

The verifier reconstructs all three staged runtime files from the
authenticated upload commands and compares them byte-for-byte with the
manifest-pinned local build.  Relevant source pins are:

- `Program.cs`:
  `868a94de9e721f5de7607a98ccdc2ca67887260ad8b81a1fd4ff87182a44d101`
- `run-once.py`:
  `f5e1b1789f73e49babd0d571d9ba5e02b204c3ecdb5201445cd38582c9e256f8`
- staged DLL:
  `c88ffb51ece2c743459014164ac12f94c092cf13f2da5138c92d262e2e3ab269`

The native helper passed 26 self-tests with zero target operations, then made
one native invocation.  Its exact steps were:

```text
open 25; claim 0; OUT 12; IN 64; release 0; close 0
```

It reported `Stage=complete`, `Accepted=true`, exact counts, release and
close success, and `HELPER_EXIT=0`.  `DataBase64` decodes exactly to
`returned-block.bin`; `DataSha256` matches it.  Cleanup returned exactly
`STAGE_ABSENT`.  Thus offset `0x30` being `00 00` is returned controller-window
data, not a failed-read placeholder, a missing-output default, or wrapper
interpretation.

## Conditional address association

The selected package is pinned at SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Its fixed common-object accessor at image-0 VA `0xe670` returns CPU
`0x2000f0e0`; the ordinary selector-8 accessor at `0x21e66` loads the
halfword at `+0x10`, CPU `0x2000f0f0`.

The reviewed AJ selected-image-1 mapper body `[0x1bb74,0x1bbc4)` has SHA-256
`94da5bec3c7fd05448a66d3828ec420e5cb08e03cb4474a54d07570732d1fe5c`.
For selector zero and CPU addresses in `[0x20000000,0x20020000)`, it adds
`0x25000000`.  Therefore:

```text
map(0, 0x2000f0c0) = 0x4500f0c0
map(0, 0x2000f0f0) = 0x4500f0f0
0x4500f0f0 - 0x4500f0c0 = 0x30
```

AJ's final report/verifier pins are respectively
`f9c341e50eaee8fdcddf2a6e13ccd7d21f79a12d311e988c44c26098dab756cc`
and
`48b381845284d754cf46b01d01b964be41d1ad9f8b7175cc21c06520e057ad34`.

E's acquired current-image mapper independently contains the same
`+0x25000000` branch for core tag `0xa` and `+0x27000000` otherwise.  Its
body/literals `[0x9a48,0x9a78)` have SHA-256
`f2180e3657acd60cdbfc3b30c28d01a782d60bfe8ff89803cc0bf0cefeba7d85`.
The historical transaction did not sample that live core-tag register, nor
does it prove every executing instruction.  Consequently the report retains
the raw fact as “bus `0x4500f0f0` was zero” and treats the CPU-field identity
as conditional rather than silently assuming it.

## Temporal comparison and its limits

All retained records use Linux boot ID
`00000000-0000-4000-8000-000000000000`:

| Evidence | Linux uptime | What it directly says |
|---|---:|---|
| E raw read | `106924.06..106924.58` | bus `0x4500f0f0` halfword was zero, conditionally the common status field |
| V6 finite logger | `115887.39..115907.45` | RT fault changed `0` to `0x1001`; no physical panel observation |
| later stock host query | `116071.70` | kernel output changed from sentinel to `0x00000010` |

The minimum separation from the end of E to the beginning of V6 is
`8962.81` seconds (about 2.49 hours).  V6's accepted result and native outcome
are pinned at SHA-256
`3c653c425050c327f984a044c610abea8b0fdef44ff970dfb16dfbe06f3923c9`
and
`1dad737eac2e3f9d9ca08b13e6e57484f84e3af9aafa81c856f9a39b1d6752d9`.

The later host-query record is pinned at
`5f8662e4cfed25563b59a303bd94190d2463e5c584dd117de15b219fd2e0e6e0`.
It records `CLASSIFICATION=kernel_output_written`, but it also explicitly
records `controller_transaction_proved=false`.  It must not be described as a
second raw controller-window sample or conflated with E.

There is no event-aligned common-status read.  Same Linux boot does not rule
out an MCU/controller restart during the gap.  Neither the E raw bytes nor
the later software samples observe emitted light, panel visibility, audio,
or owner-visible state.  They do not prove that V6 uniquely caused the later
status, that the recurring RT poll was the writer, or that no initialization,
copy, zero-selector call, or unmodelled writer intervened.

## Reproduction

Run both modes; output must be byte-identical:

```sh
python3 verify-historical-zero.py
python3 -O verify-historical-zero.py
```

The standard-library-only verifier pins the raw record, build/native bytes,
authenticated envelopes, exact native transaction and cleanup, package and
mapper bodies, V6 bracket, and later host-query limitation.  It performs zero
target operations and does not print retained command bodies or upload data.
