# QD image-0 UART to host logging boundary

Recorded 2026-10-27 UTC. This is bounded offline analysis of retained
firmware, kernel, module, device-tree, and log bytes. It made no TV, root,
network, UART, tty, USB, debugfs, device-node, module, GPIO, or controller
call.

## Result

No retained source establishes an existing host/kernel collector for the QD
image-0 diagnostic UART at controller-local MMIO `0x40150000`.

The controller route itself is exact: the selected packaged image formats
common error text into a `0xc00`-byte RAM ring at `0x20205000`, then drains it
through a byte writer that polls `0x40150000+0x24` and writes
`0x40150000+0x2c`. What remains missing is the boundary after that controller
TX register: no retained schematic/net, complete device-tree node, host UART
instance, serdev child, tty, shared-memory bridge, or kernel log forwarder is
bound to it.

Two real host log facilities must not be substituted for that missing edge:

* the host boot console `ttyS3` is an SDP SoC UART selected by the Linux
  command line; no retained evidence wires it to the QD controller TX; and
* `/sys/kernel/debug/tcon/tcon_micom_log` is a read-only host view of a
  different, internal `sdp_tcon` shared-memory log. Its retained text names
  `RHEA_M_TCON_FW_20250103_1715` and image `F77ABU2D20`; the exact QD fault
  query instead crosses the external adapter-5/address-`0x76` boundary.

The selected asset's USB CDC formatter is also separate. Its endpoint-`0x81`
ring receives direct calls for `RDY` and USB/TCDATA diagnostics, while the
common RT/error path uses the `0x20205000` UART ring. There is no source-backed
RT-error-to-CDC forwarding edge.

Consequently a no-write host collection route is **not technically ready**.
Randomly opening a `/dev/ttyS*` or changing either retained UART mux lead would
not test a proved route: a tty open can consume bytes or alter session state,
and both mux setters are active controls. The missing fact is technical
binding, not user authorization.

## Exact inputs

| retained input | bytes | SHA-256 |
| --- | ---: | --- |
| selected QD profile `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` | 5,242,880 | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| paired host kernel `overnight/kernel-Image.bin` | 11,786,752 | `77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d` |
| kernel-slot metadata | retained JSON | `f244c357cfcadd006c1dd6d4ab35b3d23e46ccf9827a426233f1a30f81b32720` |
| targeted display DT archive | 102,400 | `2be5e7807f99bbab655ceb265e3226a88095d1280bde154cb1040600990c9955` |
| targeted GPIO DT archive | 225,280 | `419acbb99a698f432e4d192a1e9f65a5506dc3509d298225008eea008d371275` |
| extracted display-DT record | 4,006 | `a63fb1af4150a570c8d3199f10e9491253adedd5cd4093a9003294c0fc98fdfc` |
| extracted GPIO-DT record | 5,742 | `3c0726b9cfc5567f7dcbc06ffb00e132ac55e99764996264490201060dbc1251` |
| copied `sdp_tcon.ko` producer analysis | 10,794 | `26d87ff90ef77b5f66f2a54db608171f4867e84943be4f5ccb26b92ffead84ef` |
| controller-identity boundary analysis | 12,219 | `c60b1fd868583f5e36c649c12844a5a3228350d1016a9c60fbb8759c07bd94c3` |
| QD USB/UART output-route analysis | 14,474 | `a14f5280bd15244ac702d5f1fb9131b42be74504722be3a7bdf3d81f80e5ba50` |
| copied `tztv-battery.ko` | 174,902 | `dd7e9c1c68b3802e8e8fc04a9097c2cc6baaedd5960e7a25bb387499edbc2270` |
| copied `sdp_ocl_jp.ko` | 594,110 | `e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c` |
| copied `sdp_ocl.ko` | 261,166 | `80b9e66f4129a31207f1eee8d7636d7565193ecf9ba87e3bded6196c5e1b02e7` |

Image-0 addresses below are Thumb linked addresses equal to stored offsets in
the selected file's first `0x40000` bytes. The selected-file/runtime profile
match is strong but does not prove current-flash byte equality.

## Proven controller-local UART path

The exact path, independently bounded in `qd-usb-log-output-route.md`, is:

```text
common error 0xb860
  -> formatter/ring writer 0x39594..0x395eb
  -> RAM ring 0x20205000, counter 0x20000e5c, modulo 0xc00
  -> drain 0x39604..0x396a1
  -> byte writer 0x3acf6..0x3ad31
  -> poll [0x40150000+0x24], write [0x40150000+0x2c]
```

The byte writer inserts carriage return before line feed. This is strong
UART-shaped behavior inside the controller address space. It does not show
whether the TX pin is bonded, where it is routed on this product, which baud
and framing the receiver uses, or whether a host receiver is enabled.

The common error path includes strings `System Emergence!!` and
`Entry -> %s err_src[%s]`. The separate USB formatter at `0x2b334` is not on
this direct path. A literal `TCON RDY` in the retained internal-MICOM log is
therefore not proof that the QD image-0 UART ring was forwarded there; a
coincident readiness phrase does not establish producer identity.

## Host kernel and device-tree census

The paired Linux Image contains the expected general SDP UART support:

* `samsung,sdp-uart2`, `sdp1202-uart`, and `ttyS%d`/`ttySD` strings;
* `samsung,sdp-uart-serdev-ctrl`; and
* embedded source names for `sdp_uart_serdev_controller` and
  `sdp_uart_serdev_udio`.

The retained command line selects `console=ttyS3,115200N8`, `rs232=1`, and
`earlycon sdp-soc`. This proves the host has its own serial console. It does
not bind `ttyS3`, a serdev instance, or any other host port to controller
address `0x40150000`.

An exact little-endian byte scan of the 11,786,752-byte kernel found zero
literal occurrences of `0x40150000` and zero of controller ring base
`0x20205000`. Literal absence cannot exclude a DT-provided, computed, or
electrically connected bridge; it only supplies no positive static binding.

The retained targeted DT corpus comprises 98 display-archive entries and 277
GPIO-archive entries. Neither path names nor property bytes contain
`uart`, `serial`, `console`, `tty`, `debug`, or `log`. The corpus does include
the display, TCON, FRC, I2C, fault GPIO, and broad pin-controller records used
by this investigation. It is not a complete flattened device tree, so this
is a bounded negative, not proof that the live tree lacks all UART nodes.

## Copied-module census and two mux leads

Seventeen locally retained `.ko` files were scanned for the exact
little-endian `0x40150000` literal; the total was zero. Specific UART-related
strings appeared in four relevant groups:

1. `sdp_tcon.ko` contains the known `tcon_micom_log` reader. Exact host code
   maps reserved `samsung,tcon_info + 0xa0000`, not `0x40150000`, and only
   copies the external producer's shared-memory bytes.
2. `tztv-battery.ko` has a live-platform-compatible linker facility with DT
   properties `samsung,mb_sel_uart` and fallback `samsung,sel_uart_51`.
   `mb_sel_uart_store` at `.text+0x15e0` writes the selected GPIO through
   `tztv_gpio_write_num`; its show routine requests and samples that GPIO.
   Neither function receives serial bytes or identifies the QD controller.
   This is a possible board-routing lead, not a logging route. Changing it
   would be an active GPIO control and is outside this report.
3. `sdp_ocl_jp.ko` exports `sdp_jp_set_uart_usb_mux` at `.text+0x2bb8`.
   Its body sends an OCL I2C mailbox write with command `0x37`; `sdp_ocl.ko`
   resolves that exported setter. This is an active OCL/SerDes control, not a
   byte collector, and no retained source binds it to the QD image-0 UART.
4. General occurrences of “serial” in QDF/HDMI modules describe cell or chip
   serial numbers and are not UART evidence.

The scan covered the 11 `binaries/*.ko` inputs plus six separately copied
providers under `overnight/`; it is not a census of all 195 installed modules.
An earlier installed-module literal scan concerned a different symbol and
cannot fill this UART binding gap.

## Existing host log path is a different controller

The `sdp_tcon.ko` analysis proves that
`/sys/kernel/debug/tcon/tcon_micom_log` is a bounded, non-clearing read of a
reserved-memory buffer. Its host handler sends no QDF/I2C command and does not
take a real runtime-PM reference. That makes it a useful log source for the
internal TCON producer, but not a bridge to the external QD image-0 UART.

The retained 1,405-byte prefix and later 1,477-byte capture name the RHEA
firmware, image `F77ABU2D20`, startup/output state, and `TCON RDY`. By contrast,
the QDF error query uses `/dev/tztv_tcon` and the external controller path
whose wire command is `F3 80 00 00 00 08`. The identity-boundary analysis
explicitly leaves these as different producers. Reusing the MICOM reader
would not recover the QD common-error ring unless a new producer-side
forwarding edge were proved.

## Retained-log negative is bounded

Fifteen retained dynamic log files were searched byte-for-byte: all captured
`vlog-after.txt`/`partial-vlog-after.txt` files plus the MICOM prefix and
binary capture. They contain zero exact occurrences of:

* `System Emergence`;
* `EEPROM Check RT Protection`; and
* `Entry ->`.

This does not show that the controller emitted no such text. The physical
UART route may be uncaptured, logs have finite coverage and retention, and
the executing controller image is not proved byte-identical to the package.
The negative only says the sought strings are not already present in this
finite retained host-log corpus.

## Good-versus-black diagnostic context

The owner reported Apps visible and working in the later paired state. Two
accepted machine records on the same boot then returned:

| contextual state | status query | separate fault-pin query |
| --- | --- | --- |
| prior owner-reported black panel | `0x00000010`, vendor-labelled RT Protect | `1` |
| later owner-reported Apps visible | `0x00000000` | gpiochip15 line5 value `0` |

The good-state source records are:

* status JSON SHA
  `4dd3f5cb6c414f1f1f90d6ec40713b31e791379e93c5dfe3279f6e5b46d872d2`;
* pin JSON SHA
  `76cea107152dbfa4d21e39f1f58accf2673b5a46ee603c781c2870b2471be577`;
* owner observation SHA
  `2365aa1207e9abe00a6ed80531bb4cafb4890666883c97f74e201493c12acaac`.

The black-state reports are SHA
`2015b8a9da976ba716fa4fa6d2491ec54949ebcb5c81e53103d32fbf9b1f7412`
and
`8482b98c9f6c9abd755dd6a1c7a176b46b7a00e13013b8e1ccbff9c3823b0621`.

This is a useful paired association, not a causal or UART observation. The
status records prove a kernel-written word but do not prove a fresh hardware
transaction in the good sample, exclude debug override, or establish
read-to-clear behavior. The pin helper is an input request/read, and the two
read times are not calibrated physical annotations. Neither result exposes
the UART ring or identifies the RT initiating condition.

## Smallest evidence that would close the boundary

A defensible host capture needs one of these source-backed bindings before
opening anything:

1. a product schematic/net or board-routing table connecting the QD
   controller UART TX to a named host UART/bridge and defining the mux level;
2. a complete live-DT/sysfs lineage from that named receiver through a bound
   host driver to a read endpoint, with pinctrl and baud/framing provenance;
   or
3. controller and host code proving that the `0x20205000` ring is copied into
   an already understood shared-memory/debugfs buffer.

Without one of those, `/dev/ttyS*`, the linker GPIO, and the OCL UART/USB mux
are guesses across a hardware boundary. No tty or device open, mux read or
write, module action, or new capture is proposed or performed here.

## Limits

This report is a bounded negative over the exact retained corpus. It does not
prove that no electrical test header, factory jig, omitted DT branch, external
USB-UART bridge, bootloader collector, or unretained module can receive the
controller UART. It does establish that none of the retained host routes can
currently be named as that receiver without adding an unsupported edge.
