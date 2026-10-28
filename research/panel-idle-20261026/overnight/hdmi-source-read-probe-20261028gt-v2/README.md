GT-v2 is a minimal host-authored successor to frozen GT. No target, root, network or device calls were made by its author. The original GT and its actual refusal remain unchanged. No independent review is claimed.

The parent-owned actual GT request in `../hdmi-endpoint-trial-20261028gp/tv-source-01/root.json` completed with authenticated model/UID envelope, expected boot/build/kernel and observed SMACK User, then remote exit1 immediately after uname. Its next command was the `/bin/sh` canonical-path guard, before hash checks or either source get. The parent then performed a separate read-only component discovery. Its accepted response at `../hdmi-endpoint-trial-20261028gp/source-component-discovery/response.txt`, SHA256590e467af5cea825c49b89f7a029aa330c4a5e425368edd17f28e33ef66bc0bb, positively resolves `/bin/sh` and `/bin/bash` to `/usr/bin/bash`; loader/libc aliases resolve beneath `/usr/lib`. All six query-component byte hashes equal the original offline pins. Discovery uptime214072.77..214072.84 and the initial refusal are retained as separate actual operations; this successor has not queried source values yet.

`production-diff.patch` records the complete production delta: family schemas are now gt-v2; three expected canonical destinations use the actually observed usrmerge paths; six additional exact canonical guards cover the hash aliases and fixed query entry points. Every original path guard is retained with its observed target. Six component hashes, two get keys, parser semantics, query/transport bounds, no retry and no selection behavior are unchanged. This admits only the ten exact observed canonical pairs, not arbitrary path equivalence. On every execution, the canonical guards and all six byte hashes run before either source get. It does not bypass a file/label/model guard.

All original GT limitations in [its README](../hdmi-source-read-probe-20261028gt/README.md) apply: root-client model envelope is not a fresh hardware model getter; build is separately observed; UID/SMACK do not attest future Cynara permission; these on-disk query-component checks do not attest all transitive dependencies or loaded code. The two service keys are non-atomic caches, and `acceptedRead` does not identify primary Ugoos or prove HDMI/video/physical light. This successor still stages no target files, changes no source/settings/labels, invokes no framework methods and makes exactly one root request with two fixed gets.

Host tests pass 95 checks and 52 negative cases identically normal/-O, including the original finite parser/wrapper tests, all actual discovery canonical pairs, unchanged six hashes/keys, and predecessor parser equivalence. All26 input pins, including frozen GT and parent actual discovery/refusal, are checked. The command is 2051bytes, below8192; root/host45/75seconds and envelope65536/source12288/key4096 limits remain unchanged. No current-source fixture is represented as actual. Reproduce using `python3 -B test-host.py` and `python3 -B -O test-host.py`.

Dry parent invocation:

```bash
python3 -B ${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/hdmi-source-read-probe-20261028gt-v2/probe.py --expected-boot 00000000-0000-4000-8000-000000000000
```

The frozen manifest digest is **0ee307cf63b8176aca008772c85df44191915cd89f47748d9749a25bbecae68d**. After parent review and sole-owner scheduling, one execution with a new absolute private output directory:

```bash
python3 -B ${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/hdmi-source-read-probe-20261028gt-v2/probe.py --expected-boot 00000000-0000-4000-8000-000000000000 --execute --manifest-sha256 0ee307cf63b8176aca008772c85df44191915cd89f47748d9749a25bbecae68d --output ${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/hdmi-endpoint-trial-20261028gp/tv-source-02
```

The unique result schema is `gt-v2-source-observation-v1`; all scope flags remain as GT. Root responses/returned data are private and survive refusal; no automatic second query or cleanup is attempted. A new legitimate unrecognized vconf representation can still conservatively refuse. Inventory seals package files except itself. No OEM binary is copied into this package.
