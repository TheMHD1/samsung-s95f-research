# Copied-userspace census for private HDMI suspend/resume controls

This offline census follows the corrected control IDs proved in [private-hdmi-invocation-roots.md](private-hdmi-invocation-roots.md): `0x00a009be` (suspend) and `0x00a009bf` (resume). They are **not** `0xa00009be/bf`; the switch code computes its base as `(0xa00 << 12) + 0x998 = 0x00a00998`.

## Result

No positive userspace producer was recovered from the 41 copied ARM `ET_EXEC`/`ET_DYN` files in `binaries/`. The hash-pinned inventory manifest is `6ac980c13bc4318a77519fa2dbfada3346de05c73fc4d8765df2666196becba2` and individual input hashes are preserved in [the generated census](private-hdmi-control-producers-v2.disasm).

The verifier found neither exact little-endian 32-bit CID literal anywhere in those files nor the ordinary same-register immediate construction:

- ARM, condition `AL`, `MOVW Rd,#0x9be/#0x9bf` followed within 64 bytes by `MOVT Rd,#0xa0`.
- Thumb-2 `MOVW`/`MOVT` equivalent at every two-byte alignment.

The latter checks the standard common synthesis form without confusing a raw literal pool for a call argument. It does not rule out arbitrary arithmetic construction, values carried over IPC, JIT/managed code, code loaded after this corpus was copied, or any live call.

Some copied userspace files contain generic V4L2-adjacent strings (`TIFSDaemon`, `libfactory-impl-sec.so.0.1`, and `libvideo-ft-control-impl-sec.so.0.1.0`), but none contains either control ID by either tested representation. Those strings therefore do not create a positive link to the HDMI private-control path.

## Concrete boundary

The copied `avocd` ELF has a `DT_NEEDED` entry for the exact, currently unacquired `libhdmi-control.so.0`; copied `tv-viewer` has an unacquired `libsource-api.so` dependency. Either is a reasonable *acquisition boundary* for later static work, but this evidence does not identify either as the CID producer. No exact missing file can honestly be named as the producer from the available corpus.

Consequently, this census provides no source/UI/content causality. The only positive static route remains the kernel module's V4L2 extended-control dispatch to the two private helpers.

## Reproduction

[private-hdmi-control-producers-reproduce.py](private-hdmi-control-producers-reproduce.py) pins the complete userspace inventory and each input hash, performs literal and encoding checks, confirms the two noted `DT_NEEDED` boundaries, and requires equality with the exclusively-created [census listing](private-hdmi-control-producers-v2.disasm). Its ARM and Thumb adversarial fixtures put a misaligned matching `MOVT` before a later aligned true match, ensuring the bounded scan continues past the decoy.

```sh
PYTHONPATH=/tmp/tcon-capstone python3 private-hdmi-control-producers-reproduce.py
PYTHONPATH=/tmp/tcon-capstone python3 -O private-hdmi-control-producers-reproduce.py
python3 -m py_compile private-hdmi-control-producers-reproduce.py
```

Normal and optimized checks passed offline. No TV, network, root, ioctl, or source-control action was performed.
