# BI lower-lifecycle, recorder-integrity, and delayed-read review

Recorded 2026-10-27 UTC. This is an offline review of the retained BI
artifacts. It made no TV, network, USB, I2C, GPIO, reset, power, UI or
controller request and did not rerun or relax the recorder. The owner's
screensaver observation is evaluated separately from the recorder's preserved
physical-state field.

## Decision: delayed read is not eligible

**BI is a hard stop for a delayed post-action X/read under the predeclared AU
contract.** The stock lower lifecycle and owner-visible recovery have strong
positive evidence, but the recorder has a shared export-integrity failure and
the MODE2 PID itself has one failed I2C transfer inside its replay. Fresh host
metadata cannot repair either missing premise. No vendor read/header should be
sent on the authority of this bracket, and neither the recorder nor MODE2 is
to be retried.

The original recorder correctly remains `accepted=false`,
`diagnostic_eligible=false`, `technical_capture_complete=false`, and
`physical_state=unobserved-or-incomplete`. Its error is
`ValueError: vlog/trace/hash export failed or window malformed`. No AVOC,
physical absence, or complete-capture claim is accepted from it.

## Retained bytes and the shared recorder failure

All declared sidecars were salvaged, their complete and `partial-*` copies
are byte-identical, collector stdout ends `CAPTURE_COMPLETE`, and collector
stderr is empty. The retained hashes are:

| artifact | bytes | SHA-256 |
| --- | ---: | --- |
| trace | 12,015,996 | `c2eff8adb06b852f4fc612f6c338967eb5a127d08672e5526331b43088689801` |
| metadata | 494,819 | `c6deab89d6ebda7517b621320f4edbdb6bd9399201c3ac687c50c4774147509c` |
| samples | 84,362 | `83c31fd9e397fabc2ef51660f5db986019252df4da46c1ce6b32119b11039e39` |
| sample errors | 144,421 | `514581f00f640e223e3fcccc52954f27685d20a27bce969f0e8ce71f2bb5475d` |
| vlog | 28,134,765 | `efcf8ff9363341a718613d7c85382e0c548fa50daac91a1d7944789e8de55cfc` |
| kernel artifacts | 148,910 | `cd288ef9dab974169c3c1c37e61b942e9d5ecaf3125606a6fdec00b6e5831260` |
| FD snapshot | 5,739 | `804a3be9136ee3b6109e5690dd026ce1895ecacc42ff46c19cc2325c6e013a1e` |

The recorder record is SHA-256
`158588899c2f21f89ffa58078f3ae6c0d6926d82cf7f3ef8735cf6012994339f`.
Its exact `CAPTURE_WINDOW` row is:

```text
157449.030 157449.03 157509.16 157509.26 157447.030 157512.030 143 1 0 0 0 0
```

The final six fields are the recorder's `vlog exit`, `vlog forced-stop`,
trace-export, hash-identity, sampler, and artifact statuses. Here the vlog
exit is 143 and its forced-stop flag is 1. The pinned strict metadata validator
therefore rejects before PM/runtime accounting. The offline runtime-context
replay also refuses at that same unchanged metadata check; it cannot be used
to turn this record into the qualified mutable-context false-negative class
seen in BH. The 28 MB saved vlog remains retained evidence, but its intended
bounded completion/coverage was not established.

This is a shared capture/export failure under AU's contract, not a harmless
AVOC-only duplicate. It is independently sufficient to withhold X.

## Positive stock lifecycle, with an incomplete action replay

The fixed operation-41/mode-2 helper is accepted, one-shot,
cleanup-confirmed, non-retryable, and SHA-256
`59795127ed9b3de9c0f0997201e57813fc630c9ac4cd58a237f6b5fb53213677`.
Its PID is 31720. Its ioctl return zero remains only
`kernel_return_zero_only`; the retained kernel and trace bytes positively show:

1. PID 31720 logs QDF `Reset(2)` and `Tcon Power Off` at
   `157460.712188..157460.712197`, followed by GPIO425 low.
2. The off mailbox `[01 3f 01 01 00]` and `Reset TCON power=1 ret=0` occur at
   `157460.751052..157460.751070`.
3. USB device 48, identity `04e8:2001`, disconnects and completes disappearance
   at `157460.889006..157460.914656`.
4. `Tcon Power On`, the on mailbox `[01 3f 00 01 00]`, and
   `Reset TCON power=0 ret=0` occur at
   `157461.890979..157461.911092`.
5. USB device 49 begins enumeration at `157462.402935`; the same
   vendor/product, revision 2.50, product/manufacturer/serial, and
   configuration 1 are logged through `157462.551467`.
6. GPIO425 returns high and the named init/access/display checks appear from
   `157462.755083`. Those names are software log interpretations, not
   electrical measurements.

The kernel-start and kernel-end sections both validate on boot
`00000000-0000-4000-8000-000000000000`:

- start: 499,297 decoded bytes,
  `0b726a7054616c5b9a0909549ddc54cf0b730d0438781bec84107cc02f070d19`;
- end: 498,436 decoded bytes,
  `c7f4af324e722ae888a6dc4f8a705f6585b8f1bdc01eb034367614620e970fae`.

The fixed offline I2C decoder can account for the trace bytes independently
of the failed vlog premise: ring `106329/106329`, exactly 106,329 observed
event lines, zero parse errors and zero orphan results. But PID 31720 owns 347
transfers, not 346 uniformly successful transfers:

- 346 are structurally complete and report `ret=2` (233 write6/read4 and
  113 write6/write4);
- one PID-31720 `F3:01` write6/read4 begins at `157462.986311`, has no retained
  read reply, and ends at `157462.987034` with `ret=-6`.

That failed transfer occurs inside the MODE2 PID's replay between its first
transfer at `157462.752223` and final transfer at `157463.071046`. It is not a
later unrelated monitor read, ring loss, parse error, or orphan result. The
AU gate requires a complete action I2C replay; 346 later/neighboring successes
do not erase this explicit failure. This is independently sufficient to
withhold X.

The accepted helper records and kernel log observe status `0x10 -> 0x00`,
GPIO125 raw `1 -> 0`, and duty `207 -> 207`. They are sequential software/bus
samples, not rail, light, or permanent-health measurements.

## Cleanup

Cleanup itself passes. The authenticated quiesce command exits zero with
`QUIESCED`. The authenticated cleanup command exits zero with stdout
`0\nCLEAN\n`, empty stderr, global tracing off, and guarded trace/output/stage
removal. Their hashes are:

- `quiesce.json`:
  `95d273f0c4a5ff8eb8121638fa23c5adae332d1066ae765f4775bc0d01497894`;
- `cleanup.json`:
  `bdf0ea4c9e16a37fa62732c6ddcb03e4a2c885831f076afa526a536748d16e35`.

Clean teardown does not cure the earlier shared export failure or the action
PID's failed I2C transfer. It only establishes that the rejected recorder left
no guarded capture residue.

## Owner observation and UI preparation

The separate owner record, SHA-256
`db13765d082daa59599f9ae7a2623eaeb7b2413f2cb6c4d6400a7853d000cf84`,
records: “yes it has returned in screen saver mode.” This is a second valid
owner-observed visible-picture recovery after a separately guarded stock
lifecycle. It does not make the I2C replay complete, prove MODE2's exclusive
causality, identify the failed transfer's physical effect, or establish
prevention/permanent repair.

The first later ordinary Apps preparation did not execute a UI action. Its
first root-access attempt failed before network dispatch with
`BlockingIOError; no automatic retry`; the retained record reports
`target_operations=0` and `no_retry=true`. Its SHA-256 is
`d17007e26fdd7e8f850a6355ea96010da692d617318607e9cf72dd6908759f2a`.

After the BI recorder had terminated, a separate sequential attempt then
succeeded. The fresh preparation completed and staged its six pinned files;
`apps-prepared-sequential/prepare-record.json` has SHA-256
`623cff44d567b75d6c4c762ea453f511326f916dc4a5b5997430e4a9a311815a`.
Exactly one unchanged managed AppControl send to `d/apps.tab` was attempted
and returned. Its result reports `target_operations=1`, `send_attempted=true`,
`send_returned=true`, `execution_confirmed=false`, and no physical picture
observation; the result SHA-256 is
`ddf1dd4e6b7f1a02266c2c0e14e3488e73a388fad7d496558b78ba4308917cdb`.
Guarded cleanup then reports `stage_absent=true` and zero target operations,
SHA-256
`a9d817b8cb61fcea923f2c01b9b5d613f77c718493d87aa7818fdd06b9b007d8`.
The sequential prepare/send/cleanup exits are all zero in
`apps-sequential-exit.json`, SHA-256
`fb6da8b802f18fe55b90ce07075fe824203a938cb05d7fb3637ec602b51453a6`.

That later UI chronology is separate from the stock action and recorder. It
contains no controller/vendor-USB request and no post-X read. Its physical
Apps result was pending at this review point, and it does not alter the BI
post-X hard stop.

## Bounded conclusion

BI adds a second owner-confirmed return of a visible screensaver and another
positive stock off/on USB lifecycle. It does **not** provide an AU-complete
scientific bracket: vlog completion was forced and one action-PID I2C read
explicitly failed. Preserve both the positive physical observation and these
negative integrity facts. Do not issue a delayed read/header, retry MODE2, or
relax/replay the collector as if the missing gates had passed.
