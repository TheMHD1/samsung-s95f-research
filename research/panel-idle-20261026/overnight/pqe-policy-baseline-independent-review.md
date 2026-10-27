# PQE policy baseline: independent review

This records an independent, read-only audit of the failed first capture and
the accepted optimized capture. The reviewer used only retained local files;
the review made no TV, root, network, device, getter, setter, ioctl, service,
key, display, power, factory, or staging call. It is an audit of software
state and acquisition provenance, not a physical panel observation or a fix.

## Exact acquisition inputs

The first attempted capture used these archived bytes:

* reader `8575b16accb3f3b623d29229ec82ab54a7945d551c5aebe0e57d3057aceba3c7`;
* tests `5b1698caac0fbebb7b6c85025c4ead853b98261a3fe7fd64824c6ba4829752e4`;
* remote command `ad641e7b0ac4902aa955ad647d837a787ebd89c3a2d4b7a4f289e730d0bfa18e`,
  4069 bytes; and
* retained result
  `pqe-policy-baseline-20261026T173952Z.json`, SHA-256
  `02386f896fd7af1f3131aec7133152344695c9702609c11c65851425e9fc39ce`.

The accepted retry used these archived bytes:

* reader `161af4bd011cb81f32cf69e8e189ced3b15045c0eaf7df5820120cf2ff99bb07`;
* tests `1199faf2dbb695a9af79474737b4ba71bf64c0bd2785b59824a0e74e35ab977c`;
* remote command `b963044af371423a1245c41180dac5f8c821e6d99215b74a3acfb580b76fb9b7`,
  4167 bytes;
* archive manifest
  `7be8c9434bd53eb2cd2e7a71305aaf072b96e829dbc6601b58579e82f7e1a122`;
  and
* retained result
  `pqe-policy-baseline-20261026T174544Z.json`, SHA-256
  `5c36124d0d510fff8ac5ff282cfc43c1a70854d065b76da68ad760ceb56482a4`.

The successful record, its intent, and the archive all contain the same
remote-command hash. The archived and active reviewed reader/test files are
byte-identical. The successful intent explicitly excludes event queries,
getters, setters, ioctls, display/power/factory control, target-code
invocation, and staging. Offline evidence before execution was 21 passing
tests, successful Python compilation, generated-shell syntax validation, and
default dry behavior.

## First attempt: preserved timeout, not a baseline

The first nested root result was authenticated as uid/euid 0 on the expected
model and boot. It ended with exit 124 and `timed_out=true`; the host record is
`accepted=false` and contains no accepted summary.

The partial stdout retains `ID_START`, the 1,345-line `MAPS_START`, a full
`POINTERS_START`, all twelve ordinary `READ_*` blocks, and
`READ_backend_cache`. It then prints the `POINTERS_END` marker without a
pointer value. Its stderr contains 28 complete `dd` diagnostic groups:
12 initial pointer reads, 12 layout reads, one backend-cache read, and only
three reads from the attempted ending pointer pass. A complete typed capture
requires 37 groups. `MAPS_END`, `ID_END`, `UPTIME_END`, and `UTC_END` are
absent.

The retained read blocks have their expected individual byte lengths, and
the retained QD header happens to agree with the initial pointer chain. That
does not repair the missing end guards. The partial values are therefore raw
timeout evidence only: they are not a paired baseline and cannot support a
physical, onset, fault, or causal inference.

The timeout is consistent with the original Bash `mapok` rescanning all
1,345 map lines for every pointer and range check. The optimized reader
replaced that loop with a fresh, fixed-width ARM32, `LC_ALL=C` awk containment
check; it did not extend the timeout or cache a potentially stale map. The
exact local root-agent implementation launches the command in a new session
and sends `SIGKILL` to its process group on timeout, then waits for the leader
and output readers. The returned timeout result shows that handler completed,
and the acquisition command creates no detached task. The protocol does not,
however, retain a post-kill process-group-empty observation, so cleanup is a
source-backed expectation rather than separate runtime proof of group
emptiness.

## Accepted capture: raw completeness and provenance

The optimized capture's outer transport exited 0 with empty controller
stderr. The nested response records the expected model, authenticated root,
host-assisted persistence, and the global-system-file invariant as true. It
contains exactly one command, identical to the command saved in the result;
that command exited 0 and did not time out.

Independent parsing found all 23 expected framed sections. The following
guards are complete:

* `POINTERS_START` and `POINTERS_END` are identical;
* `MAPS_START` and `MAPS_END` are byte-identical and each contains 1,345
  lines;
* start and end identity are the same boot
  `00000000-0000-4000-8000-000000000000`, PID 706,
  `/usr/bin/avocd`, and start ticks 603;
* installed avocd and libave hashes match the offline-pinned hashes
  `ab450eaf99c793f3c7a9360629b1a1677e9d86dcd74a1f93796b56ba07401de9`
  and
  `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`;
* all 111 stderr lines form exactly 37 successful `dd` groups: 12 starting
  pointer reads, 12 layout reads, one typed-backend cache read, and 12 ending
  pointer reads; and
* every base64 payload has the required decoded length, totaling 240 requested
  memory bytes.

The captured uptime advances monotonically from 58355.79 to 58356.56, a
0.77-second software snapshot window; UTC advances from 1793036746 to
1793036747. Re-running the frozen validator offline against the retained root
response reproduces the saved summary exactly.

## Runtime pointer and type bindings

The libave load bias is `0xf6b77000`. The guarded runtime chain identifies:

* base `RoseMVideoEnhancer` object `0xf71291a0`, vptr `0xf7113bf8`, and
  state `0xf6389c58`;
* the separate DLSR global-storage route at bias `+0x5b24e0`, which resolves
  to that same state in this capture;
* base `QDDimming` object `0xf7203698`, vptr `0xf71162e8`, inner state
  `0xf63895d8`, and initialized byte 1; and
* `DimmingBackendRoseMQD` object `0xf7203630`, vptr `0xf711852c`, and slot
  target `0xf6d3d275`.

The VE, QD, and backend vptrs are in the exact read-only libave mapping. The
backend slot target, with its Thumb bit removed for the range check, is in the
exact executable libave mapping. QD header words 0, 1, and 4 equal the guarded
QD vptr, inner pointer, and backend object. This supports the recorded runtime
software types and the eligibility of the one backend-cache read. It does not
prove that a cached request reached or changed the panel.

## Retained values

The accepted raw words decode to:

* DLSR class 5;
* HDR brightness-optimizer class 1;
* VE configuration words `16, 15, 14, 13, 0xffffffff`;
* GSR enable 0, AI genre 0, and cached GSR class 0;
* raw color-booster word 513626;
* QD working-duty words `236, 236`;
* the QD Weber-policy block
  `1023, 53, 1, 2, 980, 990, 5, 2, 9, 5, 200, 300`, where the second word is
  the recovered object-count field;
* Weber gain 1023, target 1023, and count 0; and
* typed backend cache 236.

These are sequentially read software fields and caches. Equal endpoint
pointers do not exclude a value changing away and back, and concurrent daemon
changes are explicitly not excluded. The capture did not observe the physical
screen. Equal working/cache values do not prove command transport, panel
application, luminance, physical light, panel health, the time or cause of a
blackout, or recovery. No fault-causality conclusion is supported by this
baseline alone.
