Same recorded boot/USB58 as the accepted DH02 stock initialization. DJ only ran
its completed zero-I/O self-test. DL and DN each completed a single open, cached
descriptor validation, successful claim, pre-vendor driver-guard refusal, release
and close. All exact stages were removed after authenticated receipt/file hash
checks; original rejections remain. No controller vendor headers, bulk/control
transactions, RAM writes or reset have occurred since that initialization. Later
TV calls are ordinary Apps wake and cached filesystem metadata reads only.
The parent is the sole TV coordinator; agents are host-only. DO is strictly a
kernel-cached metadata/claim/release diagnostic with no controller vendor path.
Its new receipt must not be treated as qualification of a subsequent driver
policy without examining actual results. The inherited conditional first-header
premise remains untested by this zero-vendor operation; neither FD census nor
cached metadata nor claim success proves endpoint queue liveness or continuous
global exclusion. A fresh cached identity/FD census is required before invocation.
