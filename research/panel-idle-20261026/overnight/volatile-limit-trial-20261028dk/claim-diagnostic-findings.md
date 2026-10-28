# Completed zero-vendor binding diagnostic

DO `claim-diagnostic-01` completed once and was accepted for its diagnostic
lifecycle. Self-test and production used separate exclusive receipt files;
runtime stdout was not interpreted as the receipt. Fixed USB58/interface2
open/claim/release/close succeeded. All three vendor-operation counters and
target-memory-write count are zero. The exact staged files were removed.

Before claim, native readlink/statx found no interface-driver link (ENOENT2),
.NET LinkTarget was null and both existence predicates were false. The
kernel-cached GETDRIVER call returned -1/ENODATA61 and no driver name.

After this program's successful claim, native readlink and .NET LinkTarget both
retained `../../../../../../../bus/usb/drivers/usbfs`. Native no-follow statx
reported a symlink (mode41471); follow statx reported a directory (mode16877),
inode23111. The separately retained expected `/sys/bus/usb/drivers/usbfs`
directory has the same inode on sysfs. The kernel-cached GETDRIVER call returned
0/errno0/name `usbfs`. Directory.Exists was true and File.Exists false.

Crucially, DirectoryInfo.ResolveLinkTarget(true).FullName, called through the
aliased `/sys/bus/usb/devices/7-1:1.2/driver` path, returned
`/bus/usb/drivers/usbfs`. That differs from the expected absolute driver path
and explains DN's exact predicate refusal. The native follow and kernel name
observations support an alias-resolution mismatch in our guard, rather than
evidence that a foreign driver owned the successfully claimed interface. This
does not claim every .NET version or every filesystem path behaves the same.

DN's original target refusal remains rejected; no receipt is retrospectively
accepted. Its exact cleanup is separate. A new DQ source revision will check
the kernel-cached driver identity after its own successful FD claim and use
native canonicalization or checked native filesystem identity rather than the
managed alias-derived path. It must preserve the fixed controller profile,
transaction/ambiguity rules, source pins and explicit preclaim absence check.

DO's `driverPolicyEstablished=false` remains unchanged: its acceptance is only
the completed diagnostic lifecycle. Parent interpretation of the observed
fields does not alter that contract. No endpoint liveness, physical picture,
threshold change, permanent fix, firmware flash or boot modification follows.

Sources are `claim-diagnostic-01/result.json`, `native.receipt.json`,
`record.json`, and `usbfs-static-metadata/metadata.txt`. Upstream ABI/handler
proof is in `../usb-owned-claim-diagnostic-20261028do/upstream-linux/abi-proof.json`.
