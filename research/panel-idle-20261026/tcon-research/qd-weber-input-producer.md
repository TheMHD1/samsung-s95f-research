# QD Weber-input producer: object count, register statistics and FRC reading

This is bounded offline analysis of the exact acquired `libave.so.0.1`, SHA256 `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`. No TV command, target function, getter, ioctl, service or memory read was performed for this analysis. Addresses below are ELF VAs; function symbols include the Thumb bit, while instruction addresses do not.

## Newly resolved interface

The [consumer report](pqe-event-userspace-consumer.md) left the producer at `QDDimming+0x10`, virtual slot `+0x1c4`, untyped. The independently accepted [174544Z baseline](../overnight/pqe-policy-baseline-runtime-results.md) identifies its enclosing backend class: outer-header word4 at `Q+0x10` equals the guarded backend object `0xf7203630`. Its captured vptr is `A+0x5a152c`, the base DimmingBackendRoseMQD address point. The exact ELF relocation at `0x5a16f0` (`vptr+0x1c4`) names `DimmingBackendRoseMQD::t_GetWeberValue(BackendWeber_t*)`, Thumb symbol `0x1c78d5`, size 844. At that capture's load bias the statically expected target is `0xf6d3e8d5`; the live contents of slot `+0x1c4` were not read. The baseline read slot `+0xd8` for backend typing, a separate method.

This resolves the static class method against a captured backend identity. It does not establish the live slot contents, that the method executed during the read, that all virtual tables remained unchanged between sequential reads, or that it caused a physical event. The MNT slot has a distinct implementation at `0x1caac1` and is not substituted here.

## Four-word query record

`QDDimming::m_CalcWeberGain` (`0x1793d1`, size 236) zeroes a 16-byte local query block, writes the object-count field `inner+0x45c` into word0, and passes it to the backend slot. On exactly zero return, words1..3 enter the existing ShareWeber input at `+0x30/+0x34/+0x38` respectively.

| Query offset | Base RoseMQD producer |
| --- | --- |
| `+0` | Input object-count word; retained |
| `+4` | Output of `ave_frc_read_i2c(0x45238, out+4)` |
| `+8` | Count of 35 sampled register values that are unsigned greater than 14 |
| `+12` | Signed object-count word multiplied in double precision by `0.05750475823879242`, then converted to signed integer toward zero |

These are recovered scalar operations, not established luminance, pixel-area, voltage or physical protection measurements. Diagnostic strings use labels such as `ColorNum`, but they do not establish calibrated physical units.

## Register sampling and ignored read failures

The backend zeroes a separate 140-byte stack array. At `0x1c7920..0x1c7994` it calls `sdp_read_register` for each aligned address in the inclusive range `0x760800..0x760888`: 35 words. The loop reads each local output, increments query word2 only when it is unsigned greater than 14, and continues. It does not test the read's return. Debug logging branches do not change the register range or threshold.

The local wrapper `sdp_read_register(unsigned,unsigned*)` is Thumb symbol `0x2b061d`, size 168. Its shared-state check `get_ave_shm()+0x572f8 == 1` takes a log-and-return-zero branch without writing the output. Another shared word `+0x28bc != 0` also bypasses the lower read and returns zero. On its real lower path it calls imported `sdp_dpreg_read` at `0x2b067e`, then returns zero without propagating the lower return. Register-offset handling exists before this gate; its special high-byte branches do not establish the meanings of these two shared flags.

Thus skipped or unwritten register outputs can remain zero in the backend's prezeroed array and contribute no threshold count. That is a source-supported failure/skip ambiguity. It is not evidence that either shared flag was set, that a lower read failed, or that any such skip occurred at the owner's blackout. The imported `sdp_dpreg_read` implementation is outside this bounded audit.

## FRC status and the distinct fallback

After register sampling, the backend calls `ave_frc_read_i2c` with selector `0x45238` and query word1 as destination at `0x1c79a0..0x1c79aa`. It saves this call's return, computes word3 from the signed input object count using the literal double at `0x1c7bd0`, and returns the saved FRC status. No return from the preceding 35 register reads contributes to that status.

The [FRC read-ABI report](frc-ioctl-6626-analysis.md) shows that a zero return does not by itself prove a hardware transfer or changed output. For this prezeroed query, an unwritten successful read can therefore leave word1 zero. This is a possible software path, not an observed selector payload or failure in the retained syscall trace.

When this backend returns nonzero, `m_CalcWeberGain` branches at `0x179420` to `0x1794a2`: it writes 1023 directly to `inner+0x458` and exits without calling DimmingShare. It does not update DimmingShare's separate gain/target/count statics on that branch. Therefore a future discrepancy between `inner+0x458` and the global gain is interpretable as different cached state; neither field alone identifies a particular cause. A zero return instead allows query outputs to select the existing Weber predicates and ramp.

If the backend pointer at `Q+0x10` is null, the calculator skips the query and continues with zeroed query outputs. That static branch is not the actual accepted baseline, which has a nonnull, typed backend.

## Diagnostic consequence and limits

This closes a previously unknown content/statistics edge:

```text
PQE type3 object count -> inner+0x45c -> query word0
35 register reads -> threshold count word2
FRC selector0x45238 -> query word1
signed scaled object count -> query word3
  -> ShareWeber predicates -> gain -> conditional final-duty calculation
```

The accepted baseline sampled object count 53 and gain/target 1023/1023, but it did not sample these per-call query outputs, the two shared read gates, or actual FRC selector data. Its physical picture state was unobserved. Nothing here identifies the panel fault or establishes a software-generated zero-duty request. The gain stage itself clamps to 1..1023; later final-duty arithmetic is a separate investigation.

For a physically observed transition, this finding makes the query inputs and skipped-read conditions useful discriminators. It does not justify forcing a register value, bypassing a protection mechanism or repeatedly invoking the getter.

## Local reproduction

Run `PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/qd-weber-input-reproduce.py` from the investigation directory. The helper hash-gates the ELF and retained baseline, checks three symbol spans, two backend-slot relocations, four PLT targets, 35 instruction landmarks and the exact scale literal, then prints code separately from literal-pool data. The companion `qd-weber-input-reproduced.disasm` retains that output. Loop bounds, signed arithmetic, error ordering and reachability above are manual CFG interpretations anchored by those landmarks, not automatic proof of live execution or hardware behavior.
