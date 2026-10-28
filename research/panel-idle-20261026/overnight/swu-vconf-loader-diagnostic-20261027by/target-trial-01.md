# BY loader-only target diagnostic

The central one-shot diagnostic completed with exit 0. Both `dlinfo` and
`dladdr` named `/lib/libvconf.so.0`, rather than the held `/proc/self/fd/N`
spelling. Both owner files resolved to the original canonical file and
matched its stat identity, pinned size, SHA256 and ELF Build ID. The exact
`vconf_get_bool@VCONF_BUXTON_1.0` symbol resolved successfully. Before and after
maps named `/usr/lib/libvconf.so.0.3.1`.

This supplies a concrete target mechanism sufficient to reject BY's exact
filename-string binding check: the library was already mapped before the
explicit `dlopen` and the loader returned its existing spelling. BY's earlier
stage-only report did not identify that cause; this subsequent diagnostic
must remain a separate observation. Matching the on-disk object does not
hash or authenticate already mapped executable pages.

The getter pointer was never converted into a delegate or invoked. No TEE
library binding/session/command, plaintext extraction, UI key, controller
power command, USB vendor transaction, firmware change or blackout fix was
performed. Library and dependency constructors may run as part of loading;
this is not described as a file-only operation. Native deadline25sec and
outer root deadline45sec remained in place.

The exact DLL was 23,552 bytes, SHA256
`45264f7c7d62b2c985870097f0fbb8a59fc8ee1b8e54fb47d6b34b3175d9378e`.
Full authenticated transport records remain private in
`s95f-vconf-loader-diagnostic/target-run-01`. The known stage
`/tmp/swu-vconf-loader-diagnostic-20261027by` is retained; this record makes
no cleanup claim. No automatic retry occurred.

The next additive adapter revision must prove canonical owner-file identity
and pinned content for allowlisted owner aliases rather than demand equal
filename strings. BX/BY frozen sources and results remain unchanged.
