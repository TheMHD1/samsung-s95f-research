# Independent review: AVEMon all-syscall V3

## Reviewed bytes

* `avemon-syscall-checkpoint-v3.sh` SHA-256
  `4b747bf00e53643463bc5d48f0d6ff19a0e53da7962cbc5bb4e5877ec9eb6863`
* `run-avemon-syscall-checkpoint-v3.py` SHA-256
  `e8f817c97d7fa98676e85438a207fb63c95e07e5a7ac4311c56e55c630a84fdb`

No target command was sent for this review.  `sh -n`, Python compilation, and
the wrapper's default dry path passed locally.

## Capacity change and preserved guards

V3 changes the V2 capacity failure in bounded ways:

* it captures for two seconds rather than five;
* it rejects an uncompressed trace at one MiB or more;
* it compresses the complete private-instance trace with `gzip -c`, base64
  encodes that result, and rejects a packed value at 32,768 characters or
  more; and
* it uses a distinct private trace instance and an exclusive `...2027c`
  destination, preserving the rejected V1 and V2 records.

The identity, boot, AVOC executable/task-start, endpoint-FD, trace-clock,
event/filter, strict stats/loss, trace stop, instance-removal, and independent
global-quiescence guards are otherwise retained.  The wrapper remains dry by
default; execution needs both explicit flags and leaves `accepted` false.
The shell contains no UI, controller, panel, GPIO, or QDF operation.

## Export validity boundary

The bounded compressed export is valid only as a *transport mechanism* for a
future offline decoder.  It is not self-authenticating evidence:

* POSIX shell exposes only the final `base64` status for
  `gzip -c ... | base64`; a gzip failure can therefore not be accepted from
  the shell exit code or a nonempty packed string alone.
* The host must strictly isolate exactly one
  `TRACE_GZIP_BASE64_BEGIN`/`TRACE_GZIP_BASE64_END` body, reject malformed
  base64, decompress it with CRC validation, and require decoded byte length
  to equal `TRACE_RAW_BYTES` before treating trace text as available.
* It must then parse the normal ftrace header plus both explicit markers and
  account for every filtered entry/exit event.  The new cap is not evidence
  that no event was omitted unless those checks and the retained zero-loss
  stats pass.

Those requirements are compatible with the current runner because it saves
the successful command stdout verbatim in `raw.txt` while keeping
`accepted=false`; however, no such offline decoder is present in the reviewed
V3 bytes.  A successful transport alone must remain unaccepted pending that
separate validation.

The 32-KiB packed ceiling, plus the short configuration/stats text, remains
below the existing 64-KiB root-response limit.  Conversely, if either cap
rejects, that run is a rejected capacity observation rather than a sampled
trace result.

## Verdict

**Clear for one bounded V3 transport attempt, with mandatory post-run offline
gzip/CRC, decoded-length, marker, and pairing validation before acceptance.**
This does not rehabilitate V1/V2, predict packed size from V2, or establish
anything about panel state or fault causality.
