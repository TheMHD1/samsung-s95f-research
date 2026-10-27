# Independent runtime audit — ERR_DET cdev metadata probe

Audit date: 2026-10-26 UTC

## Outcome

**ACCEPTED for the narrow metadata-only contract.**

The immutable input record is
`metadata-result-20261026a.json`, 142,028 bytes, SHA-256
`8f123bdfae89480b34f303b78b91b801181c3fe29b8b0c73e8ea3a50f6da0426`.
It records `accepted=true`, `read_usable=true`, and
`cleanup_confirmed=true`.

This result proves that the metadata ioctls identified the expected GPIO chip
and that line offset 5 was unclaimed and carried no reported line flags at the
sample time.  It is not a GPIO value sample and says nothing about whether the
physical ERR_DET signal was high or low.

## Independent replay

I replayed all 11 retained root responses from their base64 transport bytes,
parsed each as strict UTF-8 JSON, and confirmed byte-for-byte equality with
the corresponding stored response object.  For every call:

- the retained command echo exactly matched the issued command and its stored
  byte count;
- transport exit was zero, no host timeout occurred, and client stderr was
  empty;
- the response reported the expected TV model, authenticated root UID/EUID
  zero, host-assisted root persistence, and the global-system-files-unchanged
  invariant;
- there was exactly one remote command with exit zero, no timeout, and empty
  remote stderr.

The sequence was exactly: preflight, private-directory creation, six staging
chunks, one helper execution, postflight identity validation, and cleanup.
The final retained response was exactly `PRIVATE_REMOVED`.

The record pins the reviewed runner/build contract:

- runner `91b292f607bca3f9e150548d9b3f8a2173a35f8e8dc9ce507d755025ed66524a`;
- build manifest `c34ac1153af5fc7e3e39fac6337b4be8243448b6f59dba675ea18b21fd9abf46`;
- managed source `266b0cc7e74c2265f4839d24b363f7db535c4864f5376147bc54f390aafaa01a`;
- managed DLL `2d2c243d32100811de1c3fcf34e7e258871d74b908a0aafb093f853f294ac0c1`;
- ABI report `2e569fee229a30f291d0b4712344f5e5694b1430ea62e0c4f20dbe1000337170`.

I reran the frozen parser against the raw retained preflight and execute
responses.  The reproduced objects exactly equalled the stored `preflight`
and `execution` objects.

## Actual result

- Same boot ID before and after:
  `00000000-0000-4000-8000-000000000000`.
- Uptime advanced monotonically from 78077.33 to 78078.73 seconds.
- Helper identity was PID 8145, start ticks 19519613; it completed before its
  deadline with exit zero.
- Managed runtime was ARM32, four-byte pointers, little endian, UID/EUID zero.
- Device open returned fd 26 with errno zero.
- CHIPINFO returned zero: name `gpiochip15`, label `gpio15`, 8 lines.
- LINEINFO returned zero for offset 5: empty name, empty consumer, flags
  `0x00000000`.
- Chip close returned zero; managed stderr was empty.

The exact staged program was invoked without `--input-once`.  Its output was
`GPIO_CDEV_MODE=metadata_only` and `METADATA_COMPLETE`; it emitted no handle,
GET-value, or input-completion fields.  Thus no line-handle request or native
GPIO value read was executed by this run.

## Boundaries

- `consumer=""` and `flags=0` are point-in-time metadata, not a reservation;
  another consumer can race a later request.
- No physical panel state was observed by this probe.
- No electrical value, fault assertion, recovery effect, or black-panel cause
  follows from this accepted result.
- The separate `--input-once` path remains outside this audit and requires its
  own exact-byte review before use.
