GT is a fixed, dry-default S95F cached current-source probe. It uses the existing pinned root adapter, stages no target files, performs exactly one root request containing two fixed `get` operations, and contains no source selection, UI key, framework deployment, AVOC heap access, USB/controller call, setting write or automatic retry. This package was built and tested entirely on the host. It has not been independently reviewed or executed on the TV.

The route is positively retained: `../optimization-vconf-cli-discovery-20261026.json` reports `/usr/bin/vconftool` on model QN77S95FAFXZC. The accepted platform tree from DB supplies its exact 5,322-byte script. Its `get_key` branch calls `/usr/bin/buxton2ctl get memory <key>` for these fixed memory keys. It does not call libvconf directly. Both CLI argument lists contain only `get` and the literal keys:

```text
/usr/bin/vconftool get memory/system/source_type
/usr/bin/vconftool get memory/eden/source/current_source
```

The first key and 13..16→HDMI1..4 candidate mapping come from the retained source-control implementation; the second key, JSON source_type and uuid parsing are additionally positive in exact S95F CoBA.Core CurrentSourceMonitor.CheckCurrentSource0600046b/IL0087,00c8,00ed. GS preserves that exact assembly/source trace. No generic QN90 CLI or model-guard bypass is used.

The fixed 1,663-byte command checks expected boot, observed uptime brackets (maximum10seconds), expected build line, kernel5.4.261, real/effective UID0, and records a bounded SMACK label. It verifies on-disk SHA256 for vconftool, buxton2ctl, libbuxton2.so.1.1, bash, loader and libc, plus the expected shell/loader/libc/Buxton symlink resolutions. These exact files are pinned from the accepted retained platform tree. It clears loader/shell environment overrides for subsequent children and uses fixed PATH/LC_ALL. This is a bounded query-component binding, not complete transitive-library, loaded-byte, daemon, root-shell-startup or race-free file attestation. It does not change labels or privileges. Success proves that the two get operations returned through the observed context; it does not attest Cynara platform privilege for a future SourceList operation.

The MODEL constant is an expected admission value. The unchanged root adapter validates its model/authentication/UID envelope, and GT independently rechecks the retained completed envelope against the exact command/result. This is not a newly queried hardware model: `freshModelGetterPerformed` remains false. The build line is queried from /etc/tizen-release. No firmware-file authenticity stronger than DB's retained extraction is claimed; a mismatch refuses before source gets.

Each get is piped through head -c4097 under pipefail. The strict parser permits at most4,096bytes per single canonical vconf row and12,288bytes overall. Truncation, error output, wrong keys/types/order/frames, hash/build/boot/UID disagreement, reversed/long uptime windows and trailing data refuse. Current-source JSON must be a flat object of2..16 unique string-valued fields with source_type and uuid; duplicate keys, nonfinite/nested values and control characters refuse. This deliberately conservative shape may reject an unobserved legitimate service representation; such data is retained without automatic follow-up. The two keys are non-atomic and may contain stale or conflicting service state. The numeric storage bound0..65535 is a parser admission bound, not a sourced full semantic domain.

An accepted result has schema `gt-source-observation-v1`, expectedModel, rootEnvelopeModel, modelBinding, boot/uptime, observedRootSmackLabel, cachedSourceType, optional cachedPortCandidate and cachedCurrentSource. `acceptedRead` only accepts a bounded completed observation. Flags explicitly leave sourceListQueried, primaryUgoosIdentified, currentSourceKeysAtomic, loadedBytesAttested, transitiveRuntimeAttested, sourceSelectionPerformed and physicalPictureObserved false. Even cached type15 plus a plausible uuid does not identify primary Ugoos, JBL topology, active video/HDCP or OLED emission. A separate reviewed source-list probe/selector must establish its own fresh identity/library/privilege bindings.

Parent invocation uses Python -B to avoid bytecode writes outside the package. Dry mode performs no root-client import or subprocess target call:

```bash
python3 -B ${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/hdmi-source-read-probe-20261028gt/probe.py --expected-boot 00000000-0000-4000-8000-000000000000
```

For that boot and frozen files, the manifest SHA256 is **1f945229d991031a63aecff2319c851fd0aa4165b9002db4e236552e11ca4a9e**. After review and sole-owner root scheduling, the parent can invoke once with a new absolute private output path:

```bash
python3 -B ${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/hdmi-source-read-probe-20261028gt/probe.py --expected-boot 00000000-0000-4000-8000-000000000000 --execute --manifest-sha256 1f945229d991031a63aecff2319c851fd0aa4165b9002db4e236552e11ca4a9e --output ${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/hdmi-source-read-probe-20261028gt/capture-01
```

The root adapter remains SHA256 bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a with45second remote/75second host,8,192-byte command and65,536-byte envelope caps. Output must not already exist and may not traverse symlink ancestors. It is created0700; artifacts are retained privately with terminal root/response files0600. Intent precedes submission. Root raw data and returned text survive semantic refusal; result.json is only committed after envelope and parser checks. Ambiguous/failed requests retain refusal.json and root.json, and never trigger a second root request or cleanup request. There are no remote staged files to clean. The parent must coordinate all root operations; this adapter does not introduce a cross-process scheduler.

Reproduce with `python3 -B test-host.py` and `python3 -B -O test-host.py`. The identical host qualifications cover65 positive/source checks and52 finite negative cases, including quoting/injection rejection, fixed get/delegate/caps, malformed/duplicate/truncated/type/JSON/envelope refusals, exact dry manifest, wrong-manifest refusal before root import, and mocked one-request success/semantic refusal/transport ambiguity with raw preservation. Fixtures are explicitly synthetic; no current-source capture is relabeled actual. All18 input pins are checked. `inventory.json` seals package files except itself; no OEM binaries are copied here and no public export is performed.
