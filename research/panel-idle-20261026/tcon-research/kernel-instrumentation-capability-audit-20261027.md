# Retained-kernel dynamic instrumentation capability audit

Recorded 2026-10-27 UTC. This is an offline-only audit of the retained kernel
Image, reconstructed export table, two exact installed-module copies and
previously retained read-only target metadata. It did not build, sign, load,
or unload a module; register a probe; alter tracefs; access the TV; or use the
network.

## Result

The retained kernel has a positive, module-visible **tracepoint callback**
surface. Its reconstructed 9,379-entry export table contains:

* `tracepoint_probe_register` and `tracepoint_probe_unregister`;
* the priority registration variants;
* `for_each_kernel_tracepoint`;
* tracepoint module notifier registration/unregistration; and
* concrete exported tracepoint objects including runtime-PM idle, resume,
  suspend and return, plus suspend/resume.

The saved machine code at those exact export targets is non-stub registration,
enumeration and unregistration code. Therefore a separately built module
could, **in principle**, enumerate built-in tracepoints and attach a bounded
callback, then detach it before unload. That is a real capability finding,
not an inference from tracefs filenames.

The retained evidence does **not** provide a module-callable kprobe/kretprobe
surface. `register_kprobe`, `unregister_kprobe`, `register_kretprobe` and
`unregister_kretprobe` are absent from the reconstructed export table and as
strings in the saved Image. The target sample also had no `kprobe_events`,
kprobe blacklist, `available_filter_functions`, `/proc/kallsyms`, or kernel
config file. This does not prove `CONFIG_KPROBES=n`; it proves the narrower and
operationally relevant point that no supported exported registration API or
target symbol-address source has been established for an external module.

`kallsyms_lookup_name` is likewise not exported. Exported `__symbol_get` is
present and already used by Samsung modules, but it resolves exported symbol
names; it is not evidence that an absent kprobe export can be recovered.

There are two independent blockers before any observer module could be called
buildable or loadable:

1. The exact kernel headers, generated configuration, `Module.symvers`, and
   private ABI definitions are not retained. Installed modules use the custom
   vermagic `13781815, release SMP preempt mod_unload aarch64`, not merely the
   public banner `5.4.261`.
2. Exact installed module files end in a Samsung `:UEP` trailer. The standard
   kernel helper `is_module_sig_enforced` is compiled as `return 0`, and the
   sampled `modules_disabled` value was zero, but those facts do not establish
   acceptance of a newly built file by the separate UEP policy. No signing
   key, accepted unsigned test module, or module-load policy proof exists.

Thus a tracepoint-only observer is theoretically supportable without flashing
firmware, but it is **not deployment-ready**. An arbitrary function/UART RX
kprobe observer is not supported by the retained capability surface.

## Exact sources

| retained input | size | SHA-256 |
| --- | ---: | --- |
| `overnight/kernel-Image.bin` | 11,786,752 | `77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d` |
| `overnight/kernel-export-index.json` | 1,939,571 | `6d3ffe0edfd2ab92fc4439ffe35371db4c3f2ad8a99cf5b2b20ae2ef4eb937ac` |
| artificial `kernel-export-view.elf` | 12,204,096 | `83a91462c65fd80a4a0ddcd7d5c295b35ea38fc8823298f9018c7353f3cafbc7` |
| copied `sdp_pqe_frc.ko` | 1,015,070 | `1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4` |
| copied `sdp_ocl_jp.ko` | 594,110 | `e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c` |
| retained kernel-access metadata | 1,492 | `5e92bbfcc7ee2844e7dd43a4d73fe4b42ff8178240aac89888a2313a6628c15b` |
| retained probe-capability metadata | 6,674 | `6dbca53fdc4885fe7cc359cd25b8364fb53619f5693642b73a3ec54cdf69b22e` |

The export index describes itself as a reconstructed contiguous namespace-zero
PREL32 export table around verified exports, with Image offsets rather than
runtime virtual addresses. It is not original vmlinux or kallsyms. The
artificial ELF merely gives those Image bytes and reconstructed exported
labels to an AArch64 disassembler; its symbol labels outside exact exports
must not be treated as original debug information.

## Positive tracepoint API evidence

The exact export records are:

| export | Image/file offset |
| --- | ---: |
| `tracepoint_probe_register_prio_may_exist` | `0xe62d8` |
| `tracepoint_probe_register_prio` | `0xe6358` |
| `tracepoint_probe_register` | `0xe63d8` |
| `for_each_kernel_tracepoint` | `0xe63f0` |
| `tracepoint_probe_unregister` | `0xe6470` |
| `register_tracepoint_module_notifier` | `0xe5c20` |
| `unregister_tracepoint_module_notifier` | `0xe5cb0` |

`tracepoint_probe_register` is a 24-byte wrapper that supplies priority ten
and branches into the full priority registration routine. The latter locks a
global mutex, constructs the callback/data/priority tuple on its stack, calls
the internal update routine, unlocks and returns its status. It is not a
constant-success stub.

`for_each_kernel_tracepoint` walks the kernel tracepoint pointer range, resolves
each PREL32 pointer and invokes the caller-provided callback. This provides a
positive path to built-in tracepoints even when a particular
`__tracepoint_*` object is not separately exported. The module notifiers
provide the corresponding dynamic-module inventory surface, but using them
would add more lifetime work and is not required for a fixed built-in event.

`tracepoint_probe_unregister` locks the same global state and matches the
tracepoint callback/data tuple before removing it. A future module would still
need exact headers and correct teardown ordering; the existence of this body
does not by itself prove that an arbitrary hand-written structure definition
is ABI-compatible.

Five concrete event objects relevant to the prior PM work are independently
exported:

| object | Image offset |
| --- | ---: |
| `__tracepoint_rpm_return_int` | `0xb29ef0` |
| `__tracepoint_rpm_idle` | `0xb29f50` |
| `__tracepoint_rpm_resume` | `0xb29f80` |
| `__tracepoint_rpm_suspend` | `0xb29fb0` |
| `__tracepoint_suspend_resume` | `0xb29d70` |

This agrees with the actual retained tracepoint formats and prior passive PM
captures. It does not add coverage of Samsung's proprietary private power
dispatch, arbitrary module functions, UART RX, or controller firmware.

Some useful tracepoints such as scheduler lifecycle or device-PM callback
events are not individual exports in the reconstructed table. The enumerator
could theoretically find built-in instances by name, but safely consuming
their callback argument ABI still requires the exact matching trace-event
headers/configuration. Existing textual `format` files describe event-ring
records, not necessarily the C callback prototype well enough to substitute
for those headers.

## Kprobe, kretprobe and function-ftrace boundary

The full reconstructed export-name set contains none of:

```text
register_kprobe          unregister_kprobe
register_kretprobe       unregister_kretprobe
kallsyms_lookup_name
register_ftrace_function unregister_ftrace_function
ftrace_set_filter        ftrace_set_filter_ip
```

The saved Image contains no literal kprobe/kretprobe registration names. The
target-side sample, on the same boot at uptime `89313.77`, recorded all of
these paths absent:

```text
/proc/kallsyms
/proc/config.gz
/sys/kernel/debug/tracing/kprobe_events
/sys/kernel/debug/kprobes/blacklist
/sys/kernel/debug/tracing/available_filter_functions
```

Absence of the files alone was never enough to assign a `CONFIG_*` value. The
new export audit adds the important module-link boundary: even if unlabelled
internal kprobe code existed, a normal external module has neither its
registration exports nor a supported way to resolve their addresses.

The exports `register_ftrace_export` and `unregister_ftrace_export` do exist.
They are not the standard arbitrary-function `ftrace_ops` registration/filter
surface, whose named APIs above are absent. No arbitrary function hook is
claimed from the two exporter names.

## `__symbol_get` and address discovery

`__symbol_get` is exported at Image offset `0xbe450`, and exact copied Samsung
modules have undefined relocations against it. Its body searches the kernel/
module symbol export structures by name, checks module state, takes a module
reference where needed and returns the resolved target. `__symbol_put` is
also exported.

This is a legitimate way for a module to use another **exported** optional
provider, as the installed Samsung code does. It is not a replacement for
`kallsyms_lookup_name`, and the missing `register_kprobe` export is not made
available merely because `__symbol_get` exists. No loaded third-party wrapper
exporting kprobe registration was identified in the retained corpus.

## Module loading, signature and ABI evidence

The retained Image banner is exactly:

```text
Linux version 5.4.261 (abuild@A2001DPG) (gcc version 9.2.0 (GCC))
#1 SMP PREEMPT Wed Jul 1 16:51:36 UTC 2026
```

The two exact installed AArch64 modules instead contain:

```text
vermagic=13781815, release SMP preempt mod_unload aarch64
```

Both end in `:UEP` after an encoded trailer and neither contains the standard
`~Module signature appended~` marker. The Image itself contains UEP
verification/blocking strings and `uep.version=v.0.0.1`. This is strong
evidence of a distinct Samsung file policy, but this audit does not reverse
its trust chain or assert exactly where module loading invokes it.

At Image `0xbc988`, exported `is_module_sig_enforced` is exactly:

```text
mov w0,#0
ret
```

The retained root metadata separately read
`/proc/sys/kernel/modules_disabled = 0`. These facts show that the standard
kernel signature-enforcement helper and global module-disable switch are not
the demonstrated blockers. They do not prove that an unsigned or incorrectly
UEP-signed file will be accepted, and the metadata script did not retain a
value for `/sys/module/module/parameters/sig_enforce`.

No matching build tree, generated config, exact headers, `Module.symvers`,
UEP signing key, or accepted test-module record exists in this workspace.
The host's x86-64 Linux headers are unrelated. A source-compatible 5.4 header
set would not establish Samsung structure layouts, config-dependent callback
ABIs, symbol CRC expectations, or the custom vermagic.

## What a reversible observer would require

The positive theoretical design is tracepoint-only:

1. Build an AArch64 module against the exact generated Samsung 5.4.261
   headers/configuration and matching symbol ABI.
2. During init, enumerate or bind only a source-proved tracepoint; register a
   bounded, non-blocking callback and allocate bounded output storage.
3. Treat every registration failure as init failure and leave no callback.
4. During exit/failure, unregister every exact callback and complete required
   synchronization before freeing storage or allowing unload.
5. Verify output/drop accounting and module absence after teardown.

This is architectural feasibility, not an implementation or deployment
recipe. Loading a module changes privileged kernel state and crosses a
security boundary; no load was attempted. Until exact headers/ABI and UEP
acceptance are solved offline, even a tracepoint-only observer remains HOLD.

A kprobe/kretprobe observer is a different design and is not supported by
current evidence. Reaching an arbitrary private function by guessed address,
patching the export table, scanning live memory, disabling UEP/signature
checks, or using a flash modification would exceed this audit and is not a
reversible supported observer path.

## Reproduction

Run locally only:

```sh
python3 tcon-research/kernel-instrumentation-capability-audit-20261027-reproduce.py
python3 -O tcon-research/kernel-instrumentation-capability-audit-20261027-reproduce.py
```

The checker pins the complete Image and export index, exact API/object export
offsets, relevant absent exports, five code slices, the two module hashes,
custom vermagic and UEP trailers, and the two retained metadata records.

| Image interval | bytes | SHA-256 |
| --- | ---: | --- |
| tracepoint register `0xe63d8..0xe63ef` | 24 | `cd4e36410618ae522d5bd9731c0c7dfe25577344c3f7a14f587a8df30aa89565` |
| tracepoint enumerator `0xe63f0..0xe646b` | 124 | `73bbb634a5f5d63a20686f7bbba00944b6901a50895b3e9ac5307684e32601e1` |
| unregister prefix `0xe6470..0xe64ff` | 144 | `c1ea6b13000fd45981a7f5d067b9665d8ef94f959584432982118637d3e47161` |
| `__symbol_get` `0xbe450..0xbe50f` | 192 | `743661c922eb2b7069bbafba89068a248892078a4da81bde3c2a4e7595235b85` |
| signature-enforced helper `0xbc988..0xbc98f` | 8 | `2f6110664dbd16b514a0c2c7c8326932a36e85d2f15b91e57ca76efd2c7a625a` |

## Limits

This is a static/export and retained-metadata capability audit. It does not
prove exact build headers, module ABI, symbol CRC policy, UEP acceptance,
module-load authorization, callback safety for a chosen event, output
transport, unload success, or current live addresses. It does not observe the
panel, RT condition, UART, HDMI, controller, Apps, or a failure onset. It
identifies one positive tracepoint mechanism and closes the currently
unsupported kprobe/function-hook route without claiming that instrumentation
is impossible in every modified or in-tree kernel.
