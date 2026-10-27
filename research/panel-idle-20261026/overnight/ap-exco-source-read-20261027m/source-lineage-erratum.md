# Additive correction: AP_EXCO callback source lineage

Recorded2026-10-27 UTC. This supersedes a static interpretation in earlier
reports, without changing their frozen bytes, captures, source checkpoints,
review records or acceptance decisions. Root independently disassembled the
original startup wrappers, literal roots and callback stores after the fixed
capture rejected the old expected pointer. The new pointer-layout follow-up
then reproduced the correction with a standard-library verifier.

## Correct lineage

The selected ordinary startup has three lookups for the same AP_EXCO name.
They are distinct objects, not a global eight-byte relocation:

- lookup1bbfc uses registry descriptor10000, takes row+4 and stores the
  result at CPU200002c4: ordinary first block4500ff14;
- lookup1bbd4 uses descriptor10000, takes row+12 and stores it at200002c8:
  ordinary second block4501024e;
- lookup1bc24 uses descriptor1000c, takes its row+4 and stores it at200002cc:
  distinct AP_EXCO object450158a8.

Getter38e8 returns the third slot. Callback3934 reads source+3d8 into
context6c7, source+0 into context6c8, and separately source+1 into r8. The
captured pointer neighborhood agrees with this startup layout, including TED,
AP and a reset-initialized code word. This is strong local dataflow/layout
corroboration, not proof that every executing instruction matches the package.

The old fixed reader's expected pointer4500ff14 at cc was an incorrect
semantic assumption. Its fail-closed interpretation correctly rejected that
expectation; transport still completed and cleanup succeeded. Its two source
reads were safe allocated ordinary blocks but did not sample the callback's
third object. No shift, rewrite or reclassification of the original result
is performed.

## What earlier claims are superseded

The frozen D7 `rtp-alternate-source-context.md` and verifier incorrectly
assigned the third lookup the ordinary first-block result. The AP_EXCO row,
allocation geometry, package payloads, callback byte-store instructions and
raw captured mirror remain valid. The connection between that ordinary row's
20/0 source bytes and the callback's 1/3 mirror does not.

J's runtime-writer trace correctly maps ordinary logical addresses1b0000 and
1b049e to the ordinary blocks, but it does not establish a writer for the
callback's third object or explain the mirrored1/3 values. K's two baseline
payloads remain byte-identical; their20/0 comparison is a historical raw-data
comparison, not proof of a runtime mutation from20/0 to1/3.

M's original address review and qualification verifier correctly place its
fixed reads within allocated ordinary blocks. Their expectation that slotcc
would bind those windows to the callback is superseded. The source review and
runtime review remain records of the pinned reader and actual rejected
interpretation; neither needs to be silently rewritten.

Earlier mutable navigation and working-model statements suggesting an active
layout mismatch are superseded by this correction: the observed neighboring
words are consistent with the selected static layout once the two registry
roots are distinguished. Live executable fingerprints remain a useful next
check, for which a newly identified ordinary code-domain mapper is being
qualified separately. No new target read, write, reset or flash was performed
for this correction.

See `pointer-layout-followup.md` (SHA256
26fcc2f0a0a448fbee5ac66c767c8614ad6c4bac2c39af7f7b4395170882d0b7)
and `verify-pointer-layout-followup.py` (SHA256
ccbc619eb4ddba2078f162bc1de520f9cb90aec0a9422d13015cbf13d393b1cd).
