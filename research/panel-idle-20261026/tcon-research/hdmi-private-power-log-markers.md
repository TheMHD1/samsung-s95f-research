# Stock trace messages around a private HDMI power-management caller

The reconstructed private Samsung callback route has useful stock messages
that the existing `early_trace/early_event` capture can retain. They are
positive correlation candidates for a future owner-observed blackout. They
are not universal callback coverage, a hardware-success signal, or evidence
that this path caused any retained blackout.

## Exact caller and logger

Acquired `tztv_hdmi_switch_api.ko`, 1,143,558 bytes, SHA-256
`c586a2601665a778a1e7401cd6b7553e03684f2e4536a282047b17059b7eec97`:

- Exported `suspend_hdmi_suspend`, `.text+0x1bb8`, size 152, checks cached
  byte `.bss+0x1e8+5`. Only when zero does it proceed. It logs an IN row at
  `0x1bf8`, calls imported `sdp_runtime_pm_put` at `0x1c04` with literal
  `sdp-hdmi`, and logs an OUT row at `0x1c10`. It later stores one to the
  same cached byte and invokes another suspend helper. An early return is
  zero; the private call's return is not retained as a hardware result.
- Exported `suspend_hdmi_resume`, `.text+0x1c50`, size 188, proceeds only
  when that byte equals one. It logs IN at `0x1c94`, calls imported
  `sdp_runtime_pm_get` at `0x1ca0` with the same `sdp-hdmi` record name,
  and logs OUT at `0x1cac`. Later it may create a separate resume thread,
  clears the cached byte, and returns zero. The call's return is discarded.
- Both logging sites invoke `hdmi_hwc_log`, `.text+0x320`, size 152.
  The function formats its message through `vsnprintf` at `0x38c`, invokes
  imported `trace_early_message` at `0x394`, then calls a second cached log
  callback through `.bss+0`. This latter callback's live binding is unknown.

The literal spellings differ: the resume log prints `sdp_hdmi` while the
actual argument string is `sdp-hdmi`. The exact marker contract preserves
that distinction rather than silently normalizing it:

```text
[HDMISW] suspend_hdmi_suspend : sdp_runtime_pm_put(sdp-hdmi) [IN]
[HDMISW] suspend_hdmi_suspend : sdp_runtime_pm_put(sdp-hdmi) [OUT]
[HDMISW] suspend_hdmi_resume : sdp_runtime_pm_get(sdp_hdmi) [IN]
[HDMISW] suspend_hdmi_resume : sdp_runtime_pm_get(sdp_hdmi) [OUT]
```

These are caller-specific messages. Other callers of the private kernel API
can invoke the same callbacks without these messages. No complete invocation
root for the two exported switch helpers is claimed here.

## Relation to the existing observer

The retained `overnight/early-trace-format.json` records a successful read of
`events/early_trace/early_event/format`: ID 132, a dynamic string `str`, and
print format `%s`. Its SHA-256 is
`26d92050dcb1acdafda01a242d9d11f6be11e2debcfe39d70a84fcbfedff0559`.
That historical acquisition is not a fresh exact-format endpoint check.

The frozen base observer enables `early_trace/early_event` in its private
instance; the accepted pre-roll observer inherits it. The accepted smoke's
raw trace already contains an ordinary `[HDMISW] Current_Src...` row at
`65182.775131`, line 6527. This demonstrates retention of that emitted stock
message in that passive run. It does not demonstrate emission or retention
of the four private-power markers, or the physical screen state.

A matched IN and OUT can bracket return to this particular caller. It cannot
establish a saved callback was actually called: private API bypass, lookup,
reference-count and callback-null gates are separate. An OUT marker also
does not report callback status or panel light. A missing marker cannot
exclude a private operation, especially since stock trace emission has
additional runtime gates and the same text is not unique execution provenance.

No live capture or display action was performed for this analysis. The
previously accepted smoke remains unchanged. A future report should retain
exact raw rows and clock bounds and correlate positive messages with an
owner-observed onset, without treating temporal proximity as causation.

## Reproduction and review

[Offline verifier](hdmi-private-power-log-markers.py) pins the existing ELF
reader and exact module, checks all three function identities, both cached
flag gates, literal-to-log-call relocations, private target record literals,
get/put imports and exports. It compares the [saved disassembly](hdmi-private-power-log-markers.disasm)
and [exact message contract](hdmi-private-power-log-markers.json).
Normal and optimized runs passed:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 hdmi-private-power-log-markers.py
PYTHONPATH=/tmp/tcon-capstone python3 -O hdmi-private-power-log-markers.py
```

The first verifier attempt rejected an incorrectly transcribed resume size
of 192; the actual ELF symbol size is 188. That was corrected before any
saved artifact was created. This was an offline verifier failure, with no
TV interaction. Independent read-only review subsequently confirmed both
literal/call chains, the logger dataflow, the captured event format, and the
referenced raw smoke row. Normal and optimized verification passed. This
clearance establishes the stated static scope, not a runtime diagnosis.
