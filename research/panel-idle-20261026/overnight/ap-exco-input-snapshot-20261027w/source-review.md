# W source/build review before execution

Root read the native read machine and host parser; an independent read-only
agent reviewed the complete pinned helper and reported CLEAR with no
P0/P1/P2 findings. No target or network operation was made by that review.

Reviewed manifest:
`5d760fbdabf7b23b6e57f13fc40914a8ede43bf1b488738dc7c42f203321ca69`.

| File | SHA256 |
| --- | --- |
| Program.cs | ef5dd6f33a9daece5fbcaca8decf1328128a0b648268d21a1dc97d28da9136b9 |
| run-once.py | 92b6b36e9001fed8817d3b34420fd5b85cb5cf25c20f5a957c6d8deeb3f9b37e |
| ManagedUsbRtBlockReadOnce.dll | 6ee73254087fcf34e19159b25b16d3cd3afd8e63ee033fcc19db5f7b3473e0b0 |

All12 manifest entries match their sizes/hashes; the parent's O manifest,
wrapper and native pins match. The fixed three requests use only target101.
Both pointer anchors gate dependent headers. Every nonexact count/exception
leaves Unknown and prevents another vendor request; mismatch after an exact
pointer response stays Ready but sends no dependent header. Earlier exact raw
windows are attached to the result before later transfers.

The wrapper records unknown/in-flight accounting before its sole invocation,
retains the complete envelope and native bytes before interpretation, bounds
stdout to16384 and stderr to2048 under the root channel limit, and accepts
cleanup only after the exact complete terminal/lifecycle/transfer contract.
Partial, ambiguous, pointer-mismatched or framing-failed outcomes retain the
stage and are not retried. No writes, resets or dynamic-address route exist.

The reviewer freshly ran the native zero-I/O tests (48), wrapper tests (26)
normally and optimized with identical outputs, and dry default (exact3reads,
zero target operations). No builder rerun or reviewed source change occurred.

Together with address-review.md, this clears one fixed source-pinned read.
It does not establish a physical repair, exact event tuple, or permission to
infer continuous state from sequential samples.
