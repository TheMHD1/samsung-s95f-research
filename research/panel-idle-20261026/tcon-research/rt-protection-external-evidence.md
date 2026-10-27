# External evidence boundary: `RT Protect`, `ERR_DET`, and Samsung OLED Screen Optimization

## Scope and result

This is a public-source supplement to the retained local reverse engineering.
It does not replace the exact local evidence that the current device emitted
`ERR DET Status:0x10` and whose local decoder labels bit 4 `RT Protect`.

The public record supports a clear, narrower distinction:

1. **Samsung Screen Optimization is OLED image-retention maintenance.**  It
   can intentionally turn the set off for roughly ten minutes, operates after
   accumulated viewing-time thresholds, and has a documented one-minute
   automatic-start path when overdue.
2. **No reviewed primary public source defines the internal labels `RT
   Protect`, `ERR_DET`, `F77ABU2D20`, or `RSM1` for a Samsung S95F/QD-OLED
   controller.**  In particular, no source found identifies a producer,
   clears bit `0x10`, or says that Screen Optimization clears a controller
   error state.

Therefore, public documentation supports treating the 10-minute popup/cycle as
panel-care maintenance, but it does **not** support relabeling the observed
local `RT Protect` bit as pixel refresh, burn-in protection, a thermal fault,
or a particular hardware failure.  The two mechanisms may coexist without
being the same fault domain.

## Samsung’s documented Screen Optimization behavior

Regional scope: the principal article explicitly applies to Hong Kong
products and says models, sequences and settings may differ by location.
The owner's TV is a Canadian QN77S95FAFXZC. The matching popup wording is
useful identification evidence; the published thresholds are not independently
verified as the exact Canadian firmware's policy.

Samsung's current OLED TV support article says Screen Optimization detects the
screen state to help prevent image retention.  It says the normal automatic
case follows TV power-off after four cumulative viewing hours and takes about
ten minutes.  It also says interruption by turning the set back on or removing
power cancels the cycle.  When the product has missed optimization past the
twelve-hour threshold, Samsung documents a prompt to start immediately; if
there is no action, it starts after one minute.

This independently matches the owner's observed one-minute decision window
and “power ... off and on for about 10 minutes” wording.  It is a strong
identification of that popup/cycle as documented OLED maintenance, not an
inference from the local symbol names.

Samsung's older OLED TV image-retention article describes the same general
mechanism: automatic activation after four cumulative hours while the TV is
powered off but remains connected to power, with a 10–15 minute duration.  It
also frames the feature as image-retention prevention.

These sources say nothing about the internal `ERR_DET` word, any RT-labelled
controller state, a GPIO fault pin, QDF, TCON recovery, or a safe command that
clears a controller latch.  They cannot be used as authorization or evidence
for bypassing local protection logic.

## S95F relevance

Samsung’s support page for the S95F family (`KQ65SF95AF`) links the same
Samsung “How to use Screen Optimization on a Samsung OLED TV” support topic.
That establishes that the generic support guidance is offered for the S95F
family.  It still does not supply a service-level bit dictionary or a
controller-clear procedure.

## Public search boundary for the RT/ERR labels

On 2026-10-27, searches were run for exact phrases and identifiers including:

- `"RT Protect" Samsung OLED` and `"RT Protection" Samsung OLED`;
- `"ERR DET" QD OLED` and `site:samsung.com "ERR_DET" Samsung TV`;
- `"F77ABU2D20" OR "RSM1" Samsung`.

The results did not produce a Samsung manual/support article, semiconductor
manufacturer document, or original reverse-engineering repository that maps
those labels to this television/controller.  Incidental results used `RT` or
`ERR DET` in unrelated products and were excluded.  This is a query-bounded
absence, not proof that no service documentation exists.

## Useful next discriminators

The following are more discriminating than trying to infer an RT meaning from
the maintenance popup:

| question | evidence that would answer it | current public support status |
| --- | --- | --- |
| Does the current controller error persist? | a narrowly reviewed current error-status / ERR_DET observation, preserving raw value and read-side-effect limits | local RE, not public docs |
| Is an SSB/USB recovery endpoint present? | node/class/driver and interface-binding metadata before any open; the recovered SSB open path can acquire USB runtime PM | local static/runtime metadata, not public docs |
| Did maintenance run successfully? | Samsung-described completion message after an uninterrupted, powered-off optimization cycle | Samsung documents the user-visible completion behavior, but not controller state |
| What exactly is RT bit 4? | a model-matched Samsung service source, panel/controller manufacturer documentation, or independently reproducible controller protocol trace | unresolved |

No public source found justifies treating a black picture as a Screen
Optimization cycle, or treating completion/cancellation of that cycle as a
clear for the observed local RT-protection status.

## Sources (reviewed 2026-10-27)

- Samsung, “[How to use Screen Optimization on a Samsung OLED TV](https://www.samsung.com/hk_en/support/tv-audio-video/how-to-use-screen-optimization-on-a-samsung-oled-tv/)”, last updated 2026-03-19.  Samsung documents the four-hour automatic condition, the ~10-minute process, cancellation by early power-on/unplugging, and the twelve-hour/one-minute overdue path.
- Samsung, “[How to troubleshoot image retention on your Samsung OLED TV screen](https://www.samsung.com/levant/support/tv-audio-video/how-to-troubleshoot-image-retention-on-your-samsung-oled-tv-screen/)”, last updated 2022-05-13.  Samsung describes Screen Optimization as image-retention prevention and gives the 10–15 minute, powered-off behavior.
- Samsung, “[KQ65SF95AF support](https://www.samsung.com/hk_en/support/model/KQ65SF95AFXKR/)”, retrieved 2026-10-27.  The S95F-family support page links Samsung’s Screen Optimization guidance and its model manuals.

No non-primary forum, binary download, or unauthenticated service-manual claim
was used as evidence for RT/ERR semantics.
