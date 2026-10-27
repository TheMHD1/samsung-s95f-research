# UID `0x506e` factory readback and storage boundary

This is an offline audit of copied ELFs and already captured read-only process
maps. It makes no FactoryService request, does not alter a factory record, and
does not contact the TV.

## Bottom line

The predicate in `deviced` does **not** directly read the named
`db/factory/.../OFFSENSING_TEST_PERIOD` key, nor does the evidence show a
per-process value cached in `deviced`. Its imported
`factory_get_data(0x506e, &value)` reaches the factory PPI getter on each call.
The recovered paired static backend then reaches the exact copied PRD factory
interface: UID `0x506e` takes its ordinary `GetFactoryUID` path. Its actual
32-byte `FactoryIndexFile` tuple has storage type `2`, which selects
`PrdNvramMap::ReadFactoryArea`, not the unrelated type-1 volatile-vconf arm.

This is concrete evidence for an on-demand PRD NVRAM-area read, not a direct
read of the named `db/factory/...` key and not a vconf volatile-key lookup.
The copied data cannot establish whether a later setter is visible immediately
to an already-running `deviced`, whether NVRAM writes persist through power
cycles, or whether a service/process/lifecycle reload is needed.

The factory setter's `FCStorageBaseCommon::SetFactoryUID` is a separate,
storage-oriented path with virtual storage-region dispatch. It is not evidence
that the public getter always reads that path directly. In particular, a
FactoryService display of `0` is not proof that the named key exists, and no
verified stock, single-UID delete/reset API was recovered that would restore an
originally absent record. No mutation is recommended from this audit.

## Identity and observed baseline

The copied factory sources map service child `200802` to UID `0x506e`, label
`Offsensing TEST Period`, and key
`db/factory/FC_STORE_LEVEL_EER_B/OFFSENSING_TEST_PERIOD`; see
[`factory-off-sensing-test-period.md`](factory-off-sensing-test-period.md) for
the hash-gated record offsets.

At the same boot, the read-only FactoryService capture returned success and
the display string `"0"` for child `200802`, while `vconftool get` for that
exact key failed with “No such file or directory” (exit 1):
[`optimization-factory-period-baseline-20261026T134120Z.json`](../overnight/optimization-factory-period-baseline-20261026T134120Z.json).
Therefore `0` can be a definition/default/fallback or a value held behind the
factory API. It does not demonstrate a pre-existing writable record. Writing
`0` later cannot be represented as a proven restoration of record absence.

## Public getter: exact static boundary and return contract

`deviced` imports `factory_get_data`; its
`OledDevice::OffSensingDisabledInFactoryMenu` calls it with UID `0x506e` and
returns true only for the public success result and output value `6`. The
copied public provider, `libfactory-interface-ATSC.so`
SHA-256 `1fc40fa93b3bf81ee79b610d8c699ba94e3f4ee49e3a737d4dfe1e2e803425dd`, has
`factory_get_data` at Thumb `0x439a4b0c` (176 bytes).

Its two possible call instructions at `0x439a4b14` and `0x439a4b28` enter the
ARM PLT stub whose resolved GOT cell is `0x439d5d0c`, the relocation for
`ppi_factory_get_data`. Every public invocation reaches PPI at least once;
only a first result other than `-3002` reaches the second call:

```text
0x439a4b14  call PPI getter; result == -3002 (0xfffff446) -> return -1
0x439a4b28  otherwise call PPI getter; result == -3001 (0xfffff447) -> return 0
otherwise                                         -> return 1
```

That is the relevant public success convention for the `deviced` predicate:
`1` means neither wrapper-recognized failure was returned. It does *not*
describe the `value` as valid, prove persistence, or say that the PPI made a
new storage-system query rather than serving a cache.

The separately copied `libfactory-api-impl-sec.so`
SHA-256 `671575f611a69fdbac1c43d27597db640bd963ed9bbce9ecb2f6f5eb1300d12c`
exports `factory_get_data_impl` at Thumb `0x1dc4` and imports
`prd_factory_get_data`. Its first call at `0x1dcc` returning `-1` maps to
`-3002` directly; otherwise its second call at `0x1dd8` can map `0` to
`-3001`, and the remaining path returns `0`. This proves a second API layer
exists; it must not be conflated with the public wrapper's `1`-on-success
contract.

`libfactory.so.0.1` itself (SHA-256
`31dc9c0705ae864105cb60bd952e2f06f9bb5524f38612b611906343d11d418d`) exports
`ppi_factory_get_backend*` and dynamically loads
`/prd/usr/lib/libfactory-impl.so`; it exports no symbol named
`factory_get_data`. Thus “`libfactory.so.0.1 factory_get_data`” is not an
actual symbol/function pairing in the supplied binary. Naming alone cannot
select the runtime getter implementation.

## Concrete PPI-to-PRD reader path

The newly supplied `libppi-factory-api.so` SHA-256
`5c7026ae05f5d0ecbd2460245ac604ab718f0af97f6c7a2df717c7a224a8f517`
provides the previously missing PPI body. `ppi_factory_get_data` is at Thumb
`0x43ab2020` (232 bytes). It obtains its backend descriptor, checks the
initialization word and backend table, then tail-calls table slot `+0`:

```text
0x43ab2028..0x43ab2038  obtain/check backend descriptor and table
0x43ab203e..0x43ab2042  load/check function pointer at table + 0
0x43ab2044..0x43ab2058  reload table + 0; tail-branch(uid, output)
```

The loader text names `/prd/usr/lib/libfactory-api-impl.so`. Static paired
evidence in copied `libfactory-api-impl-sec.so` shows
`factory_api_impl_set_funcs` at `0x1f10` installs relocation `0x130b4`,
`factory_get_data_impl`, into table slot `+0` (`0x1f1c..0x1f1e`). This
implementation calls `prd_factory_get_data` through its PRD import. This is a
static pairing, not a capture of the live descriptor or table pointer; the
same-boot map shows that the `-sec` implementation was loaded.

The exact copied, runtime-mapped PRD provider is
`libprd-factory-interface-ATSC.so` SHA-256
`ef872d9d90135ffcf4bea4470df4f37f4b06b51cd53a9a482568113a3970d0a5`.
`prd_factory_get_data` (`0x12e9c`) forwards to
`prd_factory_get_data_with_source_info` (`0x12d40`), which calls
`PrdStorageBaseCommon::GetIntDataSrcRes`. UID `0x506e` is greater than the
special `0xb4` cases and is not `0x1fa`; its static branch therefore reaches
the regular `GetFactoryUID` call at `0x10bfa` (PLT/GOT relocation `0x2e07c`).

`GetStoreData` first calls `t_GetFileItemNode` (`0x10a2c`, PLT relocation
`0x2e0f0`). That body binary-searches entries at a **32-byte** stride
(`0xf2f8` and `0xf338`), i.e. `FacFileItem_s` entries in
`FactoryIndexFile_Part1.dat`, rather than the 0x164-byte Part1 UI/data record.
The UID-`0x506e` tuple at file offset `0x8bc0` is:

```text
(uid 0x506e, 0, 6, 0, 5, type 2, length 1, offset 6240 / 0x1860)
```

Therefore its type is `2` at tuple `+0x14`, not the `1` at offset `+0x14` in
the unrelated 0x164-byte `Factory_Part1.dat` record. `GetStoreData` branches
at `0x10a5a` to its type-2 arm at `0x10aa0..0x10aac`, loading tuple length
`1` and offset `0x1860`, then calling `PrdNvramMap::ReadFactoryArea` through
relocation `0x2e0d0`. There is no type-1/vconf miss-fill on this UID route.

## Corresponding PRD setter

`PrdStorageBaseCommon::SetFactoryUID(unsigned,int,source)` starts at
`0x137e4`. Type `2` follows its normal storage arm (`0x138c6..0x1390a`), not
`t_SetDataVolatile`. It obtains a storage-length/index quantity, combines it
with the tuple's length and base offset (`0x1390e` is not reached for type 2),
then calls `PrdNvramMap::WriteFactoryArea` via relocation `0x2e1fc` at
`0x13906`. The call arguments statically include tuple length `1`, tuple base
offset `0x1860`, requested value, and a computed adjustment
`storage_index * length`; the final logical factory-area offset is consequently
not asserted as exactly `0x1860` without recovering that storage-index value.

This proves the PRD read/write pair **when the corresponding PRD setter is
invoked** for UID `0x506e`: `ReadFactoryArea(offset 0x1860, length 1)` and a
matching `WriteFactoryArea` path. It is not a demonstrated write to the named
`db/factory/FC_STORE_LEVEL_EER_B/OFFSENSING_TEST_PERIOD` key.

The earlier `TIFSDaemon` path reaches the different copied
`FCStorageBaseCommon::SetFactoryUID` through its FactoryService setter. This
report does not equate that FC call with `PrdStorageBaseCommon::SetFactoryUID`;
an inter-library call edge or live binding would still be needed to prove the
FactoryService write takes this PRD route.

No explicit cache update, IPC notification, or watcher callback occurs in the
recovered PRD type-2 setter arm before its NVRAM call. This does not prove that
`PrdNvramMap` lacks persistence, cache invalidation, or notifications.

## PRD NVRAM backing: concrete reader/writer, not a process cache

The exact PRD provider contains the `PrdNvramMap` implementation itself; it is
not an unresolved `libnvram` import. The byte overloads enforce
`logical_offset + length <= 0x4000`, add `0x3e00` to the logical offset, then
dispatch through the map object's virtual read/write slots:

```text
ReadFactoryArea(byte*)  0x1569a add(offset,length); 0x156a0 bound check
                         0x156ac offset += 0x3e00; 0x156b2 call vtable +0
WriteFactoryArea(byte*) 0x1557e add(offset,length); 0x15584 bound check
                         0x15590 offset += 0x3e00; 0x15596 call vtable +4
```

Thus the getter's logical `(0x1860, 1)` resolves to translated
**driver-request** offset `0x5660` for this implementation. That does not
identify a physical-media address. The integer read wrapper at
`0x156f8` calls that byte overload and sign-extends a length-one result at
`0x15736`; the integer write wrapper at `0x155dc` truncates a length-one
input to a byte at `0x15612` before calling its byte overload. The desired
value `6` is unaffected by that signed conversion, but the detail matters for
other byte values.

The map's vtable implementations are local:
`PrdNvramMap::t_ReadE` at `0x14bf0` and `t_WriteE` at `0x14db4`. They retain
separate read/write descriptors, open on demand with retry loops (up to
`0x1f4` attempts with `usleep(10000)`), and issue `ioctl` rather than reading
or writing a copied per-process value:

```text
t_ReadE   0x14c30..0x14c48  ioctl(fd, 0x80044906, request)
t_WriteE  0x14df2..0x14e08  ioctl(fd, 0x40044905, request)
           0x14c86 / 0x14e46 open64(path, read/write mode)
           0x14d26 / 0x14ed4 close(fd) after an ioctl failure
```

The PLT relocations resolve those calls respectively to `ioctl` (`0x2e174`),
`open64` (`0x2e190`), `close` (`0x2e138`), and `usleep` (`0x2e274`). This is
static evidence that a normal PRD getter reaches a driver-mediated NVRAM-area
read each time it reaches this type-2 arm, rather than returning a PRD-library
byte cache. It does **not** establish the driver's nonvolatile media,
cross-process synchronization, write completion, or restart/reload policy.

## Separate FactoryService FC write path reaches FC NVRAM

The prior caution about conflating FC and PRD setters remains important: they
are different classes in different copied ELFs. But the FC setter has now been
traced beyond its generic virtual-call description. In
`TIFSDaemon`, the FactoryService storage call imports the simple
`FCStorageBaseCommon::SetFactoryUID(unsigned,int,int)` at GOT `0x165ad0`.
The exact `libfactory-interface-ATSC.so` simple overload is Thumb
`0x43999b28`; it calls PLT `0x4398b010` at `0x43999b6a`, whose relocation
`0x439d5ff4` is the detailed
`FCStorageBaseCommon::SetFactoryUID(unsigned,int,fac_source_info_s)` at
`0x43999998`. This is the static bridge from the already documented guarded
TIFS storage call to the detailed body below.

In
`libfactory-interface-ATSC.so`, `FCStorageBaseCommon::SetFactoryUID` first
uses `t_GetFileItemNode` (PLT `0x4398a6b0`, relocation
`0x439d5ce4`) to obtain the same 32-byte `FacFileItem_s` index tuple—not the
0x164-byte UI record. For UID `0x506e`, tuple `+0x14` is therefore type `2`.
The `type - 2 <= 0x37` arm at `0x439999dc..0x43999a76` reaches the FC
NVRAM writer at `0x43999aa6..0x43999ab2`:

```text
tuple + 0x18 / +0x1c     length 1 / base logical offset 0x1860
0x43999aae               offset = base + index * length
0x43999ab2               FCNvramMap::WriteFactoryArea(offset,length,value)
```

`FCNvramMap::WriteFactoryArea` applies the same `+0x3e00` and `0x4000` bound
policy (`0x439b0780..0x439b079a`), then its local `t_WriteE` calls the
undefined PPI import `ppi_nvram_write` via PLT `0x4398b07c`, whose relocation
is `0x439d6018`. This connects the *conditional* FactoryService storage edge
already documented in `factory-off-sensing-transmit-target.md` to an FC NVRAM
write attempt. It does not prove that the TIFS call's guard succeeded in the
running process, nor that the PPI write succeeded.

The map vtable bindings are also statically relocated, rather than inferred
only from call names: PRD `PrdNvramMap` slots `0x2ded0/0x2ded4` resolve to
`t_ReadE` `0x14bf1` / `t_WriteE` `0x14db5`; FC `FCNvramMap` slots
`0x439d5760/0x439d5764` resolve to `t_ReadE` `0x439afa45` /
`t_WriteE` `0x439afb69`.

The now-copied NVRAM PPI wrapper,
`libnvram.so.0.1` SHA-256
`3f4477b347980727fd1de7ec7709e76a8946a047514d4eeee5e8113f9c80dd95`,
exports `ppi_nvram_write` at Thumb `0x43a7074c`. It lazy-loads the named
backend `/prd/usr/lib/libnvram-impl.so`, obtains a backend-data object, and
tail-calls its write function pointer at table `+4`
(`0x43a7076a..0x43a7077e`). The same-boot map shows the paired installed
implementation `/prd/usr/lib/libnvram-impl-sec.so.0.1`; its exact copied SHA
is `8b7b8adf55415aa19b0c55a8f562a3c428620ebf823e1b48c3412f142d5e62fc`.

That paired static implementation's `nvram_write_impl` (`0xb3c`) lazily
creates `NvramSecImpl`, then dispatches to `NvramSecImpl::write` (`0xa64`).
That method calls its imported `eeprom_write` through PLT `0x7b4`. The exact
next provider is now copied: `/prd/usr/lib/libeeprom-map.so.0.1`, SHA-256
`2a7df2af3997c810066585b0186fe3c8455a6a8eb97a47213ef11a8342c5478c`.
Its `eeprom_write` (`0xa40`) initializes/checks the EEPROM descriptor and
issues `ioctl(fd, 0x40044905, request)` at `0xa74..0xa90`; its paired reader
uses `0x80044906` at `0xe1a..0xe2a`. Its initialization literal is
`/dev/eeprom` (rodata `0x11c8`).

This proves a static convergence at the same driver ABI: PRD's local
`PrdNvramMap::t_WriteE` opens its own `/dev/eeprom` literal (rodata `0x1be20`)
and sends the same `0x40044905` ioctl; the FC route reaches the same device
protocol through `ppi_nvram_write → NvramSecImpl → eeprom_write`. The map
confirms that both NVRAM wrapper and implementation were loaded in TIFSDaemon,
but no backend-table-pointer capture was made, so the FC half remains a paired
static route—not a proof that a live table dereference or write succeeded.
Even this shared endpoint does not prove physical-media persistence, driver
flush semantics, cross-process cache behavior, notifications, or when an
already-running `deviced` rereads it.
The exact source already available for this request is
`binaries/libfactory-interface-ATSC.so` SHA-256
`1fc40fa93b3bf81ee79b610d8c699ba94e3f4ee49e3a737d4dfe1e2e803425dd`;
the import/relocation target is link-time VA `0x439d6018`, not a stale
process-relative address.

For an exact, non-mutating runtime binding check, the PPI library's backend
descriptor is at link-time VA `0x43ac3048` (load-base-relative `0x13048`),
where the getter reads the initialization word and table pointer. The PPI GOT
cell for `ppi_factory_api_get_backend_data` is link-time VA `0x43ac300c`
(relative `0x1300c`). A read-only capture of those words, together with the
existing mapped-library SHA, would determine whether the paired static table
is the live one. No such capture is used by this report.

## Runtime evidence — and its limit

The captured same-boot `deviced` maps show these modules simultaneously
loaded: `/usr/lib/libprd-factory-interface-ATSC.so`,
`/prd/usr/lib/libfactory-api-impl-sec.so`,
`/prd/usr/lib/libfactory-data-config.so.00.00.0057`, and the factory data
index. They also show mappings for `shm_vconf_key_list`,
`shm_vconf_key_str_storage`, `shm_vconf_str_storage`, `shm_vconf_dbl_storage`,
`shm_buxton`, and `shm_buxton_lite`; see
[`runtime-deviced-maps-20261026T114137Z.json`](../overnight/runtime-deviced-maps-20261026T114137Z.json).

This is strong evidence that the live process has both factory components and
shared configuration facilities available. The separately acquired
`libprd-factory-interface-ATSC.so` is the exact pathname in that map. It is
still **not** a GOT/table capture of the PPI `factory_get_data` binding, and
does not show the NVRAM contents for UID `0x506e`, whether an additional cache
participated, or any change notification/reload policy. The older copied
provider called `libfactory-interface-ATSC.so` is a different file and is not
treated here as proof of the PRD provider's runtime binding.

Accordingly, the only supported conclusion about read timing is narrow:
the static public wrapper enters PPI on every call. The following remain
unresolved without an appropriately authorized, read-only runtime trace or
exact binding capture:

- whether the paired static PPI table is the actual live table;
- the concrete NVRAM-area byte at the time the FactoryService displayed `0`;
- whether the NVRAM driver/PPI backend persists, caches, or publishes updates;
- whether `deviced` needs a lifecycle event to observe a changed value.

## Setter storage path is separate and conditional

The setter path is described in
[`factory-off-sensing-transmit-target.md`](factory-off-sensing-transmit-target.md).
The FC NVRAM route above identifies the type-2 storage backend after the
guarded call reaches `FCStorageBaseCommon::SetFactoryUID`; it is not a
readback guarantee, a live-transaction observation, or proof of persistence.

## Removal/reset inventory

The available public interface has broad `factory_reset`/`factory_reset_grpc`
and proxy reset symbols, plus `FCStorageBaseCommon::ResetAdditionalItems`.
The copied code also imports libc `remove`, but its relocation alone does not
connect it to UID `0x506e` or the named Offsensing key. `factory_unset_ticket_number`
is a different, specifically named ticket API. No supplied ELF exposes or
proves a UID-`0x506e` `delete`, `unset`, or “restore absence” operation.

Therefore there is no demonstrated stock, narrow rollback for either the
named definition key or the recovered NVRAM area. The only observed absence
was for the named definition key; no NVRAM-area read was performed. Broad
factory reset operations are not substitutes: their scope and consequences for
this panel were not recovered and they must not be invoked as a workaround.

## Decision

Do not infer that setting item `200802` to `6` will be immediately visible to
`deviced`, survive a reboot, or be reversible. The named-key absence does not
describe the actual getter's NVRAM source. The static evidence supports an API
boundary and a matched conditional PRD NVRAM read/write path, not a safe live
setting procedure. No live action was performed.

## Offline reproduction

```sh
python3 tcon-research/factory-off-sensing-storage-readback-reproduce.py
```

The checker hashes the supplied binaries and verifies the public PPI getter
relocation, the PPI table-slot dispatch, the paired API table installation,
the PRD normal-UID/type-2 NVRAM landmarks, the 32-byte UID tuple, matching PRD
NVRAM setter, FC type-2 NVRAM landmarks, and the absence of a
`factory_get_data` export from `libfactory.so.0.1`. It does not prove the live
PPI table binding, NVRAM-driver/PPI persistence/cache/notification policy,
lifecycle reload, or deletion semantics.
