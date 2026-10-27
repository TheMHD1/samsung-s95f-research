# First target attempt: preflight refusal, no TEE sequence

The centrally dispatched first target invocation returned exit 65 with exactly:

```text
REFUSED_OR_FAILED stage=file-preflight metadata_published=0
```

This is a **failed preflight**, not a decryption success or a TA denial. The
reviewed assembly hash was
`a55539aa106b542905926f5bb6761adbd542d2111bcff2a68ba2ecbc559838db`;
the runner hash was
`d969ac178d7761c01ac1f1091f65b81aa97bbc21cfc8bbe348cee4715b1864a5`;
the deployment manifest hash was
`48c3d5618e8596ed2b6b4bcf582b6dff3fc28be881cb21731a959de7c0a51b2b`.
The complete authenticated records are retained privately outside the source
tree, in the local state trial `s95f-live-trials/swu-bx-01`.

## What executed and what did not

The runner staged four reviewed files, then dispatched the adapter once.
The native process returned normally with exit 65 and no stderr. The source
sets `file-preflight` before constructing six pinned ordinary-file readers
and validating the two input arrays. The following `selector-binding` stage
was not reached. No `Binding`, vconf getter, TEEC initialization, session or
command is on this preflight path. There are no selector rows or native
sequence diagnostics in the returned output. No plaintext was produced or
saved by this path. No TV menu, panel reset, threshold or firmware change was
requested in this trial.

The runner refused acceptance and retained its six-file stage instead of
retrying or deleting an ambiguous failure. Its conservative operation ledger
still says `inflight_or_unknown`; this later classification uses the returned
native marker and exact reviewed source to narrow that result. It does not
rewrite the original record into a success.

## Follow-up observations

An ordinary metadata-only request at target uptime 165551.20–165551.23 found
the same Linux boot and exact expected paths, modes, sizes and hashes for
the staged envelope, installed encrypted master blob and four libraries.
The envelope's `/tmp` path resolved to itself; the vconf symlink resolved to
the previously acquired versioned file. These later shell observations do
not identify which native preflight predicate failed or prove that every
native syscall/marshaling result was correct at the earlier invocation.

The preflight stage does not expose a safe reason code or per-file label.
Consequently the present result cannot distinguish a native syscall/marshal
issue from another failed guard. A diagnostic-only fixed-file probe must
identify it without loading the selector/TEE libraries or invoking a TA.

## Independently found ARM open-flag defect

The subsequent source audit found that `PinnedFile` passes `0x20000` with
the comment `O_NOFOLLOW`. That is the x86-64 value. For Linux ARM32,
`O_NOFOLLOW` is `0x8000`, while `0x20000` is `O_LARGEFILE`. The existing
qualified ARM USB helper uses `0x8000`. Thus the advertised no-follow guard
in this first adapter is incorrect on the target architecture. This is a
real ABI-specific guard defect missed by the earlier host/source reviews;
their broad no-defect conclusions are superseded for this point.

The defect does **not** establish the cause of exit 65: opening an ordinary
file with the extra large-file flag need not fail. Preserve the original
source and assembly. A corrected revision must select flags by actual ABI,
test the exact constants and symlink rejection, retain all identity/hash
checks, and use the diagnostic result to address the actual refusal. Do not
remove a check merely to reach TEEC.

A separate offline lookup in the hash-pinned saved kernel finds compat
syscall 397 and native syscall 291 pointing to the same non-stub wrapper at
Image offset `0x18ce38`, which calls `0x18cca8`. This narrows a possible
statx-ENOSYS hypothesis for the stored kernel only. It does not prove the
executing-text identity, successful syscall return or correct ARM CLR array
marshaling. No kernel patch follows from this lookup.

## Status

One target invocation, no automatic retry, no TEE sequence, no validated
metadata, no permanent blackout prevention. The source/host tests remain
useful evidence but did not establish target preflight compatibility. The
public research snapshot cut off before these trial records; this report
must accompany any later publication of the adapter's readiness claims.
