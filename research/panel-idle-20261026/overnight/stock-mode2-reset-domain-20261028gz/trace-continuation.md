# Stock-power branch instrumentation: capability boundary

The retained **actual** `GP/kernel-trace-capabilities/response.txt` reports only `nop` in `available_tracers`, no `available_filter_functions`, global tracer`nop` and global tracing disabled. A function/function_graph proposal is therefore not supported on this device. This is a new positive runtime limit, not a statement about this host's tracing support. No tracer or probe is installed by GZ.

The parent's second retained metadata request, `GP/kernel-probe-capabilities/root.json`, positively prints `ABSENT` for all four fixed interfaces: `kprobe_events`, `dynamic_events`, `events/kprobes` and `kprobe_profile`. It then fails opening `/proc/kallsyms` (remote exit2, transport exit1), before its terminal marker. The original request remains refused/partial; the completed path-absence observations are retained without promoting the whole request to success. No probe registration, tracing write or controller operation occurred in that request. This rules out implementing the proposed dynamic probe through those interfaces on the observed system. No kprobe prototype is implemented here.

DH's existing private trace instance is a useful lifecycle/container precedent: it uses a unique instance,128 KiB buffer, mono trace clock, private spool, finite90-second disable watchdog, per-CPU overrun statistics and explicit instance cleanup without modifying global tracer/tracing_on. It records fixed GPIO/IRQ/power trace events already emitted by stock operations. It does not capture the actual QDF branch, ERR sampled output or the OCL reset argument/result. Do not solve that gap by actively requesting GPIO values or reusing its historical evidence as a branch trace.

The following source-bound candidate is retained to describe exactly what the unavailable instrumentation would have measured, not to suggest a bypass or a retry through a different guessed interface. If a future independently established kernel environment exposes a supported probe interface, it would additionally require actual current module text bases/symbol ownership and architecture-specific fetch syntax before implementation. A matching retained module file does not cryptographically attest loaded instruction bytes. The current failed symbol lookup did not reach module-section discovery, so it establishes neither availability nor absence of those separate section files.

Do not dump an unrestricted symbol table or tracing buffer into a public report. The evidence can retain fixed matched names, private runtime addresses and hash/framing records privately.

The unimplemented conditional candidate set contains seven fixed events; event definitions are proposed data, not command strings or an installation API:

| Event | Retained source binding | Value sought |
|---|---|---|
|power entry|`qdf_tcon:m_set_power_control`, `.text+0x11848`|incoming mode0/1|
|power return|same function return probe|signed callback aggregate|
|ERR decision after callback|same function+`0xac`=`0x118f4`|`w1` sampled ERR and `w0` callback result; this site is reached only when that callback exists|
|normal-tail entry|same function+`0xb0`=`0x118f8`|positive branch witness before normal-tail work|
|ERR early-tail entry|same function+`0x14c`=`0x11994`|positive skipped-recovery witness|
|OCL reset entry|`sdp_ocl_jp:sdp_ocl_reset_tcon_power`, `.text+0x2b38`|byte argument0/1|
|OCL reset return|same function return probe|signed sender result|

The offsets are four-byte aligned AArch64 instruction boundaries inside the source-pinned functions. The actual kernel's probe syntax/architecture register names and return-fetch support remain to be observed/qualified; these are **not** preapproved `%register` expressions. Runtime addresses must come from positively bound module sections/symbols, not these unrelocated ELF offsets alone. Entries/returns need ordering/thread identity; return-probe misses/overruns make absence inconclusive.

A future implementation can inherit DH's unique private-instance, bounded ring, mono clock, watchdog, readback/statistics and cleanup shape, while creating/removing only its own uniquely named probe definitions. Dynamic event definitions are global tracefs objects even when enabled only in a private instance; it must preserve all preexisting definitions and global tracer/settings. Requiring globally empty `kprobe_events` or clearing it would be unjustified. Atomicity against other tracers and interruption cleanup need explicit handling. An expiry that stops recording does not prove immediate callback/probe removal or bound uninterruptible kernel work.

The seven-event set distinguishes branch/callback execution and sampled ERR without additional controller/GPIO requests. It does not establish delivery or success of the normal tail's many I2C commands, which can be gated lower down; exact transport-skip instrumentation can be a subsequent narrowly source-qualified extension if the first trace exposes that need. It does not identify the OCL mailbox receiver, a full controller reset, shared-root clearing, instruction reload or optical recovery. Do not invoke a reset merely to qualify a tracer in this source-only task.

The currently usable narrow route is the existing private static GPIO/IRQ/power-event container together with already emitted normal QDF/OCL printk branch markers. It can preserve sender-side chronological evidence without extra GPIO requests or modifying global tracing. It still cannot directly capture the selected controller instruction PC or observe a source branch whose event/log is absent. A firmware stock-event-ring observation or a separately source-qualified SRAM checkpoint remains a distinct controller-domain instrument; neither should be represented as a substitute kernel kprobe or a proof that the emergency loop executed. GZ does not add a second controller logger or overlap the parent's HA work.
