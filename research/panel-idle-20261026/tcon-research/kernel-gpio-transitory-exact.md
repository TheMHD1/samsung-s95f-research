# Exact acquired-Image GPIO persistence helper

The paired boot ARM64 Image has SHA256
`77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d`.
The existing hash-identified artificial ELF export view has SHA256
`83a91462c65fd80a4a0ddcd7d5c295b35ea38fc8823298f9018c7353f3cafbc7`.
Its recovered PREL32 export names `gpiod_set_transitory` at Image file offset
0x3c22b0. These are file/artificial analysis addresses, not live kernel VAs.
The acquired paired slot is not a measured hash of executing kernel text.

A bounded [disassembly](kernel-gpio-transitory-exact.disasm) covers the helper
through the next exported function at0x3c23a8. Ten selected instruction words
were checked directly against the pinned raw Image before generating evidence.
This adds exact paired-image evidence beyond the upstream source comparison.

With a valid descriptor and input bool=false, the implementation clears mask
0x1000 in the descriptor flags at+8. It obtains the gpio_chip through the
descriptor's gpio_device and loads callback slot **gpio_chip+0x68** at3c2350.
If null, it returns0 after the descriptor flag update. Otherwise it computes
line offset, packs config **0x116** (parameter0x16 with argument1 in bits8+),
and calls that callback at3c2370. The 0x16 parameter agrees with upstream
PIN_CONFIG_PERSIST_STATE. It normalizes callback result-524 (-ENOTSUPP) to0;
other return values propagate. Both atomic implementation variants are in the
Image; no assertion is made about the live CPU alternative patch selection.

The vendor driver's value at gpio_chip+0x68 remains unresolved. This helper
proves why a zero-return cdev/sysfs request alone would not establish that no
configuration operation happened: null and unsupported callbacks also report
success after updating the descriptor flag. The callback/driver registration
trace is the next bounded static task.

No TV access, GPIO request, pin/config write, live kernel memory access,
firmware modification or execution of this Image occurred. This is offline
analysis of existing evidence only.


A scan of aligned Image words for direct AArch64 BL targets finds exactly
three syntactic calls to this helper:3c3a30,3c54a8,3c9378. Their bounded
[caller windows](kernel-gpio-transitory-callers.disasm) show constant w1=0
at the first and third calls. The middle derives its boolean from a flag bit.
The first window later allocates an anonymous file; the third subsequently
calls exported gpiod_export with w1=1. These are consistent with the upstream
line-handle and sysfs-export wrappers, but recovered nearest-export labels
are not internal function names and do not by themselves prove dispatch
binding. Data words can imitate instructions, so the count is a syntactic
scan with only these locally decoded windows interpreted, not a whole-kernel
call graph or runtime coverage claim.
