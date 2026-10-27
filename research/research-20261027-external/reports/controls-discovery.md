# Remote-control sources and topic discovery

Reviewed 2026-10-27 UTC. These sources improve control/protocol understanding;
they do not expose the panel fault's comparison operands or an electrical
repair. The local [source inventory](../sources/controls/source-inventory.json)
records commits and reviewed-file hashes. No upstream code was installed or
executed and no TV command was sent for this review.

## Supplied OVOS skill

Repository: [JoergZ2/ovos-skill-my-samsungctl](https://github.com/JoergZ2/ovos-skill-my-samsungctl),
commit `4e1e25048de0a01f6243bbdeef7bffd95b7b6d71`.
The README identifies the developer's test model as UE55ES6760; this does not
establish S95F compatibility. Both Apache and GPL license files are present;
source reuse needs per-file license review.

The [implementation](https://github.com/JoergZ2/ovos-skill-my-samsungctl/blob/4e1e25048de0a01f6243bbdeef7bffd95b7b6d71/__init__.py#L30-L120)
defaults to legacy control on port 55000, sets timeout zero, maps voice intents
to `KEY_` strings, and opens a samsungctl connection for each command.
Exceptions are logged but do not become a structured delivery result. It
contains no kernel/controller telemetry, new panel API or reliable page-focus
observer. Its abstractions are less useful for our controlled transitions than
the already-demonstrated local keys with per-step cached-tab verification.

**Delta:** confirms that a voice-control wrapper is a control client, not a
new firmware interface. No causal gap closed. Do not adopt its unbounded
timeout or exception-only reporting for onset tests.

## Supplied samsungctl fork

Repository: [jakubpas/samsungctl](https://github.com/jakubpas/samsungctl), commit
`ebdaf6b896f69c2d87e4738f58360a510cb6404e`, MIT. The README itself describes
WebSocket dependency constraints and connection problems; model compatibility
is not proved merely by the QLED description.

The [WebSocket implementation](https://github.com/jakubpas/samsungctl/blob/ebdaf6b896f69c2d87e4738f58360a510cb6404e/samsungctl/remote_websocket.py#L18-L98)
selects ports 8001/8002, waits through informational events for connect or
unauthorized, and caches a token in the package directory. Key control sends
`ms.remote.control` with `Cmd=Click`, then sleeps 200 ms; it does not consume a
per-key response. Thus send completion is not key acceptance, page transition
or physical visibility. The installed-app request assumes the next response
is its expected data, unlike the more tolerant connection loop. Do not copy
its shared token-file strategy into the existing private per-TV access path.

The [application layer](https://github.com/jakubpas/samsungctl/blob/ebdaf6b896f69c2d87e4738f58360a510cb6404e/samsungctl/application.py#L33-L83)
uses HTTP application endpoints and a fixed app-ID dictionary. Critically,
state-query exceptions become a JSON value with `running=false` and
`visible=false`. This conflates transport failure with a successful negative
observation. Launch/stop use shell curl and mutate application state. Neither
the dictionary nor a `visible` field measures the damaged panel's output.

The [UPnP layer](https://github.com/jakubpas/samsungctl/blob/ebdaf6b896f69c2d87e4738f58360a510cb6404e/samsungctl/upnp.py#L11-L71)
mixes audio getters with setters and media playback controls. Failed volume
queries can return initialized zero; failed mute queries can return initialized
false. This is a source-level false-negative pattern, not evidence that the
same services or paths exist on this S95F.

**Delta:** protocol-error handling and unknown-state handling are concrete
review criteria. Our existing local normal-key path has already demonstrated
Apps/For You navigation while physically black, so switching libraries does
not presently improve recovery or diagnose the fault.

## Topic page and additional discovery

The owner's [Samsung-smart-TV topic](https://github.com/topics/samsung-smart-tv)
was saved with a hash and acquisition timestamp. The snapshot yielded 20
repository-shaped links. They are recorded in
[topic-discovery.json](../sources/controls/topic-discovery.json), not claimed as
20 audited implementations. The first-page candidates are dominated by apps,
remote integrations and media players rather than kernel or external TCON
research. GitHub topic membership/ranking is not a compatibility test.

[awesome-smart-tv](https://github.com/vitalets/awesome-smart-tv) is a useful
discovery index for official developer material and control libraries. It is
not a source for private QDF register semantics, a pinout, or a flashing route.
Specific S95F firmware/capture research discovered outside this topic is
assigned to the root and hardware workstreams instead of inferring that the
topic exhausts the ecosystem.

## Actions tied to the investigation

| Gap | What these sources contribute | Next action |
| --- | --- | --- |
| G01: align trigger and fault | Key-send return cannot stand in for actual UI change | Keep local keys, per-step cached page and separate physical feedback; instrument the lower fault path |
| G04: dependable observations | Several clients convert transport failure to a false state | Preserve `unknown/error` distinctly; do not use those getters unchanged in an observer |
| Control fallback | Documented WebSocket methods, app endpoints and UPnP patterns | Keep as reference; test endpoint compatibility independently before use |
| Kernel/TCON/pinout/flash | No direct contribution in the two supplied implementations | Use specialized primary sources and exact target artifacts |

An independent review also identified a limitation in our optional WebSocket
navigation wrapper: it does not reject all negative receipt categories even
though the underlying remote client reports them. The successful recovery
uses the local backend, so this does not invalidate BU/BW. Treat optional WS
transport success as unconfirmed until corrected and independently tested.
