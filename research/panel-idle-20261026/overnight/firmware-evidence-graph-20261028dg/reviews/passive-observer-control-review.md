# Existing passive observer for an automatic Apps control

Verdict: no blocking source/lifecycle defect found for this fixed no-key observer when the central coordinator separately records its fresh first-header, USB identity and sole-ownership qualification. It can supply a finite Apps software-stability control after recovery. There is no owner confirmation, prompt or physical-verification gate. This review performed no TV, root-client, USB, GPIO, key, reset or network operation and introduced no controller code.

## Exact existing invocation

Dry local inspection:

```sh
python3 managed-usb-rt-passive-observer/run-once.py
```

The existing live CLI, for use only by the central device coordinator, is:

```text
python3 managed-usb-rt-passive-observer/run-once.py --execute --manifest-sha256 915d19e20d7e5e7fc81a1962cec150ef17f2d00229277666918d199e755d2fe1 --output /ABSOLUTE/FRESH/OUTPUT
```

These are the only three live options: execute, reviewed wrapper-manifest digest and a fresh absolute host output directory. There is no key, arbitrary address, duration, reset, readiness, owner confirmation or UI argument. Native invocation is exactly the fixed three-file assembly with `--execute`. Native default invocation is dry; `--self-test` uses FakeOps; unknown arguments refuse; live execution requires ARM32 little-endian16-byte usbfs ABI. The frozen wrapper uses its existing qualified `/usr/bin/dotnet` launch; it has not been rewritten here.

## Readiness and first-header premise

Unlike the later DF synchronized recorder, this wrapper has no readiness-JSON schema, full FD census or closed-world vendor-OUT lineage check. It cannot independently establish that a fresh header is safe. Native `Run` initializes its protocol state to ReadyForHeader. Before dispatch it checks boot, active USB status, IDs, complete descriptors, configuration1/authorized1, unbound interface2/alternate0/vendor class, bus7 and a dynamic device number1..127. It opens the exact derived usbfs character device with ARM nofollow/cloexec flags, verifies major/minor and cached device descriptor, rechecks native metadata and claims interface2.

Those checks establish its stated identity/open/claim conditions, not endpoint queue freshness or absence of another independently opened reader. The central record must carry the actual recovery/disconnect/re-enumeration lineage, the new device identity, zero-holder/error census and sole ownership through the observer. Cached Apps alone establishes neither USB phase nor physical visibility. Do not reuse a prior device number or a stale readiness premise after another vendor request. There is no extra first-header probe in this wrapper: first vendor request is its ordinary fixed R header. The separately coordinated current recovery can supply that premise if the retained lineage actually supports it; this review does not invent that evidence.

## Bounded no-key behavior

Fixed production bounds:20-second monotonic observation, maximum80 cycles, nominal250ms cycle period,2-second timeout per bulk call. Each full cycle is R256/M68/C16/H96/L64/R256 at the frozen addresses. The helper performs no key, UI, reset, gate, threshold write, arbitrary-memory access, vendor payload write or retry. Its OUT transfers are the required read-request headers.

Every exact12-byte accepted OUT is followed by exactly its matching IN, including when the monotonic deadline expires or a clock read fails between the calls. Only an exact IN length restores ReadyForHeader; ambiguity/short/failing transfer forbids any following header. A current pair can overshoot the observation deadline by at most the requested two2-second calls under normal kernel timeout behavior. This is a bounded attempt, not a guarantee against an uninterruptible kernel/native call. Existing remote45-second/host75-second limits remain; no new native alarm was added.

A clean first R permits repeated observation. Fault0x1001/stop1/gate0 at initial R returns AlreadyFaulted after one post set, explicitly missing onset. A new fault at R-end or next R-start retains transition plus one post set and stops. An unexpected tuple stops and rejects. Therefore this helper does not promise20seconds of traffic after a fault; early stop is intentional. For a clean stability conclusion retain accepted clean TimeLimit/CycleLimit, actual start/end timestamps, clean/global counts and all retained R bytes. CycleLimit is a finite80-cycle control and must not be renamed a measured20-second interval without its times. Neither accepted clean nor accepted fault proves emitted light or exact physical onset.

## Receipt, counts and cleanup

The wrapper locally pins the complete wrapper/native manifests and exactly three deployment files before loading the root adapter. It creates a fresh root0700 stage, uploads fixed0600 payloads, verifies inventory/hash/mode and runs75 zero-I/O native self-tests. Native execute is recorded as one inflight-or-unknown invocation before dispatch; there is no replay. Foreground stdout<=24576/stderr<=2048 return through the bounded authenticated envelope. Authenticated bytes are saved before interpreting exit/JSON. GC handling accepts at most32 bounded exact-prefix diagnostic lines; unexpected/interleaved output rejects rather than being silently repaired.

Accepted result parsing requires terminal ReadyForHeader, opened/claimed/released/closed, no errors, exact native schema/counters/role sequence/raw hashes and R tuple decode. Maximum accepted headers485/bulk970 covers80 full six-read cycles plus one five-read post set. The native accepted-transition counts distinguish one-read R-start from six-read R-end. Last-clean rolling retention is intentional; discarded clean cycles remain in global counts. All windows remain sequential/non-atomic.

Cleanup occurs only after accepted exact native receipt, rechecks the complete known stage inventory/size/hash/mode, removes only the three payloads plus two native output files, and requires STAGE_ABSENT. Transport/receipt/parser/cleanup failure remains a rejection with retained records/stage and unknown action count where appropriate. A successful operation or cached Apps state cannot rehabilitate a rejected lifecycle record.

## Independent host verification

The unchanged wrapper/native manifests and all local contract entries passed `load_contract` without importing the root adapter. The exact frozen native DLL passed75 FakeOps self-tests with largest10541-byte output. The wrapper suite passed55 checks normally and55 with Python optimization, using fake root calls and generated shell validation only. No build scripts were run or frozen files changed.

Reviewed original pins:

- `run-once.py`: `a4146bc302a764f476e068f456398b8dc34a6e3cc480b876f6e44ed65098cc82`
- `Program.cs`: `0edd0363c0969e3abc1d69c9116e2b06c9414632a069a78a767379f1cd19887e`
- `root-with-margin.py`: `e69b79a103931c4eecca6f6f505975acdd8f9de2e1e8189b8321dd77d8bc6938`
- `wrapper-build-manifest.json`: `915d19e20d7e5e7fc81a1962cec150ef17f2d00229277666918d199e755d2fe1`
- `native-build-manifest.json`: `44f74a8a695f41ed21d68a7a36e13934eebc74050bf991c634e6015ec88043a2`
- `bin/Release/net6.0/ManagedUsbRtPassiveObserver.dll`: `ffcba3f95040114a4ee3c6476a2d686d9e874d198898d678707ccc31b1cf6e2d`
