# AVEMon all-syscall checkpoint: rejected first attempt

## Scope and retained inputs

This is an offline audit of the first attempt only.  It sent no target
command.  The retained record is
`avemon-all-syscalls-20261027a/record.json`, SHA-256
`29a2f76e738e8f9444a8755937d6f2ef6bd72e2225930dfb53d626d2888b9531`.
The executed shell is SHA-256
`79c7c1cdc63afa7798732c707f419d5085e9015a08aa033e829a7c432b59fbdb`.
The independently retained empty-CPU format sample is
`empty-cpu-stats-format.txt`, SHA-256
`5b8a0e992510bd07f2a25c108ce0fdb37832688a33ee6f1fb57fb058eb989bc4`.

## What the record establishes

The first root command returned exit code 1 without a transport timeout or
stderr.  Its retained stdout reaches the end identity rows:

* the expected boot UUID, AVOC executable, AVEMonMain task start tick, and
  the two required FD targets were printed at both endpoints; and
* it ends immediately after the second `21 /dev/tztv_frc` and
  `33 /dev/dri/card0` rows.

It contains neither `TRACE_BYTES` nor `TRACE_BEGIN`.  The shell orders the
strict per-CPU stats loop immediately after those endpoint rows and before
both markers.  Therefore the attempt rejected in the stats-validation region.
It did **not** export a raw syscall trace, so it cannot answer whether syscall
entries/exits paired or whether a different syscall ID occurred.

The wrapper then made its separate, verification-only request.  That request
returned `CHECKPOINT_QUIESCENT`; the private trace instance was absent and
global tracing was off.  This establishes cleanup, not successful evidence
capture.

## Likely grammar mismatch, not a loss conclusion

The rejected attempt does not retain the failing stats file, so no particular
CPU or counter can be identified.  The local empty-CPU sample shows why the
specific grammar is likely too strict:

```
oldest event ts:     0.000000
oldest event ts:     1.209411
```

With the shell's `awk -F ': '`, the value includes leading spaces.  The
executed predicate accepts only `^[0-9]+[.][0-9]+$`, so it rejects those valid
formatted values before trace export.  A thread-filtered capture can leave one
or more per-CPU buffers empty even while the target thread emitted events on
another CPU; that is compatible with this formatting path, but was not
observed in the discarded attempt.

This is not evidence of overrun, dropped events, a bad AVEMon identity, or a
panel condition.  It is also not proof that whitespace was the sole failure:
the unretained stats records prevent that conclusion.

## Safe correction boundary

If the recorder is revised, it should trim only leading/trailing ASCII spaces
from each parsed value before applying the existing exact eight-key grammar.
It must retain the same eight keys, numeric requirements, and all-zero checks
for `overrun`, `commit overrun`, `dropped events`, and `read events`; it must
not weaken those loss checks or interpret this rejected record.

Before any later attempt, an offline fixture should include both padded
zero-valued and padded nonzero historical timestamp forms, and a nonzero
overrun fixture.  The latter must still fail.  A new run, if separately
approved, remains a distinct finite observation.

## V2 correction review

The isolated V2 shell is SHA-256
`60832356c98aa96250dfde4cbe2f324e947c3c6f66c27db993a8e72ad2f5d4bd` and
the V2 wrapper is SHA-256
`01b437edc73e2c26cce9a74a1885132658fb7a7c3454425a876ab27598841695`.
It uses a new private trace-instance name and exclusive local destination, so
it cannot overwrite the rejected V1 record.

V2 trims surrounding POSIX whitespace from the already-delimited stats value
only, then retains the original exact key/count/numeric checks and zero-loss
requirements.  It emits each raw stats file before validating it, so a future
stats-grammar rejection is retained inside that command's transport envelope.
I checked the exact V2 AWK body against all four padded retained empty-CPU
blocks: all pass.  A padded `overrun:    1` fixture and an unknown-key fixture
both reject.  Shell syntax, Python compilation, and wrapper dry mode also
pass locally.

**V2 is clear for one separately recorded five-second private checkpoint.**
This clears the formatting defect only.  It does not turn V1 into evidence,
does not establish that V2 will export a trace, and does not relax the
zero-loss, identity, endpoint-FD, boot, trace-size, or cleanup guards.
