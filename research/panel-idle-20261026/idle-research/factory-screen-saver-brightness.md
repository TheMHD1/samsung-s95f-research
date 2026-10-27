# Factory service: Screen Saver Brightness (offline analysis)

## Exact live item identity (read-only traversal)

The live `org.tizen.tv.factory-service` object exposed the following tree:

```
root (-1)
  Control (2)
    QD option (802)
      Screen Saver Brightness (60802) = "7"
```

`GetChildItem(802, 5)` returned factory key `60802`, type fields `5/5`, value
string `"7"`, and label `"Screen Saver Brightness"`.  This is the first
confirmed mapping of the service-menu control to an external factory-service
key on this TV.  It also establishes a read-only backup value of **7**.

## Setter semantics

The service methods expose only two arguments for either candidate setter:

```
SetDecimalValue(int key, int value)
SetParameter(int key, int value)
```

There is no `save_type`, `volatile`, transaction, or no-save parameter in the
introspection or the corresponding factory-interface client ABI.

`factory_set_decimal_value` in `libfactory-interface-ATSC.so` is only an
external client proxy: it passes `(key, value)` to
`factory_proxy_call_set_decimal_value_sync`.  It does not call the imported
`ppi_set_data_volatile` itself.

The D-Bus service handler `on_set_decimal_value` calls the control object's
decimal setter and converts a **zero** internal return into D-Bus return
`1`; a non-zero internal return becomes D-Bus return `0`.  Thus a D-Bus `1`
means the daemon accepted the request, not that the setting was transient or
that its physical display effect was verified.

The matching live `TIFSDaemon` implementation makes the risk concrete.
`FCControl::SetDecimalValue(int,int)`:

1. looks up the item and transmits it to the panel/chip;
2. on the normal successful path calls
   `FCStorageBaseCommon::SetFactoryUID(item_uid, value, -40)`.

`SetFactoryUID` is a factory-storage operation, not a documented transient
display lease.  The same daemon includes persistent factory/NVRAM machinery;
the interface library also imports `ppi_factory_set_data`, and its strings
refer to FactoryIndex/Factory_Part data stores.  Separately, the firmware has
an internal `ppi_set_data_volatile`/`t_SetDataVolatile` facility, but neither
the D-Bus service contract nor the two public setter methods select it.

Therefore `SetDecimalValue(60802, 0)` and `SetParameter(60802, 0)` must be
treated as **potentially persistent factory writes**.  Neither is a justified
RAM-only workaround.  A later value of 7 can restore the observed value, but
cannot make a power loss or interrupted write reversibly safe.

No min/max is carried in the eight fields returned by `GetItem`: for this
leaf they are `(60802, 0, 5, 5, 5, 1, "7", label)`, where the leading zero is
the leaf child count and the following fields identify its index/type.

The copied, TV-hash-verified factory data closes the identity mapping:

```
FactoryIndexFile_Part1.dat record 1099:
  (20505, 0, 7, 7, 5, 2, 1, 6091)

Factory_Part1.dat record for index 6091:
  label: Screen Saver Brightness
  storage key: db/factory/FC_STORE_LEVEL_EER_B/SCREEN_SAVER_BRIGHTNESS
  factory UID: 20505 (hex 0x5019)
```

The surrounding numeric record fields include `7, 7, 0`; together with the
QDF driver's independently verified 0--7 bound, this is strong evidence that
the factory item represents the same seven-step brightness setting and that
zero is its lower setting.  Field names for those three integers have not
been recovered from the factory struct, so this should not be described as a
separately documented external min/max contract.

## Relationship to the observed blackout

Kernel/QDF analysis separately shows that AVEMonDIM's normal `value=1`
operation restores the factory screen-saver baseline (`m_fac_ss_brightness`,
currently 7).  The kernel-internal QDF factory-data branch for identifier
`0x5019` updates both the current and factory baseline in RAM.  The factory
record proves that `Screen Saver Brightness` has that exact UID (`20505 =
0x5019`); the external-to-item mapping is therefore established:

```
DBus item key 60802 -> FacItemNode UID 20505 / 0x5019
```

`SetDecimalValue` passes the full item node and requested value to
`TransmitAItemToChip`, making its connection to the QDF factory-data branch
very strong.  A direct disassembly of the implementation behind that virtual
chip-transmit call has not yet shown the final QDF invocation, so retain that
last call-edge as evidence rather than a runtime proof.  In particular, the
ordinary `ave_tcon_api_set_qd_ss_brightness` setter remains unsuitable: it
changes only current brightness and is undone by the next AVEMonDIM restore.

## Decision

There is **no proven genuine external RAM-only/no-save API** for this item in
the copied firmware.  Do not use a factory setter as the next automated
experiment.

If a future owner explicitly accepts a persistent factory-menu modification,
the narrowest recoverable workflow would be:

1. read and record `GetItem(60802)` (currently 7);
2. set exactly one bounded value within the service-advertised range, with
   `SetDecimalValue` preferred over generic `SetParameter` because it is the
   item's dedicated decimal setter;
3. immediately read it back, test only while attended, and restore the exact
   recorded value through the same path before any standby/reboot;
4. verify the post-restore readback and after a controlled reboot.

That is a *persistent-write test with restoration*, not a temporary policy.
It is outside the safety threshold for an unattended or automatic workaround.
