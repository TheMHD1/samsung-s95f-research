# Host identity-check correction

The first host-side recovery-instance check expected the generic Linux text
`USB disconnect, device number60`. Samsung's retained message inserts its
SDU/vendor/device description before `device number60>`, so that literal
check failed. The following readiness preparation then refused the missing
instance-check evidence before loading the root transport. It issued no
vendor or root request. No controller retry or recovery followed this host
format error.

The corrected check matches the explicit retained Samsung same-port message,
then the later same-port high-speed enumeration of device61 using sdp-xhci.
It also verifies same boot, old60/new61, unchanged descriptors and structured
accepted one-shot recovery. The accepted instance-check.json binds the
original cached metadata and recovery-result hashes. This is log-order and
instance evidence, not a mapping of printk time into native monotonic time.

Fresh readiness then succeeded and one EB validation completed16 read pairs,
ReadyForHeader/release/close and exact stage removal. R was clean0/0/1 at40,
N/latch0, both sampled eligibility tables zero, and both104-byte reference
windows zero. No extra MODE2 was needed. The original first check's failure
does not invalidate the retained USB lifecycle evidence or establish an
exact enumeration timestamp.
