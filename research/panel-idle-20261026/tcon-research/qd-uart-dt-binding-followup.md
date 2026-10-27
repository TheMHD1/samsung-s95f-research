# QD UART device-tree binding follow-up

Recorded 2026-10-27 UTC. This is bounded offline analysis of retained bytes.
It made no TV, root, network, tty, UART, debugfs, tracefs, module, mux, GPIO,
or controller call.

## Result

The new live-tree archive identifies all four Linux SDP UART instances, but it
does **not** bind the QD image-0 diagnostic UART to one of them.

The strongest new fact is about host software topology:

* `ttyS1` is the live platform device at SoC MMIO `0x00550e00`, port index 1,
  and is bound to the ordinary `sdp-uart2` tty driver.
* Its DT node also carries compatibility strings
  `samsung,sdp-uart-serdev-ctrl`, `samsung,sdp-uart-direct-io`, and
  `samsung,sdp-uart2`, in that order.
* The paired kernel has a separate serdev-controller driver matching the first
  string, but the live platform-device driver link is `sdp-uart2`, not that
  controller.
* The paired kernel's direct-I/O serdev client matches the different string
  `samsung,sdp-serdev-udio`. The archived ttyS1 node has no child node with
  that compatible, and the contemporaneous `/sys/bus/serial/devices` listing
  is empty.
* The literal `samsung,sdp-uart-direct-io` occurs zero times in the exact
  paired kernel Image. It therefore does not, by itself, identify an
  executable driver match or receive callback in this build.

The active `sdp-uart2` receive path is nevertheless recoverable from the exact
Image. Its RX loop at Image file offset `0x437d58` reads each hardware byte,
calls exported `uart_insert_char` at `0x433310`, and finally calls exported
`tty_flip_buffer_push` at `0x41c450`. That is an ordinary tty flip-buffer
route, not a persistent log buffer or a proved QD-specific reader.

This gives a technically narrow *potential* passive observation site, but the
installed system does not currently expose a supported dynamic-function
probe surface: `/proc/kallsyms`, `/proc/config.gz`, `kprobe_events`, the kprobe
blacklist, and `available_filter_functions` were all absent in the exact
metadata read. No local RX symbol name was recovered, no probe was installed,
and no function-event capture is ready. Even if such a hook were made
available later, silence would not prove no controller output: the ttyS1
receiver may be closed or interrupts disabled, and the electrical connection
to QD remains unproved.

Most importantly, the two numeric MMIO bases are in different processor
address spaces: the QD MCU writer uses its controller-local `0x40150000`,
while Linux ttyS1 uses SoC `0x00550e00`. Similar UART semantics do not prove a
wire, pinmux, level shifter, or producer identity between them. The new DT
archive closes the Linux-node gap, not that board-level edge.

## Exact retained inputs and acquisition audit

| retained input | bytes | SHA-256 |
| --- | ---: | --- |
| UART-node acquisition record | JSON | `924e2a841be61faa6dd2141a030e084bb2329da23daaea309f491235c7cd90c9` |
| UART-node archive | 1,015 | `ce20e991a2849682f5dbedada20a3b1bede5418ec1c3c3918cc8685fad8a1c16` |
| UART-path metadata | JSON | `9f519d7df22fe974a8b34b2d125bea915ab5871a5b53e5f3e54977e292481b7a` |
| paired Linux Image | 11,786,752 | `77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d` |
| reconstructed export index | JSON | `6d3ffe0edfd2ab92fc4439ffe35371db4c3f2ad8a99cf5b2b20ae2ef4eb937ac` |
| prior QD UART boundary | report | `e933ac9084b79253a68bb665c1c2f7f38eb595a9e763a6d2229625b5883d9b8c` |
| prior QD USB/UART output route | report | `a14f5280bd15244ac702d5f1fb9131b42be74504722be3a7bdf3d81f80e5ba50` |
| failed kallsyms read record | JSON | `1271a9bb64a8e24d3dcae44493ec1ed23416db5057ce3698ab3ee07d9004dd34` |
| probe-capability metadata | JSON | `6dbca53fdc4885fe7cc359cd25b8364fb53619f5693642b73a3ec54cdf69b22e` |

The UART-node record contains exactly one authenticated uid/euid-0 command,
exit 0, with empty remote stderr and no timeout. It reads four DT subtrees,
tty symlinks, and the serial-bus directory. Boot ID
`00000000-0000-4000-8000-000000000000` is unchanged across uptime
`88980.74..88980.77`.

The base64 archive recovered from the authenticated stdout is byte-identical
to the retained `.tgz`: 1,015 bytes and the archive hash above. It contains 44
members and expands to a 51,200-byte tar stream. All member paths are below
the four requested `soc/serial@...` directories; there are no archived child
directories below those four nodes. This checks provenance and scope. It does
not prove that unrequested DT subtrees contain no board-routing information.

The earlier path-only record is likewise an authenticated, status-0,
empty-stderr read on the same boot at uptime `88942.12..88942.15`. It found
the four serial nodes and no serial/uart aliases. An absent alias is not an
absent UART.

## Exact live-tree topology

The archived properties decode as follows. `reg` is a pair of big-endian
32-bit cells.

| tty | DT node / `reg` | index | distinguishing retained property | live driver link |
| --- | --- | ---: | --- | --- |
| `ttyS0` | `serial@00190A00`, `<0x00190a00 0x4000>` | 0 | `samsung,add-debug-port`; `enhanced` | `sdp-uart2` |
| `ttyS1` | `serial@00550E00`, `<0x00550e00 0x4000>` | 1 | `enhanced`; three-compatible list discussed below | `sdp-uart2` |
| `ttyS2` | `serial@00550F00`, `<0x00550f00 0x4000>` | 2 | purpose `CEC interface with OCBox using ttyS2` | `sdp-uart2` |
| `ttyS3` | `serial@00551000`, `<0x00551000 0x4000>` | 3 | no purpose property in this subtree | `sdp-uart2` |

All four nodes have `status = "okay"`. The mapping is stronger than a string
scan because `/sys/class/tty/ttyS0..3/{device,device/of_node,device/driver}`
were resolved in the same command. It establishes that ttyS2 is the named OCB
CEC channel and ttyS0 is a debug port. It does not turn the unnamed ttyS1 into
a QD channel by elimination: the product can contain other controllers,
service routes, or unrecorded board wiring.

The complete ttyS1 compatible byte list is:

```text
samsung,sdp-uart-serdev-ctrl\0
samsung,sdp-uart-direct-io\0
samsung,sdp-uart2\0
```

Compatible strings enumerate permissible software matches. They do not prove
which driver won the live bind; the sysfs driver link supplies that fact and
names `sdp-uart2`.

## Paired-kernel driver separation

The paired kernel contains one inline `of_device_id` string at file
`0x8650b8` for `samsung,sdp-uart-serdev-ctrl`. Its controller-probe body is
the slice below. It allocates a serdev controller, reads
`samsung,port-index`, and calls exported `serdev_controller_add` at
`0x438950`. A return of `-ENODEV` is treated as “no have serdev device node.”
This is the code path that needs a serdev child; it is not the live ttyS1
driver link in the acquired topology.

The direct-I/O client has one separate inline match at file `0x865418`:
`samsung,sdp-serdev-udio`. Its `struct serdev_device_ops` table points to the
receive callback at file `0x401550`. That callback has the standard inputs
`serdev_device`, byte buffer, and count; when its device-open flag is set it
copies bytes into a 512-byte circular queue and wakes a waiter. When not open,
it logs that state and returns the supplied count. Other code creates an
`sdp_udio%u` character endpoint for a successfully bound client.

This is a real receive callback, but it is not reachable from the archived
ttyS1 node as captured:

1. ttyS1's node has no child directory at all;
2. no archived compatible equals `samsung,sdp-serdev-udio`;
3. `/sys/bus/serial/devices` is empty; and
4. the platform device is already bound to `sdp-uart2`.

No `/dev/sdp_udio*` census was acquired, so this report does not claim node
absence from `/dev`. The empty serdev-device bus and exact DT/kernel mismatch
are the source-backed binding result.

The kernel string census also matters narrowly:

| exact string | count / file position |
| --- | --- |
| `samsung,sdp-uart-serdev-ctrl` | 1 at `0x8650b8` |
| `samsung,sdp-uart-direct-io` | 0 |
| `samsung,sdp-uart2` | 2 at `0x867e60`, `0xa673c8` |
| `samsung,sdp-serdev-udio` | 1 at `0x865418` |

The zero is bounded to this exact Image; it is not a statement about every
Samsung kernel or an omitted external module.

## Active tty RX path and bounded probe assessment

The live driver name directs analysis to the ordinary `sdp-uart2` body. Its
probe at file `0x437628` reads `samsung,port-index`, chooses one of four static
port objects at file `0xaec4a0` with stride `0x240`, and registers a
`uart_port` beginning at object offset `0x30`. The four initialized line
numbers 0, 1, 2, and 3 occur at object offset `0x1ec`, which is
`uart_port+0x1bc`.

The RX loop at `0x437d58`:

1. polls the mapped UART receive/status registers;
2. loads the next byte;
3. accounts framing/parity/break/overrun state;
4. calls `uart_insert_char(port, status, overrun, ch, flag)` at file
   `0x437e28`; and
5. calls `tty_flip_buffer_push` at file `0x437db8` after draining up to 64
   iterations.

The two callees are independently named by the exact export table:
`uart_insert_char` = `0x433310`, `tty_flip_buffer_push` = `0x41c450`.
On AArch64, the `uart_insert_char` call carries the `uart_port *` in `x0` and
the received character in `w3`; this exact caller's line identity is the
32-bit value at `x0+0x1bc`. A hypothetical bounded probe could therefore
retain only line 1 and the byte plus status/flag arguments, while preserving
loss accounting. This is a source-backed observation design, not a deployed
or currently supported mechanism.

Two limits prevent calling it ready:

* The local RX function name is absent from the reconstructed export index,
  and `/proc/kallsyms` is absent. The first metadata attempt stopped with exit
  2 at that missing file and made no probe.
* The adapted read at uptime `89313.77` found all of
  `/proc/kallsyms`, `/proc/config.gz`, debug-tracefs `kprobe_events`, the
  kprobe blacklist, and `available_filter_functions` absent. This does not
  prove the corresponding kernel configurations are disabled; it proves no
  supported named kprobe/function-tracer surface was demonstrated at those
  paths.

Using raw runtime addresses would additionally require a current load-base
and executable-text identity guard. The artificial export ELF contains Image
offsets, not a live KASLR binding. Planting a generic probe at
`uart_insert_char` without a line/caller filter could collect unrelated UARTs
and exceed a bounded trace budget.

Finally, a probe does not enable a closed port. The recovered RX loop is only
evidence when the driver actually services input. A no-event interval cannot
distinguish no bytes, a closed receiver, masked RX interrupts, a different
mux, an unconnected wire, or a different producer.

## Slice provenance

The following slices are from the exact paired Image and were hashed directly
over half-open file ranges:

| bounded body | file range | bytes | SHA-256 |
| --- | --- | ---: | --- |
| serdev-controller probe | `[0x400a28,0x400f74)` | 1,356 | `bc4217c8e7a01c19856c30af967838f1807b050321f74f3d9e78901d32c5634f` |
| UDIO serdev receive callback | `[0x401550,0x401678)` | 296 | `5c49c9673a93b1203691cd4c203f70a2154334c0400de0af2638d7a08d19a870` |
| `sdp-uart2` probe | `[0x437628,0x437a20)` | 1,016 | `8beda3e17dec181cec73b458eaf32c67fb2e385e2d17fbfd2d7535e57b2a1b8e` |
| `sdp-uart2` RX loop | `[0x437d58,0x437ec8)` | 368 | `7485e1c10425cbcc5d17ef9245118393b891cde0390bfe037680208ba0f6a818` |

Function names for the two non-exported Samsung bodies are descriptive labels
derived from their call graph, strings, match tables, and registration slots;
they are not recovered local ELF symbols. The exported callee names are exact.

## What is and is not closed

Closed by this follow-up:

* the host has a concrete ttyS1 at `0x00550e00`, index 1;
* it is bound to the stock `sdp-uart2` tty driver;
* the alternative serdev client/buffer route is not instantiated by the
  captured node hierarchy;
* the exact active driver feeds received bytes to the ordinary tty core; and
* no current named dynamic-function probe surface was demonstrated.

Still open:

* whether the QD MCU TX is electrically connected to ttyS1 RX;
* pinctrl/mux and voltage-level provenance for such a connection;
* ttyS1's configured baud/framing and whether it is already open;
* a supported bounded hook on this installed kernel; and
* whether the currently executing controller image emits the packaged common
  error strings on its UART during the observed RT fault.

Therefore the new bytes improve the next diagnostic design but do not yet
authorize a generic tty read, identify ttyS1 as QD, or provide an absence
test. A future route needs either the missing board/pinctrl identity or a
supported passive RX event surface with positive, recognizable controller
bytes. No tty open, mux operation, or debugger was performed here.
