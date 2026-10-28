# Independent ERR_DET GPIO route: current evidence

This follows the accepted vendor queries0x1f/0x1d returning0x10/1. A standard
Linux GPIO character interface may provide an independent raw input sample
without QDF's cached-power or debug-output branches. Initial work used only
filesystem/device metadata. The later actual metadata-only cdev check below
opened the chip and queried its metadata. A subsequently reviewed one-shot
input sample returned1; the actual result and side effects are linked below.

## Actual metadata

[Raw metadata](gpio-route-metadata-20261026a/client.stdout) is authenticated
root, one exit0 command, no timeout, empty stderr, same boot00000000-0000-4000-8000-000000000000,
uptime76487.67..76487.77. Its framed response is7500 bytes. It shows:

- `/dev/gpiochip15`, major254/minor15, root:root0600, among60 GPIO cdev nodes.
- `/sys/class/gpio/gpiochip120/{label,base,ngpio}` = gpio15/120/8.
- Debugfs independently prints `gpiochip15: GPIOs120-127`, labelgpio15,
  parent platform4630000.pinctrl.
- GPIO125 is not exported under `/sys/class/gpio`; no value/direction file
  could be read. Debugfs has no requested gpio125 line in this sample.

The preserved device-tree property `tztv_frc_tcon/samsung,err_det` is bytes
`00000036 00000005 00000000`: phandle36, line5, flags0. The preserved
phandle36 node is gpio15; old independently recorded sysfs label/base mapping
also resolves GPIO125. This links the proposed cdev bank15 offset5 to the
stock getter's property. The pending cdev path must revalidate chip identity,
line count, flags and DT mapping before any request; filenames alone do not
prove a line's identity.

## Next work and boundaries

Review exact Linux5.4.261 fixed-width cdev ABI, ARM32 compatibility and a
single INPUT-only line request/get/release. Refuse busy/output/active-low or
unexpected metadata and retain errno. Such a request temporarily acquires the
line and sets input direction; it is not a passive memory read. It must never
request output, set a GPIO value, disable protection or hold the line open as
a monitor. Check potential contention with Samsung's own request/free getter.

Physical state during metadata retrieval was unobserved. The owner-visible
Apps comparison is still pending; no dependent visible-control query has run.


## ABI review found an additional configuration operation

The [exact Linux5.4.261 cdev review](../tcon-research/errdet-gpio-cdev-abi.md)
finds that an input line-handle request also calls `gpiod_set_transitory(false)`
before input direction. This clears the descriptor's transitory flag and may
invoke `PIN_CONFIG_PERSIST_STATE=1`; closing the handle does not restore that
configuration. The sysfs export alternative also performs the same persistence
operation and adds export/cleanup ownership concerns. Neither was executed.
The next technical prerequisite is identifying the actual bank driver's
`set_config` behavior; default assumptions about generic Linux drivers do not
establish this Samsung implementation.

A separate [controller metadata read](gpio-controller-metadata-20261026a/client.stdout)
is authenticated/root/exit0/no timeout/empty stderr, same boot,
uptime76783.19..76783.20. Device4630000.pinctrl is actually bound to
`sdp-pinctrl-v2`; its compatible is `samsung,sdp-pinctrl-v2`. No pinctrl module
is listed in `/proc/modules`. `readlink -f` printed a module-like path but that
alone does not prove that a module symlink exists; built-in binding is a
candidate, not a verified executable image attribution. Debugfs
pinctrl-devices returned its header without a registered device row, which
alone does not establish that the GPIO chip's config callback is null.

One additional [passive power-log retrieval](post-query-passive-power-log-20261026a/client.stdout)
at76840.79..76840.85 returned zero retained matches for its selected TCON power,
GPIO-fault and DPMS forms. No physical state or lack-of-event claim follows:
this is a bounded current ring-buffer read with unknown historical coverage.
No new TCON/GPIO diagnostic query, cdev open/request, sysfs export, power
control or protection/config write occurred in these metadata follow-ups.

The owner-visible Apps comparison remains pending. Source research into the
exact sdp-pinctrl-v2 callback is proceeding independently of that physical
response.


## Paired-kernel binary closes the persistence callback question

The [bounded driver analysis](../tcon-research/sdp-pinctrl-v2-config-binary.md)
was independently checked against the acquired paired boot Image. Its probe
explicitly zeros `gpio_chip+0x68` and does not populate that `set_config` slot
before registration. The exact generic helper therefore clears its Linux
software descriptor flag without calling a vendor persistence callback. This
supersedes the unresolved callback prerequisite above for that acquired Image;
it is not a hash of executing kernel text or recovery of Samsung's source.

The separate input-direction callback still performs locked register writes.
A future input request remains a temporary acquisition/configuration operation,
with possible contention with the stock getter. No line request or sysfs
export has been made. A new managed tool is being prepared with a default
metadata-only mode (chip/line information, no line handle) to validate the
actual ARM32 interface before considering a separate one-shot input sample.
No ordinary GPIO CLI or libgpiod was found in the bounded PATH/library search
retained in `gpio-user-tools-20261026a/client.stdout`; no such tool was run.

The owner's latest clarification is that the physical panel is off. This is
not confirmation of the pending visible Apps control, nor evidence of a TV
power-off. No dependent visible-control reading has been taken.


## Actual metadata-only cdev compatibility check

After independent code review, one finite managed metadata invocation completed
on the TV. [Retained result](managed-errpin-cdev/metadata-result-20261026a.json)
SHA256 `8f123bdfae89480b34f303b78b91b801181c3fe29b8b0c73e8ea3a50f6da0426`.
All11 authenticated root calls succeeded, managed stderr was empty, postflight
passed and private-helper cleanup was confirmed. Same Linux boot as prior
samples; preflight uptime78077.33 and execute end78078.73, helper PID8145 /
start19519613. Device open returned fd26; CHIPINFO, LINEINFO and close returned0
with errno0. Actual ARM32 layouts were68/72/364/64 bytes.

The chip reports name `gpiochip15`, label `gpio15`, eight lines. Line5 reports
flags0, empty name and empty consumer. Current-run sysfs device and DT phandle
joins passed. This validates the interface and point-in-time metadata; no line
handle was requested and no GPIO value was sampled. Metadata does not lock
ownership or establish electrical state. Physical panel state remains
unobserved in the machine record; the latest owner context is black/off panel.
A separate one-shot input runner is being prepared and requires its own code
review. No power, reset, protection or panel control was sent.


## Actual one-shot input sample

The separately reviewed input runner completed once and returned **1**. See
[actual result and limits](errdet-direct-actual-result-20261026.md). It uses the
standard cdev route rather than the QDF cache/debug branches. All11 root calls,
both descriptor closes, postflight and helper cleanup succeeded. It temporarily
claimed the input, executed input-direction MMIO, and cleared a software
transitory flag; no output/SET/protection/power/reset operation was sent. No
retry or polling loop is active. Owner context was black, but physical state
at the exact read is unobserved; this is not yet the visible Apps comparison.
