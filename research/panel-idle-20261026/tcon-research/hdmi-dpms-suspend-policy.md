# HDMI DPMS cached-byte suspend policy

## Scope

This is a static, offline trace of the exact copied
[`tztv_hdmi_switch_api.ko`](../binaries/tztv_hdmi_switch_api.ko), SHA-256
`c586a2601665a778a1e7401cd6b7553e03684f2e4536a282047b17059b7eec97`.
No kernel routine, private control, I2C write, or TV state was invoked.

The earlier DPMS route establishes that a userspace DPMS notification can
reach the API module's one-byte local `s_dpmsType` cache at `.data+0xa38`.
This report traces one later **static consumer** of that cache: `Suspend`.
It does not establish that the cache was written, that `Suspend` ran, that any
runtime guard was true, or that any external chip or panel changed state.

## Cached-byte reads and policy gates

`s_dpmsType` is a one-byte local symbol at `.data+0xa38`.  The 452-byte
`Suspend` body occupies `.text+0xe588..0xe74c`.  Its relocation-backed
`ADRP`/`LDRB` pairs at `.text+0xe630/.e634` and `.text+0xe65c/.e660` both
address `.data+0xa38`; they are not same-offset guesses.

The relevant conditional flow is:

| condition in `Suspend` | static action | result treatment |
| --- | --- | --- |
| `g_external_switch_information` bit 1 is set (`0xe61c`) | call `ext_switch_suspend` at `0xe620` | its return replaces `w20` at `0xe624` |
| bit 2 is set (`0xe62c`) | compare `s_dpmsType` to exactly one; call `ext_se22s_set_mode(2)` for equal (`0xe640/.e644`), otherwise mode one (`0xe714/.e718`) | returned value is immediately superseded by the next path; it is not accumulated into the final result |
| bit 0 is set, and driver field `[x19+0x10] == 0x0a` (`0xe64c..e658`) | compare the same cached byte; call `ext_sw_SetMode(2)` for equal (`0xe66c/.e670`), otherwise mode one (`0xe730/.e734`) | likewise ignored for the enclosing return |

`w20` is initialized to `flags & 2` at `0xe618`; only the bit-1
`ext_switch_suspend` call can replace it.  The final `mov w0,w20` at `0xe6dc`
therefore confirms the two mode-call results are not propagated by this
function.  The numerical mode values are proved argument values only; their
human meaning is not inferred here.

## Private suspend bridge

The exported `suspend_hdmi_suspend` is `.text+0x1bb8`, size 152.  If its
local byte at `+5` is already nonzero, it returns zero immediately.  Otherwise
it calls the private PM put import at `0x1c04`, stores one into that byte at
`0x1c1c`, and calls `tztv_hdmi_switch_suspend` at `0x1c20`.

The target is correctly in **`.text.unlikely+0x228`**, size 104—not
`.text+0x228`.  It loads an operations pointer, tests it and its `+0x90` slot,
and conditionally executes `blr x1` at cold-section `0x25c`.  The
callback-present path then reaches `mov w0,#0` at `0x26c`, so it ignores that
callback's return.  Either null test branches to `0x274`, which reaches
`mov w0,#-0x13` at `0x280` instead.  Thus the wrapper has a static zero result
only when both pointers are present; its null-ops/null-slot alternative is
`-19`.  The enclosing `suspend_hdmi_suspend` still does not inspect the return
from its call at `0x1c20` and itself ultimately returns zero.  The static code
does not identify the live operations object or prove that the callback is
installed or delivered.

## Lower calls reached by the two mode branches

`ext_se22s_set_mode` at `.text+0x36da8`, size 100, forwards its incoming mode
unchanged in `w3`.  It sets `w0=1`, `w1=-0x60`, `w2=0x41`, and `w4=1`, then
calls relocated `tztv_i2c_write_8bit` at `0x36dcc`.  A nonnegative lower
return is retained; a negative lower return follows `tbz w0,#31` at `0x36dd4`
and is normalized to `INT_MIN` (`0x80000000`) at `0x36ddc`, which is returned
at `0x36dfc`.

`ext_sw_SetMode` at `.text+0x343c8`, size 104, first stores the incoming mode
as one stack byte, obtains its first argument from relocated
`g_extsw_i2c_bus`, then supplies `w1=-0x60`, `w2=0x41`, stack-byte address in
`x3`, and `w4=1` to relocated `tztv_ext_i2c_write` at `0x343f4`.  It initializes
the eventual result to `INT_MIN` at `0x343f0`; only a nonnegative lower return
replaces it at `0x3440c`.  Thus a negative lower result is normalized to
`INT_MIN`, rather than being returned directly.

These are concrete call/argument-register facts.  They do **not** prove a bus
address ABI, I2C transaction format, adapter selection, device identity,
successful transfer, or external-device behavior.  In particular, this report
does not call either lower routine or assign a panel-power meaning to mode one
or two.

## Reproduction and limits

Run:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/hdmi-dpms-suspend-policy-reproduce.py
```

The verifier pins the API module hash, exact symbol locations, complete decode
coverage of the five bounded functions, selected branch/register landmarks,
the two `.data+a38` relocation pairs, named call relocations, both cold-wrapper
return alternatives, and both negative-return normalizations.  The original
[v1 listing](hdmi-dpms-suspend-policy.disasm) is preserved.  The verifier now
generates and equality-checks [v2](hdmi-dpms-suspend-policy-v2.disasm) by
exclusive write.  `PASS` proves those landmarks, not the surrounding dynamic
policy state.

This creates a static route from the already-recovered DPMS notification cache
to conditional external-device selection.  It is not evidence of the
owner-observed blackout, the OLED's condition, a TCON failure, or a safe repair
action.
