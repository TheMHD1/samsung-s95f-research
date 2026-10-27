# Reset-coupled USB `04e8:2001` identity and logging boundary

## Scope and result

This is an offline correlation of already retained kernel/vlog rows, USB
descriptor metadata, and copied binaries.  It made no TV, root, network, USB
open, bind, control, bulk, serial, firmware, or controller call.

The stock MODE2 observation gives strong operational evidence that the USB
device at Linux path `7-1`, device identity `04e8:2001` / `STL1 CDC and Bulk`,
belongs to the reset-coupled controller subsystem:

* the recovered stock QDF path issued OCL mailbox command `0x3f` with value1;
* that exact device disconnected about139ms after the OCL callback returned;
* the path later issued command `0x3f` with value0;
* the device enumerated again at the same port with the same retained
  VID/PID, revision, product, manufacturer, and serial identity; and
* QDF then resumed its normal GPIO and I2C-5/address-`0x76` check/replay tail.

This is a real host-observed USB disconnect/enumeration boundary, not merely a
software status-cache change.  It does **not**, however, prove what electrical
signal mailbox command `0x3f` controls, that the USB function and I2C endpoint
are the same processor, that the copied selected profile was executing, or
that the USB transition caused, cleared, or measured a panel condition.

The useful currently grounded logging surfaces are narrower than the device
identity match: retained Linux kernel/console logging records enumeration and
QDF/OCL events; the packaged firmware has a separate CDC formatter route for
`RDY`/statistics-style output; and its RT/common-error output instead goes to
a controller-local UART-shaped MMIO route.  No safe no-write host route to the
latter has been recovered.  The vendor SSB interface is an active update/data
transport candidate, not a passive diagnostic log endpoint.

## Exact retained inputs

| input | SHA-256 | role |
| --- | --- | --- |
| `stock-mode2-transport-audit.md` | `70b0d0f2f7a8301d2b598d45a3510a4304bd493c2e7507e0bb1c8f270baf8847` | pinned chronology and rejected-capture boundary |
| rejected capture raw trace | `5ade657ba4c253e70cbb26eab2431a0a8bde2acd73f85386d9e7d1fce78633ab` | GPIO/I2C event record |
| rejected capture kernel artifacts | `e95377fe9dd44cac41bcf54fe6e030a783a1d556411829545d33ebc4367379e4` | OCL/QDF/USB chronology |
| rejected capture vlog | `b85d7c51898abacaf4900bf74068f432d147df8a36f5d60dd90244f286e37b8a` | independent logging corroboration |
| `qd-usb-interface-metadata-20261027a/client.stdout` | `065113d8f9d133570a72a4c086e2fdbff26567c9f8c082612f794f7414430530` | cached descriptors and child-interface binding state |
| `ssb-registration-metadata-20261026a/client.stdout` | `2807922e63b27c2aef8d9b3ad9c9b5eb3b20a49f5d6e2808928784b6bff48351` | module/nodes/driver-name sample |
| selected packaged profile | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` | static firmware USB personality only |
| copied `sdp_ocl_jp.ko` | `e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c` | lower reset callback body |
| copied `sdp_pqe_frc.ko` | `1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4` | Linux SSB transport implementation |

The containing observer record remains rejected for `duplicate AVOC ioctl
enter`, with `accepted=false` and `technical_capture_complete=false`.  This
report uses the preserved kernel/USB rows and narrower complete I2C decode; it
does not rehabilitate the observer record or its physical eligibility.

## Reset chronology and identity continuity

The retained same-boot sequence is:

| uptime | retained event | bounded conclusion |
| ---: | --- | --- |
| `94420.503051` | OCL mailbox log `Write [01 3f 01 01 00]` | command `0x3f`, one-byte value1 was requested; receiver semantics remain unknown |
| `94420.503080` | `Reset TCON power=1 ret=0` | lower callback returned0, not an electrical measurement |
| `94420.641740..94420.649049` | `usb 7-1` `04e8:2001` disconnect and completion | host USB core observed device disappearance about139ms after callback return |
| `94421.655057` | OCL mailbox log `Write [01 3f 00 01 00]` | same command requested with value0 |
| `94421.655090` | `Reset TCON power=0 ret=0` | lower callback returned0 |
| `94422.123180` | new high-speed USB device on `7-1` | enumeration began about468ms after callback return |
| `94422.271427..94422.271451` | `04e8:2001`, revision2.50, `STL1 CDC and Bulk`, `Samsung`, serial `0x12345678` | complete identity announcement about616ms after callback return |
| `94422.496752..94422.499661` | ACDET GPIO425 high and ERR_DET GPIO125 raw0 | subsequent QDF stock-on work, separate from USB identity |
| `94422.496806..94422.799187` | complete QDF I2C checks/replay on bus5/address`0x76` | normal tail resumed after enumeration; USB-to-I2C processor identity is not thereby proved |

The earlier USB metadata sample, on the same boot but at uptime
`83382.46..83382.52`, records the parent path `/sys/bus/usb/devices/7-1` with
VID/PID `04e8:2001`, revision `0250`, product `STL1 CDC and Bulk`, manufacturer
`Samsung`, one configuration, and three interfaces.  The exact cached
descriptor has device class `ef/02/01` and these children:

| interface | class/subclass/protocol | endpoints | retained interface text |
| --- | --- | --- | --- |
| `7-1:1.0` | `02/02/01` | interrupt IN `0x83` | `USBSerial` |
| `7-1:1.1` | `0a/00/00` | bulk OUT `0x01`, bulk IN `0x81`, 64-byte max packet | `USBSerial` |
| `7-1:1.2` | `ff/00/00` | bulk IN `0x82`, bulk OUT `0x02`, 512-byte max packet | none retained |

All three child-interface `driver` links were absent in that bounded sample.
The separately present `/dev/ttyUSB0` was not mapped to this parent, and no
ACM node was printed.  The older SSB metadata found no `/dev/ssb1`,
`/dev/ssbs1`, `usbmisc/ssb*`, or named `*ssb*` USB-driver path.  Those are
timestamped negatives only; they do not establish binding state during the
later reset or at every boot.

## What the copied code adds

### OCL reset request

The recovered QDF MODE2 path dynamically resolves exported
`sdp_ocl_reset_tcon_power`.  Copied `sdp_ocl_jp.ko` implements that callback at
`.text+0x2b38`: it retains the integer argument as one byte and calls
`SDP_OCL_I2C_MBox_Write(op=1, command=0x3f, length=1, flags/unknown=0,
payload=&value)`.  The helper reaches `i2c_transfer` after its gates.

The actual rows `[01 3f 01 01 00]` and `[01 3f 00 01 00]` agree with that
static envelope.  This closes the caller/provider/observed-log chain for the
request.  The receiver implementation for command `0x3f` is not recovered,
so the names `Reset TCON power` and argument polarity are not promoted to
electrical topology.  The device could disappear because of reset, shared
power, a hub/PHY effect, firmware restart, or another receiver behavior not
distinguished by these bytes.

### Packaged controller USB personality

The selected 5MiB profile contains concrete descriptor construction for the
strings `USBSerial`, `Samsung`, `STL1 CDC and Bulk`, and `STL1 CDC and Bulk
Control Interface`; it also constructs the CDC control/data plus vendor-bulk
shape that agrees with the retained descriptor inventory.  Under the corrected
image-0 mapping, linked code addresses are stored at `file = VA + 0x200`.
Historic relative-control-flow conclusions remain useful, but this report
does not reuse the superseded old absolute callback attribution.

The corrected class callback handles CDC `SET_LINE_CODING` only and may call
an optional hook stored at RAM `0x2000063c`; reset scatter initializes that
word to zero and no packaged nonzero producer was recovered.  DTR is a
separate state-changing control path: its rising edge clears local USBSerial
ring/transfer bookkeeping and primes receive state.  Consequently an open or
line-state operation is not a passive identity test.

The descriptor/body match is strong package provenance but still not runtime
firmware identity.  No retained boot measurement proves that these exact
packaged executable bytes were the code that re-enumerated at `7-1`.

### Linux SSB transport

Copied `sdp_pqe_frc.ko` includes an SSB USB driver whose ID table matches
vendor/product `04e8:2001` without an interface-class restriction.  When
registered and successfully probed, it can create `ssb%d`/`ssbs%d` usbmisc
devices.  Its `open`/`release` obtain and release USB runtime-PM usage, and its
read/write/ioctl paths perform active USB transfers.  This makes the vendor
interface a plausible update/data-transport candidate, but not a passive log
surface.

The matching ID table is not proof of a live probe or of interface2 ownership.
At the retained metadata points the expected SSB nodes and named driver path
were absent, and the later comprehensive interface sample showed no child
driver links.  No SSB probe or bind row was identified in the retained MODE2
reset window.  That last statement is a bounded log inventory, not proof that
no probe occurred silently.

## Useful logging surfaces, ranked by present grounding

1. **Linux kernel/console and private trace capture.** The MODE2 record
   directly retained the OCL request, USB disconnect/enumeration, QDF logs,
   GPIO events, and subsequent I2C traffic.  This is the best-proved passive
   surface for future reset chronology.  It does not reveal controller-local
   RT producer state unless firmware/QDF emits it.
2. **CDC bulk-IN `0x81` packaged formatter.** Static image code links a
   formatter ring to the CDC data IN endpoint and directly emits limited
   `RDY`/statistics/`TCDATA`-style messages.  It is not proven scheduled in
   the running image, no child host driver was bound in the sample, and
   establishing a CDC session/DTR can clear queued state.  It is not a
   demonstrated safe backlog reader.
3. **Controller-local RT/common-error UART ring.** The relevant common-error
   output is routed through a different RAM ring to UART-shaped MMIO
   `0x40150000`, not to the CDC formatter.  Retained DT/module work has not
   established an existing host bridge for that channel.  This is the most
   relevant static diagnostic content but currently lacks a host acquisition
   path.
4. **Vendor bulk `0x82/0x02` / SSB.** The host module implements an active
   update/readback protocol, with runtime-PM and USB requests.  It is not a
   generic log drain, its nodes were absent, and opening it was correctly not
   attempted.

There is therefore no source-backed claim that a read-only, no-DTR host receive
would yield current or historical RT/error data from this USB identity.

## Exactly proved versus still open

Proved by retained observations and copied bytes:

* one stock MODE2 lifecycle brackets a real `7-1` disconnect/re-enumeration;
* the reappearing device announces stable, detailed `04e8:2001` Samsung STL1
  identity, including revision and serial;
* the reset caller/provider request uses OCL mailbox command `0x3f` with the
  observed one-byte values;
* the selected package implements a highly concordant three-interface USB
  personality; and
* the Linux SSB module has a static VID/PID match and active transport, while
  the retained metadata shows no corresponding bound/named interface.

Not proved:

* command `0x3f` receiver semantics, electrical reset/power topology, or
  whether the USB disappearance is direct rather than a shared effect;
* equivalence of USB function, I2C address`0x76`, image0/image1 execution
  context, OCL mailbox receiver, or the physical panel controller;
* current execution equality with the selected packaged profile;
* interface binding during the MODE2 window, successful CDC/SSB data transfer,
  queued log retention, or safe no-control-read behavior;
* controller fault clearing, rail voltage, emitted light, or physical recovery.

## Concrete next safe offline targets

1. **Recover command-`0x3f` receiver provenance from already copied code.**
   Search only retained OCL/MICOM/controller binaries for a positive mailbox
   dispatch body and bind its value0/value1 leaf.  This is the smallest edge
   needed to distinguish direct USB/controller reset from a shared side
   effect; absence of the receiver should be recorded rather than guessed.
2. **Bind the complete packaged USB device descriptor, not only its strings.**
   Recover the exact VID, PID, bcdDevice, serial construction, interface and
   endpoint constants under the corrected `file=VA+0x200` map, then compare
   them byte-for-byte with the cached 114-byte descriptor.  A full match would
   strengthen packaged-image identity but still would not prove runtime
   equality.
3. **Trace static USB initialization reachability.** Recover the normal reset
   call path into descriptor registration and the service scheduling of the
   `0x81` formatter, retaining its DTR/session gates.  This can decide whether
   CDC is a realistic newly-produced-message surface without opening it.
4. **Map retained topology offline.** Correlate already archived DT/sysfs USB
   parent/hub/controller paths with OCL/MICOM device-tree nodes.  A matching
   physical controller/reset-domain property would be useful; ordinary port
   numbering or shared timing alone is not enough.
5. **Keep RT UART and SSB distinct.** Search retained binaries for a host-side
   bridge from firmware MMIO `0x40150000` before considering any interface
   operation.  Do not substitute vendor SSB reads or CDC DTR for that missing
   bridge.

None of these offline targets requires opening, binding, resetting, writing,
or updating the USB device.  The present evidence supports identity and reset
chronology, not a USB diagnostic procedure or a repair claim.
