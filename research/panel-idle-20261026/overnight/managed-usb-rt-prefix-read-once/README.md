# Experimental fixed RT-prefix read

This derivative reads only32 bytes from image0's mapped RT configuration
address0x47012400, target0x101, header010100000024014720000000. Source and
wrapper derive from the independently reviewed streaming descriptor reader;
the fixed target, length, label, assembly/staging names and acceptance scope
are changed. Exact device identity, boot, full cached descriptors, native FD
validation, interface claim, release/close and two-second transfer bounds remain.

The selected package initializes this address through both reset scatter and
the AP_RTP loader; its normal RT check reads byte+0x0a. The32-byte prefix
also contains mode+0x10. CPU access does not prove USB DMA access. The
independent static review identified an experimental, recoverable-risk boundary:
a bus/DMA failure may timeout, stall the USB protocol or reset the controller.
This header does not select a payload memory/storage-write operation, flash,
protection setting, driver detach, device reset or retry. Its parser and USB
completion do update ordinary protocol state.
Only one request is allowed per explicit wrapper execution; any anomaly stops it.

Accepted=true here means exact OUT12/IN32 and successful release/close only.
There is no known-answer validation for this new region. Returned bytes are
opaque until separately compared with initialization and software status;
all-zero data would not by itself prove an accessible/fresh RT block. This is
different from the earlier18-byte known-descriptor test.

The helper defaults to no device access and passes26 injected I/O and stream
cases. The removed descriptor-content test is inapplicable to opaque RT data;
all lifecycle/short-count/failure/cleanup and nonseekable-stream cases remain.
Host execution refuses its non-ARM32 ABI. The five-file manifest fingerprints
the four recorded host checks and three deployment files. Live outcomes are
retained separately in the controller investigation.
