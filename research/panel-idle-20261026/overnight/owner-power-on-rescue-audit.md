# Independent audit of the failed-capture rescue

Offline audit performed 2026-10-26. I did not contact the TV, root transport,
network, tracefs, or any display/device API. This report replays only the
already retained host responses and reconstructed sidecars.

## Provenance and result

The rescue helper `rescue-owner-power-on.py` is 6,539 bytes with SHA-256
`93a41e9f97f9398b727a37c5cec53a15078bf044a20a57cd71c8473d51bb5db2`.
Its preparation command has SHA-256
`300013cbdb53b2226ccb99a1f0c1db5defab508223f656ba0a4774dd1a5b4937`.
The helper pins root-client SHA-256
`3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5`.

`result.json` completed at `2026-10-26T21:57:00.897952+00:00` and correctly
retains:

- `copied:true`;
- `original_capture_accepted:false`;
- `physical_timing_unresolved:true`; and
- the still-retained remote rescue directory
  `/tmp/researcher-owner-power-on-rescue-20261026a`.

The failed capture's original local record remains SHA-256
`0bff4bc8ac35966f388f9d5e8867a4ebc98f4794cd6d724f7d1d70c474f18578`.
It remains rejected; rescue does not revise that status.

## Independent transport replay

I replayed the preparation response and all 354 chunk-fetch responses from
their raw intent, stdout, stderr, and result files. For every one of the 355
root calls, I independently required:

- exact intent command SHA and exact equality among intent command, final argv
  argument, and returned command;
- pinned root client, `--persistent-only`, timeout25, and `retry:false`;
- host return0, no host timeout, and empty host stderr;
- model `QN77S95FAFXZC`, host `198.51.100.20`, authenticated true, uid/euid0,
  host-assisted root persistence, and unchanged global system files;
- exactly one returned command with exit0, `timed_out:false`, and empty remote
  stderr.

The preparation response has exact boot
`00000000-0000-4000-8000-000000000000`, exactly seven `FILE` rows in the
declared order, and the completion marker. Each fetch command addresses only
the corresponding fixed gzip member in the private rescue directory, uses a
32,768-byte raw chunk, and has a continuous zero-based chunk index.

For every file I then independently:

1. decoded each base64 response strictly;
2. checked every full/final chunk length and the total compressed length;
3. checked the compressed SHA-256 from the preparation manifest;
4. decompressed with gzip CRC validation;
5. checked decompressed length and original SHA-256; and
6. compared the decompressed bytes exactly with the retained host file.

All checks passed. The retained directory contains exactly the seven declared
files and no substituted member.

| File | Fetch chunks | Compressed bytes | Compressed SHA-256 | Original bytes | Original SHA-256 |
|---|---:|---:|---|---:|---|
| `trace` | 74 | 2,400,273 | `2768dcd6593646064e1db523e2c8ab756860e92beb54a4d6556786c85f2ba800` | 19,310,261 | `44f68ebd1fb301c74cab501a04e84b73b95223e96c977062ed6db0b92977b575` |
| `meta.txt` | 2 | 38,676 | `e60efaa501917602cf1b7283e081982fd29cea9206e54c95eab916637e1b815a` | 254,743 | `3f36476bea2b434e7364ee86f019708290ed118f3123e4b993ba46d573c9ba0b` |
| `samples.txt` | 1 | 3,332 | `b88a7b9e4065d8445d3511217c1425ec3d92065ba0c0b07483e492d7c8247703` | 117,490 | `38931ba5c3eab82233d534e0de39e6cd279835d0b8d559b1e6244b86a8212a2f` |
| `sample-errors.txt` | 1 | 22,608 | `639541a94f32714a90fca1857f39d7ec0a0d3be5ba5e87dc04eaaf79d0c6d059` | 201,684 | `98d132e7f83e86b7d724586d7f73e05898edbf6f578522d4ecd5249b13b11c50` |
| `artifacts.txt` | 1 | 739 | `eea8bf90d4eae94067e902494926d485fe8485fbdacd9e562c905be372bf35d7` | 3,570 | `978bcadf1d6808708f4d0bcff3cdc977f9e95d4cd91dc9c96ec127b4d6181372` |
| `fds.txt` | 1 | 1,316 | `6c4e9346c8185733f9fede7f1092e2d8290469f4ed6e5e70546a17bcfee0b9f9` | 4,690 | `93684e83a3293716db9a5252283a78efbaa2cc12a937eb12e1e04fff7ea11b66` |
| `vlog-after.txt` | 274 | 8,962,367 | `967439baa5904abba6018fc6f4288a19ab4b396dae71f05ba3f0c1e58f0d1a15` | 67,108,864 | `eac02d7bf3a4fb216295edba8be99466d7b80c7a43f7535841f882b052c1c3d3` |

The preparation command hashed every original before gzip and rechecked its
size and SHA afterward. The successful exact manifest therefore binds the
remote originals read during preparation to these host bytes. The remote rescue
copies are intentionally retained until separate exact residue cleanup.

## Bounded capture-runtime interpretation

The capture used exact source
`observed-quiescent-pm-onset-capture.py` SHA-256
`8390e85eff9a40fe774c5e2bd7488ebaaa703c734af20a19fd0a780b58cdc43f`
and rendered remote shell SHA-256
`236a5f93f11c60f18fd7adf36f0818884f2a7e88767af1f79c69f887a510f3cb`.

The recovered trace contains all five owned markers:

- trace armed at event timestamp `73050.982300`;
- pre-roll start at `73051.217140`;
- capture start at `73052.233218`;
- capture end at `73137.840506`; and
- drain end at `73138.033049`.

Its header is `172200/172200` retained/written. The end metadata reports CPU
entry counts `41800`, `41678`, `50124`, and `38598`, which sum to 172,200; all
four CPU records have zero overrun, commit overrun, and dropped events. These
facts establish preservation of this exported trace buffer. They do not by
themselves validate every higher-level pairing or physical interpretation.

`artifacts.txt` has both its baseline and end sections, with the end sampled at
uptime `73141.06`. `meta.txt` reaches PM configuration/source end and all four
per-CPU stats. It does **not** contain the later final blocks for Q-sampler hash,
boot/sync end, capture-window status, AVOC/deviced identity end, pointer/maps
end, script hash end, global-trace end, or vlog semantics. `fds.txt` likewise
stops after pre-roll/FDS data and has no TID/FDS end blocks.

This constrains the collector failure to after trace export and the artifact-end
sample but before final identity/manifest completion. The exact 64 MiB vlog,
the surviving stale `vlog.pid`, and the source ordering make the vlog shutdown
section—and its explicit exit62 on an undrainable vlog process—the strongest
bounded explanation. It is not proven as the sole cause because collector
stdout/stderr contain no explicit exit status or message, and an external
termination at the same boundary is not independently excluded.

Consequently, neither the complete trace markers nor the successful rescue can
upgrade the original run to a technically accepted capture: required end
identity, FD/TID end, pointer/map, vlog coverage, and completion-manifest guards
are absent. Physical timing also remains unresolved; the owner result arrived
after scheduled capture end and was not an in-window annotation.

This report makes no I2C transaction, PM/state, sensing, gate, causality, or
event-absence claim. Those require separate bounded decoding of the rescued
bytes. There is no justification for an automatic capture retry.
