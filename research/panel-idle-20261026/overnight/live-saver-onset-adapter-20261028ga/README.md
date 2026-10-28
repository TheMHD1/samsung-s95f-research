# GA cached Live+saver recorder adapter

GA implements FX option A as a wrapper-only, host-qualified derivative. It removes the complete ordinary VOLUP wake workflow. After unchanged staging, exclusive self-test and fresh identity/census checks, it performs only bounded cached queries requiring exactly one canonical Live row, saver window presence and CSFS presence. The unchanged FN native then attempts its own strict baseline/arm/first-clean admission before its sole native Left workflow. There are **zero wrapper UI operations and zero wrapper key children**. No FU preparation, Up, navigation, automatic fallback or retry is added.

GA does not create the required initial condition. A clean native pre-arm state under cached Live+saver may be unavailable after ordinary Apps recovery or after entering Live. The separately proposed Live+saver MODE2 prerequisite remains unimplemented and unqualified here. There is no stock reinitialization, recovery, saver launcher, policy change or target operation in this workstream. GA must not be run merely because a saver window is present after a fault.

## Exact unchanged backend

The three FN payload files, host checkpoint, strict native parser and native/key/controller sources are consumed in place from `../combined-event-successor-20261028fn`, with their exact hashes checked. There is no native build, local DLL/parser copy or native configuration change. Native schema, packets, fixed read map, arm `01 00` and restore `00 00` at the sole logger halfword, pending-IN/payload completion, binding, C8/scan guards, 56 rows, 58-byte layout, 25 ms period, 2-second nominal observation, 40-second cooperative budget, 26-second cleanup reserve and 7-second key join reserve remain FN. Root45s/host75s, command8192/response65536, receipt24576 and two15372-byte ring sidecars remain unchanged.

The wrapper/readiness/manifest family is GA. The remote stage still has FN's native-required `/tmp/researcher-fn-<32hex>` prefix, with a fresh UUID for each single attempt; changing that prefix would change the native stage contract. Accepted cleanup is the same exact11-file guarded cleanup. A native refusal is saved as its original primary outcome before any complete-ring check, followed by no root request, sidecar fetch, cleanup, recovery or retry. Initial known fault therefore cannot produce an arm or Left. A later semantic/clock/transport refusal may retain ownership or the remote stage, exactly as FN documents; GA adds no guessed restoration.

## Cached-only admission and time meaning

`cached-check.py` retains FN's exact boot/uptime/getter command bytes. Its local decoder requires the unique canonical `d/ug.tab@Live` row. Apps, ForYou, duplicate/missing/noncanonical tabs and malformed responses refuse immediately. A valid Live snapshot with missing saver or CSFS may settle through at most ten queries, 250 ms between unsuccessful queries and a ten-second cooperative host budget. No key is sent to manufacture a qualifying snapshot. Every submitted command and available bounded response is retained, including a response returned before a subsequent host-clock failure.

The first Live+saver+CSFS query ends settling. The host monotonic interval from its returned-query timestamp to native root submission must be between zero and one second, inclusive. A stale, future, malformed or failed clock refuses before submission. The unchanged native root command performs its own immediate cached identity guard. These bounds are not root latency or continuous saver-state guarantees. CSFS/saver listing presence does not prove compositor focus, physical pixels or key consumption. The intended native action is **saver wake from cached Live**; it is not a claimed Live-header→ForYou trajectory. Native key overlap, later UI and optical observation remain separate.

## Offline qualification and CLI

Run `sh build-host.sh` for the finite source-equivalence and mocked tests in normal and optimized Python. It uses HOME-backed private scratch, never imports the real root adapter in tests, never builds native code and never contacts a TV or network. `production-delta.json` reconstructs every derivative wrapper edit from frozen FN; source checks separately prove the unchanged native/parser/key/payloads and command sequence with only FN's wrapper wake removed. Fixtures are read from existing frozen retained sources, not copied into this directory.

All CLIs are dry by default. Print and independently review the exact GA manifest:

```sh
python3 -B run-once.py
python3 -B run-once.py --print-manifest
```

A future centrally coordinated readiness decision uses the exact supplied current identity, explicit known-phase/closed-world lineage note and evidence. `prepare-readiness.py` locally validates the manifest and complete candidate identity before any root import. Its dry invocation performs no metadata query; only explicit `--execute` permits one ordinary cached identity/census request:

```sh
python3 -B prepare-readiness.py --wrapper ga --wrapper-sha256 <GA-wrapper-sha> \
  --manifest-sha256 <GA-manifest-sha> --identity <absolute-current-identity.json> \
  --phase-note <absolute-explicit-phase-note> --evidence <absolute-evidence> \
  --output <fresh-absolute-readiness-dir>
```

Only after the separate Live+saver clean premise and readiness/review are qualified could the parent add `--execute` above and submit the wrapper once:

```sh
python3 -B run-once.py --execute --manifest-sha256 <GA-manifest-sha> \
  --readiness <absolute-readiness.json> --readiness-sha256 <decision-sha> \
  --output <fresh-absolute-capture-dir>
```

No such operation was performed here. `qualification.json`, the generated manifest and source inventory seal the actual local test counts and pins. This adapter proves neither current readiness nor queue state, physical light, executing PC/FP, the fault cause or a permanent fix. FX's separate Live+saver MODE2 proposal is not implemented by any GA CLI.
