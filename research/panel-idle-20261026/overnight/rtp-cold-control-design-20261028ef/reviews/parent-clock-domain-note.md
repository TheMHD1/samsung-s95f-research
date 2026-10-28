# Parent note: future live binding must qualify clock domains

The frozen EF implementation is a pure host state machine, with no live port.
Its required `disconnectUs` and `enumerationUs` are normalized **target
monotonic** values, not an instruction to copy numbers from a kernel log.

Earlier retained SDP trace work found an approximately61.5-second offset
between trace timestamps and uptime/embedded printk in the same capture.
See `sleep-investigation-20261027a/sdp-checkpoint-runtime-audit.md`. That is
not proof of the offset between every later USB message and EH/DP's native
clock, but it rules out assuming an unmeasured common domain.

Before a real EF adapter compares lifecycle times with native read brackets,
it must establish their same-clock mapping or use explicit measured native
clock brackets with interval semantics. Preserve original message order,
boot/instance binding and the associated request evidence. Neither a changed
devnum nor an uncalibrated dmesg timestamp supplies an exact reinitialization
age. If only an interval is proved, retain that interval and change the
future normalization contract and quality calculation accordingly; do not
quietly label an identity-confirmation time as exact enumeration time.

This is a future live-adapter admission requirement. It changes no frozen
EF source or input and performs no target operation. EF's mock tests prove
ordering given valid normalized inputs, not this missing measurement.
