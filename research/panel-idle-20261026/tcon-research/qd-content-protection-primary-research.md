# Content-dependent panel-protection mechanisms: primary-source boundary

## Question and boundary

The observed pattern is narrow: the panel can remain visible with a Kodi/Ugoos
library UI or an overlay while video continues in the background, but can go
black on return to full-screen video.  This note asks only whether primary
sources describe **plausible display-side mechanisms whose inputs depend on
the driven image**, not whether this TV implements any of them.

No source below identifies the S95F, its QDF firmware, `RT Protect`, the
observed `ERR_DET` bit, the damaged area, or a firmware-to-patent mapping.
None proves that a protection event powers this panel down.  In particular, a
Samsung patent is not evidence that the patented implementation ships in this
model.

## Primary-source findings

| Candidate mechanism | What the primary source actually describes | Relevance to the symptom | What it does **not** establish |
| --- | --- | --- | --- |
| Defect / excessive-current sensing in non-image circuitry | [Samsung Display's US20260045186A1](https://patents.google.com/patent/US20260045186A1/en), definitions [0002]-[0011] and claim 1, describes applying a voltage to a pixel, sensing current through a dummy pixel line, comparing a current-derived signal with a reference, and determining a defect when the threshold condition is met.  The stated purpose includes finding a short circuit in a repair line/dummy-line arrangement. | This is the strongest *physical-fault* candidate in the limited source set: a current comparator can distinguish an abnormal panel/interconnect condition from ordinary picture processing.  If a damaged conductor changes electrically with a particular scan, load, or temperature state, its threshold crossing could be repeatable. | The application does not describe the user's panel, a crack, full-screen-video-specific triggering, a shutdown action, or any relation to `ERR_DET`/`RT Protect`.  It also describes dummy/repair lines, not an identified active-image-pixel measurement path in this TV. |
| Low-gray drive can use higher instantaneous current and changed emission time | [Samsung Display's US20250078713A1](https://patents.google.com/patent/US20250078713A1/en), abstract/summary and claims 1-2, describes two drive periods.  At or below a reference grayscale, the pixel can use a higher first-period level and reduced/no second-period emission, so low grayscale is represented by duty/time modulation rather than simply a uniformly low current. | A video frame, menu, subtitle plane, or overlay can have materially different pixel-code distributions even when it looks comparably dark.  Therefore “full video fails but a UI overlay is visible” is compatible with a **content-dependent drive waveform** hypothesis; average screen brightness alone is not a sufficient discriminator. | This is an image-quality/low-gray technique, not a documented fault latch or safety shutdown.  It does not say an overlay prevents a fault, that this model uses this technique, or that a high instantaneous drive level damaged the panel. |
| Image/grayscale-dependent sensing cadence and temperature compensation | [US20260279291A1](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/20260279291), claim 1 and paragraphs [0001]-[0010], is a Samsung Display application that senses pixel driving current, derives block temperature, and—after stated deterioration/temperature conditions plus an average-grayscale threshold—shortens a later sensing period while outputting compensated data voltage. | It supplies a concrete class of policy where both sensed electrical state and image statistics influence display timing.  A useful future discriminator is whether the failure tracks scene grayscale/local pattern at a fixed source and mode, rather than merely playback application or Home state. | The described consequence is compensation/sensing-period selection, not a panel-off decision.  The application was published after this investigation began and is not model-specific evidence.  It cannot identify the field or threshold in the saved firmware. |
| Scheduled pixel-maintenance / image-retention care | [Samsung's OLED TV Screen Optimization support article](https://www.samsung.com/hk_en/support/tv-audio-video/how-to-use-screen-optimization-on-a-samsung-oled-tv/) says Screen Optimization is associated with accumulated use and a roughly ten-minute off/on cycle; the same article says the automatic prompt can start after one minute when the stated longer-use condition is met. | This separates the previously observed ten-minute prompt from an immediate, content-switch-linked blackout.  Maintenance is a real competing explanation for some power-cycle behavior, so it must be logged separately. | Samsung explicitly limits that page to Hong Kong products and says model, sequence, and settings vary by market.  It does not explain the current issue, identify a defect detector, or establish timing/thresholds for this Canadian-set TV. |

## Candidate mechanisms worth discriminating later

These are observational hypotheses only; this note does not authorize a panel
test, a firmware change, or a protection bypass.

1. **Electrical fault/threshold candidate.** A repeatable event should follow a
   particular electrical drive state or temperature/load history more closely
   than UI identity.  Stronger evidence would be a fresh controller/host fault
   status change aligned to the transition, not merely a black panel.
2. **Low-gray waveform candidate.** Hold source, output mode, and panel state
   fixed, then compare frames with similar average luminance but different
   low-gray distribution, duty-like content, subtitles, or UI overlays.  A
   different outcome would make “brightness alone” inadequate; it still would
   not identify the mechanism.
3. **Pixel-maintenance candidate.** Its discriminator is the documented
   cumulative-use/off-state schedule and a ten-minute cycle, rather than an
   immediate transition when returning to full-screen content.  A timed
   maintenance notice must not be treated as a controller-fault observation.
4. **Application/compositor alternative.** If a failure follows the same
   rendered pixels across independent sources/modes it favors a panel-drive
   hypothesis; if it follows one pipeline regardless of rendered content it
   favors a source/compositor path.  The existing comparison is suggestive, not
   controlled enough to decide between them.

## What this changes in the investigation

The patents make two modest points: OLED systems can sense current and alter
drive/sensing behavior according to image conditions, and a current threshold
can be used for a defect determination.  They do **not** supply a safe clear
command, prove a crack/short is the producer, or justify suppressing a safety
path.  The next high-value evidence remains model-specific: an accepted fresh
fault/status observation tightly time-aligned with a future authorized,
controlled content transition, together with the already retained firmware
call-chain evidence.

## Source and quotation discipline

Only the four primary sources linked above were used.  This note paraphrases
them rather than reproducing extended patent text.  The Samsung support page
is manufacturer documentation, but its regional disclaimer is material and is
not generalized to this TV.
