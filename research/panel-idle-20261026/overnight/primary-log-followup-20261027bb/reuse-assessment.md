# Reuse assessment for one unchanged primary event-log read

Recorded 2026-10-27 UTC. This is a bounded, read-only assessment of existing
helper source, manifests, and retained records. It made no TV, root, network,
USB, controller, UI, power, reset, firmware, or filesystem-staging operation
and did not build or modify a helper.

## Decision

**Conditionally eligible for exactly one positive-only attempt, using the
unchanged helper, after the pending fresh host metadata passes.** The source
review itself does not authorize dispatch before that metadata exists. The
required immediate preflight is:

1. the same boot ID `00000000-0000-4000-8000-000000000000`;
2. USB path `7-1` still identifies the same active, authorized, configured
   `04e8:2001`, revision `0250`, device 46 instance;
3. all three interfaces remain unbound and the current usbfs node has zero
   file-descriptor holders;
4. the last vendor lineage remains the accepted late W transaction at uptime
   `137706.50`, which ended with exact transfers, release/close, and
   `ReadyForHeader`; and
5. no vendor OUT, power lifecycle, USB re-enumeration, boot change, ambiguous
   transfer, or other controller helper has intervened.

If any item is false, missing, stale, or ambiguous, do not execute. Host
metadata alone does not prove parser phase; eligibility comes from combining
it with the closed vendor-transaction lineage. The one attempt must not be
retried after any outcome.

There is one operational qualification: the old `run-once.py` wrapper is not
self-certifying. Its shell captures a nonzero native exit in `rc`, then exits
zero after printing `HELPER_EXIT`, and the Python wrapper does not parse the
native JSON. Therefore neither wrapper completion nor its final printed JSON
is acceptance. Acceptance requires a separate strict parse of retained raw
stdout showing the exact native success described below. This gap does not
increase controller traffic—the native path still has one header and one
matching input and no retry—but it makes an external post-run parser and a
hard no-retry rule mandatory.

This decision seeks only positive evidence. A retained occurrence of newly
mapped `Failmode`, `F-Set`, or `F-Clr` text may be compared with the already
qualified source strings. Absence is not evidence of non-execution because
the buffer can wrap, the snapshot is not event-aligned, and the reader does
not atomically capture the separate index.

## Exact unchanged artifacts

The existing helper directory is
`overnight/managed-usb-main-event-log-read-once/`. Its current files still
match the historical reviewed run:

| artifact | SHA-256 |
| --- | --- |
| `build-manifest.json` | `ac4133ccb6e2b12576006a981f1d585ad0fe1384a2a6d1a5096f3a81bced5371` |
| `run-once.py` | `245323c709dc098d343a1ee470c505ba909249126d4fe5645b12b20709ff7031` |
| `Program.cs` | `6bb6d6313beeea6ef464ce09e3d4c3a98e39d3d53ed78f53d19ccd7074e02c4f` |
| managed DLL | `1b239c2e2790bc402c85bd4d647ca9410288edc816960f8fa75b9e6815d6bfc4` |
| pinned root runner | `7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a` |
| root-access client pinned by that runner | `3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5` |

The build manifest fixes all request geometry:

```text
target         0x101
address        0x20205000
length         3072 (0x0c00; six 512-byte packets when full)
header         0101000000502020000c0000
OUT transfers  1
IN transfers   1
retries        0
```

No caller option can change target, address, length, endpoints, or interface.
The native helper has no write-payload, reset, control-transfer, alternate
address, or retry path. The README's old statement that it had not been
deployed is superseded by the retained accepted execution described next; it
is not used as runtime evidence.

## Historical execution proof

The old accepted execution is retained under
`executing-image-identity-20261027e/main-event-log-read-once/`:

| artifact | SHA-256 |
| --- | --- |
| `record.json` | `d2f0796fb5dd131cd8ea97aadaf37f63c9a36f7177a3d7deddda93695e1a161f` |
| `returned-block.bin` | `6d82903d4abeb366af859c8966345514a50315a14a891ee1370f69fe173b912a` |
| `stdout.txt` | `6e3924aae81c6d4359669045a8cb58c56e1e6d780c9a59ec07936741376c1491` |

Its record contains 16 authenticated root calls. Every call had host transport
exit zero, no host or target timeout, one echoed target command, target exit
zero, and empty target stderr. The native run at target uptime
`107245.86..107246.37` reported exactly:

```text
open 25; claim 0
OUT 12; IN 3072
release 0; close 0
Stage=complete; Accepted=true; HELPER_EXIT=0
```

The decoded `DataBase64` is exactly the saved 3072-byte block and has the
saved hash. The wrapper's final filesystem-only cleanup returned
`STAGE_ABSENT`. This proves the exact helper and transport succeeded once on
this TV; it does not prove current contents, current phase, logger freshness,
or running-image identity.

The runtime also emitted known `[GC_INFO]` lines around the JSON. A new strict
parser must allow only the previously classified GC line grammar, require
exactly one self-test JSON and one native outcome JSON after
`ACTIVE_READ_BEGIN`, require one `HELPER_EXIT=0`, and reject unknown or
duplicate lines. It must not assume stdout is a single JSON line.

## Current first-header premise

The most recent accepted vendor transaction in the supplied closed lineage is
the late W snapshot under
`stock-rt-state-delta-20261027aw/post-lifecycle-inputs/`. Its retained record
SHA-256 is
`f4722be28e23b953c1befbd60482f592741b90b231bc43dd415f66ae04946cd9`,
and its result SHA-256 is
`778cb7e9ab4f3950c6a466f799e41b13115e0b9e4cef8f8ac412466041d90e57`.
It performed three exact fixed reads—six bulk transfers—and ended at uptime
`137706.50` with native exit zero, `ProtocolPhase=ReadyForHeader`, release and
close successful, and `STAGE_ABSENT` cleanup.

Its immediate host preflight had positively observed the same boot, USB
device 46, revision `0250`, configuration 1, all interfaces unbound, and zero
usbfs holders. That preflight is historical, not sufficient for a new run.
The pending fresh metadata must repeat the relevant facts immediately before
staging.

Under the reviewed vendor protocol, an exact completed fixed read returns the
host model to the header boundary. The firmware source additionally shows
that the completion path rearms a 12-byte OUT header receive, though the rearm
submission return is not checked. The accepted W terminal plus no-intervening-
vendor-OUT lineage is therefore the phase premise for the new first header;
USB descriptors alone are not.

## Native failure and phase behavior

The native state machine is fail-closed with respect to additional vendor
traffic:

- a preflight, open, FD-validation, identity-recheck, or claim failure sends
  no header;
- an OUT result other than exactly 12 prevents the IN request;
- after an exact 12-byte OUT, exactly one 3072-byte IN is attempted;
- a short, overlong, error, timeout, or exception sends no later header; and
- release and close are attempted when applicable, but neither is treated as
  parser recovery.

Only this exact terminal combination is acceptable:

```text
Stage == complete
Opened == Claimed == Released == Closed == Accepted == true
OutCount == 12
InCount == 3072
steps == open, claim, out, in, release, close
all six step values exact and errors zero/null
DataBase64 decodes to exactly 3072 bytes
DataSha256 equals SHA256(decoded bytes)
native exit == 0 and HELPER_EXIT == 0
```

Any failure after the first OUT begins makes the controller phase unknown for
future work. The wrapper preserves full stdout on an ordinary completed root
request; on host timeout it preserves partial transport stdout/stderr in
`record.json`. The native helper does **not** retain a trustworthy partial IN
prefix when the count is short, so such a run cannot answer the diagnostic
question. Preserve the record and any stdout, perform no second vendor
request, do not reinterpret release/close as recovery, and do not retry.

Release or close failure also rejects the run even after exact bulk counts.
It does not authorize another read. If staging or execution transport is
ambiguous, the only subsequent action allowed by the existing wrapper is its
single allowlisted filesystem cleanup attempt; that cleanup is not a vendor
transaction. Cleanup failure leaves evidence/stage residue for review and is
not a reason to rerun.

## Wrapper, timeout, and cleanup bounds

The final target command contains the 26-test injected-I/O self-test and one
native `--execute` invocation in the same synchronous shell. There is no loop
or retry around `--execute`. The native bulk timeout is 2 seconds per transfer,
so the two-transfer nominal bound is 4 seconds. The pinned root runner allows
25 seconds remotely and 55 seconds at the host, well above that nominal
native bound. A timeout is still ambiguous, not evidence that no bytes moved.

The wrapper stages only three pinned runtime files into a random private
`/tmp/researcher-usb-rtblock-<32 hex>` directory under `umask 077`. Its `finally`
block removes only those allowlisted files and the private directory, verifies
the stage is absent, and sends no controller request. The cleanup is older and
less richly guarded than current wrappers, but its target is a fresh
unguessable private directory and it does not add USB traffic. Any stage-
creation, upload, execution, or cleanup ambiguity must be retained; none may
be retried.

## Diagnostic interpretation boundary

A successful read is one sequential opaque 3072-byte snapshot of the fixed
candidate primary log buffer. A source-qualified ASCII occurrence can supply
positive compatibility evidence:

- `Failmode:<value>` records the bytes and formatted value present in the
  returned buffer;
- `F-Set` or `F-Clr` records the corresponding literal in the returned
  buffer; and
- relative byte order within this returned buffer can be reported, subject to
  circular-wrap ambiguity.

It does not by itself prove when the text was written, that it belongs to the
current fault, that the mapped function executed after MODE2, that the buffer
did not wrap, or that the physical panel changed. The separate existing index
reader is not atomic with this buffer and should not be added to this one-shot
attempt. Absence of any string is not a falsifier.

## Existing alternatives

No other already-built fixed helper found in the retained helper set reads
`0x20205000` for 3072 bytes. The existing
`managed-usb-main-log-index-read-once` reads a different fixed address and
cannot replace or atomically accompany this snapshot. Modern multi-window
observers do not include this primary log buffer. Consequently there is no
unchanged alternative that improves the exact diagnostic while preserving
the requested one-read scope.

## Final gate

This is a **one-attempt clearance conditional on fresh metadata**, not a
clearance to run immediately without it. If the pending preflight confirms
the five decision premises, root may invoke the exact pinned wrapper once
with its exact manifest hash and a fresh absolute retained-output directory.
Afterward, wrapper return alone is insufficient: strict native-output parsing
must either accept the exact terminal result or classify the run as rejected
or ambiguous. Every non-accepted outcome stops all further vendor traffic.

The decision authorizes no rebuild, helper mutation, parser recovery, second
read, index companion, UI action, reset, power action, or repair claim.
