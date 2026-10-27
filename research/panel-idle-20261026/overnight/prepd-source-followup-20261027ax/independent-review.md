# Independent review of the AX Pre-PD and host-histogram follow-up

Recorded 2026-10-27 UTC. This was a bounded, local, read-only review. It made
no TV, root, network, USB, controller, power, UI, MMIO, firmware, collector,
or flash operation and did not modify the evidence under review.

## Findings

### P2 — live source binding is overstated for the retained histogram rows

`host-histogram-reset-comparison.md` lines 12 and 125 describe the retained
values as reports “from the host DP register paths” and as
“histogram-register values.” `findings.md` line 20 similarly calls them host
display-processor register reports. The pinned source report is narrower: it
recovers compatible producer bodies from a **copied relocatable module**, says
those offsets are not a live-address/current-module binding, identifies two
possible `INP` print routes, and calls the simultaneous `DE/VE` rows static
compatibility rather than a live call trace.

The proven runtime fact is that the retained console rows with the six exact
labels and values are identical at all 58 unique sampled timestamps. Their
DP-register interpretation should therefore be phrased as conditional on the
copied-module source attribution, for example: “console values whose labels
are statically compatible with the recovered DP-register formatter paths.”
This correction does not change the numeric equality, bracket, or conclusion
that the rows cannot establish fresh/constant content, Pre-PD input, panel
light, or physical state.

### P3 — qualify the type-7 copy as a static conditional copy path

`prepd-control-consumers.md` lines 17–24 and `findings.md` lines 31–32 call the
type-7 path a positive producer/initialization edge and say the copy
initializes the range. The same report correctly states at lines 62–63 that
execution on the observed boot and current contents are unproved. To keep the
opening conclusion consistent with that limit, it should say that this is the
only positive selected-image **copy/write path found in the bounded evidence**
and that, **if the type-7 loader executes**, it copies the stored payload into
the named range. It is not an observed initializer or runtime producer.

The report's later negative-scope language is otherwise sound: absence of an
embedded prefix word or `MOVT 0x5841` does not exclude caller-supplied or
computed pointers, DMA/hardware updates, another image, or a producer without
an embedded destination. The known companion paths only establish forward
reads for those two bodies; they do not establish global producer absence.

No P0/P1 implementation or evidence-integrity issue was found.

## Reproduction and evidence checks

Reviewed artifact pins:

| artifact | SHA-256 |
| --- | --- |
| `prepd-control-consumers.md` | `b64fbfb9f0001b13c10f43da3d71021fb1f243e34c7aeb90fcefc5e1c1c39117` |
| `prepd-control-consumers-reproduce.py` | `e090bf8e39c8930ccf4a514e0f6c8056c1d09b2adc15912ceed58df0f9ec78b1` |
| `host-histogram-reset-comparison.md` | `e1c79e5e90c4b36d910bdbe405145aaff869b75f2a3bf3fe62738a62149167a3` |
| `host-histogram-reset-reproduce.py` | `9a35b56627ffc5d97ee21ec1e3e31a7454964d24f9dbca20d475098de1facc0e` |
| `findings.md` | `04d163eea4b37ac4a1ab512c7948429dbabd04870fe4acfa1a5525f93e253ddd` |

The Pre-PD reproducer passes normally and under `python3 -O` with byte-equal
compact JSON (SHA-256 `c6415d01f55c0624da14785e6ab6b143d77ab9059256133ab40a17e5f8b00b56`
when hashed without its final shell newline). It reports four focused checks,
zero image-0 embedded words in the half-open prefix, no `MOVT 0x5841`, the one
whole-package metadata word at FILE `0x80624`, and no runtime producer claim.

I checked the scan bounds directly:

- the image slice is exactly `0x40000` bytes;
- `words_in_range` visits every legal byte start `0..len-4`;
- the Thumb `MOVT` census visits every halfword-aligned instruction start;
- literal-pool references are checked at their aligned literal addresses; and
- the two complete companion bodies and the relevant indexed-load bytes are
  hash/byte pinned. Independent disassembly reproduces the literals loaded at
  `0x10340/0x10342` and `0x190ae/0x190b2`, the guarded `(index-1)` path in the
  first consumer, and the forward indexed load at `0x1912a` in the second.

The histogram reproducer also passes normally and under `python3 -O` with
byte-equal JSON (SHA-256 `cc84e0ec15eeb7958ec9f6bfea1f6af359465016052eb20331994db492a8e754`
without its final shell newline). It independently reconstructs the two gzip
kernel sections, binds them to the saved extracts, and reproduces:

- 51 complete six-row groups in the start extract and 50 in the end extract;
- 43 overlapping timestamps and therefore 58 unique sampled timestamps, not
  101 independent observations;
- one value signature across all retained complete groups;
- the nearest pre group at `136361.560322..136361.560374`;
- the MODE2/I2C bracket `136363.892943..136366.222190`;
- the nearest post group at `136371.577002..136371.577049`; and
- no retained complete group intersecting the action interval.

The end-extract group times are strictly increasing. The 2.332621-second
pre-to-action and 5.354812-second action-tail-to-post separations reproduce.
The report correctly treats the two rolling extracts as overlapping views,
not independent sample populations, and correctly refuses to infer polling
cadence, continuous stability, frame association, fresh register contents,
constant content, simultaneous controller state, or physical panel output.

## Synthesis review

Apart from the two wording qualifications above, `findings.md` preserves the
material limits: no group during MODE2, no synchronization of W/AK/AW to the
action, no controller/host dataflow, no proven patch parameter, no physical
recovery, no new collector, and no present recovery proof for a failed flash.
Its links to the write-readiness and flash-recovery-gap documents resolve.
The proposed next test still requires a fresh synchronized physical/RT state
and does not rehabilitate the rejected collector or imply a flash action.
