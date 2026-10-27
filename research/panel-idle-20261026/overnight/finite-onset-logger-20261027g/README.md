# Finite onset capture work, 2026-10-27

This is a mutable work block. No physical picture observation or permanent repair is established. The owner permits unattended tests, system changes and flashing if necessary, while requiring that the TV not be bricked. Authorization does not establish firmware compatibility or a recovery method.

## Current checkpoint

V6 captured a controller fault0→1001,31detailed RTP rows and the paired
event736 text. The code trace now connects that numeric event through the
RT1001 setter to hoststatus10/RTProtect; later stockstatus10 and faultpin1
match earlier owner-confirmed blackouts. The ordinary local predicate is
low16accumulator greater than a mode-selected limit. Physical light and a
ForYou transition were unobserved in V6.

The subsequent `fault-context-after-v6/` fixed two-window read passed all
four exact transfers, terminal phase, release/close and stage cleanup. It
retained54/44score latches and five candidate limits200/0/0/200/40 about
32minutes later. The missing event-time mode/alternate selection prevents
choosing among those comparisons. Allfive limit fields match both retained
package and controller-backup initializers. See
`fault-context-after-v6-findings.md`, its reproducible decoder and the
independent runtime review. No helper remains active from these captures;
faultstate remains uncleared.

The sections below preserve the work sequence, including rejected runs and
earlier pending-work statements. They do not supersede the current checkpoint.

The further `selector-context-after-v6/` capture is accepted and cleaned,
with independent runtime audit. Its expected root, aa0/ac2, numeric mirror1,
candidate alternate byte1 and three matching context constants narrow the
late interpretation to a mode1/alternate-limit40 hypothesis compatible with
the earlier score44. The source-byte pair1/3 differs from packaged20/0, and
the separate mirror-control field is0. These values came in separate late
epochs; no event-time comparison or physical repair is claimed. See
`selector-context-after-v6-findings.md` and
`rtp-post-fault-ordinary-gating.md` for the update rules.

## Preserved diagnostic follow-up

`diagnostic-followup-evidence-manifest.json` freezes 75 files / 1,111,428
bytes, SHA256
`4b93587a1062f2611fa0c2cdaeb6b0f7f0ef1fac637693d0003e0e0ed0bd33da`.
It preserves both accepted fixed-read captures, exact reader source/build
copies, completed predicate/count/mode/layout/consistency proofs, corrected
verifiers, the additive frozen-report erratum, and independent source/runtime
reviews. The earlier 84-file and 194-file checkpoints remain byte-identical.
All listed files are now immutable; ongoing work belongs in new files or a
separate block. This README, the incident narrative and the root investigation
entry point remain mutable navigation.

The image-1 code-bus qualification found no proven executable address for a
live logging patch. Its linked code VA and known data-bank mapping must not
be conflated. A separate finite ordinary diagnostic-route search in
`../executing-code-diagnostic-route-20261027h/` is outside this snapshot. No
code read at a guessed address, flash, protection modification or physical
repair has been performed.

`diagnostic-followup-manifest-review.md` independently verifies all 75 file
hashes/sizes and exact inventories, plus both complete 84-file/194-file
parents. It records one metadata-only relative-path typo in the published
manifest's excluded-navigation label; the explicit frozen scope is correct
and the original manifest remains unchanged. The real mutable entry point
is `../../../CURRENT-INVESTIGATION.md` from this directory.

## Established boundary

The frozen D6 qualification proved one finite three-second secondary-log gate operation, exact transport, restoration and cleanup. It did not capture the physical blackout onset. The current native onset candidate adds a ready marker and twenty-second no-USB observation interval; its offline tests do not establish successful deployment.

## Attempt history

1. `control-smoke-once`: staging and 85 fake/self-tests completed on the ARM CLR. Host acceptance incorrectly required a fixed success-output byte length, although the output includes a variable-width PID. The failure occurred before a real execute/launcher request. Supplemental hash-guarded cleanup proves that private stage absent. Original rejected record is preserved.
2. `control-smoke-v2`: a background-launch receipt reported PID2667, but no ready marker, supervisor marker, native result or completion was observed. Later metadata found PID2667 absent and only the four staged inputs. The launcher discarded stderr and used a script pathname. This is an unresolved launch, not an accepted controller execution and not proof of zero USB activity. The supervisor was not fail-closed at its first marker writes. Preserve its remote stage `/tmp/researcher-usb-onset-5e113630055b4e81a0e0b94e5fd52ad6` unchanged. Do not send further controller debug requests, reset it or infer a clean USB phase from absent files.
3. `launcher-qualification-once`: a separate marker-only script passed on the same boot. The launcher closes inherited file descriptors, uses nohup/setsid with shell command content, binds the actual child's PID/start ticks/process group/session, and checks identity twice before acknowledgement. Child6083 ran for3.01seconds, produced the exact seven-file inventory, exited, and its private stage was removed after local artifacts were saved. No native controller helper, USB operation, UI call, signal or reset was involved. This qualifies that launch pattern only and does not resolve attempt2.
4. `ui-apps-control`: the ordinary AppControl helper constructed a request but failed while assigning its contents because `Tizen.Log, Version=4.0.0.0` was absent from its package. Recovered native JSON says `send_attempted=false`, `target_operations=0`, handle disposed. The stock Apps selector was never sent. Its private stage was subsequently removed, verified in `ui-cleanup-after-preflight-failure`. Preserve the rejected package under `ui-rejected-missing-logbuild`.
5. The stock `/usr/share/dotnet.tizen/framework/Tizen.Log.dll` was copied through authenticated read-only transport to the host framework directory. Size10240, SHA256a2b27f2033177328d0d609f8fab47f3c45bc20a0a30b5f29992b142b02fdf66b. The corrected six-file package passed independent review, then root performed one prepare→Apps send→cleanup qualification (`ui-prepared-v2`, `ui-apps-control-v2`, `ui-cleanup-v2`). The fixed Apps API call returned without exception; native construct/attempt/return/dispose flags are true, target_operations=1, and the private stage is absent. Independent raw-envelope/upload/outcome replay is recorded in `ui-apps-runtime-audit.md`. This qualifies the managed API-return path only: no CSFS consumption, rendering, focus or physical light is inferred, and For You has not been runtime-qualified.

## Cached system follow-up

`cached-system-followup.json` retains a read-only boot/uptime/tab/kernel-ring request. Boot remains `00000000-0000-4000-8000-000000000000`, uptime113353.38, selected tab `d/apps.tab`. Cached graphics logs report ongoing GFX VSync and repeatable input histograms. This is software pipeline activity, not proof of physical light emission. No fresh controller status or pin was requested and no panel state is inferred. Repeated SIG11 rows name a .NET thread. Follow-up `/proc` metadata binds thread28637 to running CSFS Home process16097, UID5001, `/usr/bin/dotnet-loader`, command `/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll`. The process remains alive. These rows alone do not distinguish handled CLR exceptions from a UI defect, and are not assigned as the panel-blackout cause without exception context and a coordinated onset. Raw records are `cached-dotnet-thread-identity.json` and `cached-dotnet-process-name.json`.

## Diagnosis that still needs an onset capture

Owner-coordinated earlier samples distinguished visible populated Apps (status0/pin0) from sparse For You persistent black with continuing audio (status0x10/RTProtect, pin1). Full-screen PROGRAM_04 and PROGRAM_B also failed, while overlays and several other titles were working controls. Physical impact damage and a vertical dark line predate software changes. The strongest unresolved question is which controller event changes first at the content transition, rather than whether Linux keeps drawing afterward. The executing callback table matches the selected packaged generation, but whole-image runtime identity and initiating event remain unproved. No flash/protection patch is justified by an identified corrective change yet.

## Next work

The marker-only runtime and Apps API path have passed independent raw-evidence audits. A new wrapper copy `../managed-usb-secondary-logger-onset-qualified` ports the successful launch shape offline with fail-closed startup, child identity binding, inherited-FD closure and retained diagnostics; independent source review found no additional implementation blocker. Its19offline test cases pass normally and with optimized Python, but do not cover the entire planned negative-case matrix; `onset-test-coverage.md` lists the gaps. The native starts after publishing its handshake, before host acknowledgement, so a launch acknowledgement failure remains potentially active rather than proof of no execution. Native controller bytes are unchanged. Establish a defensible clean controller protocol state before any new USB request. `controller-clean-state-options.md` verifies that prior stock mode2 caused USB re-enumeration, but does not prove application-parser reset; it therefore does not clear a new vendor header by itself. Only then qualify an onset capture and pair it with a known UI transition. The previously automatically blocked persisted/high-bank/POFLG branch remains excluded; it is not retried through another worker.

## Preserved runtime evidence

`runtime-evidence-manifest.json` freezes84files /4,515,096bytes, manifest SHA256 `2d1d1427ea37c70e5b6ee37e301488027f6b2a0ff64f7d591884ca6faa252534`. It includes completed target attempts (including failures), authenticated records, marker-only qualification, corrected Apps qualification, rejected UI build and finished bounded audits. Do not rewrite any listed file, even identically. This README, ongoing wrapper review/source work and later captures are excluded. Original failed/ambiguous outcomes remain unchanged. Frozen does not mean accepted.

## Subsequent offline reviews

`qualified-wrapper-review.md` reviews aggregate `aa4fc99a5cd22f86736e49487322b1c6aa6996eae482c8fda3a1971049b386d6`; native bytes remain unchanged. Source has one detached dispatch, actual-supervisor identity binding, retained diagnostics and terminal-only cleanup, with no automatic UI, retry or signal. Launch command7879/8192bytes. This is an offline candidate and has not touched the TV.

`control-v2-launch-lineage.md` reconstructs101authenticated calls, including71read-only polls. It finds no recorded removal of the absent marker/native-output files. The strongest useful inference must be expressed under an explicit no-unrecorded-remover assumption; the old `set -u` supervisor could continue after an early marker write failure. The separate output-redirection ordering is being independently reviewed before any new controller traffic.

## V3 control and exact receipt recovery

A later independent lineage review (`control-v2-lineage-review.md`) accepts no detached managed v2 execute child under the ordinary private-stage/no-unrecorded-remover assumption. Its decisive fact is absence of native.stdout/stderr, which shell redirections must create before exec; early marker absence alone is insufficient. With the complete known normal-session census, D6 ReadyForHeader is conditionally carried forward. Fresh read-only stage hashes and the bounded one-run decision are preserved in `prequalified-smoke-metadata.json` and `qualified-control-execution-decision.md`. This supplements rather than rewrites historical ambiguous records.

Root then launched exactly one corrected control, `control-smoke-v3`. Its target-side live handshake checks passed, but the host parser rejected receipt formatting. RootAgent QuoteArgument doubles textual backslashes, so the generated printf emitted literal backslash-n instead of an LF. The19tests missed this transport interaction; `control-v3-escape-diagnosis.md` identifies the gap. No retry, further USB request, UI action, signal, reset or cleanup followed.

`control-v3-receipt-review.md` independently validates one exact hash-pinned delimiter correction in memory. `control-smoke-v3-receipt-recovery` retains raw and normalized receipts separately and runs the original unchanged parser. It binds dispatch9136, supervisor9140/session9140/group9140/start28569437, same boot, start114277.76 and receipt114278.03. Original v3 record remains unchanged. This proves the same-request handshake, not native completion. Protocol phase remains UNKNOWN pending a separately reviewed bounded read-only terminal fetch after the native deadline. Remote v3 stage remains preserved. A new transport-framing regression/fix is being prepared offline only.

## Recovered native v3 outcome

The initial read-only fetch stopped on an empty-file envelope parser bug after two reads; it did not execute or alter a controller. The original fetch helper and failed record remain preserved. A narrowly reviewed new reader accepts the real seven-line empty-base64 envelope while preserving every framing/count/hash check. `control-smoke-v3-terminal-complete` successfully retained all ten outputs through17read-only root calls and matching before/after metadata; remote stages were not cleaned.

`control-smoke-v3-validated/result.json` independently applies the original native parser and outcome validator, exact READY binding, exit/PID/hash checks, fixed16step sequence, artifact lengths and hashes. The recovered native control is accepted: gate0→1→0,20.08second observation, RT64bytes restored exactly, pre/post fault0, no errors/deadline violation, interface released and FD closed, final ReadyForHeader. This is the finite native control result. The original host-wrapper run remains rejected for receipt framing; no live host READY observation, UI transition, physical picture observation or repair was established. This restores a known completed protocol boundary without rewriting the failed host record.

The secondary ring advanced from11/11/0 to67/67/0, retaining56new bytes: `t[10]`, `t[11]`, `[RTP]Frame end`, `t[12]`, `[RTP:NORMAL][365]`, `t[1]`, each terminated by LF. A new bounded offline trace is following those normal-log callers. The number365 has not yet been assigned a unit or fault meaning. Native control and independent raw-evidence audit are kept separate from static packaged-code interpretation.

The framing-corrected wrapper is separately reviewed at aggregate `b1ffc0f91b614163e10e4132b9410c60116d22101b5666f1614ef471b4938780`. Its only production behavior change emits a real LF in the launch receipt. An actual .NET6 ProcessStartInfo/QuoteArgument regression proves the old framing fails and corrected framing passes the unchanged parser;20offline tests pass. It has not yet run against the TV.

## New primary incident

See `fault-incident-v6.md`: V6 captured RTfault0→0x1001 plus1756new log bytes with31RTP sample rows and two rtp_act_736 lines. Later accepted hoststatus0x10/rawkernelrow and faultpin1 corroborate the technical fault signature. No physical panel observation or ForYou transition was established. All temporary logger gates restored; V4/V5/V6stages and sharedUIstage cleaned. Preserve the fault state; no reset/flash/bypass was sent. New offline traces are focused on the actual sample formatter and action caller.
