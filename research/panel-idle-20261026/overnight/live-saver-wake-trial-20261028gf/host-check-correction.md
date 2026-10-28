# Local postprocessor correction

The first parent-only invocation of `check-eb.py` failed with `ValueError: too many values to unpack (expected 2, got 3)`. The frozen EB parser returns `(name, bytes, sha256)` triples. The new host postprocessor initially unpacked pairs; it was corrected to unpack all three values and compare the supplied digest against both the saved result inventory and recomputed SHA256.

This failure happened while reading already retained baseline files on the host. It sent no target command, repeated no USB read, changed no capture and did not alter the frozen EB parser. The corrected postprocessor verifies all16raws for the original baseline, fault confirmation and later validation. This note records the observed diagnostic; it is not an additional original shell transcript.
