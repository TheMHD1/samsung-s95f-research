# Existing read-only route to executing image-1 identity

Recorded 2026-10-27 UTC. This is a finite offline audit of retained firmware,
host ABI binaries, and already recovered read/diagnostic dispatchers. It made
no TV, root-agent, network, USB, I2C, UART, controller, process, or device-node
call. It did not build a helper or construct a target request.

## Result

**No existing address-free read-only diagnostic was recovered that reports or
computes a fingerprint of currently executing image-1 code.** The finite
surfaces expose stored/profile identity, fixed status, caller-addressed memory,
or exception-only register output. None closes the code-bus-address gap from
the preceding image-1 qualification.

The closest positive mechanisms are deliberately kept separate:

- USB vendor target `0x101` is a proven direct-address memory-IN route, but it
  still requires a source-qualified hardware-visible address. It has no
  “current PC,” “current image,” or address-free code-CRC operation.
- The local UART console has a `LOG VERSION` command, but its leaf returns the
  hard-coded bytes `03 03 04` (`0x040303`, displayed as `3.3.4`). It does not
  inspect executable memory.
- Both embedded images have HardFault handlers that print the stacked PC, but
  they are exception vectors and finish in an infinite loop. They are not
  normal diagnostics and deliberately faulting the controller is outside this
  scope.
- CRC/checksum functions validate a supplied Mks container or display a loaded
  configuration dataset. No retained read dispatcher invokes them over the
  currently executing text.

Therefore this report supplies no command, selector, bus address, code read,
or helper. A stored-image checksum or version match would remain storage
identity, not running-code identity.

## Finite surface census

| Surface | Bounded dispatcher/domain | Identity-like result | Running-code proof? |
| --- | --- | --- | --- |
| Controller I2C ingress | Complete first-byte families `F3`, `D0`, `FE`, `F7` | `FE` returns profile/storage-derived FW/MD fields; other families return finite status/arrays/action responses | No code memory, PC, or image digest route |
| Local UART console | 19 handlers plus `END_TABLE` | `LOG VERSION` returns constant `3.3.4`; query/debug handlers expose ordinary state/configuration | No executable fingerprint; UART is not bound to USB CDC |
| USB CDC OUT | RX completion/worker and bounded mixed-code interval | Internal circular buffer/re-prime only | No direct edge to UART parser/dispatcher |
| USB vendor bulk | Twelve-byte `(target,address,length)` ABI | `0x101` reads the supplied address; `0x203` returns eMMC storage data | `0x101` needs the missing code address; `0x203` is storage, not execution |
| QDF host operation 19 | Six command bytes then four-byte I2C response | Reaches the same finite controller I2C families | No code-identity selector recovered |
| QDF debug routine | Registered internal routine with fixed `0x99` input helper | Normal build prints menu/exit | No public passive transport; dormant table mixes reads and writes |
| Fault diagnostics | Image-0 and image-1 HardFault vector handlers | Stacked registers including `PC [R15]` | Only after an exception; terminal infinite loop |
| CRC/checksum code | Mks header/payload CRC and configuration checksum display | Supplied/stored buffer integrity | No executing-text input or read-dispatch binding |

This is a census of the copied ordinary USB/I2C/UART/debug surfaces already
recovered. It is not a claim that boot ROM, a different firmware build, an
undocumented hardware trace block, or unavailable factory equipment has no
such mechanism.

## I2C and exact host read ABI

The controller ingress parser at file `0x12ac4..0x12dbe` selects exactly four
first-byte modes:

- `F3`: bounded logical getter, 35-entry `F3:80` selector table, and fixed
  framing result;
- `D0`: five fixed arrays, commands `D000..D004`, with bounded byte indexes;
- `FE`: ten exact commands, including four profile identity arrays; and
- `F7`: three finite response commands backed by protocol/action state.

The complete code-backed census has no caller-selected firmware/code address,
whole-image digest, or PC result. `F7` “checksum” bytes are additive checksums
of protocol/value or response bytes, not firmware hashes. `F7` is also paired
with a control-capable receive dispatcher, so it is not promoted to a passive
diagnostic channel.

On the host, the exact ARM32 `ave_tcon_api_read_onecommand` ABI uses operation
19 in a 16-byte ioctl envelope and reaches `QDFTcon_ReadOneCommand`. That path
writes six controller command bytes and requests four response bytes. This
solves host packing only for an already known controller command. Since the
finite controller census provides no executing-code identity selector, the
generic host ABI does not create one.

The four FE-visible fields are particularly easy to overstate. Their producer
reads fixed regions of a selected storage bank and assembles the FW/MD arrays.
The retained selected package contains the corresponding bytes, but the
producer does not hash linked code or observe a program counter. The printed
identity is storage/profile provenance subject to bank and read-success
limits, not a running-text fingerprint.

## Local UART console: complete top-level table

The command table at file `0x3d334..0x3d563` has these 19 entries followed by
`END_TABLE`:

```text
model?  bin?  bin  param?  param  ELV?  CURRENT?  TEMP?  TIME?
RTDBG  RTDBG?  TCDBG  LOG  fab  fab?  test  RT_EN  RTCFG  RTCFG?
```

The line parser at linked VA `0x16fc0` dispatches through the table at VA
`0x17084`. Its positive ingress is controller-local UART MMIO `0x40152000`,
either polled or through the associated 512-byte ring. The USB CDC RX worker
has no bounded direct edge to this parser, dispatcher, or ring producer.

The only explicitly version-named subcommand recovered here is within `LOG`:

```text
LOG CLEAN    -> state/storage-cleaning path (mutating; irrelevant here)
LOG INDEX    -> reads a scalar index
LOG VERSION  -> returns constant bytes 03 03 04
```

The `LOG VERSION` leaf at linked VA `0x20430` constructs those three bytes on
its stack and returns `0x040303`. Its only direct caller is the `LOG` handler
at VA `0x10eb0`. It contains no memory walk, CRC call, or executable base.
It is a subsystem/protocol version constant, not evidence of which image is
executing.

Other command labels are not silently treated as identity diagnostics.
`RTDBG`, `TCDBG`, and configuration/query names can emit state, but their
names do not prove a code fingerprint, and some neighboring handlers are
mutating. No textual command or UART operation is proposed.

## USB surfaces

### Target `0x101`: valid memory read, missing code address

The vendor interface uses bulk OUT `0x02`, bulk IN `0x82`, and a 12-byte
little-endian `(target,address,length)` header. Target `0x101` normalizes to
operation 1/mode 0 and schedules IN directly from the caller-supplied address.
The known descriptor and later fixed RAM reads validated that bounded ABI.

This route is not address-free. Its validator does not translate “image 1” or
“current PC” into an address, and it does not constrain the supplied family-1
address to executable memory. The separately proved mapper covers image-1 CPU
RAM `[0x20000000,0x20200000)`, not linked code VA `0..0x3ffff`. Consequently
target `0x101` cannot identify executable image 1 until a code-bus mapping is
independently established.

### Target `0x203`: storage read only

Target `0x203` reaches an aligned eMMC-sector reader and returns buffered
storage bytes. Even a checksum computed on those returned bytes would bind a
stored slot. It would not show that the core fetched or is currently executing
that slot, and the leaf's return/freshness limitation further constrains a
single result. It is therefore not substituted for live code identity.

### CDC console is not the local UART console

The CDC bulk-OUT worker maintains a separate `USBSerial` circular buffer and
re-primes a 64-byte receive. In the bounded CDC implementation interval there
is no direct call to the UART line parser VA `0x16fc0`, dispatcher VA
`0x17084`, or UART ring producer VA `0x21084`. The one generic-reader call in
that interval is the separate TCDATA sampler. Thus the local command table is
not promoted into a supported USB console ABI.

## PC output exists only on a terminal fault path

Image 0 vector index 3 contains Thumb pointer `0x12071`; image 1 vector index
3 contains `0x4045`. These are their HardFault handlers. Both handlers load
the exception frame's `+0x18` word, print it with the exact shared text:

```text
PC [R15] = %x  program counter
```

and end in `b .` (`fe e7`). This is positive evidence that a naturally
captured fault log could contain a contemporaneous stacked PC. It is not a
normal query: triggering it would be an active fault, the handler does not
return, and the firmware-local formatted-output path still lacks a proven
safe host console binding. No breakpoint, deliberate exception, reset, or
fault injection follows from this observation.

## CRC and checksum candidates are not live-text fingerprints

The Mks validator at linked VA `0xcb74` calls generic CRC helper `0x2e6c4`
exactly twice: once for a supplied 14-byte header and once for its declared
payload. Its sole direct caller is VA `0xcc54` in the container acquisition
path. Its diagnostic strings are `Mks : HEADER CRC ... MISMATCH` and
`Mks : DATA CRC ... MISMATCH`. This validates a buffer/container supplied to
the routine; it does not select the core's current executable mapping.

The displayed `Checksum : %04x` at file `0x175a4` belongs to the configuration
dataset formatter at VA `0x1732c`, whose sole direct caller is the loader at
VA `0x176dc`. That caller obtains a configuration dataset around fixed source
`0x04d00000`. It is not a whole-image code checksum.

No recovered read dispatcher binds either checksum routine to image-1 linked
code or exposes a “checksum current text” request. Reusing the generic CRC
routine through a new arbitrary executor would be a new active mechanism and
is explicitly outside this audit.

## QDF debug and diagnostic output boundaries

The copied QDF module registers `QDFTcon_Tcon_Debug`, but all copied
`t2ddebug_get_hex`/decimal helpers return fixed `0x99`. The normal build takes
the menu/exit path before its dormant selector table. No public device/ioctl
ABI reaching only a passive branch was recovered, and dormant branches mix
state printing with flash/control operations. It therefore provides no
read-only running-code fingerprint.

Firmware-local formatting also does not imply a host-readable console. The
image-0 print pipeline is real, but an exact safe USB endpoint/driver binding
for it remains absent. Diagnostic strings are code evidence, not proof that a
host can passively retrieve them on demand.

## What would close the gap

An existing route would need one positive edge absent here, for example:

- a decoded read selector whose handler itself walks the executing code range
  and returns a CRC/hash;
- a normal read-only command returning a current PC plus a source-proven
  mapping from that PC to image-1 bytes; or
- a boot/runtime identity register whose defined result uniquely binds the
  active image and whose ordinary read ABI is already recovered.

A stored profile version, eMMC checksum, cached USB descriptor, hard-coded
subsystem version, or naturally matching data structure remains corroboration
only. No address guess or target call is justified by their agreement.

## Reproduction

Run the standard-library-only checker normally and with Python assertions
disabled:

```sh
python3 executing-code-diagnostic-route.py
python3 -O executing-code-diagnostic-route.py
```

It pins the selected package, exact host ABI binaries, prior bounded checker
sources, dispatch slices, all 20 console table rows, the constant version leaf,
HardFault vectors/terminal loops, CRC direct-call census, and CDC-to-UART
negative direct-edge census. It prints one compact JSON record with
`status=diagnostic_route_gap`, `existing_address_free_route=null`, and
`target_operations=0`.

No protected/high-bank, persistence, POFLG, return-guard, flashing, alternate
bank, bypass, or write path was investigated or modified in this work.
