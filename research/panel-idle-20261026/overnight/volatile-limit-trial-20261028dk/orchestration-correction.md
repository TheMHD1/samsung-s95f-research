# Apps preflight scheduling correction

The parent mistakenly treated exec_command's returned session as completed:
Apps preparation was still running when the first cached readiness collection
started. Both operations were ordinary UI/cached-metadata work, with no USB
vendor call or threshold write. The root client's process lock refused the
Apps runner's final snapshot (BlockingIOError, no automatic retry). Its original
overall failure is preserved. The completed normal wake down/up both returned0.

A separate zero-key cached snapshot in record-baseline-context-continuation
confirms CSFS present, no screensaver window and cached Apps. The original
record-baseline-readiness metadata result remains a valid narrow cached
observation, but is not used for the baseline invocation. A fresh readiness02
will follow the completed context check. No overlapping vendor operation or
unknown controller endpoint phase occurred; the first-header premise remains
the same explicit conditional one. Subsequent target commands are awaited to
actual process completion before dependent actions are launched.
