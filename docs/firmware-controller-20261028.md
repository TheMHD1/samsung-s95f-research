# Firmware, controller and stock-initialization workbench

This fixed cutoff adds reusable source maps, bounded readers and logging tools. It extends the authenticated firmware/filesystem work into controller input-buffer ownership, shared fault state, stock initialization, host status queries and an OCL mailbox receiver candidate. The [format and address-domain guide](controller-firmware-formats.md) is the shortest route into the firmware work; the [complete catalog](catalog.md) retains the authored reports, annotated instruction excerpts, source reproducers, tests and independent reviews.

The archive remains an experimental Samsung S95F/Tizen workbench. A printed diagnostic, acknowledged ioctl, new USB enumeration, sampled RAM state and emitted light are different evidence classes. There is no demonstrated permanent blackout fix. New work uses exact source hashes; its relationship to running firmware is qualified separately.

## What is included

| Work | Reusable result | Remaining boundary |
| --- | --- | --- |
| [GR namespace correction](../research/panel-idle-20261026/overnight/operating-mode-label-audit-20261028gr/README.md) | Distinguishes sampled global R+0x10=4, formatter category1 and predicate argument1 | Source call arguments are not observed invocations; compact rows do not retain every context field |
| [GS source-control plan](../research/panel-idle-20261026/overnight/hdmi-source-control-plan-20261028gs/README.md) and [GT-v2 fixed probe](../research/panel-idle-20261026/overnight/hdmi-source-read-probe-20261028gt-v2/README.md) | Two cached source keys, exact component hashes and canonical-path guards, bounded parser/dry-default wrapper and tests | Cached keys are non-atomic; no physical input, video/light, source-selection success or primary external-device identity follows |
| [GV input producer](../research/panel-idle-20261026/overnight/rtp-input-buffer-producer-20261028gv/README.md) | Actual software selector and descriptor-driven copy into a three-slot ring | Physical aperture producer, input epochs, dynamic/DMA writers and complete alias census remain open |
| [GX state initialization](../research/panel-idle-20261026/overnight/rtp-fault-clear-paths-20261028gx/README.md) | Image0 shared-root initializer differs from image1 counter clearing | New USB and N0 do not prove image0 startup or a cleared fault tuple |
| [GY emergency boundary](../research/panel-idle-20261026/overnight/menu-fault-rearm-design-20261028gy/README.md), [HB status bridge](../research/panel-idle-20261026/overnight/rtp-host-status-bridge-20261028hb/README.md), [HD unwind design](../research/panel-idle-20261026/overnight/ap-emergency-unwind-design-20261028hd/README.md) | Positive fault-lowbit → reason16 → AP status/host bit4 path, with separate teardown and output effects | Rewriting a few root halfwords is not a qualified emergency unwind; historical branch choice and current PC remain unknown |
| [HA fixed witness reader](../research/panel-idle-20261026/overnight/ap-fault-witness-reader-20261028ha/README.md) | Fixed low-SRAM read plan, modern owned USB binding, exact phase/receipt/cleanup and host tests | Sampled witnesses are non-atomic and do not prove a unique writer, current execution or physical state |
| [GZ MODE2 domain map](../research/panel-idle-20261026/overnight/stock-mode2-reset-domain-20261028gz/README.md) | Operation41/off-on callbacks, conditional ERR/monitor/platform paths and discarded return boundaries | A zero return can be narrower than completed initialization; instruction reload/full-domain restart remains unproved |
| [HC original logger](../research/panel-idle-20261026/overnight/stock-log-instrumentation-map-20261028hc/README.md), [HC-v2 correction](../research/panel-idle-20261026/overnight/stock-log-instrumentation-map-20261028hc-v2/README.md) | Nonclearing dmesg capture, bounded chunk framing, private raw-before-classification archive, source-associated markers | Original real empty-stderr guard refusal stays refused; v2 uses numeric regular-file proof and tests real GNU stat behavior |
| [HE OCL sender](../research/panel-idle-20261026/overnight/ocl-reset-receiver-map-20261028he/README.md), [HG receiver candidate](../research/panel-idle-20261026/overnight/ocl-mailbox-system-dispatch-20261028hg/README.md) | Linux mailbox3f framing, checksummed extracted SPARC candidate, operation dispatch and secondary STBC command40 | Candidate file identity is not active flashed identity; secondary receiver, pin electrical meaning and reset domain remain unresolved |

The frozen original GT authored source is included as the minimal GT-v2 predecessor closure. Its canonical-path refusal is preserved, not promoted to a successful probe; no original root/runtime response is copied.

GQ's private SSH endpoints, authentication fingerprints, reservation/host identity and provisioning records are withheld. The reusable method is to inspect fixed local literals without executing the controller, compare independent retained records and keep configured routes separate from current reachability, authorization or active interface. No current external-device connection is established by that offline method. The TV cache/source work above is included; personal network administration is outside the public corpus.

## Actual HF observation, with rejected outcomes retained

The [tenth offline fixture](../fixtures/stock-mode2-observation.json) is a typed projection of a sealed 26-input private cutoff. Its [builder](../tools/build_stock_mode2_fixture.py) verifies original hashes and embedded raw-window bindings; its [verifier](../tools/verify_stock_mode2_fixture.py) checks the public projection. It does not replay omitted authenticated commands, publish kernel logs/identities/PIDs/clock values, or manufacture a success for a rejected wrapper.

1. A completed fixed EB read samples equal full R windows with stop1/fault4097/ordinary0, limit40/logger0. Both N windows are zero; that alone is not a clean-state criterion.
2. One unchanged stock operation41/MODE2 helper returns zero and completes its own cleanup. Its terminal classification is **kernel_return_zero_only**. No threshold write or automatic retry occurs.
3. An accepted HC-v2 post snapshot preserves raw bytes before classification. Positive source-associated reports include off/on, OCL reset returns, normal-tail entry, init/access/display/PMIC/LPDDR4 status, unchanged frame mode and register replay completion. QDF marker PIDs match the native receipt; OCL return lines themselves lack a PID. This is positive normal-tail evidence for this attempt, so the ERR-skipped branch does not explain this particular attempt. Subsystem reports are not independent optical measurements.
4. Positive disconnect followed by enumeration retains Linux boot/descriptors; the sixteen identity fields differ only in four device-instance metadata fields. A later complete EB read samples equal software-clean0/0/1 at40/logger0 and N0. This is historical sampled software recovery, not proof of the exact clearing path, all-domain reset, universal memory clearing or instruction reload.
5. A separate later HA attempt refuses in metadata before staging, native invocation or vendor transfer. A later retained kernel snapshot records a standby request from `hdmicec-service`, reason46. The originating peer/owner is unknown, and neither RTP relapse nor a causal link to the preceding recovery is established.

The first HC capture had already run dmesg when its overly literal regular-file guard rejected a legitimate empty stderr file. It produced no terminal capture frame; its dmesg exit is **unknown**. A separate forensic fetch preserved the existing bytes without another dmesg run and kept the refusal. HC-v2 corrects that file-type proof additively. These facts stay separate from the later accepted snapshots.

The cutoff excludes subsequent ordinary wake, ongoing HH/HI, disabled partial GU, nonexistent GW and mutable CURRENT. It does not claim present-day device state. Earlier publication fixtures, source interpretations and corrections remain unchanged.

## Reproduce and adapt

Run public checks entirely offline:

```sh
python3 -B tools/verify_stock_mode2_fixture.py
python3 -O -B tools/verify_stock_mode2_fixture.py
python3 -B -m unittest discover -s tests
python3 -O -B -m unittest discover -s tests
python3 -B tools/verify_public.py --root . --check-git
```

The fixture tests reject promoted refusals, invented dmesg exit values, incorrect lifecycle/counter types, wrong global-selector labels, complete-reset/optical claims and peer attribution. They validate a typed observation, not the original private transport.

Archived device helpers are provenance-bearing experimental source, not portable unguarded commands. Authenticated transport, original OEM inputs and private runtime readiness are intentionally absent. Source-only audits can be reproduced with independently acquired matching inputs and the specified tools; do not reinterpret missing private dependencies as successful target qualification. Original code is covered by the repository's scoped reuse grants; vendor snippets and third-party dependencies retain their own rights.
