# Self Diagnosis resource candidate — bounded follow-up

Later October26 follow-up: the exact automatic ten-minute warning was found
in native `tv-viewer`, not these Self Diagnosis files. Its ongoing
forced/reinforced notification has an intended one-minute/60-tick expiry
that automatically requests off-sensing. See the
[resource match](tv-viewer-optimization-resource-match.md) and
[native expiry flow](tv-viewer-off-sensing-timeout-flow.md). The earlier
unidentified-popup statements below record this candidate audit's state at
12:10, not the current implementation boundary. Owner-event execution and
blackout causality remain unverified.

This follows the October26 off-sensing/UI reference scan. It closes one
discovery lead, not the automatic-popup implementation or panel-blackout cause.
Physical picture state remains unobserved. Only installed files were read;
no TV key, output setter, service restart, power change or patch was sent.

## Acquired source identity

The source directory is `/opt/usr/apps/com.samsung.SelfDiagnosis/bin`.
The allowlisted [copier](../overnight/pull-optimization-ui.py) checked byte
length, local SHA-256 and remote source SHA-256 before and after each copy.
The [acquisition manifest](../overnight/matching-optimization-ui-manifest.json)
records all four new files. The inventory response is
`../overnight/optimization-selfdiagnosis-inventory-20261026T120448Z.json`.

| File | Bytes | SHA-256 |
| --- | --- | --- |
| SelfDiagnosisTextResources.dll | 306176 | `95d76c273d796ede8dfc4bc1a28987d6bfe2a12ddbdd84a06f6c8a8a38c3a4d7` |
| SelfDiagnosis.dll | 292352 | `56ddbafd42e4d925cfca4ffbee5fc6c30e747457c2c691634251d76dc9bd71fc` |
| SelfDiagnosisData.dll | 143872 | `6467b153417c665b1d5e61e5c8100e7bbd0507deba3fecb0daedb10deb48cc5d` |
| SelfDiagnosisTextResources.xml | 144854 | `731b893998a55076e13576cb2c836c222203c816f85b6514b3d3f6df86f7e0bd` |

## Positive findings and limits

The XML contains two matching resource properties:

- `COM_SID_SELFDIAGNOSIS_CDMAR_PIXEL_REFRESH_FUNCTION`: Pixel Refresh function.
- `COM_SID_SELFDIAGNOSIS_CDMAR_SCREEN_OPTIMAZTION`: Screen optimization.

The misspelling `OPTIMAZTION` is in the installed key. Matching getter names,
keys and text also occur in `SelfDiagnosisTextResources.dll`. The resource DLL
has15 matches in the specified string scan; the XML has2 matching members.
Neither `SelfDiagnosis.dll` nor `SelfDiagnosisData.dll` has a matching run for
the exact search pattern. These are bounded string/resource results, not IL
call-graph results. Generic Device Care optimization and timeout names are
insufficient to identify a panel-maintenance countdown.

The [offline scanner](scan-selfdiagnosis-resources.py) hashes all four inputs
before extracting contiguous printable ASCII and UTF-16LE runs, and parses the
XML members. Its exact pattern and [generated JSON](selfdiagnosis-resource-scan.json)
preserve the offsets, encodings and matches. It never loads or executes the TV
assemblies. Reproduce locally:

```sh
python3 idle-research/scan-selfdiagnosis-resources.py
```

The scan does not inspect compressed resources, resolve dynamic/localized keys,
follow generic API calls or establish absence elsewhere. A separate read-only
native-client scan of the exact recorded app/library globs printed no matching
file names and no stderr
(`../overnight/optimization-native-client-scan-20261026T120708Z.json`). Its final
date command makes the shell status0 independent of grep's match status;
it is not a firmware-wide exclusion or proof of a missing maintenance client.

The owner's automatic top-right prompt with60seconds to answer and a stated
approximately ten-minute power cycle remains unidentified. The earlier
[manual Pixel Refresh trace](menu-screen-optimization.md) is a different,
proven button/mode path. No timer or protection was disabled on the strength of
these resource labels. The exact client/service that creates the automatic
prompt, and its relationship to the physical blackout, remain open questions.

## Photo correction and evidence continuity

Both screen close-ups were opened again. The local lower-edge black patch and
upward narrow dark line are visible. **No larger than the owner's thumb** is
the owner's reported scale; the photos do not provide an independent physical
measurement or exact pixel count. This correction is already integrated into
the main diagnosis and [photo map](../tcon-research/owner-photo-board-map.md).
All10 uploaded source files still match the photo manifest byte lengths and
SHA-256 values. Neither patch size nor upload time identifies the electrical
extent, current physical state or whole-screen blackout mechanism.

The prior29-entry runtime/control snapshot was also checked:27 entries still
match. The copier and its acquisition manifest changed intentionally to add
these four files. The original evidence snapshot is retained, not silently
rewritten as if it described the new acquisition.
