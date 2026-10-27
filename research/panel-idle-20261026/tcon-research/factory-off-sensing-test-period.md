# Factory “Offsensing TEST Period” — bounded static audit

This is an offline audit of copied files. It makes no FactoryService call,
does not change the setting, and does not send a TCON, sensing, or power
command.

## Identity and current observed state

The factory index maps QD-option child item `200802` to UID `20590`
(`0x506e`). `FactoryIndexFile_Part1.dat` contains the associated tuple at
file offset `0x8bc0`: `(20590, 0, 6, 0, 5, 2, 1, 6240)`. In
`Factory_Part1.dat`, UID material is at `0x691dc`; the adjacent label is
`Offsensing TEST Period` (`0x691e8`) and storage key is
`db/factory/FC_STORE_LEVEL_EER_B/OFFSENSING_TEST_PERIOD` (`0x69238`).

The prior read-only FactoryService capture reports child `200802`, index 19,
numeric/type fields `5,5`, byte `1`, value string `"0"`, and that same
label. A newer same-boot baseline confirms the service returned success and
value `0`; `BurnInProtectionInProgress` was `0`. That is an observed service
value, **not proof that a persisted vconf/Buxton record exists**: its
`vconftool get` lookup for the named key failed with “No such file.” Thus `0`
may be a factory default/fallback/in-memory value. A write could create or
persist a record, so writing `0` later would not necessarily restore the prior
storage state.

At13:57:47 the copied index/part sources were independently rechecked against
the live `/factory_peq/factory-data/` files: byte lengths and SHA-256 values
match exactly. The raw identity response is
`overnight/optimization-factory-data-identity-20261026T135746Z.json`.

## Exact device-side predicate

Copied `binaries/deviced` SHA-256
`2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2` is
ELF32 ARM. `OledDevice::OffSensingDisabledInFactoryMenu()` begins at ARM
`0x7ad00` (340 bytes):

```text
0x7ad04  r0 = 0x506e
0x7ad34  factory_get_data(0x506e, &value)
0x7ad38  require return == 1
0x7adb0  value is converted to (value == 6)
```

Therefore the predicate returns true **only** when the factory read succeeds
and the returned value is exactly `6`; a failed read returns false, as does
every successfully read integer other than 6. This establishes a software
disable sentinel, not a documented interpretation of the other values as test
periods. In particular, the label does not prove that 0–5 represent durations,
that 6 is a supported user setting, or that 6 is safe for this hardware.

## Recovered use boundary

`off_sensing_is_disabled_in_factory_menu` at `0x769cc` is a small global
wrapper. It selects the legacy `OffSensing` object and dispatches its virtual
`isDisabledInFactoryMenu` method; that ultimately reaches the `OledDevice`
predicate above. The bounded ARM mapping-symbol scan found one direct caller
of the global wrapper: `qd_get_state` at `0x71688`. No direct branch to
`0x7ad00` exists because the object path is virtual.

The recovered legacy and Y23 `startByUser` bodies (`0x79368` and `0x80374`)
perform their own state/power checks and call their respective `start` methods;
their decoded bodies contain no direct call to this wrapper or predicate.
Likewise, the recovered start bodies (`0x774e0` legacy, `0x7eee0` Y23) do not
directly call it. This **does not prove** manual Start Now is unaffected: an
unrecovered virtual or higher-level policy path could still consult it. It
does prove there is no direct branch in these bounded bodies to the known
factory predicate.

The existing power-suspend handlers are separate, structured paths. This audit
does not yet establish a guard edge from the `value == 6` predicate to either
automatic power-suspend sensing implementation. Consequently it is inaccurate
to claim value 6 disables all automatic sensing, all panel power actions, or
all user starts.

## No demonstrated immediate TCON write

The predicate itself only calls `factory_get_data`, compares, logs, and returns
a Boolean. It has no relocation or direct call to
`ppi_displaypanel_set_tcon_power`, `ppi_displaypanel_set_offsensing`, or a QD
factory/TCON setter.

The FactoryService implementation **is** present as copied `binaries/TIFSDaemon`
SHA-256 `d2ebc1d11be46b4a189ec87666b68b73ae58d6f5a3c10da901c80e1125620c11`.
Its generic `FCControl::SetDecimalValue(int key, int value)` at Thumb
`0x1077d8` resolves the service key to a `FacItemNode_s`, then calls
`TransmitAItemToChip(node, value, &status)` at `0x107838`. Only if that call
returns0 and its status byte is0 (`0x10783c..0x10784e`) does the normal path
reach the PLT call for
`FCStorageBaseCommon::SetFactoryUID(unsigned,value,-40)` at `0x10789a`; that
relocation is the factory-storage symbol at GOT `0x165ad0`. Thus the setter is
not a documented transient-only control: it has a chip-transmit stage followed
by a factory UID storage update.

For item `200802`, the factory index supplies UID `0x506e` in the node passed
to that generic path. `TransmitAItemToChip` is a broad item-type dispatcher
(its node type is read at `+0x44`), not a UID-specific off-sensing routine.
Every successfully resolved decimal item enters the generic transmit stage;
only the successful transmit/status path attempts the storage update. The
saved code does **not** recover a final,
UID-`0x506e`-specific panel callback or prove which receiver consumes the
transmit. Therefore an immediate TCON command for this particular item remains
unproven, while persistence risk is directly evidenced.

The known static UID reader is the `deviced` predicate described above. A
mapping-symbol-aware scan of its executable ARM code found no other direct
branch to that predicate; `TIFSDaemon` carries the UID as factory-item data and
uses the generic node path instead of materializing `0x506e` in its setter.
This inventory is bounded to copied executable code and does not exclude
unacquired processes, data-driven callbacks, or future firmware.

The service baseline's absent vconf key matters here: setting `200802` to 6
could create/persist storage that the original fallback value 0 did not have.
Writing 0 afterward may restore the displayed number without restoring the
original no-record state.

## Decision status

Value 6 is a strong lead for a **specific device-daemon factory-disable
predicate**, but it is not yet a validated repair. Before any authorized
change, the missing evidence is: the UID-0x506e-specific transmit receiver
and apply effect, complete automatic/explicit-request guard coverage, and a bounded
reversible observation plan. No setting change is recommended or performed by
this report.

## Reproduction

Run offline from the investigation root:

```sh
python3 tcon-research/factory-off-sensing-test-period-reproduce.py
```

It hash-checks `deviced`, checks the UID/read/result/value instructions, scans
all `$a` mapped ARM intervals for direct predicate-wrapper calls, and does not
contact the TV.

The updated verifier also hashes the two factory data sources and TIFSDaemon,
checks the exact index tuple/UID/label/storage key, and asserts the generic
transmit return/Boolean-status branch and storage relocation. It does not
resolve a UID-specific lower apply callback or prove all-route disable behavior.
