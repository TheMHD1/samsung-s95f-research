# Apps-selected panel recovery

Updated 2026-10-27 UTC. This is a demonstrated recovery procedure, not a
permanent prevention of the content-dependent blackout.

## What worked

With the physical panel black but the TV operating, select the populated
Apps page using normal local keys, verify the cached page, then run **one**
unchanged stock display-controller operation 41/mode 2. In the BU trial the
owner saw Apps return and stay visible, and later saw the screensaver remain
visible. No post-reset wake key was needed.

The successful sequence and owner observations are retained in
[BU](panel-idle-20261026/overnight/apps-selected-panel-recovery-20261027bu/).
Earlier controller restarts returned a visible screensaver (BH and BI).
The immediately preceding BT operation, with For You still selected, did not
visibly recover the picture. This comparison supports selecting Apps before
recovery; it does not yet prove exactly why BT stayed black.

## Checked host command

Run only for an observed persistent black panel, using a new absolute output
directory each time:

```sh
python3 ${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/recovery-quickpath-20261027bv/recover.py --execute --output /absolute/fresh/recovery-record
```

Without `--execute` the routine prints its plan and does not contact the TV.
It selects Apps using bounded normal keys, verifies the cached tab, checks
the known Linux boot and public upgrade/display/maintenance values, and runs
one stock MODE2 request. Any rejected check stops it. It has no automatic
retry, firmware write, protection modification, or post-reset wake key.
The owner must separately confirm the physical picture; software status and
screenshots cannot establish that the OLED is emitting light.

Source identities at this checkpoint:

- `recover.py`: `4fddc3f6e933a19b15ba208e1ffc029ccd7df323c66cdb7ae24157f374e64a0f`
- `navigate.py`: `74b60a9611f35a76d272b33677f773cc955838c2c6dda2c3565c371cc9d4d530`
- unchanged MODE2 runner: `5c7ec5d3581e349d7f91669977123497147777e573fbdefd8a9b6f96dcf3cb75`

## Navigation lessons

The working utility is the TV's stock `/usr/bin/input_keyevent` Bash script,
which sends a keysym through Enlightenment's system D-Bus interface. Use a
150 ms down/up pair. The saved utility hash is checked before input, and
key release is attempted even when key down fails. No transport retry is
performed because a timeout does not prove that a key was not delivered.

The observed For You-to-Apps route was Right (sidebar into Home), Up, Up,
Right (Live), Right (Apps). When focus already rests on the tab strip, the
first Right can reach Live immediately. The runner checks the cached tab
after each step and branches only through these recorded outcomes. It is
not a universal focus-recovery algorithm. A white selected tab is not proof
of keyboard focus. Direct AppControl Apps requests returned without selecting
Apps; use the demonstrated local key route instead.

The runner is pinned to Linux boot
`00000000-0000-4000-8000-000000000000` and the captured stock sources. A boot
or source mismatch requires renewed inspection. Public `lcdon`/screen-state
values are reject checks, not proof that the physical panel is lit or that
all maintenance is idle. Never turn this procedure into an automatic reset
loop.

## Current limitations

The owner reports a thumb-sized damaged region at the bottom edge with a
vertical line above it. Sparse For You/Live and some fullscreen films can
trigger persistent black while audio and Linux continue; populated Apps or
the same video behind Ugoos Home can remain visible. The controller fault
path has been partly reconstructed, but the actual onset operands, input
producer and final electrical loss-of-light edge are still unproved.
Recovery does not repair the physical damage or establish a permanent fix.

## Full-cycle confirmation

The BW test reproduced the requested cycle: normal keys woke the Apps
screensaver and selected For You; the owner reported the panel off. Two
Right keys selected Live then Apps while black, and one stock MODE2 returned
visible Apps, confirmed by the owner. No post-reset wake key was sent.
See the [full-cycle findings](panel-idle-20261026/overnight/full-confirmation-20261027bw/findings.md).
This is a second successful Apps-selected recovery (BU and BW), and the fourth
owner-confirmed controller recovery including BH and BI.
