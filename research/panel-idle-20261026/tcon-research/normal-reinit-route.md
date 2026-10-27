# Normal panel reinitialization route (offline evidence)

## Scope

This records only the stock route visible in the copied `deviced` binary.  It
does **not** authorize calling private AVE APIs, PPI APIs, driver ioctls, or
clearing monitor/fault state.

## What the binary establishes

`deviced` owns an ordered OLED/backlight transition.

| Function | Address | Observed role |
|---|---:|---|
| `OledDeviceY23::turnOn()` | `0x81218` | Branch thunk to `backlight_on` |
| `backlight_on` | `0x5a658` | Takes the Deviced backlight lock, invokes the registered ON callback, then signals waiting state-machine clients |
| `OledDevice::turnOnTCON()` | `0x7b234` | Calls `OledDevice::setTCONState(1)` after its status/log wrapper |
| `OledDevice::turnOffTCON()` | `0x7b2d4` | Calls `OledDevice::setTCONState(0)` |
| `OledDevice::setTCONState(int)` | `0x7b150` | Deviced-internal panel state method |

The `backlight_on` path is not an exported panel command: it accesses
Deviced-private state and a registered callback.  The TCON methods likewise
are C++ methods on Deviced's initialized object graph.

## Rejected control surfaces

* AVE's `ppi_ve_*` functions rely on AVOC/AVE's initialized in-process
  backend; loading/calling them from a new process is not the stock route.
* AVE TCON functions that issue vendor ioctls are lower-level driver controls,
  not a public reinitialization service.
* The observed DeviceD `changestate(string)` method maps into generic
  system-power state machinery.  Its accepted values and authorization were
  not established as a display/TCON recovery protocol, so it must not be used
  as a guessed recovery trigger.
* `QD_TCON_OFF` is a monitor recovery-history latch.  Clearing it would not
  recreate this ordered wake sequence and could weaken recovery accounting.

## Practical conclusion

The only evidenced way to request a clean reinitialization without bypassing
fault handling is the product's normal complete power-state transition (the
physical remote/UI power transition followed by a normal wake) or a system
reboot.  The former should be tested manually with before/during/after logs;
the latter is presently the only confirmed route that rebuilds all service
state.  There is no safe external command proven by the copied firmware to
force an isolated panel/TCON reinit while the rest of the TV remains on.
