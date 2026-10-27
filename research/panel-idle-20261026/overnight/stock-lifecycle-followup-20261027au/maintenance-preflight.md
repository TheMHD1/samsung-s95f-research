# Read-only maintenance preflight discovery for a possible stock MODE2 test

## Result

The existing host/service getters can provide useful, bounded **reject**
signals, but they do not currently prove the full maintenance-idle premise
required by the AU readiness review.

In particular, no already-supported passive public getter was found for the
private QDF `tcon_flash_update` gate, and no public screen-state getter proves
that controller-side screen optimization/off-sensing/EL compensation is idle.
Likewise, an unbound USB interface is not proof that no userspace process has
the usbfs device open or that no transfer is in flight. Therefore a result set
such as software-upgrade key `0`, burn-in getter `0`, `GetScreenState=1`, and
all three USB interfaces unbound is correctly classified only as **no conflict
observed in those bounded host/service samples**. It is not positive clearance
for MODE2 under the strict “firmware/panel-maintenance and competing TCON
activity excluded” requirement.

No TV, root, D-Bus, VCONF, `/dev`, USB, GPIO, or network call was made for this
report. Everything below comes from retained commands and copied-code analysis.

## Exact safe public/host queries already used

The following is a compact composition of exact getter invocations already
used in the retained records. It performs only service/VCONF and procfs reads;
it does not request sensing, open `/dev/tztv_tcon`, or access USB endpoints.
Root must serialize any future execution and retain its authenticated envelope,
boot ID, both uptime anchors, stdout, stderr, and each exit status.

```sh
date -u
cat /proc/sys/kernel/random/boot_id
cat /proc/uptime
vconftool get memory/enterprise/swupgrade/working_status
echo "UPGRADE_STATUS_GET_EXIT $?"
dbus-send --system --print-reply --reply-timeout=1500 \
  --dest=org.tizen.system.deviced \
  /Org/Tizen/System/DeviceD/Display \
  org.tizen.system.deviced.display.GetPowerState
dbus-send --system --print-reply --reply-timeout=1500 \
  --dest=org.tizen.system.deviced \
  /Org/Tizen/System/DeviceD/Display \
  org.tizen.system.deviced.display.GetScreenState
dbus-send --system --print-reply --reply-timeout=1000 \
  --dest=org.tizen.system.deviced \
  /Org/Tizen/System/DeviceD/Display \
  org.tizen.system.deviced.display.BurnInProtectionInProgress
cat /proc/uptime
cat /proc/sys/kernel/random/boot_id
date -u
```

The exact historical sources and results are:

| Getter | Retained result | Source-backed meaning | Limit |
| --- | --- | --- | --- |
| `memory/enterprise/swupgrade/working_status` | integer `0`, getter exit `0`, uptime `44109.06..44109.18` | The recovered reinforce-notification consumer treats value `1` as “suppress the notification while software upgrade is working”; its other path writes value `2` itself before launching the notification. | Value `0` proves only that this VCONF key was not `1` at the sample. It does not expose QDF's private flash gate or prove that every firmware updater is idle. Process absence must not be substituted for that missing fact. |
| `GetPowerState` | string `lcdon`, uptime `34606.16` | Exact `deviced` table value/index `1`. | Daemon power policy state, not measured light and not maintenance state. |
| `GetScreenState` | integer `1`, same sample | A separate public screen-state accessor. | It is explicitly not the `deviced` power enum, an optimization-state enum, or the controller's update/maintenance gate. No recovered source assigns “maintenance idle” to integer `1`. |
| `BurnInProtectionInProgress` | integer `0`, uptime `43690.51..43690.61`; also `0` after the old direct-state snapshot | The copied client returns true only when the parsed reply is exactly integer `1`. Thus `1` is a source-backed positive/busy public result and should reject a test; `0` is false at this API boundary. | The retained analysis does not prove that this one Boolean covers every off-sensing/EL/TCON state or an MCU firmware update. A zero is useful negative bookkeeping evidence, not a global controller-idle proof. |

Relevant retained records are:

* `optimization-notification-process-state-20261026T134819Z.json`, SHA-256
  `e3d03cead23d8773809a44825c2c6a2314a90e04f876f82b7c45fb66da1e4119`;
* `power-contract-baseline-20261026T110956Z.json`, SHA-256
  `6cc68868952b28300cc0a95cf50ba4fdb4d7d13266c71208d1ee9d791a746bec`;
* `optimization-factory-period-baseline-20261026T134120Z.json`, SHA-256
  `b091fd13906c38e5180ffebad6392bb10bc5384c01c5f98dfc00ee420cda5acd`;
* `tcon-research/app-control-off-sensing-producer.md`, SHA-256
  `2a3ddf2336b271bc0504fd11528b4ba293c931b15e70e5fe1c3a8e1192caf3c5`;
* `tcon-research/maintenance-ipc-client.md`, SHA-256
  `7614aca39a44d78acd06445595b672bc4047362147cea4fd71d65f5ed141b454`.

### Factory item 200802 is not an in-progress getter

The already-used read-only FactoryService request is:

```sh
dbus-send --system --print-reply --reply-timeout=1500 \
  --dest=org.tizen.tv.factory-service \
  /TIFacSerObj \
  org.tizen.tv.factoryservice.GetItem int32:200802
```

It previously returned label `Offsensing TEST Period` and value string `"0"`.
Copied `deviced` proves only that a successful read equal to `6` makes its
specific factory-disable predicate true. The other values have no recovered
duration or in-progress meaning. The named VCONF key was absent, so the
service's `0` may be a fallback/default. Consequently this getter may be
retained as configuration context, but neither `0` nor any non-`6` value is
maintenance-idle evidence. No setter belongs in a preflight.

## Stronger daemon state existed once, but it is stale and not a public getter

The old read-only snapshot
`runtime-deviced-state-20261026T114500Z.json` (SHA-256
`b052d21308fd78316b4c159edc1e70055f168612552462b4a569d53b0e02a844`)
validated the exact `deviced` executable, PIE maps, selectors, selected object
pointers and vtables, then bracketed direct `/proc/675/mem` reads. At uptime
`36710.33..36710.37`, its paired fields agreed and reported:

* selected legacy EL local state `+0x30 = 0`;
* selected legacy off-sensing local state `+0x24 = 0`;
* daemon power index `1` (`lcdon`); and
* subsequent `BurnInProtectionInProgress=0`.

The static map gives those object words more specific meaning than the public
screen getter: EL start rejects an already-`2` object and a qualifying
successful start changes the word to `2`; off-sensing's ordinary suspend
start path requires `+0x24 == 0`, while other lifecycle paths change and
consume that state. This supports “selected daemon objects were in their
zero/pre-start-compatible state at that old, non-atomic sample.” It does not
prove a lower TCON operation was absent, and it is not current.

The old command hard-codes PID, load bias, object addresses, and one boot ID.
Replaying it is unsafe and invalid after PID/map/object changes. The existing
`tcon-research/deviced-runtime-observer-map.md` (SHA-256
`b8c0301a7aa60b1cddd3eddb6d97eb5250650e5f767b2a66555d2c3635e35324`)
requires fresh identity/map/pointer validation and paired reads. Creating a
new collector or equivalent observer is outside AU discovery scope, so this
historical result cannot satisfy a current precondition.

Also exclude `qd_display_get_state`/`GetQDDisplayState` from a passive
preflight. Its recovered provider can acknowledge/save results while
classifying off-sensing state. It is not a harmless observer even though its
name resembles a getter.

## The actual MCU firmware-update gate remains unexposed

The exact copied QDF path identifies the private gate. In
`QDFTcon_GetErrDetStatus`, QDF BSS `tcon_flash_update +0x6c == 1` returns zero
without issuing its normal controller transaction and without changing the
output word. This is the relevant MCU/QDF busy gate; it is distinct from:

* `memory/enterprise/swupgrade/working_status` (host notification/update
  policy);
* `BurnInProtectionInProgress` (public daemon Boolean); and
* `GetScreenState` (public screen bookkeeping).

No retained sysfs, VCONF, D-Bus, or procfs getter exposes this private word.
The generic operation-19 read used elsewhere does not check it at all.

There is one **active**, already-built indirect discriminator: the existing
sentinel-based stock error-status helper initializes word1 to `0xa55a5aa5`.
On the statically recovered exact path, an accepted changed-sentinel result
implies the `tcon_flash_update == 1` bypass was not taken at that instant.
However, this helper opens `/dev/tztv_tcon` and, when gates permit, sends
`f3 80 00 00 00 08` over I2C and reads four bytes. Controller read-to-clear or
other stateful semantics are not excluded. It is therefore not a passive
host/service preflight getter, and this report neither invokes nor clears it.
An unchanged sentinel is ambiguous among the flash gate and several other
skip/missing-interface conditions. See
`tcon-research/qd-error-status-read-abi.md`, SHA-256
`3812ca30cd846e0aee4e85da0716577c781939972d1836eeca41624b2ef0e3d1`.

Thus, under a strict “no active controller query before MODE2” rule, current
MCU-update idle cannot be positively proved with the discovered interfaces.
If a future plan elects to use the existing active status getter, that is a
separate reviewed operation and still only samples the gate at its own call
time; it does not eliminate the race before MODE2 dispatch.

## USB binding/owner checks already available

The most complete retained read-only USB topology command is preserved in
`rt-telemetry-followup-20261027b/usb-one-chunk-preflight-metadata.json`,
SHA-256
`679cc6aa3889989a64f6b6401916c43d067b51ff06e3c9d7ca5aecb04c1c597c`.
Its relevant exact fragment is:

```sh
set -eu
cat /proc/sys/kernel/random/boot_id
cat /proc/uptime
p=/sys/bus/usb/devices/7-1
for n in idVendor idProduct bcdDevice busnum devnum bConfigurationValue authorized product manufacturer power/runtime_status; do
  echo FIELD=$n
  cat "$p/$n"
done
for i in /sys/bus/usb/devices/7-1:1.0 /sys/bus/usb/devices/7-1:1.1 /sys/bus/usb/devices/7-1:1.2; do
  echo INTERFACE=$i
  for n in bInterfaceNumber bAlternateSetting bInterfaceClass bInterfaceSubClass bInterfaceProtocol; do
    echo FIELD=$n
    cat "$i/$n"
  done
  if test -L "$i/driver"; then
    echo DRIVER
    readlink -f "$i/driver"
  else
    echo UNBOUND
  fi
done
cat /proc/sys/kernel/random/boot_id
cat /proc/uptime
```

At uptime `98176.31..98176.36` it identified `7-1` as
`04e8:2001`, revision `0250`, `STL1 CDC and Bulk`, authorized/configuration1,
runtime status `active`, and interfaces `02/02/01`, `0a/00/00`, and
`ff/00/00`; all three driver links were absent. An earlier independently
retained metadata command at uptime `83382.46..83382.52` reported the same
three unbound interfaces (`qd-usb-interface-metadata-20261027a/client.stdout`,
SHA-256
`065113d8f9d133570a72a4c086e2fdbff26567c9f8c082612f794f7414430530`).

Interpretation is deliberately narrow:

* a present driver symlink is a positive competing kernel binding and should
  reject the action;
* `UNBOUND` proves absence of a sysfs driver link for that interface at that
  sample only;
* `runtime_status=active` is USB runtime-PM state, not proof of an owner or a
  transfer;
* `authorized=1` means the device is authorized, not idle; and
* cached descriptors and stable identity do not prove parser readiness or no
  in-flight userspace access.

One existing preflight also ran `fuser` against the current usbfs node:

```sh
n=$(cat /sys/bus/usb/devices/7-1/devnum)
node=$(printf '/dev/bus/usb/007/%03d' "$n")
if fuser "$node" 2>&1; then
  echo FUSER_PRESENT
else
  echo FUSER_NO_HOLDER_OR_ERROR
fi
```

At uptime `114228.71` it printed `FUSER_NO_HOLDER_OR_ERROR` while interface
`1.2` was unbound. The output intentionally conflates “no holder” with a
tool/permission/error case, so it is not positive no-owner evidence. The
record is `finite-onset-logger-20261027g/prequalified-smoke-metadata.json`,
SHA-256
`f72d83ed106fc3204357d5a7320cf4ca0ca494201fc1cf0a9011aa3ef13d43d5`.
Even a successful full `/proc/*/fd` census would be a racy userspace snapshot;
it would not exclude a kernel owner, an open created just after the census, or
an already in-flight transfer. Process absence must not be promoted to global
USB idle.

## Bounded preflight decision table

| Observation immediately before a proposed action | Defensible decision |
| --- | --- |
| getter error, timeout, boot change, malformed type, or identity drift | Reject; state is unknown. |
| software-upgrade key `1` | Reject: exact recovered consumer treats this as upgrade-working suppression. |
| `BurnInProtectionInProgress == 1` | Reject: public client classifies exactly `1` as true. |
| any other nonzero burn-in value | Reject conservatively as unqualified; do not invent an enum. |
| `GetPowerState`/`GetScreenState` unexpected | Reject under whatever separately reviewed action-state contract applies; do not call the values maintenance enums. |
| Factory item 200802 equals `0` | Configuration context only; neither accept nor reject maintenance from this value. |
| any `7-1:*` driver link present or `fuser` positively returns a holder | Reject as observed competing ownership. |
| all interfaces unbound and `fuser` says `NO_HOLDER_OR_ERROR` | Partial negative only; not proof of no userspace holder or in-flight transfer. |
| public/VCONF values look idle and USB is unbound | Still does not prove QDF `tcon_flash_update != 1` or controller maintenance idle. |

## AU prerequisite status

For the strict readiness condition in `readiness-review.md`, this discovery is
**blocked on a missing positive source**, not cleared by the available zeros:

1. The public service bundle can reject obvious host-policy or burn-in busy
   states.
2. USB sysfs can reject an observed kernel binding and preserve exact device
   identity.
3. The old direct `deviced` object snapshot proves only a historical,
   non-atomic zero-state sample and cannot be replayed with hard-coded
   addresses.
4. No passive existing getter proves the current private MCU flash gate or
   globally excludes controller-side screen optimization/compensation.
5. No standalone owner census can atomically exclude a competing USB/TCON
   actor through the later MODE2 dispatch.

Accordingly, root may safely use the exact public/sysfs queries above as
fail-closed **prechecks**, but their passing results must not be presented as
the positive maintenance-idle proof requested by AU. Resolving that proof
would require either an already-supported direct passive busy-state source or
a separately reviewed change in the experiment's admissibility/serialization
contract. Neither is introduced here.

## Addendum: operation 41 is not interlocked against the proved QD updater

### Bounded answer

**No.** The stock `/dev/tztv_tcon` ioctl wrapper holds its own
`tcon_ioctl_mutex` across the complete operation-41 callback, so two requests
that both enter through that same file-operation domain are serialized.
However, the copied exact-build modules also contain a QD firmware-update
worker that uses a different mutex and calls the update API without passing
through that TCON ioctl wrapper. QDF's power-control wrapper and lower
`m_set_power_control` neither check `tcon_flash_update` nor acquire a common
lifecycle-wide mutex. The private update word is an advisory gate used by
selected commands, not an atomic exclusion interlock for power control.

This is a positive path mismatch, not an inference from mutex names:

1. In copied `tztv_frc_tcon.ko` SHA-256
   `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd`,
   ARM32 operation 41 reaches `fop_tcon_compat_ioctl`. It constructs
   `.data+0xd8`, the symbol-table object `tcon_ioctl_mutex`, and calls
   `mutex_lock` at `.text+0x2780`. The indirect exported API call is at
   `0x27b8`, and the normal unlock is at `0x27d4`. Thus the lock remains held
   while `TCON_Request` dispatches mode 2 and while QDF runs both off and on
   halves. The native ioctl has the same span: lock `0x2910`, callback
   `0x2948`, unlock `0x2964`.
2. The proved QD upgrade worker in that same module is
   `tztv_frc_tcon_qd_upgrade_th_fn` at `0x2b00`. On its type-8 branch it
   constructs `.data+0xb0`, symbol `frc_ioctl_mutex`, locks it at `0x2c10`,
   invokes the callback loaded from module BSS `+0x8` at `0x2c44`, and unlocks
   at `0x2c20`. `.data+0xb0` and `.data+0xd8` are distinct 40-byte mutex
   objects. Therefore this worker does not block on operation 41's
   `tcon_ioctl_mutex`.
3. The callback identity is positive rather than inferred. In the provider's
   resolver, `.text+0x532c/0x5330` materializes the exact string
   `device_upgrade`; `0x5338` resolves it and `0x5348` stores the result in
   BSS `+0x8`, the word consumed by the worker. In copied
   `tztv_frc_tcon_api.ko` SHA-256
   `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6`,
   `device_upgrade` is `.text+0x7dd8`. Its type-8 branch calls interface slots
   `+0x150` and `+0x128` at `0x7e40` and `0x7e5c` without taking
   `tcon_ioctl_mutex`.
4. QDF initialization positively maps those two type-8 slots: init
   `0x2a8` stores `QDFTcon_UpgradeFlashFirmware_se` at table `+0x148` and
   `QDFTcon_UpgradeFlashFirmwareCAD` at `+0x150`; init `0x1c4` stores
   `QDFTcon_UpgradeFlashData_se` at `+0x120` and
   `QDFTcon_UpgradeFlashDataCAD` at `+0x128`. The CAD-data wrapper at
   `.text+0x13568` calls `m_tcon_upgrade_data_cad` at `0x135bc`, whose ordinary
   update path calls `m_tcon_flash_upgrade` at `0x133a4`.

The QDF-side evidence is in copied `qdf_tcon.ko` SHA-256
`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`:

* `m_tcon_flash_upgrade` (`0x12218..0x12c97`) stores plain integer `1` to
  BSS `+0x6c` (`tcon_flash_update`) at `0x1225c`. Its single return is at
  `0x12434`, after the common epilogue clears that word at `0x12414`.
  No mutex lock/unlock call spans this body.
* The function can itself call `m_set_power_control(0)` at `0x12b20` and
  `m_set_power_control(1)` at `0x12b2c` before it reaches the common flag-clear
  epilogue. This directly shows that `tcon_flash_update == 1` is not treated
  by the power function as an exclusion condition.
* Other update-family bodies use the same plain gate pattern, for example the
  SE path stores `1` at `0x8d1c` and clears it at `0x8ef8`. These stores may
  suppress selected getters/monitor work, but a plain flag does not serialize
  a caller that never reads it.
* `QDFTcon_SetQdTconPowerControl` (`0x11c48..0x11d77`) calls off at `0x11ce0`
  and on at `0x11cec`. Neither this wrapper nor the full
  `m_set_power_control` body (`0x11848..0x11b87`) loads BSS `+0x6c`, calls a
  QDF mutex wrapper, or performs an atomic flag test/set. Its GPIO/reset calls
  and sleeps are therefore not inside the per-command `frc_tcon_mutex`.
* Some transitive on-tail I2C helpers do take `frc_tcon_mutex` for individual
  transfers. Existing exact analysis shows that is a per-command transport
  lock, not a lock held over power-off, waits, power-on, and recovery tail.
  Individual transfer serialization cannot be promoted to an atomic MODE2
  versus firmware-update exclusion.

### Consequence for the fresh public preflight

The fresh AU public/getter record
`current-host-preflight.json`, SHA-256
`208cb5d8ba152ce5c7a615ace947b27cdacb4ff89700f9eda57a303879bc8bc9`,
at uptime `135607.81..135607.91`—software upgrade status `0`, `lcdon`, screen
state `1`, and `BurnInProtectionInProgress=0`—remains useful bounded
no-conflict evidence.
It does not close this kernel race. A successful changed-sentinel status
getter would strengthen the evidence to “the private flag was not `1` at that
getter's branch,” but the update worker can set it after the getter and before
or during operation 41. Operation 41 has no compare-and-lock handoff from that
sample.

Therefore the earlier AU prerequisite result stands: the exact public checks
may reject a known busy state, but the copied stock code does not supply the
required atomic update-versus-MODE2 interlock. This report cannot classify a
subsequent MODE2 dispatch as concurrency-safe merely because the public
preflight passed. It makes no claim that an updater is actually running or
that every possible update caller has been enumerated; the one positively
bound background path is already sufficient to disprove global serialization.
