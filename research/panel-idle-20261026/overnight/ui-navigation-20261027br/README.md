# Normal UI navigation runner

`navigate.py` is dry by default. It has fixed modes for a normal volume wake
key, Home, arrows, Enter, Back, cached-state snapshot, Apps, and For You.
Every real operation needs both `--execute` and a new absolute output path.

The default local key backend uses the pinned stock `/usr/bin/input_keyevent`
utility with one fixed keysym down/150 ms hold/up pair. It checks the current
boot, utility executability, and utility hash first. It attempts the `up` even
if `down` fails, then records both exit codes. There is no automatic fallback. `--backend ws` is an
explicit alternative using the saved-token WebSocket client; it is never used
implicitly.

Key actions do not use Power, factory/service keys, display power, controller
USB, or settings writes. Apps and For You use the calibrated normal-key path,
not AppControl: every key gets its own cached-state snapshot. If a screensaver
is present, that path begins with one wake key and verifies that it is gone.
It then accepts only the verified For You → Live → Apps and Apps → Live → For
You trajectories, stops on any unexpected state, and is bounded to eight keys.
If the requested cached page is already selected, it records a no-op without
sending a navigation key.

Every operation records before/after cached `current_tab` and compositor
windows. These are software UI observations. An accepted transport response
or matching cached tab is not a physical-picture acknowledgement. Apps and
For You AppControl routing remains unverified even with CSFS foreground and is
not used here. The current calibration uses one ordinary navigation key at a
time. A Right key has been observed to move from the sidebar into Home content,
not directly to the Apps bar. Owner observation must be recorded separately.

Examples (dry):

```sh
python3 navigate.py wake
python3 navigate.py apps
python3 navigate.py home --backend ws
```

Parent orchestration is responsible for deciding when to run a real action;
this runner does not retry. Page actions can send one wake key to dismiss
a screensaver, then execute a bounded sequence of normal navigation keys.
Each step records cached UI state; physical visibility requires owner feedback.
