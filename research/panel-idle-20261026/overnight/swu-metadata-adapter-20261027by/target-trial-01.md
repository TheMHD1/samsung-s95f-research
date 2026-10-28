# BY first target attempt: preflight passed, selector binding refused

One centrally dispatched BY invocation returned exit 65 with:

```text
REFUSED_OR_FAILED stage=selector-binding metadata_published=0
```

The exact reviewed DLL is
`028bcfa1641a1794a27283adf9adf1af9de2e22bb4dc54176fdf2b2fa02f2d60`;
deployment manifest
`0f7e7ceac5215322c51a699bff608d45284e74c80e20bebe7223140dc310e14e`;
runner
`645c9cf391b85dc94f2d74807e30d8eb072353a39ab448c4e3143ae23d1d8563`.
Complete authenticated records remain private in local state trial
`s95f-live-trials/swu-by-01`. The runner retained its stage and did not retry.

This reaches a later stage than BX. In the exact source, all six pinned-file
constructors and input marker/hash validation complete before the stage
changes from file preflight to selector binding. Thus the corrected statx
field policy passed this target invocation. The architecture-specific open
flags and all other identity/hash/ELF checks were retained.

The stage includes constructing the vconf `Binding`, looking up the exact
versioned getter, creating its delegate, and running the first selector
check. No `SELECTOR` output row was returned. The available output cannot
distinguish loader return, link-map name check, symbol resolution/ownership,
delegate construction or an earlier getter exception. It must not be
reported as a particular loader failure or master/submodel mismatch.

The source's following `teec-binding` stage was not reached. No common,
backend or wrapper `Binding`, TEEC initialization, session or command is on
the completed preceding path. Vconf loading/constructors may have occurred;
the output does not establish whether that load succeeded. No crypto
diagnostic, plaintext, TEE acceptance, firmware change or blackout fix is
established.

The next bounded diagnostic examines only the fixed vconf loader and symbol
ownership. It must not invoke the getter or load/invoke the TEE client. In
particular, filename spelling alone is not proof of a different loaded
object: the loader may coalesce a previously loaded object. That is a
hypothesis to measure, not a reason to remove the binding identity checks.
