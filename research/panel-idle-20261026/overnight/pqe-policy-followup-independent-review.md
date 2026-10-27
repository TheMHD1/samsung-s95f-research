# PQE policy follow-up: independent review

This is an independent offline review of follow-up analysis derived from the
accepted, physically unobserved PQE policy baseline. The reviewer did not
contact the TV or invoke a target function, getter, setter, ioctl, service,
device, display, power, or factory operation. Static control flow and
captured runtime identity are kept distinct throughout.

## Weber-input producer

The reviewed inputs are exact `libave.so.0.1` SHA-256
`a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`
and accepted baseline SHA-256
`5c36124d0d510fff8ac5ff282cfc43c1a70854d065b76da68ad760ceb56482a4`.
The corrected report, reproducer, and generated disassembly hashes are:

* `qd-weber-input-producer.md`:
  `18a493c65ff4b166129a9f2208bcedc45b5b3ffdc30e19043202a2dd76b0d506`;
* `qd-weber-input-reproduce.py`:
  `03f8f170532bc2cfcbda58b59189faf936821d62154f6d627a782c272d70ce4a`;
  and
* `qd-weber-input-reproduced.disasm`:
  `d68cbc1a7c27b1afdf2eb822de71d363370c4d50b19e1dbbc3a200439b75c8f3`.

Running the hash-gated reproducer offline produces bytes identical to the
saved disassembly. It checks three exact symbol spans, two vtable relocations,
four PLT targets, 35 instruction landmarks, the scale literal, and the exact
baseline hash and backend identity. Its PASS does not automatically prove the
loop/formula/error CFG interpretation or any live execution.

### Captured identity versus static slot binding

The accepted baseline sampled QD outer-header word 4 at `Q+0x10` as backend
object `0xf7203630`, sampled its vptr as the base
`DimmingBackendRoseMQD` address point `A+0x5a152c`, and read slot `+0xd8`
for backend typing. It did **not** read slot `+0x1c4`.

The exact ELF relocation at `0x5a16f0`, which is vptr `+0x1c4`, statically
binds that class slot to
`DimmingBackendRoseMQD::t_GetWeberValue(BackendWeber_t*)`, Thumb symbol
`0x1c78d5`. At the captured bias, `0xf6d3e8d5` is therefore the statically
expected target, not an observed live slot word. An earlier draft called it
a live runtime target; the report and reproducer were corrected to preserve
this boundary. The correction now states that the captured backend identity
selects a static class implementation while the live `+0x1c4` contents and
method execution remain unobserved.

### Four-word query and register loop

`QDDimming::m_CalcWeberGain` zeroes a 16-byte local query and stores
`inner+0x45c` in word 0 before the virtual query. On exactly zero backend
return, words 1, 2, and 3 feed the established ShareWeber input offsets
`+0x30`, `+0x34`, and `+0x38`.

Manual CFG review confirms the base RoseMQD producer:

* zeroes a separate 140-byte array;
* samples all 35 aligned identifiers from `0x760800` through `0x760888`,
  inclusive;
* treats the loaded words as unsigned for `>14` and increments query word 2
  only on that condition;
* passes selector `0x45238` and query word 1 to `ave_frc_read_i2c`;
* preserves that FRC call's return as the backend status; and
* converts signed query word 0 to double, multiplies by the exact literal
  `0.05750475823879242` (`3859079/67108864`), and converts toward zero to
  signed query word 3.

These are scalar and logical-register operations. The diagnostic name
`ColorNum` does not establish pixel area, luminance, voltage, a protection
quantity, or any calibrated physical unit.

### Read-failure ambiguity and fallback

The local `sdp_read_register` wrapper has two relevant no-write success
routes: shared `+0x572f8 == 1`, and shared `+0x28bc != 0`. Its lower route
calls imported `sdp_dpreg_read` but then returns zero without propagating the
lower return. The producer ignores every wrapper return. Because its local
array was prezeroed, a skipped or unwritten sample contributes zero and does
not increment the `>14` count. This establishes ambiguity in the software
statistics, not evidence that either gate or a lower failure occurred during
the owner's symptom.

The FRC status is distinct from the 35 register reads. The exact FRC wrapper
can return zero without proving a lower transfer, and an unwritten successful
read can leave query word 1 zero. No selector payload was captured by the
baseline or retained syscall trace.

On a nonzero backend return, `m_CalcWeberGain` stores 1023 directly at
`inner+0x458`, bypasses the DimmingShare call, and does not update
DimmingShare's separate gain, target, or count statics on that branch. On a
zero return it proceeds through the existing ShareWeber predicates and ramp.
With a null backend it skips the query and continues with output words 1..3
still zero; that null branch is not the accepted baseline, whose backend was
nonnull and typed.

The accepted baseline's object count 53 and gain/target/count
1023/1023/0 did not sample the per-call four-word query, either shared skip
gate, or live FRC data. The static route therefore adds useful future
discriminators but does not identify the panel fault, prove a zero-duty
request, justify invoking the query, or support bypassing a protection path.

## Evidence-snapshot generator review

The final generator reviewed here is
`snapshot-pqe-policy-followup.py`, SHA-256
`74b7e31cab42fa23938aefb32544b1d7111511e33b14cd49d3459cd78c08a43b`.
No snapshot was created during this review. Offline execution with the final
file-creation call replaced by a stopping sentinel completed every preceding
validation and reached that write boundary. `py_compile` passed, and the
active `pqe-policy-baseline-tests.py` ran 21 tests successfully.

The generator pins the preceding 176-file and 43-file manifests by their
exact hashes and re-hashes every row in both. It also requires exactly the
three named reader archives, an exact manifest payload set in each, and no
unexpected top-level archive entries except a real, non-symlink
`__pycache__` directory that is deliberately excluded. The active final
reader and tests must equal the final archive copies and retain SHA-256
`161af4bd011cb81f32cf69e8e189ced3b15045c0eaf7df5820120cf2ff99bb07`
and
`1199faf2dbb695a9af79474737b4ba71bf64c0bd2785b59824a0e74e35ab977c`.
Independently rebuilding the remote command from that reader produced the
same 4,167 bytes and SHA-256
`b963044af371423a1245c41180dac5f8c821e6d99215b74a3acfb580b76fb9b7`
as the final archive and accepted capture.

For both baseline attempts, the generator binds the intent's source/test
hashes and archive path, command hash and length, saved record command,
archive command payload, and nested root response command. It executes only
the definitions of the exact hash-pinned local reader and revalidates the
accepted raw root response to the saved summary. The accepted attempt must
retain controller/root exit 0 and `timed_out=false`; the incomplete attempt
must retain no summary, controller exit 1, nested exit 124, and
`timed_out=true`. Root UID/EUID, authentication, model, persistence label,
one-command count, acquisition invariant, physical-unobserved label, and
non-atomic contract are checked explicitly.

The source list includes the capacity trace's `fds.txt`, the complete direct
NewHome analysis chain, all seven source files behind the zero-match
`newhome-existing-capture-extract.json` result, the current Weber,
final-duty, DLSR, and FRC reports and reproducers, their pinned binaries and
scratch artifacts, and both baseline attempts with intents and driver output.
Stable reads use `lstat`, `O_NOFOLLOW`, descriptor identity,
before/open/end/after metadata, byte count, and digest checks; parsed inputs
are required to remain the same bytes. Immediately before publication it
rechecks historical manifests and every current file. Publication uses a
same-directory temporary file, file `fsync`, a no-overwrite hard link, and
directory `fsync`.

This clears the generator for one parent-owned local publication after the
reviewed inputs are frozen. It does not validate the truth of every manual
CFG interpretation, declare the diagnosis or goal complete, document a
repair, infer a physical picture state, or authorize another TV operation.
