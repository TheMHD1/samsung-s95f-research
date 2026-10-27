# HDMI/OCIF support predicate: boot-input provenance

The HDMI/SerDes lead remains applicable under the captured board configuration:
the kernel command line contains `ffinfo=00000401`. If the reconstructed boot
parser and probe initialization ran as shown, the cached support predicate
evaluates to **one**. This closes a static input-provenance gap. It is not a
live read of the module's cache, a binding check, or evidence that the SerDes
path executed during a blackout.

## Exact sources

- Acquired kernel `overnight/kernel-Image.bin`, 11,786,752 bytes, SHA-256
  `77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d`.
  The earlier acquisition matched the running kernel banner; it is not a live
  kernel-text hash. Addresses below are Image offsets, not runtime VAs.
- Acquired `system_drv.ko`, 46,510 bytes, SHA-256
  `fbe4eaad57c66865e2cc50b575a878a690c06303905e666e75b9f08d139dd1f0`.
  Module offsets are section-relative and distinct from Image offsets.
- [Bounded boot-metadata capture](../overnight/formfactor-boot-metadata-20261026/intent.json):
  authenticated root on `198.51.100.20`, model `QN77S95FAFXZC`, host-assisted
  root, same boot `00000000-0000-4000-8000-000000000000`, uptime
  `66546.21..66546.22`. Remote/host exit zero, no timeout or stderr. The
  on-disk module hash matches the acquired module. The physical screen was
  unobserved. Only boot ID, clocks, kernel release, module hash and a bounded
  `/proc/cmdline` read were requested. No hardware getter or control ran.

Raw client stdout SHA-256:
`279ed400c67d30707b0bca39dec3f616df72163cb202787a4915a91dd60e4bd9`.
The raw response is retained unchanged; no slash-newline normalization was
needed. The decoder checks the whole ordered frame, canonical base64,
8,192-byte decoded bound, unique hexadecimal parameter, target/authentication,
command-intent equality and unchanged boot.

## Reconstructed chain

1. In the Image, the PREL32 export record at `0x99e64c` resolves the exact name
   `get_formfactor_info` to `0x4c2490`. Its entire three-instruction body loads
   the 32-bit value at Image-relative BSS `0xc31714` and returns it. That BSS
   address lies beyond the saved file payload but inside the declared memory
   extent. No file bytes or runtime RAM were read at that address.
2. The literal `ffinfo=` is at `0xa6751e`. A setup-table-shaped 24-byte tuple
   at `0xa6deb0` contains its absolute nominal pointer, a pointer to handler
   `0xa233a4`, and zero. The linked nominal base used for those two pointers
   is `0xffffffc010080000`; this is not a recovered running address. The
   handler rejects null/empty input, constructs output address
   `0xc31710+4`, requests base 16, and calls `0x30f708`. The latter is
   independently identified as exported `kstrtouint` by PREL32 record
   `0x9a03a4`. The handler returns one on the parser's zero result, otherwise
   zero. This identifies a boot-parameter initialization route, without
   proving that no other writer exists.
3. `system_drv.ko:tztv_sys_get_formfactor_info`, `.text+0xdf8`, size 64,
   calls the imported `get_formfactor_info` at `0xe00`, copies its returned
   `w0` to `w1`, and stores that word at module `.bss+0xa8` at `0xe18`.
   The `.bss+0xa8` object is symbol `ffinfo`, size four. The module's
   `system_drv_probe`, `.text+0x858`, size 620, calls this initializer at
   `0x918` on its successful setup path. Its dynamic import binding and live
   cache have not been sampled.
4. `tztv_sys_is_oc_support`, `.text+0xdc0`, size 40, uses that same module
   object. It returns zero if byte three's upper nibble is nonzero; otherwise
   it returns whether byte one equals four. For a little-endian cached word
   `0x00000401`, the bytes are `01 04 00 00`, so this predicate returns one.

This does not establish that every invocation actually sees that word. It
shows that the captured boot input is consistent with enabling the support
gate, rather than dismissing the SerDes lead on a presumed unsupported model.

## What this changes, and what it leaves open

The support predicate now has a positive, exact-binary initialization route
to a captured input. The cached OCIF-availability byte and HDMI resume
dispatch remain separate questions. Support enabled does not mean link
locked, panel powered, or a resume operation observed.

No factory value, boot argument, runtime memory, firmware, module, panel rail,
or display setting was changed. No recovery or prevention conclusion follows.
The owner-observed transition into blackness remains required to distinguish
initial fault, subsequent recovery handling and physical consequences.

## Reproduction

[Offline verifier](serdes-support-boot-provenance.py) hash-pins both binaries,
the existing exact-ELF reader and every capture sidecar. It independently
decodes the two relevant export records and checks section-aware module
symbols/relocations, kernel instruction landmarks and the setup tuple.
[Saved excerpts](serdes-support-boot-provenance.disasm) are compared exactly.
The verifier uses explicit exceptions, including under optimized Python:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 serdes-support-boot-provenance.py
PYTHONPATH=/tmp/tcon-capstone python3 -O serdes-support-boot-provenance.py
```

These checks support reproducibility; manual dataflow review is still needed.
Two independent read-only reviews checked the raw capture, instruction
dataflow, nominal-pointer interpretation, and conditional evaluation and ran
the verifier normally and under optimized Python. Neither found a material
blocker. Their clearance remains limited to this static and metadata scope.
