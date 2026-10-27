# Independent audit of the corrected Apps AppControl run

## Conclusion

The retained records establish that the corrected six-file helper issued one
fixed normal-UI Apps request on the reviewed TV boot and that
`AppControl.SendLaunchRequest` returned without a managed exception. The
request was `com.samsung.tv.csfs` with the sole extra-data pair
`switch_page=d/apps.tab`; neither `Operation` nor `__NO_RAISE_WINDOW` was set.
The safe handle was disposed after the call.

This qualifies the managed Apps request path, not the physical result. There
is no independent screen observation, recipient acknowledgement, focus query,
or screenshot in these records. They therefore correctly retain
`physical_picture_observed=false` and `execution_confirmed=false`. The latter
means that the requested UI transition was not independently confirmed; it
does not contradict the authenticated evidence that the helper process ran and
the send API returned.

This audit was entirely offline. It read the retained records and local pinned
build artifacts and made no TV or network call.

## Evidence set

| Evidence | SHA-256 |
|---|---|
| `ui-prepared-v2/prepare-record.json` | `0379d386e669bf0f4e3a669ffb95990cfef24ee065b74d5aa57d52eb651c85d8` |
| `ui-prepared-v2/prepared.json` | `f7880621126dc32026a72aebec5e4086d62c5af534f3d233fdd73143a5c27108` |
| `ui-apps-control-v2/action-record.json` | `7e472d791be9adf3ea048b28cc0d0080826093c3e92c33bc12a56ac90e40523f` |
| `ui-apps-control-v2/native.stdout.txt` | `3797e7b0c4400d961337ca94e73415430ce98c8d2f391439eafacd4f90320574` |
| `ui-apps-control-v2/native-outcome.json` | `b799d8bb2608c83ed41156d8b7326c64910568280c78eb02922e20973691c35d` |
| `ui-apps-control-v2/result.json` | `ddf1dd4e6b7f1a02266c2c0e14e3488e73a388fad7d496558b78ba4308917cdb` |
| `ui-cleanup-v2/cleanup-record.json` | `1daa1372df9de2aca54c190357e37aadd27bf8bbcfb238ece83a8a76aafce28f` |
| `ui-cleanup-v2/result.json` | `a9d817b8cb61fcea923f2c01b9b5d613f77c718493d87aa7818fdd06b9b007d8` |

The prepared record binds build manifest
`79815f8e9d0a00f49de31f3e80a0e73ac549c4681097ef7f0453b518d3fb58ee`,
wrapper `985b97762e1379cc062b4b222873588566ad81f8e07043c46ac1a9f3fadc2b97`,
and root adapter
`bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a`.
Those hashes match the local reviewed candidate.

## Transport audit

The preparation record has 56 calls, the Apps action has exactly one call, and
cleanup has exactly one call. For every call:

- the recorded byte count equals the echoed command length and remains below
  the 8,192-byte bound;
- the host transport did not time out and exited zero;
- the retained base64 transport body decodes exactly to the stored response;
- the response authenticates model `QN77S95FAFXZC`, UID/EUID zero,
  host-assisted persistence, and the system-file invariant;
- exactly one remote command is present, its echo equals the requested command,
  and it reports exit zero, no timeout, and empty stderr.

The single Apps command is 4,439 bytes. It first verifies the reviewed boot,
the pinned `/usr/bin/dotnet` hash, the private directory, and every staged file,
then ends with exactly one invocation:

```text
/usr/bin/dotnet /tmp/researcher-ui-tab-84c56acf553f434eaca50b55c103f004/ManagedUiTabLaunch.dll --apps
```

There is no retry, second managed invocation, upload, cleanup, For You request,
or caller-selected extra data in that action command.

## Prepared-stage replay

The private stage was
`/tmp/researcher-ui-tab-84c56acf553f434eaca50b55c103f004`. Preparation checked
it as root-owned mode 0700. The final preparation call allowed exactly six
root-owned mode-0600 regular files and checked every size and SHA-256.

As an independent content check, all base64 append payloads were decoded from
the authenticated command echoes and replayed in memory. The reconstructed
169,679 bytes exactly match both `prepared.json` and the reviewed local build:

| File | Bytes | SHA-256 |
|---|---:|---|
| `ManagedUiTabLaunch.dll` | 25,088 | `90a63e61f8925ed91897c3586fd2e972eb770ee3ba30583108977b431841c509` |
| `ManagedUiTabLaunch.deps.json` | 1,501 | `05e098fa4f00555c7518f67c63f9d4bd5bba47a4f7cb91ae42b96f632b95accc` |
| `ManagedUiTabLaunch.runtimeconfig.json` | 242 | `aeb46a15366e38511c192ccf65312442c64e8753b3c16fd2ca0b4cb34a5c59f3` |
| `Tizen.Applications.Common.dll` | 118,784 | `f9d17e5e10632d4001a5381331661104302cc95d12f61567cc61c6cb74ea737c` |
| `Tizen.dll` | 13,824 | `a4f743fd522517584641eb86afe2403ce4134e6e40768da9998242cb095ca93e` |
| `Tizen.Log.dll` | 10,240 | `a2b27f2033177328d0d609f8fab47f3c45bc20a0a30b5f29992b142b02fdf66b` |

The stage became ready on boot
`00000000-0000-4000-8000-000000000000` at uptime `113618.44` seconds.

## Native outcome

The authenticated remote stdout is byte-for-byte identical to
`native.stdout.txt`. It contains one JSON outcome plus two classified GC rows;
the JSON is semantically identical to `native-outcome.json`.

The outcome reports:

- ARM, four-byte pointers, little-endian, and ABI accepted;
- the expected boot before and after the call;
- uptime `113626.25` before and `113626.27` after, a 0.02-second interval;
- request constructed, send attempted, send returned, and handle disposed;
- no exception and exactly one target operation;
- Apps mode with application ID `com.samsung.tv.csfs` and only
  `switch_page=d/apps.tab`;
- `operation_set=false` and `no_raise_window_set=false`.

The send began 7.81 seconds after the prepared-stage uptime. The parsed
`result.json` agrees with the native outcome on the send flags, exception,
operation count, and deliberately limited physical/UI claims.

## Cleanup and remaining limits

Cleanup rechecked the same six-name inventory, directory/file ownership and
modes, sizes, and hashes before removing those six files and the private
directory. Its authenticated stdout is `PRIVATE_STAGE_ABSENT`, and the result
records `stage_absent=true` with zero target operations.

The evidence does not establish that CSFS consumed the request, selected the
Apps tab, rendered a frame, or kept the damaged panel illuminated. It also does
not qualify the separate `--for-you` destination. Those require their own
bounded retained observations; the successful Apps API return must not be
promoted into a physical-panel or fault-repair claim.
