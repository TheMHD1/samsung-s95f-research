# Independent review: Mode-2 result summaries

## Scope

Read-only review on 2026-10-27 of the current top-level result summaries and
their retained runtime/transport evidence.  No TV, root, network, trace,
controller, GPIO, or filesystem mutation outside this new review file was
performed.

Reviewed documents:

| document | SHA-256 |
| --- | --- |
| `README.md` in this directory | `5157fad93c5f1725c6a5fc29e434139530ac1ca87eb356f7e09a822b96c054c6` |
| `../../../CURRENT-INVESTIGATION.md` | `7181f76312f99829e3d2dfd913704106dcdb816f0fcf0dac0769b166baed9fde` |
| `../paired-restart-progress-20261027.md` | `20d23d036dbf87ef22f337f69e6776ca426f10667b97c195e42284f4334fd90e` |
| `../diagnostic-causal-map-20261027.md` | `108a93a9f036391d931a580cb4109f46ecb80aca6a0c5298693a0b7fde6aba4e` |
| `stock-mode2-transport-audit.md` | `70b0d0f2f7a8301d2b598d45a3510a4304bd493c2e7507e0bb1c8f270baf8847` |
| `mode2-sequence-runtime-audit.md` | `e36f4893ba935da41674aaa804e4ce72694e90f55775a15e4c0347c600b2df65` |
| `diagnostic-next-tests.md` | `6b090ab394b452de88dd4a18a330754023e8df62168bd4c7a45bfa16a360efba` |

The runtime and transport reports are the controlling evidence for timestamp
and acceptance status in this review.

`diagnostic-next-tests.md` independently uses the correct distinction: it
labels `94420.463964` as the actual kernel power-off branch,
`94422.496790` onward as the stock on-tail, and `94422.87` as a post-execution
wrapper completion.  Its FD correction is also grounded: the raw syscall
register token `0x21` is hexadecimal (decimal33), matching `/dev/dri/card0`;
this does not affect the Mode-2 timing result.

## Evidence correctly retained by the summaries

The reviewed summaries correctly state the material boundaries below:

* exactly one stock operation41/mode2 request was made;
* the lower stock path has retained ACDET/reset-mailbox, USB
  disconnect/re-enumeration, ERR_DET-low, and controller-transfer evidence;
* the enclosing 60-second observer remains rejected for a **pre-action**
  duplicate AVOC syscall-enter and is not converted into an accepted onset or
  physical record;
* individual pre/post/late helpers are accepted with cleanup, but owner
  physical picture state was unobserved; and
* no flash, protection suppression, reset loop, or permanent repair is being
  claimed.

Those statements agree with the transport audit and sequence runtime audit.
The zero ioctl result is not used as the sole proof that the lower sequence
ran; the summaries appropriately cite the retained GPIO/reset/USB/I2C
substreams.

## Timing precision

Three different time notions must remain separate:

| event | retained uptime | meaning |
| --- | ---:| --- |
| first observed stock off-side hardware action | `94420.461099` | ftrace ACDET-low row; closest retained action-start anchor |
| QDF reset/off log | `94420.463964` | stock QDF off body/log timing |
| managed helper `execute_uptime` | `94422.87` | post-execution wrapper anchor, explicitly not hardware-action start |
| immediate status helper | `94425.24` | accepted, separate post-action status sample |
| immediate pin helper | `94427.94` | accepted, separate post-action line sample |
| late status helper | `94724.79` | accepted status sample, about302 s after wrapper execute and about304 s after first ACDET action |
| late pin helper | `94726.97` | accepted line sample, about304 s after wrapper execute and about307 s after first ACDET action |

Accordingly, “about302 seconds later” is valid only when explicitly anchored
to `execute_uptime=94422.87`, not to the first lower hardware action.  A
statement that says merely “five minutes after the action” obscures the
roughly two-to-five second distinction depending on which retained action
anchor is intended.

Likewise, “status/pin pair” must mean two sequential one-shot observations,
not a synchronized pair: the immediate samples are about2.70 seconds apart;
the late samples are about2.18 seconds apart.  No document should imply they
sampled the same electrical instant.

## Material wording corrections recommended

### 1. Do not say the fault was cleared

`README.md` currently says the lower sequence was observed and “fault
indications cleared for at least the later five-minute sample.”  That wording
overstates the evidence.  The retained facts are narrower:

* stock status selector `F3:0x08` returned raw zero at two later sample times;
* the separately requested line read returned zero at two later sample times;
* the selector’s controller-latch/read-to-clear semantics are unresolved; and
* a GPIO-low sample is not an electrical-health or physical-light verdict.

Recommended replacement:

> Its lower sequence is observed; separately sampled status and ERR_DET inputs
> were zero immediately afterward and again at the later same-boot samples.
> Their latch/read semantics and physical meaning remain unproved.

This preserves the useful result while avoiding an unproved “cleared” action
or five-minute persistence assertion.

### 2. Qualify the causal-map “latch-reset” wording

The causal map calls the result a “bounded stock latch-reset mechanism worth
visually testing.”  The stock route did reset/re-enumerate a controller-facing
path, but neither static code nor the retained selector-`0x08` transactions
prove a particular controller fault latch was reset.  In addition, AVE
`qd_tcon_off` remained one after Mode 2.

Recommended replacement:

> This shows a bounded stock reset/re-enumeration sequence associated with
> changed reported status and ERR_DET samples, worth visually testing.  It does
> not identify which controller state, if any, was cleared.

### 3. Use “sequential samples,” not immediate paired state

`CURRENT-INVESTIGATION.md`, this directory’s `README.md`, the paired-progress
top section, and the causal map all use variants of “immediate … status/pin
pairs were 0/0.”  They should say “sequential post-action status and pin
samples” and retain the action-anchor distinction above.  This is a precision
correction, not a rejection of the accepted helper records.

## Status/read-to-clear boundary

The summaries do not currently assert that `F3:0x08` is read-to-clear, which
is correct.  They should retain this neutral framing: zero is a raw observed
reply at that transaction, not proof the state is non-latched, persistent,
healthy, or physically visible.  The transport audit already makes this
limit explicit.  No additional status query is justified by this review.

## Verdict

**Substantively clear with the three wording corrections above.**  The direct
summary of a single stock reset/re-enumeration sequence, its accepted helper
outputs, rejected observer record, and absent physical observation is
evidence-backed.  “Fault cleared,” unspecific “five minutes after action,”
and atomically sounding “status/pin pair” language should be narrowed before
using these documents as the definitive result summary.
