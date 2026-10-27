# Public display architecture context — 2026-10-27

This supplementary literature search did not identify an S95F/RSM1 register
map, executing-code bus address, RTProtect enum, AP_EXCO field schema or
compatible firmware image. These documents are primary patent disclosures,
not evidence that a particular design is shipped in this TV. No target action
or change was based on them.

Samsung Display's [US11289018B2](https://patents.google.com/patent/US11289018B2/en)
describes protection whose current reference depends on image screen load.
It also describes black-image checks and adaptively changed references.
This supports only the architectural possibility that content can affect a
protection decision. It does not equate our firmware's lane counts, 40/200
limits, or argument 736 with current, load percentages or those patent
references. No physical brightness/load measurement was made during V6.
The disclosed intentional black-image test cannot be relabelled as our
owner-observed persistent loss of emitted light.

Samsung Display's [US11862094B2](https://patents.google.com/patent/US11862094B2/en)
describes sensed power-line values, masking during transitions, and a timed
protection count leading to shutdown. This illustrates how transient and
persistent protective outcomes can coexist. It does not identify the board
IC, controller firmware path, timescale, signal levels or reason for the
owner's separate rare audio-pausing HDMI glitches. No numerical timing or
power-reference value from the patent may be transferred to the TV.

The resulting local hypothesis remains conditional: changed content may
change panel loading or sensed data, and the captured ordinary controller
calculation may then cross a limit. Neither patent closes the missing
software-to-electrical mapping, source ownership, causal physical onset, or
safe intervention. Exact event-time operands and a qualified live diagnostic
route remain the useful next evidence.
