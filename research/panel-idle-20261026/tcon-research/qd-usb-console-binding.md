# QD image-0 USB descriptor and console-binding audit

Recorded 2026-10-27 UTC. This is offline analysis of retained image bytes and
retained read-only USB metadata. It made no USB open, registration, control,
bulk, serial, root, TV, or network call.

## Result

The selected image-0 firmware contains a concrete USB-device initialization
and descriptor-response path that uses the exact `USBSerial` and `STL1 CDC and
Bulk Control Interface` strings. This materially strengthens the identity
match with the retained device `7-1` (`04e8:2001`, manufacturer `Samsung`,
product `STL1 CDC and Bulk`), but it does **not** prove that this copied image
is executing on that device, that a host driver is bound, or that firmware
diagnostics reach a host-visible serial endpoint.

In particular, the retained sample shows the three matching USB interfaces
but no driver link for any of them. Opening a potential serial or bulk device
was deliberately not attempted: endpoint opening/line-state operations can
have runtime-PM and DTR/control side effects.

## Inputs

| retained input | identity |
| --- | --- |
| selected profile | `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`, SHA-256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| USB interface metadata | `overnight/qd-usb-interface-metadata-20261027a/client.stdout`, SHA-256 `065113d8f9d133570a72a4c086e2fdbff26567c9f8c082612f794f7414430530` |

Image-0 addresses below are linked Thumb addresses, equal to stored offsets
within its `0x00000..0x3ffff` image range.

## Positive descriptor construction and registration evidence

The following embedded string storage is exact:

| image-0 address | ASCII |
| ---: | --- |
| `0x22394` | `USBSerial` |
| `0x285c8` | `STL1 CDC and Bulk Control Interface` |
| `0x2a454` | `Samsung` |
| `0x2a474` | `STL1 CDC and Bulk` |
| `0x3c934` | `WINUSB` |

The strings are not only a bulk-string coincidence.

1. Initialization `0x24b0c..0x24b60` tests an initialized global and, on its
   first path, calls `0x22324` at `0x24b1c`.
2. `0x22324..0x2238e` stores fixed descriptor/configuration values, computes
   descriptor-related values through `0x220c`, and calls `0x286b4` followed by
   `0x28798`. At `0x22334..0x22336`, `adr r0,#0x5c` is exactly the in-function
   address `0x22394`, the `USBSerial` string, and stores that pointer into the
   initialized structure at `+0x60`.
3. `0x28554..0x285c0` contains a request/selector dispatcher. Its `r5 == 9`
   branch passes the exact PC-relative address `0x285c8` to `0x28ce4`.
   `0x28ce4..0x28d32` counts the ASCII string and emits alternating byte/zero
   pairs after a two-byte leading value, i.e. it builds a UTF-16LE-style string
   descriptor buffer rather than merely logging that string.
4. The configuration-setup helper `0x287c8..0x28824` recognizes a header
   byte pair `0xc1,0xee` and a five-byte length before forwarding to `0x285f4`.
   That is concrete callback/dispatch code, but this audit does not assign it
   a USB-standard request name from those bytes alone.

The metadata sample independently records the device-level product and the
interfaces shown below:

| interface | class/subclass/protocol | interface string | retained endpoints |
| ---: | --- | --- | --- |
| 0 | `02/02/01` | `USBSerial` | interrupt IN `0x83` |
| 1 | `0a/00/00` | `USBSerial` | bulk OUT `0x01`, bulk IN `0x81`, 64 bytes |
| 2 | `ff/00/00` | no retained interface string | bulk IN `0x82`, bulk OUT `0x02`, 512 bytes |

The exact firmware strings and this descriptor metadata support an identity
candidate: this firmware implements a USB personality consistent with the
observed Samsung STL1 composite device. It is still not a current execution
binding because descriptor construction can exist in an unexecuted packaged
image and the host sample did not bind an interface driver to the image.

## Line coding and DTR boundary

The retained bounded control-dispatch bodies establish descriptor/configuration
processing, but do not recover a complete mapping for the CDC class requests
or a DTR state writer. In particular, this audit does not label any routine as
`SET_LINE_CODING`, `GET_LINE_CODING`, or `SET_CONTROL_LINE_STATE`, and does not
claim that a host serial open would toggle DTR in this firmware. That remains
an important safety uncertainty, not evidence of no side effect.

The retained system also has no proven host binding: all driver links for
interfaces `7-1:1.0`, `7-1:1.1`, and `7-1:1.2` were absent at the metadata
sample. `/dev/ttyUSB0` existed but was not mapped to this device; no ACM node
was printed. These are bounded observations, not an inventory of all serial
paths at all times.

## Diagnostic (`printf`) path boundary

Image-0 error and monitor code calls formatter `0x2b334`; the previously
recovered live-RT checker calls it at `0x2170c`. In the complete bounded body,
`0x2b334..0x2b360` formats up to `0x100` bytes and invokes `0x2b36e`; that
routine emits one byte at a time through `0x2b362`, which calls `0x2b2a0`.

This is a positive firmware-local diagnostic pipeline:

```text
format 0x2b334 -> byte loop 0x2b36e -> per-byte helper 0x2b362 -> 0x2b2a0
```

The inspected `0x2b2a0` body begins with a retry/status loop through `0x2b23c`
and other lower helpers; this audit did not recover a direct wire to the
`USBSerial` interface or a fixed bulk endpoint. Therefore it does **not**
prove that the relevant RT/monitor text is emitted to USB, that a passive host
read would receive it, or that any console endpoint is safe to use.

## Safe interpretation

This work binds the firmware's named descriptor construction more closely to
the observed physical USB composite identity. It does not create an approved
debug-console procedure. Any later diagnostic proposal would first need a
separate static binding from `0x2b2a0` to an exact endpoint/transport and a
fresh safety review of enumeration, runtime-PM, line coding, DTR, and receive
semantics. No existing `/dev/ttyUSB0` should be assumed related to this device.
