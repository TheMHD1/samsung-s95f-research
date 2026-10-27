# BW: full For You / Apps recovery confirmation

The owner requested one Apps → For You → fault → Apps → restart → visible
Apps cycle. The initial cached page was Apps with screensaver windows present;
the owner had just confirmed the screensaver was visible.

Normal local keys sent one volume-up wake, Up, Up, Left (Live), Left (For You).
Each step was recorded. The cached final page was For You, with no saver.
A single reviewed kernel status read returned `0x00000010`.
The owner later confirmed seeing navigation and the panel off. No exact
last-clean/first-fault event was captured during this operational test.

The checked recovery routine sent Right (Live), then Right (Apps), verifying
each cached tab. Public checks required the known Linux boot, upgrade 0,
display lcdon, screen 1 and burn-in-in-progress 0. Exactly one unchanged
stock controller operation 41/mode 2 ran, returned kernel zero and cleaned up.
No post-reset key was sent. The owner then confirmed Apps physically visible
and the panel on. A later single kernel status read returned
`0x00000000` and cleaned up.

The owner's exact message is preserved in [owner-observation.json](owner-observation.json).
The structured result is [summary.json](summary.json). The routine and its
per-step raw records are under [recovery](recovery/).

This passes the requested operational recovery test and repeats BU's
Apps-selected success. Combined with BH and BI it is the fourth
owner-confirmed controller recovery. These kernel values are not raw MCU RT
reads, and no read-to-clear/debug override is excluded by this query. Physical
visibility is established by the owner, separately from software results.
No permanent prevention, firmware patch or physical-damage repair is proved.
The TV was left with Apps selected and owner-confirmed visible.
