# Offline QD command evidence decoder

`decode-qd-trace.py` consumes an already acquired ftrace text file; it has no TV access or write interface. It outputs a `.qd.json` file with raw message bytes, timestamps, task/thread identities, direction/flags, I2C result, capture completeness, known command labels, and a short mute/frame/VRR focus list. It fingerprints the input file. A Linux result equal to the requested message count means only `all-messages-reported-transferred`; it is never classified as MCU acceptance or physical recovery.

Example, on the controller:

```sh
python3 decode-qd-trace.py passive-black-i2c.trace
python3 test-decode-qd-trace.py
```

Each I2C transfer closes at its own `i2c_result`, keyed by issuing thread and adapter. Payloads/replies from another thread cannot silently complete a transfer. Missing indices, payload-size mismatches, missing replies/results, inconsistent direction flags and repeated indices are retained as incomplete evidence. An unfinished transfer is closed explicitly at capture end or a new index0. Results from a filtered-out address have no associated payload and remain orphan results; they are not assigned to a nearby QD command.

Semantic labels require adapter5, all observed messages at address0x76, a structurally complete transfer, exactly six command bytes beginning F3, and a known operation form. Labels come from the matched QDF functions, not arbitrary packet-name guesses. Every output retains raw bytes. A handshake response remains undecoded here; its scalar is not renamed a panel fault/status. Unknown selectors remain unmapped.

Before semantic pairing is trusted, the decoder requires the retained and written ring counts to match **and** requires that retained count to equal the number of recognized event lines in the exported file. A separate `semantic_capture_complete` field additionally requires all known I2C event bodies to parse. Parse errors are retained and suppress semantic labels across the capture. Thus overflow, truncation, missing accounting, unsupported event-line formats or malformed known I2C bodies cannot produce trusted semantic labels. Unsupported raw QDF transaction shapes remain raw evidence; only the recovered two-message command/payload or command/read forms are named. The original acquisition's remote-size/SHA checks remain separate evidence; a local input SHA alone does not prove a complete remote transfer.

## Results on retained samples

- `passive-black-i2c.trace`:739/739 events recognized, four complete I2C transfers, no focused mute/frame/VRR operation. It contains two command-status handshakes, power-query preparation0x174 payload1, and power-result read0x0d reply00000001.
- `passive-black-output.trace`:349/349 events recognized, four complete I2C transfers, no focused mute/frame/VRR operation.

These are short post-onset samples without a fresh simultaneous physical-screen report, not onset captures or evidence that a mute command never happened. An empty focus list does not establish a physically unmuted panel.

Fourteen integrity tests pass: real retained capture bytes, unmute-zero payload labeling without an acceptance claim, negative Linux transfer result preservation, ring overflow, truncated export, missing read reply/result, interleaved thread separation, length mismatch, missing write payload, malformed known I2C event bodies, incompatible command/payload directions for both read and write forms, and mismatched read-reply flags. They verify decoding/evidence behavior; they do not exercise TV hardware or diagnose its failure.

## Sensing-control evidence

Exact copied-code review supports neutral labels `off-sensing-control` for
F3:0180 and `EL-sensing-control` forF3:01a0. These go in a separate
`maintenance_focus` list so they can be correlated with mute/frame events.
Payload1/0 is a control request, not proof of active or completed sensing.
Both setters' input1 routes first request frame-mode0, wait500ms, issue the
sensing command and later enable command skip. Fourteen tests now pass; the
new fixture checks both labels/payloads without an acceptance/active claim.
The two retained samples still contain four transfers each, no focused
mute/frame commands and no maintenance-control command.

## Dimming requests added after the content/duty audit

The [exact QDMNT backend](../tcon-research/qd-content-duty-policy.md) builds
`F3 00 00 00 01 28` as a dimming-level request, distinct from power/mute.
The decoder now labels0x128 and adds `dimming_focus` for0x128,0x140 and the
0xc0/0xc4/0xcc/0xd0 screen-saver family. Each item retains raw request/reply
bytes and scalar values; no luminance, physical state or MCU acceptance is
inferred. This supplements the existing `focus` and `maintenance_focus`.

Sixteen fixtures pass. The additional fixtures verify raw duty/SS scalars
and failure to name an incomplete dimming transfer as semantic evidence.
Both retained traces were decoded again: four complete transfers each,
no parser errors and all three focus lists empty. Neither is an onset capture.
