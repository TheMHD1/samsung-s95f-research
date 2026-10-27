# QD sensing entry ABI and caller boundary

## Scope and result

This is an **offline static** trace of the copied S95F components.  It maps the
two QD sensing requests to the normal AVE TCON ioctl and then to the registered
QDF callbacks.  It does not send an ioctl, a private-bus command, or alter TV
state.

The trace establishes an exact transport path, but does **not** establish that
either request occurred at the owner's black-screen onset, that a particular
Home/Live page issued one, or that sensing caused the fault.

| Request | libave API | 16-byte request `word[0]` | API-module callback slot | QDF implementation |
|---|---|---:|---:|---|
| off sensing | `ave_tcon_api_set_off_sensing(int)` | `9` | `table + 0x350` | `QDFTcon_SetOffSensing(int)` |
| EL sensing | `ave_tcon_api_set_el_sensing(int)` | `15` | `table + 0x360` | `QDFTcon_SetElSensing(int)` |

Both APIs issue ioctl command `0xc010749f`.  The scalar `int` argument is
placed at `word[1]` (offset `+4`) of the 16-byte request.  That is the ABI
boundary needed to distinguish a real enable (`word[1] == 1`) from status or
availability observations.

## Binary provenance

* `binaries/libave.so.0.1` — ARM32; SHA-256
  `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`.
* `binaries/tztv_frc_tcon_api.ko` — AArch64; SHA-256
  `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6`.
* `binaries/qdf_tcon.ko` — AArch64; SHA-256
  `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`.

Addresses below are module-relative `.text` addresses (or ELF virtual
addresses for `libave`), not stable runtime/kernel addresses.

## Exact path

```text
libave caller
  └─ ave_tcon_api_set_{off,el}_sensing(enable)
       request = { operation: 9 or 15, enable, ... }
       ioctl(0xc010749f, request)
          └─ tztv_frc_tcon_api:fop_tcon_ioctl_export
               copy 16 bytes from userspace; TCON_Request(request)
                 ├─ operation 9  → callback at interface-table +0x350
                 │                  (argument request.word[1])
                 └─ operation 15 → callback at interface-table +0x360
                                    (argument request.word[1])
                      └─ qdf_tcon registered SetOff/SetEl implementation
```

## Service-facing PPI bridge (new copied facade)

The newly preserved `binaries/libdisplay-panel.so.0.1` closes a different,
service-facing edge.  Its SHA-256 is
`6cf2a638ee97772f181847e55dd9d661d9620d2601d5e0ed227562dbfa0106e8`.
`deviced` imports both `ppi_displaypanel_set_offsensing` and
`ppi_displaypanel_set_elsensing` from this facade (the corresponding PLT/GOT
relocations are `0x0012a0e0` and `0x0012a0d0`).  This establishes that the
device-management service can enter a sensing-control interface without going
through the named `libave` exports.

The facade's two exported Thumb wrappers are direct tail dispatchers over a
loaded backend table:

| PPI facade API | ELF symbol | Thumb entry | backend callback table slot |
|---|---:|---:|---:|
| `ppi_displaypanel_set_offsensing(int)` | `0x46ef5c9d` | `0x46ef5c9c` | `+0x2c` |
| `ppi_displaypanel_set_elsensing(int)` | `0x46ef5bb5` | `0x46ef5bb4` | `+0x30` |

Each wrapper saves its sole scalar argument, verifies the common facade state
and its backend-table pointer, loads the relevant slot, restores that scalar
to `r0`, and tail-branches to the backend callback.  An absent facade state or
slot produces `-95` (`-EOPNOTSUPP`) after a diagnostic, rather than fabricating
a setter success.  Adjacent status wrapper
`ppi_displaypanel_get_elsensing_status` uses table slot `+0x34`, which supports
the slot interpretation.

The copied implementation is now available: `/prd/usr/lib/libdisplay-panel-impl.so`
resolves to `binaries/libdisplay-panel-impl-sec.so.0.1` (SHA-256
`40df6d6e83da608e47d0143c268a964d97fddc7010972b5842f0e21f9b058ca4`).
It has a `DT_NEEDED` dependency on `libave.so.0` and supplies matching
callbacks `displaypanel_impl_set_offsensing` (Thumb entry `0x7e84`) and
`displaypanel_impl_set_elsensing` (Thumb entry `0x7df0`).  Each wrapper enters
the corresponding `DisplayPanelImplSec` method:

* `setOffsensing(bool)` at `0x651c` calls the `ave_api_set_off_sensing` PLT
  slot (GOT relocation `0x1b26c`);
* `setElsensing(bool)` at `0x64c4` calls the `ave_api_set_el_sensing` PLT slot
  (GOT relocation `0x1b04c`).

Thus the copied artifacts now prove this static, linked chain:

```text
deviced import → libdisplay-panel PPI wrapper (+0x2c / +0x30)
  → designated impl-sec setter export → DisplayPanelImplSec method
  → libave ave_api_set_{off,el}_sensing → [previously traced AVE ioctl route]
```

The implementation also exports `displaypanel_impl_set_funcs(ppi_displaypanel_funcs*)`
at `0x8bc0`, a table-population helper.  Static code proves it populates a
function table, but this copied set does not provide an observed runtime table
pointer or loader-call trace tying an individual loaded pointer value to the
facade's `+0x2c/+0x30` fields.  The symbol/name and plugin ABI close the
intended backend bridge; the exact live pointer contents remain intentionally
unclaimed.

`libdisplay-panel-init.so.0.1` (SHA-256
`d90147178b8f3081b442d31ebf7808aa2dfd0474f924ba33d72c016ee03d08ea`) is
also copied, but contains only the distinct framebuffer helper exports
`displaypanel_impl_set_funcs_fb` and `displaypanel_backend_data_inject_fb`; it
does not add a sensing-to-AVE path.

`deviced` also carries named sensing state-machine symbols (`OffSensing`,
`ELSensing`, `OledDevice::start/stopOffSensing`, and
`OledDevice::start/stopELSensing`), consistent with it being a lifecycle
orchestrator.  In this bounded pass, direct call sites to the two PPI imports
were not attributed to a particular one of those methods: the executable's
PIC/GOT call sequences need a full control-flow/GOT analysis.  Import presence
is not sufficient to select a caller, and no such caller is asserted here.

### Userspace request construction

`libave` has direct, named constructors for these requests:

* `ave_tcon_api_set_off_sensing(int)` starts at `0x25be04`.  It preserves the
  caller's `r0`, stores operation `9` at request offset `+0`, stores the
  supplied scalar at offset `+4`, then calls the local `tcon_ioctl` helper
  with `r0 = 0xc010749f`, `r1 = request` (`0x25be12..0x25be2c`).
* `ave_tcon_api_set_el_sensing(int)` starts at `0x25bea0`.  It is the same
  layout except operation `15` (`0x25bec4..0x25bec8`).

Those two functions are the confirmed native userspace entrypoints.  Symbols
also expose broader names such as `ave_api_set_off_sensing`,
`ave_api_set_el_sensing`, `ave_ew_api_qd_*_sensing`, and
`VideoEnhancerImpl::qd_*_sensing(bool)`.  The copied binary does not, by
itself, identify the process/event that invokes those exports at runtime; in
particular, a nearby class method or symbol name is not proof that `deviced`,
Home, Live, or a screensaver called the ioctl.

### Direct public AVE-to-TCON edge

On the eligible path, public `ave_api_set_off_sensing` (Thumb entry0x28a4f4)
restores its saved scalar to r0 at0x28a56e and calls PLT0x8e628 at0x28a572.
That PLT entry uses GOT0x5a55f0, whose relocation names
`ave_tcon_api_set_off_sensing(int)` (symbol0x25be05). Public
`ave_api_set_el_sensing` (entry0x28a61c) restores r0 at0x28a696 and calls
PLT0x8bb98 at0x28a69a, GOT0x5a47c0, relocated to
`ave_tcon_api_set_el_sensing(int)` (symbol0x25bea1). These direct edges close
the public-AVE-to-request-constructor step without requiring an inferred
VideoEnhancer/EW virtual hop. Earlier initialization/error guards can return
before the setter call; this is linked control flow, not proof every public
invocation reaches the bus.

The impl-sec table-population proof is also explicit: `displaypanel_impl_set_funcs`
uses GOT base0x1b000, literals0x348/0x32c at0x8dec/0x8df0, and thus GOT
0x1b348/0x1b32c relocated to off/EL implementation exports. Stores at0x8c10
and0x8c16 put them into table+0x2c/+0x30. This is static table construction;
no live pointer or caller occurrence is inferred.

### Kernel-side decoding

`fop_tcon_ioctl_export` is exported at `tztv_frc_tcon_api.ko:.text+0x3048`.
Its ioctl jump table maps `0xc010749f` to `.text+0x3b78`:

1. It copies exactly 16 bytes from the userspace pointer into kernel stack
   storage (`0x3be0..0x3bf0`).
2. It calls `TCON_Request` at `.text+0xe7b0` (`0x3bf8..0x3bfc`).
3. `TCON_Request` validates `operation` in `[1,99]`, selects a 16-bit jump
   table entry indexed by `operation - 1`, and dispatches through the
   registered interface table.

The two relevant handlers are exact:

* operation `9` jumps to `.text+0xf258`, loads a function pointer at
  `interface + 0x350` (`0xf264`), loads `request.word[1]` (`0xf26c`), and
  calls it (`0xf270`);
* operation `15` jumps to `.text+0xf028`, uses `interface + 0x360`
  (`0xf034`), passes `request.word[1]` (`0xf03c`), then calls it (`0xf040`).

This is direct ABI evidence that these are setters, rather than a status
getter or a passive availability timer.

### QDF registration and command-skip consequence

`qdf_tcon.ko` initializes its interface table from base `BSS+0x428`:

* `QDFTcon_SetOffSensing` (`.text+0x13690`) is registered at `+0x350`
  (`BSS+0x778`);
* `QDFTcon_SetElSensing` (`.text+0x11d78`) is registered at `+0x360`
  (`BSS+0x788`).

This closes the static chain from the two AVE operation values to the QDF
implementations.  Per [qd-command-skip-lifecycle.md](qd-command-skip-lifecycle.md),
the enable form (`argument == 1`) of either implementation sets
`m_command_skip` after its own sensing/status sequence and delay.  That gate
can return successful-looking results without issuing many later writes, so
it is a meaningful *candidate mechanism* to observe — not a safe setting to
change and not a demonstrated cause of the panel blackout.

The independently decoded, retained static samples further label the two
control requests without claiming hardware completion: EL sensing uses
`F3 00 00 00 01 A0` (the enable path carries payload `1` near
`QDFTcon_SetElSensing+0x110`; its other branch carries `0` near `+0x2c4`), and
off sensing uses `F3 00 00 00 01 80` (enable payload `1` near
`QDFTcon_SetOffSensing+0x14c`; other branch payload `0` near `+0x2e4`).  Both
enable paths have a preceding `0x160`/payload-`0` request and a 500 ms delay
before `m_command_skip` becomes `1`.  These are neutral control-request labels
from static samples, not evidence that a sensing cycle became active or
succeeded on the owner's panel.

## What the saved logs do and do not say

The contextual extraction at
[`../overnight/existing-gate-sensing-log-extract.json`](../overnight/existing-gate-sensing-log-extract.json)
shows some real `tcon_state=0`/skip observations close to ordinary `deviced`
off-sensing/power lifecycle records (including around the historic
power-off/power-on sequence).  It does not contain the ioctl operation and
argument above, and therefore cannot prove a `SetOffSensing(1)` or
`SetElSensing(1)` call.  Likewise, availability `1`, a timer, or a status
poll is not an active sensing request.

The command-skip read semantics matter when interpreting any future monitor
output:

* locking `m_read_cmd` with `state != 1` returns `-1` (apart from its exact
  `F3 80 ... 0000` exception);
* with `command_skip == 1`, locking reads normally return `0` with output
  untouched, except exact `F3 80 ... 000c`;
* suspended locking reads also return `0` with output untouched;
* the no-lock reader returns `0`/untouched output for all three gates, with no
  `0x0c` exception.

Consequently, a zero-looking value without its return code and a known output
initialization is not evidence of real panel health or a successful command.

## What to capture at the next controlled onset

Keep this passive.  Do not invoke operations `9`/`15`, force their callbacks,
or clear `m_command_skip`.

1. Capture the process name/PID, ioctl command, and the first two 32-bit words
   of each `0xc010749f` request, if an existing audit mechanism can safely
   observe them.  The decisive records are `{9,1}` and `{15,1}`; retain
   corresponding disable `{9,0}` / `{15,0}` records too.
2. Preserve return value, timestamp/monotonic clock, and event order with
   `deviced` “off sensing required/ready”, panel DPMS, QD mute, QD power
   control, `PWR lcdon`, and compositor/HWC events.
3. At the same moment, record the exact QDF gate log and status-read return
   codes/output buffers.  Do not reduce these to a boolean “healthy”.
4. Repeat one navigation-to-Live/For You onset and one stable full-Apps/video
   control capture under the same boot.  The comparison can test association;
   it cannot retrofit causation from page sparsity alone.

Until a request or QDF entry log is time-aligned to a fresh onset, the safer
working split remains: the user-interface/content-static path, normal
maintenance/off-sensing lifecycle, and the physical panel/TCON failure are
separate hypotheses.  No permanent workaround follows from this trace.

## Reproduction

The offline helper requires Capstone5.0.7, pyelftools0.33 and
`aarch64-linux-gnu-objdump`. The Python dependencies are already available on
this controller under `/tmp/tcon-capstone`. Run:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/qd-sensing-entry-callers-reproduce.py
```

[`qd-sensing-entry-callers-reproduce.py`](qd-sensing-entry-callers-reproduce.py)
reports missing prerequisites explicitly when that environment is absent.
It checks six binary hashes, prints facade/implementation/set-functions and
public-AVE Thumb windows, the relevant dependency/relocation/PLT data and
table literals, decodes the two `TCON_Request` jump-table entries, and prints
API handler/QDF initializer ranges. Windows can contain literal pools; only
the identified instructions and separately printed data are interpreted.
It does not open a device or issue an ioctl.

The saved bounded reproduction is [qd-sensing-entry-callers.raw.disasm](qd-sensing-entry-callers.raw.disasm), SHA256 `9e0644749dff880259fb23ef758547e52ecfde228223c5910f916e5986ef9291`. The expanded helper ran successfully with the documented dependency environment.
