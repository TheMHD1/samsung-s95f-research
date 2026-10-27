# Managed fixed NPC_AP divisor reader

Offline-built, dry-by-default ARM32 helper for one fixed read-only target
`0x101` request. It sends header
`0101000030d7004508000000` and requires one exact eight-byte response from
candidate selector-zero bus address `0x4500d730`. There are exactly two USB
bulk transfers, no retry, no write, no reset, no dynamic address, and no UI
operation.

The response covers candidate `NPC_AP` object offsets `+0x14..+0x1b`.
Halfwords at response offsets `0,2,4,6` are reported as context `+0x14` and
the three inputs at `+0x16/+0x18/+0x1a`. These labels are conditional on the
qualified selector-zero mapping. The helper has no live NPC pointer identity
gate and never treats packaged default values as proof of identity.

The native engine inherits the pinned USB identity, descriptor, FD,
claim/release/close, fixed-header, timeout, and fail-closed protocol phase
checks from the reviewed W reader. It records monotonic timestamps immediately
before the OUT header and immediately after the IN ioctl returns. If an IN
call returns a positive short count no greater than eight, the returned prefix
is retained separately but is never decoded or accepted. An overcount is not
reported as a valid prefix. An exception or nonexact transfer leaves protocol
phase `Unknown` and cannot issue another vendor request.

`run-once.py` is dry unless all of `--execute`, a reviewed manifest SHA-256,
and a fresh absolute output directory are supplied. It stages only the three
pinned .NET runtime files, runs zero-I/O self-tests, invokes the native helper
once, retains the authenticated envelope and native stdout/stderr, and cleans
the private target stage only after a strict exact terminal outcome. Any
ambiguous/rejected execution is not retried and preserves the target stage and
host evidence for review.

Build and focused offline verification:

```sh
python3 build-offline.py
python3 test-wrapper.py
python3 -O test-wrapper.py
```

No script in this directory has been used against the TV during this build.
