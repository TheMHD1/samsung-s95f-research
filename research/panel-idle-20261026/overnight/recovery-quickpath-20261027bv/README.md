# Apps-selected panel recovery quick path

This is the documented operational sequence from the owner-observed success:
ordinary local keys reached the populated Apps page, then one fixed stock QD
TCON operation 41/mode 2 controller lifecycle was requested. The owner saw
Apps and confirmed that the panel stayed on. It is a recovery procedure for
an observed persistent-black event, not a permanent fix or a background
prevention service.

`recover.py` is dry by default. In live mode it first uses the separately
pinned navigation runner to get the **cached** current tab to `d/apps.tab`.
It then verifies four public reject signals: no working software upgrade,
`lcdon`, screen state `1`, and public burn-in flag `0`. Only then can it
request one unchanged stock controller operation. A missing Apps result, a
busy public value, a transport error, or a helper failure stops the routine
before the operation or without retry.

The successful helper result only means the Linux ioctl returned and cleanup
completed. It does not prove electrical panel recovery. No wake key is sent
after the operation, so the owner must separately confirm that the physical
picture returned and remains visible.

The public checks are useful reject conditions. They do not prove global
maintenance idleness, emitted light, or absence of every controller activity.
This procedure never sends vendor USB headers, reads controller state, changes
firmware/protection settings, or loops/retries the reset.

After the navigation runner receives its final reviewed source pin, run:

```sh
python3 recover.py
python3 recover.py --execute --output /absolute/new/recovery-record
```
