# Actual TCON error-status result: 2026-10-26

The deliberately reviewed follow-up query `c` completed successfully. It is
a **positive vendor fault indication**, not a repair or a fully identified
initiating cause. The exact returned word is **0x00000010** (bit4), labelled
**RT Protect** in this firmware. The acronym's physical meaning is unresolved;
no temperature, short circuit, or panel-rail interpretation is inferred.

## Actual retained execution

- Result: [raw execution record](managed-tcon-status-read/result-20261026c.json).
- Installed ARM32 CLR, driver/API/QDF files and staged helper hashes passed.
- Linux boot: `00000000-0000-4000-8000-000000000000`.
- Preflight uptime75260.86; execution end75262.27.
- Helper PID3216/start18815474; libc/raw ARM syscall PID match3216.
- UID/EUID0; ARM32 little-endian; payload16B and output offset4.
- One open returned fd26/errno0; ioctl c010749f returned0/errno0;
  close returned0/errno0. Output changed from sentinel a55a5aa5 to00000010;
  operation31 and both opaque words remained unchanged.
- Helper exited0; managed stderr empty. Postflight pins passed and owned
  private directory cleanup returned PRIVATE_REMOVED. All10 root commands
  completed successfully; no further status query was sent.

The query performed no setter, reset, monitor-rearm, panel-power, protection,
factory, or firmware operation. Physical screen state was unobserved during
this call; the owner's last report was black/audio-on, without calibrated
current confirmation.

## Independent kernel log corroboration

A separately retained [filtered dmesg read](managed-tcon-status-read/status-c-filtered-dmesg/client.stdout)
returned one matching row from the retained kernel buffer:

```text
[75262.252253] [TCON:QDF] QDFTcon_GetErrDetStatus[3216:TconStatusRead.]: ERR DET Status:0x10
```

The PID and time agree with the managed call. Exact QDF code logs this word
before its optional debug override, so the positive raw log adds evidence
beyond the helper's narrow `kernel_output_written` classification. No debug
log form was retained by that filter. There was no simultaneous I2C trace;
controller-internal/live-versus-latched semantics remain unresolved. This
sample cannot yet be assigned to the physical instant the screen went black.
The earlier filtered vlog request found zero matches despite reporting12884
rows; its lack of a match is not negative evidence against the dmesg row.

## Predecessors remain rejected

Attempt `a` stopped at preflight before staging. Attempt `b` staged correctly
but failed an empty-file guard after GO; whether it issued a query is unresolved.
It may already have consumed a status read. Its raw results were not rewritten;
a separate cleanup verified its child stopped and its directory removed.
Therefore `c` must not be described as the first-ever status read, and an
otherwise zero result would have required that read-to-clear limitation.
Here the returned nonzero word and raw kernel row are positive telemetry.

## Next discrimination

Trace exact host/driver handling of bit4 and the controller-side boundary.
Determine whether stock recovery is inhibited by an asserted ERR GPIO or a
historical monitor latch; distinguish an existing fault from the initiating
content-dependent transition. Do not expand RT from intuition, clear counters,
or disable protection as a substitute for understanding the fault.


## Later owner confirmation

At chat receipt 2026-10-26T22:32:37.515931+00:00, the owner confirmed
“acreen is off”, then clarified “sorry panel is off”. The parent interprets
this as the physical panel remaining black with the TV itself on, consistent
with preceding reports. It is later physical context, not a calibrated
annotation at75262.252253 or proof of the controller bit’s time of assertion.
No reboot or display control was requested.


The [independent actual-result audit](managed-tcon-status-read/independent-review.md)
replayed all10 raw calls and validated this execution, including cleanup.
The [controller-boundary analysis](../tcon-research/rt-protect-controller-path.md)
and [host recovery analysis](../tcon-research/rt-protect-host-recovery.md)
confirm that the fault word and the monitor's physical fault GPIO are separate.
No controller-bit clear/producer/threshold is reconstructed. The stock backend's
TCON power-control method is a real forwarding boundary, not a demonstrated
recovery entry safe to invoke speculatively. A current GPIO read is being
reviewed as the next ordinary diagnostic; no such new read has run yet.
