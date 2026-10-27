# Managed USB code fingerprint reader

Offline-only fixed three-window target-`0x101` memory reader. See
`source-note.md` for geometry and interpretation limits.

Host-only verification:

```sh
python3 build-offline.py
```

`run-once.py` is dry by default. Its `--execute` path requires an absolute
fresh output directory and the exact reviewed manifest SHA. Do not execute it
against the TV until a separate independent review clears the final pins.
