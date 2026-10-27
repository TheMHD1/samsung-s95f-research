# QD AutoDim upstream route — static audit

**Scope.** Offline audit only, performed 2026-10-26.  This note does not change
the TV, does not assert that any candidate call ran, and does not infer a time
interval from the 300-invocation counter described in the companion duty-policy
note.  Addresses below are ARM Thumb: the ELF function symbols are odd and the
instruction addresses shown are their even (`symbol & ~1`) forms.

## Inputs and method

| Input | SHA-256 | Role |
| --- | --- | --- |
| `binaries/libave.so.0.1` | `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` | AVE dimming implementation and provider table |
| `binaries/libvideoenhance.so.0` | `3ce4e4741bad4883d7f097b7939e7b1f8853a354329b17398da496bf624228c9` | public PPI client wrapper |

`qd-autodim-upstream-reproduce.py` is a hash-gated parser/disassembler.  It
resolves ELF relocation records rather than treating vtable bytes as absolute
pointers, and decodes only named function bounds (not adjacent literal pools).

## What is proved inside `libave`

The concrete endpoint is `QDDimming::SetAutoDim(int)` at `0x172a34` (symbol
`0x172a35`).  If `this+0x18` is nonzero, it copies its **raw** `r1` input to
the inner object at `this->[4] + 0x2a8`; it neither converts it to a Boolean
nor derives it from a screen, source, application, or timeout.  It returns zero
on both this normal path and its not-initialized/logging path.  Therefore a
zero return is not proof that the stored request was applied.

`ave_dimming::SetAutoDim(int)` at `0x150f78` is the native entry point.  After
its local ready check (`this+8`) and instrumentation guard, it loads the active
dimming object and makes an indirect call through `vptr + 0x124`.  Under the
Itanium C++ ABI used here, the vptr address point is `vtable-symbol + 8`:

| Object table | vtable symbol | address point | call slot | relocation-resolved target |
| --- | ---: | ---: | ---: | --- |
| `ave_dimming` facade | `0x59e934` | `0x59e93c` | `+0x134` / `0x59ea70` | `ave_dimming::SetAutoDim(int)` `0x150f79` |
| `QDDimming` | `0x59f2e0` | `0x59f2e8` | `+0x124` / `0x59f40c` | `QDDimming::SetAutoDim(int)` `0x172a35` |
| `QDDimmingMNT` | `0x5a0944` | `0x5a094c` | `+0x124` / `0x5a0a70` | `QDDimming::SetAutoDim(int)` `0x172a35` |

This establishes the native chain only when the runtime-selected active object
has one of the two QD vtables:

```
ave_api_set_auto_dim_OnOff(raw value)                 0x28a380
  -> dimming facade virtual +0x134
  -> ave_dimming::SetAutoDim(raw value)               0x150f78
  -> active-dimming-object virtual +0x124
  -> QDDimming::SetAutoDim(raw value), if QD selected 0x172a34
  -> inner +0x2a8
```

`ave_api_set_auto_dim_OnOff` passes its `r0` unchanged as `r1` at the facade
call.  `VideoEnhancerImpl::set_auto_dim_OnOff(int)` (`0x29e50c`) likewise moves
its incoming `r1` into `r0` and calls that AVE API through PLT `0x8aa58` (GOT
relocation `0x5a4200`).  `impl_set_auto_dim_OnOff(int)` (`0x2a2af8`) in turn
passes its `r0` as `r1` to that VideoEnhancer method through PLT `0x90fe0`
(GOT relocation `0x5a63d8`).  These are forwarding layers; none computes a
policy value.

The previously recovered duty path starts *after* that stored request:
`m_AutoPowerOff` and the QDMNT vsync work eventually issue the F3:0128 duty
request.  That is not evidence of a direct panel-power command or evidence that
the F3 recipient accepted it.

## Home is a distinct API, not an AutoDim caller

`ave_dimming::SetHomeUI(int)` is at `0x151710`; it calls active-object virtual
slot `vptr + 0x140`, not AutoDim's `+0x124`.  The QDDimming relocation at that
slot (`0x59f428`) resolves to `DimmingInterface::SetHomeUI(int)` at `0x1555ad`,
the base stub.  Thus this copied QD implementation does not show HomeUI being
translated into `SetAutoDim`; the two names must not be conflated.

## PPI boundary and provider slot

`libvideoenhance` exports `ppi_ve_set_auto_dim_OnOff` at `0x46f44a1c`.  It
obtains a runtime backend and tail-calls the function pointer at backend-table
offset `+0x98`, with the caller's `r0` unchanged.  The actual backend pointer,
its provider, and the dynamic load/registration history are runtime facts not
present in this capture.

The corresponding `libave` provider is
`videoenhancer_impl_set_funcs(ppi_videoenhancer_funcs*)` (`0x2a078c`).  Exact
register dataflow—not merely a nearby GOT label—shows the matching slot:
`0x2a08c6` loads literal `0x2ffc` from `0x2a153c`; with the PIC base this is
GOT `0x5a6ffc`, relocated to `impl_set_auto_dim_OnOff`; `0x2a08de` loads that
GOT value into `r1`, and `0x2a08e0` stores `r1` to provider table **`+0x98`**.
Thus the copied client and provider agree on `+0x98`, yielding the complete
PPI forwarding route when that provider table is the runtime backend:

```
ppi_ve_set_auto_dim_OnOff(raw) -> backend[+0x98]
  -> impl_set_auto_dim_OnOff(raw) -> VideoEnhancerImpl
  -> ave_api_set_auto_dim_OnOff(raw) -> native AVE chain above
```

The static provider integration is also recoverable.  In
`libvideoenhance`, `ppi_videoenhancer_get_backend_data_address` (`0x46f3e5c0`)
uses an existing static backend-data object, allocates its `0x5dc` function
table, and stores that allocation at backend-data `+4` (`0x46f3e604`);
`ppi_videoenhancer_get_backend` (`0x46f3e664`) opens
`/prd/usr/lib/libave.so`.  In `libave`, init-array entry `0x59c4c0` reaches
`videoenhancer_inject` (`0x91b75`), then
`videoenhancer_backend_data_inject` (`0x2ab168`); instructions
`0x2ab1b2..0x2ab1b6` load backend-data, load its `+4` table, and invoke the
provider table-populator.  It sets provider version `0x100` (256).  This proves the
intended static integration, but does not prove that a particular boot executed
it, that the resulting table was still non-null/unchanged, or which external
client supplied the raw value.

## Answer to the observed Full Apps / sparse-page contrast

No recovered instruction in this AutoDim route turns "Full Apps", "For You",
"Live", content density, idle duration, source, or Home state into `0` or `1`.
The one nearby Home API is separately dispatched and lands in the QD base stub.
The route therefore cannot attribute the observed contrast to AutoDim on static
evidence.  Plausible next discriminators are runtime caller/value capture and
the actual selected dimming object/backend table, alongside the independently
audited compositor/power paths.  They require a controlled live capture; none
was performed in this audit.

## Bounded conclusions and safety

* A static input value can reach the QD request field through the native AVE
  chain only if the current runtime instance is QD; the binary alone does not
  prove selection or invocation.
* The copied artifacts do not establish a public/native policy caller that
  chooses `1` or `0`.  This is a scope limit, not a claim that no such caller
  exists: clients may be absent, dynamically loaded, or use a different ABI.
* No timer period, physical panel action, recovery capability, or black-screen
  cause follows from this route.  No live TV command, firmware patch, table
  write, or persistence change was made.
