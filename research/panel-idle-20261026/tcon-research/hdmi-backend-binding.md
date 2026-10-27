# HDMI input backend loader and callback-table boundary

Offline source: `overnight/serdes-hdmi-control-copy-20261026/libhdmi-control.so.0.1`, 415,124 bytes, SHA-256 `067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410`.

`ppi_hdmi_input_control_get_backend_data` is a 12-byte Thumb function at ELF virtual address `0x47e5f815`; it returns the address of library-owned backend-data storage. `ppi_hdmi_input_control_get_backend_data_address` is a 160-byte Thumb function at `0x47e5f821` (aligned code `0x47e5f820`).  On its non-null caller-output path it calls the getter at `0x47e5f850`, requests `136` bytes from `malloc` at `0x47e5f858`, stores that allocation at returned-storage `+4` at `0x47e5f860`, zeroes it through `memset` at `0x47e5f862`, and publishes the storage address through the caller pointer at `0x47e5f868`. This is a local allocation/publication path, not proof that a concrete implementation callback table has been populated.

`ppi_hdmi_input_control_get_backend` at `0x47e5f8c1` contains a loader path and the exact implementation path literal `/prd/usr/lib/libhdmi-input-control-impl-sec.so`. Its `ldr.w r8,[pc,#0xd8]` / `add r8,pc` at `0x47e5f8ec..0x47e5f8f6` computes that literal, `mov r0,r8` at `0x47e5f90c` supplies it to the call, and `blx 0x47e331b0` at `0x47e5f910` enters the ARM `dlopen` veneer. The veneer computes and loads GOT slot `0x47e82aa0`; its unique `.rel.plt` relocation names `dlopen`. This is an instruction/GOT/relocation proof, not a PLT-ordinal assumption. Both formerly missing implementation files have subsequently been copied and statically audited: the input implementation is retained at `overnight/serdes-hdmi-input-impl-copy-20261026/libhdmi-input-control-impl-sec.so.0.1` (SHA-256 `5f822a6f297e1d24a65ad8dd4363a1dcf43b7d15f405fa7799ddf20f01410126`), and the control implementation at `overnight/serdes-hdmi-control-impl-copy-20261026/libhdmi-control-impl-sec.so.0.1` (SHA-256 `5eaef7e92eac9468bf41073ccece56a64a70339c3056c3ca2b62391171f4d2a1`). See [hdmi-control-dpms-chain.md](hdmi-control-dpms-chain.md) and [hdmi-dpms-suspend-policy.md](hdmi-dpms-suspend-policy.md) for bounded downstream results.

The source-facing PPI wrappers are ordinary gated table dispatchers:

| wrapper | ELF Thumb entry | required callback table slot | dispatch |
|---|---:|---:|---|
| `ppi_hdmi_input_control_set_source` | `0x47e60701` | `+0x3c` | tail `bx r3` at `0x47e6073c` |
| `...set_foreground` | `0x47e60595` | `+0x44` | tail `bx r3` at `0x47e605cc` |
| `...set_background` | `0x47e604e1` | `+0x48` | tail `bx r3` at `0x47e60518` |

Each checks backend data, the `+4` table pointer, and then that particular callback slot before dispatch. Failure takes a logging/error path rather than a callback. The loader and copied implementations establish static code availability, but do not establish a successful live `dlopen`, a live table binding, or a call through any source-facing slot. Accordingly this establishes a source-facing callback boundary only—not a CID producer, a source/UI trigger, actual power behavior, or a black-screen cause.

[The verifier](hdmi-backend-binding-reproduce.py) pins the exact ELF and symbol identities, allocation/publication and loader-to-`dlopen` instruction/GOT/relocation path, loader literals, full Thumb decode coverage of the bounded bodies, and precise callback/gate landmarks. The original [v1 saved disassembly](hdmi-backend-binding.disasm) is preserved.  The verifier now exclusively writes and equality-checks [v2 saved disassembly](hdmi-backend-binding-v2.disasm), adding the previously omitted allocation/publication and ARM `dlopen` veneer coverage. No target call, library load, network request, or control operation was performed.
