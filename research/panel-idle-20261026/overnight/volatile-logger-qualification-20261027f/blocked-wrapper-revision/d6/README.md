# Volatile logger qualification — offline build

This folder records the offline architecture review and verifier for the fixed
secondary logger smoke helper. No live execution occurred.

Run the verifier in both ordinary and optimized Python modes:

```sh
python3 verify-offline-build.py
python3 -O verify-offline-build.py
```

Independent review is required before any TV invocation.
