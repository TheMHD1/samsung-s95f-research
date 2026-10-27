# Automatic Screen Optimization warning: exact installed text located

The owner's automatic warning is now text-matched in the installed native
`tv-viewer` application. The original report described a top-right Screen
Optimization notification, a 60-second response interval, and an approximately
ten-minute off/on cycle. This note establishes the text source. The countdown,
event trigger, callback action and relation to menu-dependent blackouts require
the separate executable trace; message text alone cannot establish execution.

## Acquired exact inputs

| Local file under `binaries/` | Installed source | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `tv-viewer` | `/usr/apps/org.tizen.tv-viewer/bin/tv-viewer` | 7,167,588 | `d32fbb420d26a27845cbb23ab216de23706c6aeb6376e4107849f74ec5a1883f` |
| `tv-viewer-en-US.mo` | `/usr/apps/org.tizen.tv-viewer/res/locale/en_US/LC_MESSAGES/tv-viewer.mo` | 61,738 | `8a7dbbe95e34aaa3d2e86fb11fa7079f0269b8c92b94c2537e491d48679eb66c` |
| `tv-viewer-en-GB.mo` | corresponding `en_GB/LC_MESSAGES/tv-viewer.mo` | 61,724 | `b151f1451c438c9652c819f08deed6813a2ede91aed65e1b05f5e7cc819b1b0f` |

The allowlisted copier checks source size/hash, exact decoded copy size/hash,
and a second source hash after acquisition. It now explicitly requires the
already available persistent root socket and refuses fallback root staging.
Its larger size allowance is limited to the named `tv-viewer` executable;
other allowlisted files retain the existing four-MiB limit. No copied TV code
was executed on the host or television.

## Message match

The installed US key
`TV_SID_QD_CBSEP_INFO_MSG_SCREEN_TURN_OFF_RUN_SCREEN_RESTORATION`
contains the exact warning the owner described:

> For a clearer screen, Screen Optimization will run automatically in a moment.
> The power will be turned off and on for about 10 minutes.

The GB catalog uses “Optimisation” with the same meaning and timing. The
executable includes this key at file offset `0x50af60`. The nearby
`TV_SID_QD_CBSEP_INFO_MSG_SCREEN_RESTORATION_CLEARER` message instead says the
operation will run on the next remote-control power-off. These are distinct
messages and must not be collapsed into one immediate-start policy.

The catalogs separately contain Pixel Refresh wording that describes more
than an hour, plus a parameterized refresh-duration message. These text
variants reinforce why the earlier manual Pixel Refresh button trace cannot
be used to identify the automatic ten-minute countdown by itself.

Reproduce the seven selected keys in both catalogs offline:

```sh
python3 idle-research/extract-tv-viewer-optimization-text.py
```

The [generated JSON](tv-viewer-optimization-text.json) retains the exact keys,
texts, input sizes and hashes. This is a gettext extraction, not TV assembly
execution, a live popup observation, or proof that a maintenance cycle ran.

## Discovery scope and unsuccessful leads

The new service catalog records both `/usr/apps` and `/opt/usr/apps`; neither
is assumed to alias the other. Five additional notification/reminder files
were acquired with the same identity checks. A bounded printable ASCII and
UTF-16LE keyword scan did not locate the warning there; this is not an IL
call-graph or compressed-resource exclusion.

The main-assembly scan inspected 326 direct `bin/*.dll` files using its
recorded case-insensitive sensing/restoration/optimization pattern. It found
the already known menu and Self Diagnosis resource assemblies. A separate
scan inspected 666 direct non-DLL/non-PDB/non-JSON/non-XML files; its sole
matching path was `tv-viewer`. These counts describe the recorded globs, not
every installed framework, satellite locale, compressed resource or firmware
component. Both raw records retain commands, timestamps, stdout and stderr.

The first locale listing mistakenly matched only filenames containing “en”;
it found no files because the language is in the directory name. The next
explicit `en_US`/`en_GB` inventory corrected that search and located both
catalogs. No missing-locale conclusion is retained from the earlier search.

## Actions and unresolved questions

This pass read installed directories and source bytes. It did not launch
`tv-viewer`, open a TV notification, invoke sensing, change VCONF, send power
or remote keys, modify a binary, or attempt a recovery. The executable caller
trace is recorded separately in
[tv-viewer-automatic-sensing-notification.md](tv-viewer-automatic-sensing-notification.md).
Exact popup text is identified; causal attribution to the sparse-menu blackout
and a permanent repair remain unverified.
