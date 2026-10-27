# Independent review: QD power-control userspace ABI

## Verdict

**CLEAR for the bounded static ABI conclusion; not clearance to invoke it.**

The reviewed report correctly establishes a source-derived path from the AVE
wrapper to the QDF callback intended for operation `0x29`, with the supplied
mode in request word 1.  It also correctly limits that result: current live
table binding, lower hardware success, controller acceptance, panel emission,
and recovery outcome are not established.

No TV, root, device, ioctl, or network action was taken for this review.

## Inputs and verification

| item | SHA-256 / result |
| --- | --- |
| reviewed report | `ff63e0c5c5c1679d870e4b816a47fcff51d6ccaf62aac0491f737962cb8e3983` |
| reviewed reproducer | `5481ce099cd2387f39033ddfcc1f53c8cab3e87490d1aeb9fc4c788c5859442b` |
| `libave.so.0.1` | `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` |
| `tztv_frc_tcon_api.ko` | `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6` |
| `qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` |
| normal and optimized reproducer | PASS / PASS |
| Python syntax compilation | PASS |

The review also independently inspected the QDF body with AArch64 objdump.
The mode comparisons at `0x11c54..0x11c68` select zero, one, or two; the
mode-two block at `0x11cdc..0x11cf0` calls `m_set_power_control(0)`, saves its
integer return, calls `m_set_power_control(1)`, and ORs those returns.  The
other-mode path logs then returns zero without calling lower power control.

## Confirmed path

1. AVE's `ave_api_set_qd_tcon_power_control` restores the supplied integer and
   calls the PLT target resolved by the reproducer to
   `ave_tcon_qd_set_power_control(int)`.
2. The lower Thumb wrapper builds the exact `0xc010749f` envelope: word 0 is
   `0x29`, word 1 is the supplied mode.  The uninitialized tail words are not
   read by the reviewed operation-41 dispatch, but a hypothetical future
   caller would still need to initialize them defensively.
3. Both API dispatch tables compute `.text+0xed80` for operation 41.  That
   body loads the interface from BSS `+0x620`, loads callback slot `+0x458`,
   loads request word 1, and calls the slot.  Either missing-interface branch
   returns zero at `0xf35c`.
4. QDF's init code places `QDFTcon_SetQdTconPowerControl` in its table at
   `+0x458` and passes that table to `map_tcon_functions`; the API's
   `0x7c58..0x7c60` installation stores the table in BSS `+0x620`.
5. At the character-device boundary, the reviewed dispatcher preserves the
   callback integer result through copy-back.  This is ABI return propagation,
   not an action acknowledgement.

The report correctly calls the init/table link an **intended static binding**,
not proof that the same object was present or unchanged at a particular live
instant.

## Important limits and one verification-scope note

* A returned zero remains ambiguous.  It can mean the API pointer or callback
  slot was absent; it cannot be treated as a successful rail sequence.
* A nonzero return is likewise incomplete: the lower lifecycle publishes some
  cache fields before lower work and discards/aggregates several lower errors.
  The established off/on path cannot establish panel light or controller fault
  clear from its return.
* The report's statement that modes zero and one call their corresponding
  lower modes is supported by the inspected QDF branch body.  The supplied
  reproducer structurally asserts the mode-two off/on instructions and the
  invalid/missing-callback behavior, not every mode-zero/mode-one branch
  instruction.  This is an automation-coverage limit, not a contradiction in
  the report.
* The `printk` calls visible in each QDF mode branch are useful stock-log
  candidates for a future passive capture, but a log row still does not prove
  completion or hardware success.  They do not make this ABI an appropriate
  diagnostic poll or recovery command.

## Why inline/production logging is not a substitute

Replacing the production kernel/module or inline-patching AVE would change
the code whose recovery behavior is being studied.  The retained environment
does not provide a validated build/signing/load/unload route, a running-text
identity proof, live relocation/lifetime guards, or tested rollback.  Function
tracing/kprobes/uprobes are unavailable in the recorded target observability
surface.  Such a change would also perturb timing in a fault-sensitive power
path.  It is therefore neither a passive observation nor a validated fallback
for the static trace-and-stock-log plan.

## Conclusion

The parent report's recovery-route finding is accurate as a static
source/ABI result: operation 41 with mode two reaches QDF's normal off-then-on
implementation **if** the intended runtime binding exists.  It does not
identify a safe reset, clear RT protection, clear the AVE monitor latch, or
justify execution while the outcome cannot be physically observed.
