# Independent launcher-qualification runtime review

## Conclusion

The single marker-only run in `launcher-qualification-once` is accepted as a
qualification of the reviewed detached shell launcher on boot
`00000000-0000-4000-8000-000000000000`. It does not qualify the managed USB
helper, establish the controller protocol phase, observe the physical panel,
or authorize a controller retry.

The reviewed qualifier source was SHA-256
`74d964fa6e80d4834409d4e3b86998c729203c8448a5237b6139e8a7649e87d0`.
The final runtime files have these SHA-256 identities:

| File | Bytes | SHA-256 |
|---|---:|---|
| `record.json` | 63,313 | `6e94e58bb1336af457c342c8501f659eb5b4d0269f6345f7435b1e93a11d0555` |
| `result.json` | 1,356 | `610a87d31cde59520f426300732c51b3c807173a6b04623a0429029b04b4783a` |
| `artifact-manifest.json` | 979 | `69d1b4e099d53aa910f00d6771c3601404f7268f1a50a5db63b3f0603e610ca4` |
| `launcher.stderr` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `launcher.stdout` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `marker.done` | 69 | `bb9a525b2e88bffe58914177ebf032f1014ad54c985420402fdfd9fe7a4cd375` |
| `marker.pid` | 5 | `ffcd61ab93d039004013e21a9c1d6d4dcaae9dfd8b2a1322ed621ec82b270db7` |
| `marker.sh` | 926 | `d78ad2763a557b41c37cb6dec17431d1163dc24509aaa6fdfdb6b64f7ae2beb7` |
| `marker.start` | 69 | `fe60854353e24aefca7d6ffc1e895c690b4fdf42ea1c86915d0efa5160c7a972` |
| `marker.stat` | 250 | `8d3e43810482d325fbb2f5f82688388a1ef62bec04201c9625aa8dd1b505ebb5` |

## Raw-envelope and lifecycle audit

The record contains exactly four calls: stage, launch/handshake, terminal
fetch, and exact cleanup. Their command sizes are respectively 2,397, 3,818,
3,776, and 5,077 bytes, all below the 8 KiB bound. Reconstructing all four
commands from the reviewed source, the recorded random stage, and the fetched
artifacts produced byte-for-byte equality with every recorded command.

Each call has one authenticated uid/euid-0 result, exit code zero,
`timed_out=false`, empty command stderr, no host timeout, transport exit zero,
and a 45-second remote/75-second host limit. Decoding each retained outer
transport envelope reproduces its stored `response` object exactly. Start and
finish timestamps are ordered and non-overlapping.

The receipts are exact:

- stage: `STAGE_READY`;
- launch: `LAUNCH_ACK 6079 6083 28325994`;
- terminal fetch: seven ordered base64 artifact frames followed by
  `PID_MISSING`;
- cleanup: `STAGE_REMOVED`.

Dispatcher PID 6079 is not used as the worker identity. The marker published
PID 6083, and the retained stat row independently decodes to PID 6083, state
`S`, process group 6083, session 6083, and start ticks 28325994. This is the
expected `setsid -f` relationship. The launch request validated the same live
identity before its acknowledgement and again after 200 ms. Terminal fetch
then established that PID 6083 no longer existed.

The start and done records have the same boot ID. Their monotonic values are
113303.98 and 113306.99 seconds, a 3.01-second interval within the reviewed
2.5-to-10-second bound. Both launcher streams are empty. The fetched marker
source is byte-identical to the source generated for the recorded random
stage. The artifact manifest and result reproduce every fetched size and hash.
`terminal_valid`, `qualified`, and `cleanup_verified` are true; the final
record has `cleanup_deferred=false` only after the exact cleanup receipt.

None of the four reconstructed commands invokes dotnet, a managed logger, a
USB device node, an AppControl request, or a UI action. This run therefore
supports `target_device_operations=0` for the qualification itself.

## What could establish a known USB protocol state

This launcher success does not retroactively classify `control-smoke-v2`.
There are only two non-controller ways to recover a known protocol-state
claim:

1. Establish a closed-world no-transfer lineage from the last accepted
   `ReadyForHeader` boundary. The lineage would have to bind the accepted D6
   result (`ProtocolPhase=ReadyForHeader`, exact restore, release, and close)
   to the same uninterrupted boot, enumerate every intervening authenticated
   command, and prove that none could submit a controller transfer.
2. Use transport evidence that was already active at the time, such as a
   complete host-side USB trace or cumulative counter with a pinned pre-v2
   baseline, to prove that no endpoint transaction or reset occurred after
   that known boundary. Starting a passive trace now can protect future
   experiments but cannot reconstruct the missing interval.

The v2 filesystem evidence can materially support the first route. Its
supervisor command redirects native stdout and stderr before the shell can
execute dotnet. On a root-writable private stage, reaching that command would
therefore create `native.stdout` and `native.stderr` even if dotnet itself
failed immediately. The later exact four-input inventory contains neither
file, no supervisor marker, and no completion file. To promote that from
strong evidence to a closed-world proof, an audit must additionally establish
that no command or other actor removed those files, bind the exact staged
supervisor bytes, cover the full interval from launch through the inventory,
and account for every other process capable of using the same USB interface.
The supervisor's former `set -u` rather than `set -eu` prevents the missing
PID/stat markers alone from proving that execution stopped before dotnet.

A post-hoc read of ordinary process state, sysfs, or kernel logs can rule out
some alternatives, such as a recorded bus reset, but cannot directly reveal
the firmware parser's current header/payload phase. Querying that phase over
the controller endpoint would itself be controller traffic. If the
closed-world no-transfer lineage or a contemporaneous complete transport trace
cannot be produced, the protocol state must remain unresolved; absence of a
current helper process is not sufficient.
