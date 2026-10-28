# CB: synchronized software onset with owner-confirmed blackout and recovery

The owner confirmed populated Apps visible after CA initialization. After a
separate normal-key header refresh, one reviewed synchronized observer ran on
fresh USB instance54 under the recorded conditional first-header premise.
It retained a full clean baseline, sent one Left down/up alongside its sole
USB reader, retained five clean cycles and then a fault transition at cycle6.

Transport, native observation and trial qualification all passed. There were
36headers/72bulk transfers. The terminal phase was ReadyForHeader, the
interface released/device closed and the exact stage removed. No automatic
retry, second Left or recovery action was part of this recorder.

The final clean R pair spans167671010145..167671010211us; first fault R spans
167671260342..167671260439us. The conservative software transition bracket
is167671010145..167671260439us (250294us), conditional on reply freshness.
The tuple changed from stop0/fault0/gate1 to stop1/fault0x1001/gate0.
Both retained clean and fault reads are after the Down return. This does not
supply compositor consumption time, an exact physical light timestamp or
proof that the keypress caused the fault.

A separate post-observation UI snapshot reports cached Live with CSFS/no
screensaver. The owner then reported 'panel went dark' and 'i think because
it navigated outside of apps'. This establishes owner-observed blackout in
the trial context, separately from the sampled software transition. It does
not put physical light loss inside the250ms software bracket.

After the observation had ended and its records were saved, a single normal
Right selected cached Apps. The existing black-panel recovery quickpath then
verified Apps/public reject signals and invoked exactly one unchanged stock
operation41/mode2. The native output reports helper exit0, exact fixed ioctl
return0 and close0, but the enclosing status lifecycle rejected remote stderr:
`cat: /proc/10225/stat: No such file or directory`. This is a helper-exit race
in its polling harness. The top-level MODE2 record remains accepted=false;
cleanup_confirmed=true. The quickpath therefore returned failure and produced
no result.json. The physical recovery must not be called a passed quickpath
acquisition. No retry or post-reset key was sent. The owner reported 'panel is
back on on apps'. The recovery is a distinct operational block, not part of
or repair to the accepted onset record.

Current limitations remain: sequential/non-atomic operands; assumed reply
freshness and source-generation binding; no measured final electrical edge;
no proven input-table producer/units; no permanent prevention or firmware
patch. The full official firmware archive has separately been acquired for
continued analysis. No downloaded firmware was applied.
