# Code-fingerprint capture runtime review

Recorded 2026-10-27 UTC. This is an independent, offline audit of the single
retained `capture-once` execution. It made no TV, network, root, USB,
controller, device-node, UI, write, reset, or helper-execution request. No
capture or implementation file was modified.

## Verdict

The retained execution is internally complete and consistent with the pinned
reader. It contains one native `--execute` invocation, exactly the three fixed
read requests, exactly six successful USB bulk transfers, successful
release/close, a terminal `ReadyForHeader` phase, authenticated raw transport
envelopes, durable local raw windows, and confirmed target-stage removal.
There is no retry or alternate-address attempt.

All three returned windows are byte-for-byte equal to the independently read
selected-package slices. This establishes the contents of those three
selector-1 mapped views at acquisition. It does **not** establish that a core
was executing them, identify a physical core or PC, prove that selector 1 is
the stored image-1 ordinal, infer whole-image equality, or observe the
physical picture.

No P1 or P2 runtime-record finding was identified.

## Pinned implementation and record

| item | SHA-256 |
| --- | --- |
| build manifest | `550be573257e5d8e726fbf5b4d223a4eeb82e03376edde5dd8062a0eeb37662c` |
| `Program.cs` | `11fc7fd599c502a0f75c38d1c216a0de844dbd9f47e4169e8f57a627b13a081e` |
| `run-once.py` | `d58abdebd1e81f17465e7d0654295e371f01ff750d619e0dbba89344cb84fbf8` |
| pinned root adapter | `bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a` |
| native DLL | `dd7b57b2be34c6a08066d9b9b6b7c53219345853ce74135719189b45577e1c70` |
| `capture-once/record.json` | `0a62bbe117fe9ddae86253e72000db48321b445ff9e8552316178f347bb8d586` |
| `capture-once/result.json` | `3119fb85c08b970794adcdf975313d825c80a301b995e293f2fc5cb458df57c1` |
| execute envelope | `ba198b530a142c57b11aeaab55e1c83b8afb662a1037a9830849bbac49aed8e2` |
| native stdout | `f4a85da709561dc8e849268e18d63b042af9ec580bfebf239a1cae9da45d0408` |
| native stderr | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| self-test stdout | `63bbd601414ef86fff581c4d14aad58033ffcc043949c9c48baa85a7c223a8a5` |

The record pins boot ID
`00000000-0000-4000-8000-000000000000`, terminal uptime
`122877.73 458413.92`, the reviewed manifest and wrapper hashes above, one
native invocation, `no_retry=true`, and `target_operations_status` equal to
`accepted_exact`.

The record contains 20 raw root-adapter calls. Independently decoding every
stored adapter response found one command per response, authenticated root
identity (`uid=0`, `euid=0`), transport exit zero, and command exit zero in
all 20. There is exactly one command containing native `--execute` and one
separate preflight `--self-test`. The latter does not open the device and is
not a second acquisition.

## Fixed requests and exact native sequence

The record's only three target requests are:

| target | address | length | native steps |
| --- | ---: | ---: | --- |
| `0x101` | `0x46001e60` | `0x200` | 12-byte OUT header, 512-byte IN |
| `0x101` | `0x460038c0` | `0x40` | 12-byte OUT header, 64-byte IN |
| `0x101` | `0x4601bb60` | `0x240` | 12-byte OUT header, 576-byte IN |

Native stdout contains ten ordered steps:

```text
open, claim,
window-a-header, window-a-data,
window-b-header, window-b-data,
window-c-header, window-c-data,
release, close
```

Each of the six USB steps reports its exact expected count and errno zero.
The local lifecycle reports opened, claimed, released, and closed. The
terminal fields are `Stage=complete`, `ProtocolPhase=ReadyForHeader`, and
`Accepted=true`. There is no fourth header, repeated header, alternate read,
write, reset, or device-control step.

## Returned bytes and independent source comparison

The selected package is
`F_RSM1_BN9659934B_COMMON.bin`, size `0x500000`, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Image-1 linked VA uses stored FILE offset `0x40200 + VA`. Independently
comparing each retained raw file to that original package produced:

| retained raw file | size | SHA-256 | selected FILE slice | result |
| --- | ---: | --- | --- | --- |
| `window-a.bin` | 512 | `8be303fddfa4aefd0f2d307f05c7522213f8017ae15b374a4fd7178aeca2bb49` | `0x42060..0x4225f` | exact |
| `window-b.bin` | 64 | `0483a632a5e65f8eba8bd623411d6f955705d012c831eac9347e7f9564d944cb` | `0x43ac0..0x43aff` | exact |
| `window-c.bin` | 576 | `035d13a7c17ac9b303ee5739a421a84d0ceec46167d6efce13f4723fc701d9b8` | `0x5bd60..0x5bd9f` | exact |

The native Base64 fields decode to these same files, their declared hashes
match independently computed hashes, and the wrapper's local files match the
native payloads. The result therefore correctly reports
`all_windows_match_selected_package=true` and
`content_comparison=all-windows-match-selected-package`.

The same result also correctly preserves:

```text
transport_accepted                  true
bus_contents_altered                false
executing_code_identity_proved      false
whole_image_identity_inferred       false
physical_picture_observed           false
windows_sequential_not_atomic       true
```

The three exact matches are correlated nonadjacent fingerprints. They are not
an atomic sample and are not evidence of instruction fetch or execution.

## Envelope, local retention, and cleanup

`execute-envelope.txt` binds boot ID, terminal uptime, exit code, stdout and
stderr sizes/hashes, exact five-file inventory, framed native stdout/stderr,
and `EXECUTE_COMPLETE`. Its decoded stdout is byte-identical to retained
`native.stdout.txt`; stderr is empty and matches `native.stderr.txt`.

The wrapper parsed and validated the terminal outcome before extracting all
three raw byte arrays to local `.bin` files. Those files survived target-stage
cleanup. The final authenticated cleanup command required the exact expected
five-file target inventory, revalidated ownership, mode, size, and hash for
every member, removed exactly those members, removed the private directory,
and returned `STAGE_ABSENT`. The record consequently has
`cleanup_required=false` and `cleanup_stdout="STAGE_ABSENT\n"`.

This cleanup followed accepted acquisition and local evidence retention. It
did not erase the host record or raw windows. The execution record contains
no retry, kill, reset, write, UI action, configuration change, or broader
target cleanup.

## Interpretation boundary

The runtime result positively establishes only that target `0x101` returned
the three stated byte sequences, sequentially, and that all three equal the
selected stored-package slices. Window B includes the selected getter at
linked VA `0x38e8`; window C includes the selected low-address mapper,
registry lookup wrappers, roots, and startup initializer. This materially
correlates the live mapped views with the selected build.

It remains unknown whether any processor was executing these bytes at the
time, whether selector 1 names the physical processor/component under
investigation, whether the entire mapped image matches, and whether these
instructions caused the panel behavior. Nothing in this capture qualifies a
write, patch, threshold change, protection bypass, persistence action,
high-bank operation, POFLG operation, or return-guard change.
