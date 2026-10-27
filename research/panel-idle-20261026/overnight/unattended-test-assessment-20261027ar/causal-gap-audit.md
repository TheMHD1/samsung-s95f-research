# RT fault-to-emergency causal gap audit

Recorded 2026-10-27 UTC. This is a read-only audit of existing retained
evidence. It made no TV, root-agent, network, USB, device-node, build,
instrumentation, debugger, controller, UI, playback, firmware, MMIO, storage,
or configuration call. It does not continue the rejected recorder and does
not enter protection-bypass, return-guard, high-bank, storage, or bootloader
analysis.

## Bottom line

The strongest supported conclusion is a **conditional software chain with
observed endpoints**, not a fully observed causal timeline:

```text
observed during V6:
  image-1-style event 736 signature
  bus window fault 0 -> 0x1001

selected image-0 ordinary code:
  poll low bit of bus 0x4701240a
  -> common error selector 0x10
  -> selector-specific emergency action and exact MMIO writes
  -> common status halfword = 0x0010

observed 164.25 seconds later on the same Linux boot:
  host F3:80 selector 8 result = 0x00000010
```

V6 directly proves the first endpoint. The packaged image-0 bytes prove every
ordinary control-flow edge in the middle. The later host result proves the
last endpoint. What is not proved is that image 0 consumed the V6 transition
during the intervening interval, rather than the status field retaining a
selector-`0x10` value from another entry. No event-aligned image-0 log or PC
sample closes that attribution.

The chain also stops before physical causality. Exact writes to four
controller-local MMIO addresses are established, but no retained datasheet,
register map, schematic, or signal observation identifies them as panel
enable, rail, reset, PWM, timing, scan, or pixel-output controls. V6 had no
human observation of emitted light. Therefore the evidence supports a real
controller fault and emergency software path; it does not prove that this
path turned the OLED panel black.

## Strongest proof, layer by layer

### 1. V6 observed a fresh technical event

The accepted V6 interval at uptime `115887.39..115907.45` began with bus
window halfword `0x4701240a == 0` and ended with `0x1001`. The secondary ring
advanced by exactly 1,756 bytes and ended with exactly two lines:

```text
rtp_act_736
rtp_act_736
```

The diagnostic changed only logger gate `+0x2406`, then restored it to zero.
The independent event flag, fault halfword, and ordinary gate changed
`0/0/1 -> 1/0x1001/0`. All native transfers completed exactly and cleanup
returned the protocol to `ReadyForHeader`.

This is fresh controller-state evidence. It is not merely a later retained
fault read.

### 2. The selected image-1 path matches every captured side effect

The selected image-1 predicate tail executes, in order:

```text
compare low16(A[mode-1]) with selected threshold
if greater:
    0x1c0c8(mode, 4)   ; OR action bit 4 into a mode bucket
    0xc1e0(736)        ; common setter
```

Setter `0xc1e0` stores root fields `+0x2400=1`, `+0x240e=0`, and
`+0x240a=0x1001`, then makes two calls using the same
`rtp_act_%d\n` format. Those values and the two output lines match V6
exactly.

The later N code-view read returned the full predicate neighborhood at bus
`0x46001e60`, 512 bytes, SHA-256
`8be303fddfa4aefd0f2d307f05c7522213f8017ae15b374a4fd7178aeca2bb49`,
byte-identical to selected/current stored image 1. This strengthens identity
for the predicate and its event-call tail. It does not fingerprint setter
`0xc1e0`, prove which core's PC executed the mapped view, or establish a
physical panel outcome. For the setter, the runtime evidence is the coherent
store-and-two-log signature rather than a live code-byte read.

### 3. Action 736 is not itself the emergency output action

The first helper, `0x1c0c8(mode,4)`, only performs a halfword read/OR/write to
one of the mode buckets at root `+0x2486/+0x2488/+0x248c`. It contains no
MMIO, output call, or cross-image dispatch. The late mode-1 bucket contains
bit 4, but no pre-V6 bucket read proves that mark was fresh, and four selected
event sites can set action bit 4.

The two `rtp_act_736` lines likewise prove that both logger calls ran; they
are not acknowledgements from image 0. The actual image-0 ingress is the low
bit of fault byte `0x4701240a`, not the action-bucket bit.

### 4. Image 0 contains an exact ordinary consumer and emergency entry

Selected image-0 poller `0x214d4..0x21511` reads the low bit of bus byte
`0x4701240a`. If set, it emits `RT-P activate!` and calls common error entry
`0xb660` with selector `0x10`.

For selector `0x10`, `0xb660` executes in this order:

1. interrupt/resource teardown, including six runtime-selected NVIC
   clear-enable operations;
2. selector action `0x14910(0x10)`;
3. common selector store `0x2b764(0x10)`.

The action clears a second-object halfword, calls `0x25b24(1)`, writes
`0x10` to `0x4013400c`, and makes the already-excluded persistent-service
calls. Inside the retained ordinary MMIO portion, exact stores include:

```text
0x40130010 <- 0x00000008       (earlier helper)
0x40132010 <- 0x00000200       (conditional earlier helper)
0x40132010 <- 0x00000080       (final 0x25b24 path)
0x40131010 <- 0x00000004       (final 0x25b24 path)
0x4013400c <- 0x00000010       (selector action)
```

The common selector store occurs after that action and overwrites the full
low 16 bits of `common_object+0x10` with `0x0010`. Thus, if a selector-10
entry is known to have produced the field, the action executed far enough to
reach all preceding ordinary operations. Static code alone does not say when
that happened or what the MMIO blocks physically control.

### 5. Host selector 8 reads the exact stored field without clearing it

The selected wire path for `F3 80 00 00 00 08` is exact:

```text
wire f3 80 00 00 00 08
 -> command 0xf380, selector 8
 -> image-0 dispatcher 0x21624
 -> selector table 0x21df8, case 8
 -> LDRH common_object+0x10
 -> reply 00 00 00 10
 -> host byte reversal -> 0x00000010
```

The selector-8 case performs no clear, acknowledgement, or other store. A
later accepted same-boot status invocation at uptime `116071.70` returned
`0x10` and has a matching QDF kernel line. This is positive host-visible
evidence of a selector-10 value, not merely a matching label.

It is still delayed evidence. V6 ended 164.25 seconds earlier, and the common
field's complete lifetime has not been proved.

## Origin confounders for the delayed `0x10`

The selected direct-call census contains three calls to `b660(0x10)`:

| Call site | Selected ordinary context |
|---:|---|
| `0x9834` | first condition in EEPROM-labelled RT check `0x97e8` |
| `0x9862` | second condition in the same EEPROM-labelled check |
| `0x214f2` | recurring `+0x240a bit0` poll |

The two EEPROM calls are not arbitrary recurring call sites: their enclosing
function has a sole direct caller in the pre-loop sequence. The recurring
poll has a sole direct caller in a block with a back edge. This makes the
recurring poll the selected direct runtime candidate for a post-startup
fault, but it does not by itself attribute the delayed field:

- selector 8 is non-clearing;
- `common_object+0x10` is an overwrite field, not a timestamp;
- the existing reports explicitly do not provide a whole-firmware
  writer/clearer and reset-lifetime proof;
- computed calls, passed aliases, another image, and different executing
  bytes are outside the direct census; and
- no event-aligned `RT-P activate!` or `System Emergence!!` record was
  captured.

An earlier same-boot getter returned zero before V6, but that record lacked a
raw controller transaction proving a successful underlying transfer. It is
useful context, not a strict proof that the common field was definitely zero
immediately before V6.

The controller-local common error text is formatted into the `0x20205000`
ring and drained toward controller-local UART MMIO. Existing UART/DT audits
found no proved host receiver binding for that route. Absence of those strings
from retained host logs therefore cannot be used as evidence that the image-0
entry did not run.

## Physical and incident confounders

1. **No V6 light observation.** The owner was asleep; a returned UI request
   and compositor state are not emitted-light measurements.
2. **No synchronous middle observation.** The image-1 event and host status
   are separated by 164.25 seconds; neither the image-0 poll nor the MMIO
   writes were sampled at event time.
3. **MMIO semantics are unnamed.** Exact addresses and values are known, but
   no retained primary hardware description binds them to panel output.
4. **The panel is physically damaged.** A controller protection response and
   a hardware collapse can correlate without the software command being the
   immediate cause of darkness.
5. **Technical and physical incident corpora are disjoint.** V6 has a fresh
   `0->0x1001` technical transition without physical annotation; owner-visible
   Apps/Live/PROGRAM_LABEL/program_b cases lack an event-time RT halfword.
6. **Later retained values are not event operands.** Mode buckets, score
   latches, thresholds, and selector state read minutes later are consistent
   with possible modes but do not recover V6's atomic `mode/r7/fp` tuple.
7. **Executing identity is local, not complete.** The predicate view matches,
   callback generation matches, and runtime behavior matches the package;
   no whole-image checksum or core-PC trace proves every middle instruction
   executed exactly as stored.

These limits prevent promoting “RT fault causes black panel” from a strong
working hypothesis to a demonstrated physical mechanism.

## Remaining offline control-flow work

No genuinely new decisive ordinary control-flow question remains after the
reviewed T action-causality trace, status-wire proof, pre-loop/recurring caller
census, UART boundary audit, and N predicate fingerprint. Further arithmetic
or another constant/caller census would duplicate completed work and cannot
establish event-time execution or hardware meaning.

One narrow **already documented**, not new, source question remains:

> Is `common_object+0x10` initialized, cleared, or overwritten anywhere
> outside the coherent `0x2b764` setter path, and what is its reset/pre-loop/
> recurring-loop lifetime?

A finite selected-image writer/clearer and initialization census could improve
the interpretation of delayed selector-8 results. In the strongest favorable
case, proving a post-pre-loop zero followed by `0x10` and excluding other
coherent writers would make the recurring poll the only selected direct
post-startup producer. In the unfavorable case, proving no later clear would
leave a pre-loop selector-10 value able to persist. Either outcome would still
not identify the MMIO hardware function or prove physical blackout causality.

Because this question is already explicitly identified in
`qd-profile-rt-status-wire.md`, it does not satisfy the request for a genuinely
new bounded static question. This audit therefore does not invent another.

The single next causal question is:

> During a user-confirmed visible-to-black transition, does the image-0
> recurring poll enter its selector-`0x10` arm at the same time as the fresh
> RT transition?

That question needs current physical-light feedback plus event-aligned state;
it cannot be answered by another unchanged late-state read, a blind power
toggle, or more constant arithmetic. A primary register map could separately
name the MMIO function, but it would not replace this timing test. No such test
is initiated or designed here. This is the present readiness limit.

## Evidence reviewed

The principal already-reviewed inputs are:

| Evidence | SHA-256 | Contribution |
|---|---|---|
| `rtp-action-causality-20261027t/rtp-action-causality.md` | `4465ca1a50b9c4a851cf0233a4172e930987b1b1dec7f1b7d3972e264755dbb5` | corrected end-to-end software causality and competing origins |
| `current-host-health-20261027v/ordinary-trace-reviews.md` | `468a9963db6a20871fa0215bb1ced9e4810b44654b31b14acfa756c10a0710aa` | independent correction/clearance of T |
| `finite-onset-logger-20261027g/rtp-act-736-trace.md` | `9f14ed08477b252ceb62a4af8386bdacd222a3948c17c1f089323e398b815f16` | V6 transition, setter match, wire boundary, timing |
| `finite-onset-logger-20261027g/rtp-736-predicate.md` | `2ea99e5cf5e77ec25e0a82b685b090c9e66487dada4eccc0b0c749564af88348` | exact image-1 predicate and missing atomic operands |
| `code-map-qualified-followup-20261027n/capture-findings.md` | `7b5c7b8281f717790976866197711ec2abf28c3f0bd1dc4164d433cbf7d39ba5` | exact predicate-view byte match and identity limits |
| `executing-image-identity-20261027e/current-fault-path.md` | `f8eb48cd056a54a932969380272df887e91a12cd05322e1f189b3f2785f18026` | pre-loop versus recurring image-0 callers |
| `tcon-research/qd-profile-rt-wire-independent-review.md` | `71972c04e8004a59307e08b261aac39774ce167e334aeeb93c254ad91d1eaf1e` | independent selector-store-to-wire proof |
| `tcon-research/qd-live-rt-protection-candidates.md` | `b565bccaf3ca47063e6a938b86b54a2c5ae73a9f953b47916882f64e583762de` | pre-loop EEPROM and recurring poll separation |
| `incident-separation-20261027z/incident-comparison.md` | `d80db221d9aef6d371989c178efa260488ad080325133cb3b635f74022bec371` | physical/technical incident separation and missing falsifier |

The UART host-logging and DT-binding reports were also checked for an existing
passive image-0 log route. They already establish that no retained host binding
to the QD controller UART is proved. Their work is not duplicated here.

No firmware bytes were newly disassembled because the reviewed evidence
already covers the relevant ordinary branches and exposes the actual remaining
gaps. No file outside this report was modified.
