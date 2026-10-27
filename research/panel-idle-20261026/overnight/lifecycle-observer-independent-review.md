# Lifecycle and observer review — parent-preserved mailbox record

The independent reviewer worked read-only against the copied exact binaries
and retained records. This note is written by the parent from the reviewer's
messages. No reviewer TV/network request, panel control or deployment ran.
This is a bounded evidence review, not validation of a physical repair.

## Monitor lifecycle

The reviewer verified the mapping-symbol inventory: all2,343,452 `.text`
bytes partition into2,045,156Thumb,28ARM and298,268data bytes, using9,826
unique markers with no undecodable code bytes. PLT relocations, startup GOT
stores and six recovered direct-call edges check out. The word “call” is
required: the reproducer scans BL/BLX, not every possible branch or indirect
target. The reviewer separately scanned exact direct branch targets and
found no extra lifecycle edge within that bounded copied-library scope.

The reviewer requested explicit input-save/convergence assertions for the
public and TCON Instant On paths and the Start API report branches. The
author added them and reran the final hash-gated check successfully. The
public Instant On object lookup must be non-null before forwarding its input;
the TCON API maps0 to0 and any nonzero input to1. Start directly sets the
monitor-on/restart words. These are host bookkeeping paths; neither their
static existence nor a counter clear proves standby/wake execution, panel
emission or recovery.

Final bounded recheck of the corrected three debug artifacts and central
lifecycle/debug section passed with no blocking findings. The reviewer
independently ran/compiled the debug and lifecycle reproducers, confirmed
the corrected PVCC load at0x147b0 and verified that the only two other
copied-module helper definitions (Rosem/FRC API) are identical8-byte stubs.
No claim of completed repair or observed physical recovery follows.

## Denied native syscall-availability helper

The reviewer verified that the recorded launch was denied with Operation
not permitted, output was zero bytes with the empty-file hash, accepted=false
was retained and temporary-directory cleanup was explicitly checked. Five
offline integrity tests pass. There is no BPF/perf syscall result, no private
kernel-state result and no proven security-policy explanation for the denial.
The root shell's final success does not mean the helper ran successfully.

## Debug dispatcher: two corrections before final integration

The initial worker assessment saw cache labels and firmware/setter branches
and classified the callback as a potentially mutating cache-print entry.
Disassembly of the exact helpers corrected reachability: `t2ddebug_get_hex`
at0x16650 and `t2ddebug_get_decimal` at0x16648 are each8-byte bodies:
`mov x0,#0x99; ret`. The CALL26 relocation at0x1442c targets the locally
defined hex helper, not an unresolved external input implementation.

Independent review then rejected a second draft's claim that this normal
exit path first prints the named caches. Entry through0x14424 prints the
menu. Selector0x99 fails the1..0x91 table range, takes0x14454, compares
against0x99 at0x14474 and returns at0x14498. The actual cache-print branch
is dormant selector0x30, table target0x1454c. Its named loads include
0x14670(BSS+0),0x146c0(+0x10),0x147b0(+0x40),0x14acc(+0x10c), and its
tail0x15248 returns to the menu loop at0x13e34. Mutating branches are also
unreachable on the unchanged constant-input path. Registration of the
callback at provider-table+24 does not change these helper bodies.

The useful bounded conclusion is that cache-print code exists, but this
callback's unchanged normal path is not a passive observer of the desired
values. Neither a guessed ioctl nor a helper patch was attempted. The
ordinary PVCC cache+0x40 and panel-DPMS PVCC guard+0x194 remain distinct.

## Photo and physical-state boundary

The parent reopened both screen closeups and retained the owner's correction:
the visible lower-edge patch is no larger than a thumb. Exact centimetres,
pixel width, electrical fault extent and current picture state are not
established by those images. No black-state recovery test ran in this pass.
