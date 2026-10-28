HA is a fixed read-only AP fault-witness reader, authored and qualified on the host only. It has not been run on the TV and is not independently reviewed here. Parent remains the sole target operator. No writer, key, logger change, reset/recovery, MMIO getter, alternate-bank probe, retry or executable patch is implemented.

The production sequence is exactly five read pairs, command0x101:

|Order/name|Fixed source bus address|Bytes|
|---|---|---:|
|start-R|0x47012400|256|
|AP|0x4500f0e0|20|
|AP-EXCO-data|0x4500ff14|12|
|AP-EXCO-context|0x45015924|4|
|end-R|0x47012400|256|

That is5headers/10bulks,60OUT header bytes and548IN data bytes. The three new windows total36bytes. Their exact intervals are **source-qualified/prospective, not previously live-qualified USB/DMA reads**. There is no fallback address or additional header on mismatch. R is the known fixed root window; the bracket is sequential, not atomic or a freeze of source state. This reader accepts transport-complete bytes without assuming the FA Clean/AA0AC2 policy, so current AA0AC3 is not silently coerced. It does not classify arbitrary root bytes as Clean.

`verify-source.py` pins selected package bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0 and checks actual Thumb instructions. Image0 source file offsets are VA+0x200; image1 VA+0x40200. Image0 getter e670/literal e674 supplies2000f0e0, e678/e67c supplies2000ff14, e76c/e770 supplies200158a8; the last window adds the sourced7c offset. The image0 mapper39d4c and image1 mapper1bb74 are identical80-byte spans. Mapper1bb7c branches on tag0, 1bb8a..1bb94 enforce20000000<=pointer<20020000, literal1bbc0 is20020000, and1bb96 adds25000000. All complete CPU intervals and bus intervals are checked: AP ends4500f0f4, data ends4500ff20, context ends45015928, all below45020000. No MMIO4013xxxx interval is admitted. GY inventory27a596fd3094779efbca3616654c774b6520b49f50cd170aea9fd511ec2b5f4b and its exact source trace, plus DW mapper audit and retained selected image, are input-pinned. No OEM binary is copied into HA.

Decoded fields are AP magic halfword+0, reason halfword+0x10; AP_EXCO-data magic halfword+0 and control halfword+8; AP_EXCO-context word+7c and its bit12; and both R stop/fault/ordinary/limit/logger tuples. Image0 b6c4/b6ce compare1234/abcd only for the initial emergency bypass. Backedge b6f8→b6dc does not recheck them. `sampledMagicPairMatchesInitialBypass` describes the sampled pair only: it cannot prove historical bypass, current PC, emergency-loop exit, root reset, reversal of hardware state or physical recovery. A sampled reason16 is not uniquely attributed to this consumer or identified with external kernel EL status. All such stronger flags remain false.

Native `NativeBinding.cs` is byte-for-byte EB. Controller transfer/clock/pending-IN logic is byte-for-byte EB. Accepted full headers still create a matching IN obligation, including clock/deadline failure after the accepted header. A short/exception ambiguous transfer marks Unknown, ends vendor operations and forbids any next header/retry. Release and close are attempted once for owned resources; success requires all five windows, exact terminal ReadyForHeader, no errors and successful release/close. Preclaim native statx/GETDRIVER ENODATA and postclaim own-usbfs device/inode checks are unchanged. ABI is ARM32 little-endian/16-byte transfer; endpoints02/82, usbfs bulk ioctl0xc0105502,2000ms per bulk. No disconnect-driver/reset ioctl is added. The cooperative40second whole budget and4second pair admission remain unchanged; this is not a hard bound on arbitrary OS stalls.

The wrapper derives from frozen EB: dry default; exact native checkpoint/three payload/parser/root pins before import; reviewed manifest digest; new HA readiness schema with all16 exact cached identity fields, no-holder census and explicit parent closed-world first-header premise. Those fields do not prove an empty endpoint queue or continuous no-holder state. It checks metadata before staging, before invocation, immediately before native and afterward. Native opens the exact current device selected by readiness, never a discovery scan. Parent's USB70/boot00000000-0000-4000-8000-000000000000 is retained context only; fresh readiness is still required.

Stage prefix is `/tmp/researcher-ha-` plus32hex; production native receipt validates root-owned0700 directory and exclusively creates0600 fixed selftest/native receipt files. Host build/tmp/caches are under HA/host-environment on the main disk. Production native JSON is read from the exclusive receipt, separately framed/bound by byte length/hash from GC diagnostic stdout. The new receipt/envelope/schema family is HA. Native output cap24576, diagnostics16384/2048, root envelope65536, root command8192, remote/host45/75seconds remain unchanged. Retained successful artifacts are checked against all9 exact staged owned files before deletion; accepted cleanup requires STAGE_ABSENT. Any refusal/ambiguity retains the stage and raw response; no second native invocation or automatic cleanup/recovery follows. This preserves the primary terminal evidence for separate parent reconciliation.

Qualification passes516 native checks;65 direct source/equivalence checks;978 host parser/wrapper checks across269 mocked shell commands, maximum7734bytes. All source/host qualifications match normal/-O. The host wrapper uses the actual retained16-field USB70 identity only inside explicitly synthetic transport/payload mocks; it is not new live readiness or an actual AP capture. Native tests cover every ten bulk positions with short/exception, preflight/binding/claim/release/close failures, clock faults, deadline-before-header/noOUT, and deadline-after-full-header/completeIN/refusal. Parser tests cover missing/duplicate/malformed fields, exact packet/window/count/hash/phase requirements, false cleanup, old family, and unsolicited MMIO addresses. Wrapper tests cover staged integrity/caps, one native invocation and refusal retention. `host-build-checkpoint.json`, `input-pins.json`, deployment manifest and source inventory bind the results. No optical or recovery claim comes from a host fixture.

Reproduce locally without target calls:

```bash
python3 -B verify-source.py
python3 -B -O verify-source.py
python3 -B test-runner.py
python3 -B -O test-runner.py
```

`sh build-host.sh` rebuilds under this directory; do not rebuild or regenerate checkpoint after independent freeze/review. SDK/NuGet configuration uses only existing local SDK and clears package feeds. Runtime is the same accepted stock dotnet/CLR family; wrapper pins /usr/bin/dotnet SHAe5840c05...73310. No whole-runtime loaded-byte attestation is implied.

The frozen manifest SHA256 is **727a80b6091c8a58b297cec50cab103ee4e13873528c7475544ef2b9a3626437**. Wrapper SHA256 is **5d1af2292602df25f0bd84e4ea27e1894356e677daf2d2b81aaecb55bb305492**. Default `python3 -B run-once.py` performs no target work; `--print-manifest` is local only.

Parent first authors a new explicit phase note binding the latest accepted same-instance terminal receipt, knownReady/released/closed/stage absent and no intervening vendor commands. After independent review, fresh HA readiness can be prepared with the existing serialized root adapter:

```text
python3 -B prepare-readiness.py --wrapper ha --wrapper-sha256 5d1af2292602df25f0bd84e4ea27e1894356e677daf2d2b81aaecb55bb305492 --identity /ABS/FRESH-IDENTITY.json --phase-note /ABS/HA-PHASE.md --evidence /ABS/LATEST-ACCEPTED-RESULT.json --output /ABS/NEW-HA-READINESS
```

That preparation is itself one ordinary cached metadata root request, no vendor transfer. Use its returned readiness path and digest, then invoke the fixed capture once:

```text
python3 -B run-once.py --execute --manifest-sha256 727a80b6091c8a58b297cec50cab103ee4e13873528c7475544ef2b9a3626437 --readiness /ABS/NEW-HA-READINESS/readiness.json --readiness-sha256 RETURNED_DIGEST --output /ABS/NEW-HA-CAPTURE
```

All `/ABS/...` paths must be concrete new private parent locations. No live step above was executed by the author. This is a small new RAM witness to inform the ForYou/Apps recovery work, not an admitted recovery operation.
