# Exact `libhdmi-control` CID boundary

The copied live-mapped library is `overnight/serdes-hdmi-control-copy-20261026/libhdmi-control.so.0.1`, 415,124 bytes, SHA-256 `067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410`.

It does not contain either private V4L2 control literal (`0x00a009be` or `0x00a009bf`). This is therefore not, by raw literal evidence, the direct userspace producer of the two controls recovered in the kernel switch module.

It does expose a separate HDMI PPI layer. In particular, Thumb entry points `ppi_hdmi_input_control_set_background` at ELF virtual address `0x47e604e1`, `...set_foreground` at `0x47e60595`, and `...set_source` at `0x47e60701` all obtain backend data through `ppi_hdmi_input_control_get_backend_data@plt`, reject null backend/table/callback fields, then tail-branch to callback-table offsets `+0x48`, `+0x44`, and `+0x3c` respectively. The actual callback table is runtime data; this copied library alone does not bind those callbacks to V4L2, the private CIDs, or a source/UI event.

The library contains power callback messages (`PowerOff Callback is called`, `Wakeup Callback is called`) and a `g_is_suspend`-related message, but string presence is not invocation evidence. Its exported RPC surface includes input source and DPMS-related PPI methods; that names an integration boundary, not a private-kernel-control producer.

No TV call, RPC, callback invocation, or source control was made. The next static edge would require the exact backend implementation or a separately captured runtime callback-table binding.
