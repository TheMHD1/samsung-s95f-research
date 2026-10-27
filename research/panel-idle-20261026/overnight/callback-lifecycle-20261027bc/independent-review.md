# Bounded review and corrections

Recorded 2026-10-27 UTC. The independent reviewer supplied read-only findings;
root records them here after corrections and independently checks the
selected bytes. No target operation was involved.

1. **Fault dependency:** descriptor `0x1c` owns the ordinary enable-8 edge,
   but teardown disables `0x1c` at `0x96e4..0x96f0` before descriptor 8 at
   `0x9724..0x9730`. The report and verifier now preserve this dependency.
   Ordinary handoff is not a demonstrated post-fault dispatch path. An
   already active callback or another enable path is not excluded.
2. **Separate state bytes:** both gate loads refer to `0x2000087c`; the later
   zero store uses `0x2000087e`. The report and verifier now pin the two
   loads, their zero arms, and that distinct clear. No alternating-call or
   cadence inference remains.
3. **Conditional disable:** descriptor 8's own callback disables/work only
   after its pointed word's bit3-one branch. Bit3-zero goes to common
   pending-clear completion. The final verifier pins this gate explicitly.
4. **Schedule and live state:** startup-installed/enabled source code is not
   an observed later invocation. Root refined the final prose to avoid a
   schedule claim or an absolute exclusion of an in-flight callback.

The independent descriptor check reconstructed row0, the 20-byte descriptor,
the IRQ39 vector slot and wrapper, with zero target operations. Root repeated
the decode and independently disassembled the wrapper and callback. The
separate root descriptor verifier passes normally and with `-O`.

Root also disassembled the ordinary handoff branch, enable helper, startup
install/enable slice and fault teardown. The final handoff verifier passes
normally and with `-O`, producing identical output SHA-256
`594fd42b71faee502b0a3ce57c0f49c5cfdecbbd455ccff0ca5eaf35ecd81b9f`.
The final artifact manifest records post-correction file hashes. Earlier
agent message hashes refer to earlier drafts when different.

These checks support the bounded selected-source interpretation. They do
not establish current IRQ enable bits, active vector base, callback dispatch,
fault timing, electrical meaning, physical recovery or prevention.
