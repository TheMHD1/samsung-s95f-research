# Independent framing-wrapper review

## Result

No concrete defect was found in the bounded framing correction. The candidate
is cleared as the corrected wrapper implementation for a future onset-logger
launch, subject to the separate controller-state deployment gate below.

Reviewed aggregate:

- `managed-usb-secondary-logger-onset-framing/build-manifest.json`
- SHA-256: `b1ffc0f91b614163e10e4132b9410c60116d22101b5666f1614ef471b4938780`
- wrapper SHA-256: `489c4391db6622918befcf365b5952f08cd3f58f3989925b8b6d0fa51a1ab36f`
- native manifest SHA-256: `316d92b64be47767cb8461d4cbde30b9446d901060b2de798da605d9f1c8131c`

## Verified delta and evidence

The production diff from the pinned qualified predecessor is limited to the
schema label and the `LAUNCH_ACK` format separator. The predecessor placed the
two characters backslash and `n` in the command template; the corrected
template places an actual line feed there. `parse_launch()` and the remainder
of the production launch, handshake, polling, outcome, retention, and cleanup
logic are unchanged.

The native source and binary remain pinned to the previously reviewed build:
`Program.cs` is
`db45feac5d5bda5e670da51be296cdb39769f898b4d7c8d9224a36cc65e13cdd`
and the DLL is
`4870eed095247b8f5c86a58044e10e8c3682248b4c0465c49e5d4642cb8e54e9`.
All five aggregate manifest rows, the native-manifest pin, and the predecessor
wrapper pin match the files on disk.

The focused regression uses the production `launch_command()` and strict
`parse_launch()` with a harmless local marker supervisor. Its .NET 6
`ProcessStartInfo.Arguments` and `QuoteArgument()` implementation match the
common Samsung root agent's relevant call path. It demonstrates both sides of
the failure: the predecessor emits literal backslash-`n` and is rejected, while
the corrected wrapper emits byte `0a` and is accepted. It does not invoke the
native USB helper or a target device.

I independently ran aggregate verification and the wrapper suite under normal
Python and `python -O`. All four runs passed; each wrapper run reported exactly
20 tests and zero target operations.

## Scope limit

This review clears the framing implementation only. It does not retroactively
classify control-v3's native outcome, prove a ready USB parser boundary, repair
controller state, or authorize a new target launch while that separate state
gate is unresolved. The retained v3 terminal-artifact fetch must be evaluated
on its own evidence before any later controller operation.
