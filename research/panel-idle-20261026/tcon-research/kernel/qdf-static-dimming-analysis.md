# QDF static-dimming path — offline module analysis

Modules inspected, read-only:

- `qdf_tcon.ko`, Build ID `ae35362dde61127ad6c9d85292b612fd978a02f6`
- `tztv_frc_tcon.ko`, Build ID `96d24eaf49d6cc43674e70269c7ec246f3cb3162`
- `sdp_tcon.ko`, Build ID `217c7fcac3a0fa4163e5a407e641ca314b5fd47e`

## Observed event

In `on-then-black-20261026.json`, the TCON completes the normal `deviced`
off-sensing power cycle and reports picture-on at uptime 3869.513. `AVEMonDIM`
immediately sends screen-saver brightness 0. At 3899.561, 30.048 seconds later,
it sends screen-saver brightness 7. This interval contains no ERR_DET record;
the next monitor report records TCON state 1 and PMIC/LPDDR status OK.

The timing makes this a correlation worth instrumenting.  It does not prove
that either command value controls physical OLED emission: a visibly stable
wake later showed the same command transitions.  It also does not identify a
safe direct driver control.

## Exact brightness semantics

`QDFTcon_SetQdSsBrightness` at qdf `.text+0xec00` uses an encoded input:

| Input | Effect |
|---:|---|
| `0` | Send the driver’s screen-saver brightness command payload 0. |
| `1` | Load and send the factory screen-saver brightness (`m_fac_ss_brightness`; current value 7). |
| `101` through `107` | Send level 1 through 7 respectively. |

The lower helper `m_set_ss_brightness` accepts payload values 0 through 7 and
sends TCON command `0xf300000000c4` with the selected numeric payload.
Therefore the log `Fac_ss:7 value:1` is not a boolean “static dimming enabled”
flag: it is the special factory-restore request that ultimately sends payload
7.  The proprietary panel firmware's emitted-luminance interpretation of those
payloads was not acquired, so payload 0 must not be equated with a physically
black panel from this code alone.

The only internal uses visible in this module are factory/resume restoration.
The observed active caller is external `AVEMonDIM`; its PID/name is in the
kernel log. Calling the exported kernel function or injecting its TCON command
would bypass the owning policy and is not a supported or safe experiment.

## ERR_DET separation

`QDFTcon_GetErrDetStatus` reads TCON command `0xf38000000008` and logs its raw
returned register value, including the previously observed `0x10`. The FRC
module's separately named `err_det` routine reads a raw GPIO and returns its
level through an output integer. No bitfield labels for raw register bit/value
`0x10` occur in the three exact modules, so this analysis cannot assign it a
hardware meaning. It must not be conflated with the GPIO level or disabled.

The historical ERR_DET GPIO fault remains a distinct recovery/fault path. The
current 30-second event has no such record and should be investigated as a
static-dimming/policy trigger rather than by suppressing fault recovery.

## Policy boundary

The supported reversible surface already identified is the `deviced` display
state lock (`lcdon` with `gotostatenow`) and its matching unlock. It can be
used only for a measured, finite A/B test of whether preventing normal display
idle transitions prevents the `AVEMonDIM` 0-to-factory-7 sequence. It does not
change the QDF command, disable ERR_DET, alter thermal/panel protection, or
repair a genuine panel/TCON fault.

No module unload, register write, GPIO manipulation, direct ioctl, or binary
patch is recommended by this analysis.
