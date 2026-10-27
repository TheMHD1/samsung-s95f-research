# SDP FRC resource translation and production-mode request gate

This phase closes two previously explicit gaps: the device-tree parent address translation, and the provider behind the SDP instance's conditional `+0x318` callback. It does not identify a blackout cause or establish successful output programming. All new target operations in this phase were finite passive reads. The physical panel was unobserved; no display-control operation, module load, callback invocation, MMIO access or recovery experiment was issued.

## Resource address now has captured parent metadata

The earlier device-tree extraction supplied `soc/sdp_frc/reg` and `reg-names` but not the parent cell widths and bus range. The new [raw metadata capture](../overnight/sdp-resource-parent-metadata-20261026/client-stdout.json) supplies them on one stable boot, uptime `63565.24..63565.30`:

| Property | Captured decoded value |
|---|---|
| Root `#address-cells`, `#size-cells` | `2`, `2` |
| `/soc/#address-cells`, `#size-cells` | `1`, `1` |
| `/soc/compatible` | `simple-bus` |
| `/soc/ranges`, four big-endian words | `0, 0, 0, 0xffffffff` |
| `/soc/sdp_frc/reg` | `0x00b90000, 0x0005f000` |
| `/soc/sdp_frc/reg-names` | `frc-reg` |
| `/soc/sdp_frc/compatible` | `samsung,sdp-frc` |

These cell properties describe direct children; they are not inherited arbitrarily through the tree. Here the bus range uses one child-address cell, two parent-address cells and one size cell. It maps child address zero to root address zero for the stated extent. This interpretation follows the [Devicetree Specification, cell widths and ranges](https://devicetree-specification.readthedocs.io/en/stable/devicetree-basics.html#address-cells-and-size-cells).

Thus the captured DT description translates the `frc-reg` resource to CPU address `0x00b90000..0x00beefff`. The independently sourced static selector `0x42b48` fits as a four-byte access and would translate to `0x00bd2b48`. The selector is prior reverse-engineering input, not a DT property. The [existing register-path report](frc-extension-and-sdp-register-path.md) establishes the static `platform_get_resource_byname(..., IORESOURCE_MEM, "frc-reg")` / `devm_ioremap_resource` path and the conditional allowed-access store.

No live `struct resource`, ioremap pointer, `devio_access` pointer, register contents, actual store or panel response was observed. Captured metadata and an ordinary static path do not substitute for those missing runtime observations.

## Decoder correction and independent review

The first decoder passed authentic input but used Python assertions and partial regular-expression matching. Independent mutation review demonstrated that unrelated inserted text and reversed clocks could be accepted, and that optimized Python removed validation. Its first [decoded.json](../overnight/sdp-resource-parent-metadata-20261026/decoded.json) remains preserved as historical output, not the reviewed result.

The corrected [decoder](sdp-resource-parent-decode.py) uses explicit exception guards, pins all six transport/intent sidecars, checks identity/root/persistence/global-state provenance and remote-output equality, consumes the full ordered frame, and checks finite ordered bounded clocks. The transport emitted forty literal slash-n framing separators; these are normalized explicitly before parsing, with raw bytes retained and each property's length/base64/hash checked. The external selector report is separately hash-pinned. New [mutation checks](sdp-resource-parent-decode-tests.py) pass normally and under `python3 -O`. Independent review cleared the corrected decoder and its new [decoded-reviewed.json](../overnight/sdp-resource-parent-metadata-20261026/decoded-reviewed.json).

| Reviewed artifact | SHA-256 |
|---|---|
| `sdp-resource-parent-decode.py` | `d7bb037cf9eeb8a542125d40488dcee155cb13b5d16e68e54918ae929c409746` |
| `sdp-resource-parent-decode-tests.py` | `fcbebc4f6c3d44547249f3612b167bea9d0a81133549e02ac6e22e503df4d2d4` |
| `decoded-reviewed.json` | `4e2ca231e44903cd48e6a04be96a40d07728b58dd26326b27001382d7c242f74` |

## A request can be suppressed with a zero return

Exact `sdp_frc.ko` SHA-256 is `05dea2eaad34a23def837fb86d2f7a4e99ef630066ad6fed18d0cf55ba37063d`. Offsets below are section-relative ARM64 ELF offsets, not live virtual addresses.

`sdp_frc_probe` in `.text.unlikely` zeroes `[instance+0x318]` at `0x134`. At `0x1e8/0x1ec`, it passes the same instance into `sdp_frc_set_env_from_boardcfg`, before `sdp_frc_resource_init` at `0x210`.

The configuration routine starts at `.text+0xc88`, preserves its incoming instance in `x19`, and conditionally resolves `tztv_sys_use_hdmi_cell_sw`. It reaches the resolver if the **low byte** of any of three identity callbacks is nonzero: callbacks at identity-object offsets `0x18`, `0x40`, and, when the first two are false, `0x48`. Tests are `tst w0,#0xff`; a full-word nonzero result with a zero low byte is not equivalent. The literal is at `.rodata.str1.8+0x580`; `__symbol_get` is called at `0xccc`, with its result stored at `[x19+0x318]` at `0xcd0`. The lookup may be skipped or fail. We have not captured this TV's resulting live function pointer.

In `sdp_frc_ex_proc`:

1. `0x2284` loads the instance into `x21`; `0x2288` loads its `+0x318` callback.
2. A null callback skips this first gate.
3. Otherwise `0x2290` presets `w25=0`, `0x2294` calls the callback, and `0x2298` branches to the return block if its full `w0` is nonzero.
4. That return block starts at `0x2344` with `mov w0,w25`, so this path **suppresses the operation and returns zero**. It does not return the callback's nonzero result.
5. If processing proceeds, a second callback invocation at `0x22b4` has its result ignored; `0x22b8` replaces `w0` with a different instance field.

This adds a concrete reason that ioctl success alone cannot prove the lower register write. It does not establish that this gate was active at a blackout.

An earlier offset-only search also found a `+0x318` store in a command-sequence object. Register-base review showed that object is separate from the SDP instance; the proposed writer relationship was withdrawn. Matching field offsets are not object identity.

## The callback provider is resolved in a newly copied module

A fixed-directory symbol-literal search scanned 67 module files and returned five matches. A string match alone did not identify the provider. Copying `sdp_sys.ko` showed that it does not contain this symbol. The next copied file, `tztv-battery.ko`, contains a defined, global, exported function:

| File | Bytes | SHA-256 |
|---|---:|---|
| `sdp_sys.ko` | 97,550 | `25c9c2eef67137465b228c1297392fa22bf8a080695f8a9c020445a48f834de6` |
| `tztv-battery.ko` | 174,902 | `dd7e9c1c68b3802e8e8fc04a9097c2cc6baaedd5960e7a25bb387499edbc2270` |

At `.text+0x8e98`, size 24, `tztv_sys_use_hdmi_cell_sw` sets `x0=0` and calls `linker_get_panel_production` through the relocation at `0x8ea4`. The getter, `.text+0x1c90`, size 40, loads a **pointer** from module `.bss+0x38` and returns the pointed-to 32-bit value when nonnull. Its null path calls `linker_get_panel_production.part.0`; with incoming `x0=0`, that helper can reload the pointer or return zero. Neither getter samples a hardware pin at call time.

The initialization path in `linker_probe` allocates an instance in `x19`, initializes its **field** `+0x38` to zero at `0x1984`, then looks up `samsung,pi_line_con0`. A negative GPIO-index result skips the sample. For an available index, `tztv_gpio_read_num` receives a pre-zeroed output slot at `sp+0x4c` at `0x19a8`; its return value is ignored by this caller. The output comparison produces `1` for exact zero and `0` otherwise, stored to `[x19+0x38]` at `0x19c0`. Therefore a reader failure that leaves the output unchanged cannot be treated as a successful physical pin measurement. The helper at `0x1898` can cache the **address** `instance+0x38` into `.bss+0x38`; these two occurrences of offset `0x38` have different meanings.

These are static initialization/cache paths, not proof of the live cached pointer's value or an exhaustive exclusion of all outside writers. We have no evidence that menu content changes this production-mode field.

## New passive cached-field observation

The provider's sysfs path was checked against its copied code: `production_mode` has the `panel_production` attribute, permission bits `0444`, a show callback at `.text+0x1528`, and no store callback in the attribute. The show routine reads the instance field `+0x38` and formats `%d`. It does not sample GPIO or call the getter above.

The [new authenticated passive capture](../overnight/hdmi-cell-production-cache-20261026/client-stdout.json) verifies module binding `/sys/module/tztv_battery`, DT compatible `samsung,tztv-linker`, and provider file hash, then reads:

`/sys/devices/platform/tztv_linker/production_mode/panel_production` → **`0`**.

Boot remained `00000000-0000-4000-8000-000000000000`; uptime was `64535.87..64535.89`, remote exit zero, no timeout, both transport/remote stderr empty. The physical panel was unobserved. The embedded command, intent, return result and raw response are retained together.

This is consistent with the ordinary initialized callback returning zero and allowing the request past this gate. It lowers the priority of this particular gate as a content-dependent explanation. It does **not** directly observe the actual SDP `+0x318` pointer, the module's cached pointer, a callback invocation, an incident transition, or the final output store. It cannot retroactively rule out a different earlier state.

## Acquisition audit and reproducibility

Every copied chunk is retained with original command intent, client response, stderr and return result. Independent review reconstructed both files, verified exact remote path/skip index, root identity, stable boot, before/after full-file hashes, bounds, chunk lengths and saved-module equality. The first `sdp_sys` chunk completed on the TV but failed the local parser because its separators were literal slash-n. That raw result was preserved and parsed offline; only missing chunks 1 and 2 were subsequently read. There was no remote retry of chunk zero.

- [Discovery](../overnight/sdp-hdmi-gate-provider-discovery-20261026/client-stdout.json) and [bounded symbol search](../overnight/sdp-hdmi-gate-symbol-search-20261026/client-stdout.json).
- [SDP sys copy manifest](../overnight/sdp-sys-provider-copy-20261026-followup/manifest.json), SHA-256 `64f94acba6eab9ebbb762cb12fce3651b912435dd5df3f2dd830e9f8eb486823`.
- [Provider copy manifest](../overnight/hdmi-cell-provider-copy-20261026/manifest.json), SHA-256 `ecad5a538afd5942e0e81b652c0e1afdc6f61322878a88fc89baf11c96826f50`.
- [Static gate reproducer](sdp-hdmi-cell-gate-reproduce.py), SHA-256 `8c97cb7cfed4b0e8694725e7017625b363b772f132ad3aaae32ccd699de28c67`, and [complete saved excerpts including the GPIO reader](sdp-hdmi-cell-gate-with-gpio.disasm), SHA-256 `d098bde67bed28430d0172a697515bb8439f0ee0b58852bd231b7fac8cb7d319`. The earlier [excerpts without the GPIO reader](sdp-hdmi-cell-gate.disasm), SHA-256 `8b3a15b072a20e16e67e78c88dc2e83c7793a9a552ca61a9fea6784bca5b7ddf`, remain retained.

The manifests' `loaded_or_called:false` describes actions of the copy operation only. It does not assert that these modules were absent from the running TV. The first `pull-sdp-sys-provider.py` is historical acquisition-only code with assertion checks and a live default; do not reuse it. The completion helper defaults to checking retained chunk zero offline, and the later provider helper requires `--run`.

Offline reproduction:

```sh
python3 sdp-resource-parent-decode.py
python3 -O sdp-resource-parent-decode.py
python3 sdp-resource-parent-decode-tests.py
PYTHONPATH=/tmp/tcon-capstone python3 sdp-hdmi-cell-gate-reproduce.py
```

Commands above run in this report's directory and make no TV request. Capstone/pyelftools decode exact captured ARM64 files; instruction landmarks and relocations support manual flow review, not execution emulation.

The remaining decisive gap is still incident-aligned output/fault evidence. The reviewed pre-roll capture design is being implemented and independently checked separately; no failed historical trace is reclassified by this phase.
