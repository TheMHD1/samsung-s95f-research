# Factory screen-saver brightness path (exact module analysis)

This is an offline analysis of the captured `qdf_tcon.ko`; it is not an
instruction to call private kernel functions or write a factory setting.

## Two different setters

`QDFTcon_SetQdSsBrightness(int)` is the normal, runtime brightness setter.
Its accepted inputs are `0`, `1`, and `101..107`:

* `0` uses brightness zero;
* `1` substitutes the current `m_fac_ss_brightness` value;
* `101..107` map to direct brightness `1..7`.

The low-level `m_set_ss_brightness()` admits only `0..7` and sends the normal
TCON SS-brightness command.  For normal calls the wrapper updates only
`m_ss_brightness`.  It does **not** modify `m_fac_ss_brightness`; therefore a
later `value=1` command from AVEMonDIM restores the existing factory value.
This exactly explains the observed `0` at picture return followed by
`Fac_ss:7, value:1` around 30 seconds later.

`QDFTcon_SetFactoryData(0x5019, value)` is a distinct factory-data branch.  It
stores `value` to both `m_ss_brightness` and `m_fac_ss_brightness`, then calls
the same bounded `m_set_ss_brightness(value)`.  The module code for that branch
contains no flash, EEPROM, file, vconf, or save-type operation: its immediate
state is RAM in the loaded QDF module.  Module initialization sets both fields
to `-1` before another component loads factory data.

## Why this does not authorize a trial

The factory-data function is a kernel-internal function (not an exported public
userspace interface).  No public ioctl/proc/sysfs ABI for factory item `0x5019`
was found in the captured QDF/FRC/SDP modules.

The exported AVE function `ave_tcon_api_set_qd_ss_brightness(int)` is *not* the
factory setter: it issues the regular device ioctl `0xc010749f`, operation
`0x20`, with the requested scalar.  It cannot replace factory brightness seven
used by a later `value=1` command.

The similarly named `ave_tcon_api_set_factory_data(int, int)` is not a usable
shortcut either.  It tail-calls `ave_common_set_factory_data(int, int)`, whose
exact code performs availability, initialization, and range checks rather than
issuing the QDF factory-data operation.  AVE's other factory-item pathways are
in-process interfaces, not a captured public no-save service API.

Thus a direct ordinary brightness-zero call would be transient, and reaching
the factory branch by guessed ioctl, direct kernel invocation, module patching,
or process injection would be unsupported.  None is a safe reversible test.

## Service-menu evidence and boundary

Independent S95F owner reports consistently identify the UI factory item as
`Control -> QD Option -> Screen Saver Brightness`, default seven, with zero
used to disable the static-brightness limiter.  That matches the exact code and
captured `Fac_ss:7` log.  These reports are corroborative only, not a vendor
API specification.  They also report that such changes can survive normal user
settings resets or be overwritten by firmware, so the service menu must **not**
be represented as a three-minute RAM-only trial.

The live factory-service object now identifies `Control 2 -> QD Option 802 ->
child 5` as scalar key `60802`, label `Screen Saver Brightness`, current value
`7`.  This is strong runtime corroboration of the UI-to-QDF linkage.  Its
two-argument `SetDecimalValue` client has no demonstrated no-save flag and the
factory stack imports persistent/NVRAM write facilities.  Treat it as
potentially persistent: obtain the current scalar first and restore that exact
value after any owner-authorized single-key test.

No other QD/ISP brightness, slope, wait-time, thermal, fault, voltage, or
calibration setting should be changed as part of this narrow hypothesis.
