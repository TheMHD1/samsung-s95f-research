# RoseMQD FRC duty-write leg

Offline analysis only. Inputs are `libave.so.0.1` SHA-256
`a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`,
`tztv_frc_tcon_api.ko` SHA-256 `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6`,
and `rosem_frc.ko` SHA-256 `c646b45d8ab5028defca91b5f8188bf905b8d29f8927fae292be591c94cdbd34`. No TV/network/root/device action
was taken. This concerns the separate RoseMQD `ave_frc_write_i2c(0x42b48,value)`
leg, not FRC read ioctl `0xc0086626` and not generic F3:0128 replay.

`ave_frc_write_i2c(unsigned,unsigned)` at `0x243db4` receives selector and
value. Unless its examined shared-state gates suppress it, it builds local
two-word `{selector,value}` at `r7+4` and invokes the imported `frc_ioctl`
wrapper with
`0xc0086623` at `0x243df8..0x243dfc`. A shared flag equal to one at the path
through `0x243de0..0x243dec` changes the value to zero and skips the ioctl;
other prior state checks branch through logging/gate paths. The wrapper returns
the ioctl result when invoked and returns zero on the shown suppression path.
Thus zero is not acceptance evidence.

In `tztv_frc_tcon_api.ko`, `fop_frc_ioctl` constructs and compares
`0xc0086623` at `0x195c..0x1968`, branches to `0x2a54`, copies eight user bytes
to a local buffer (`0x2a54..0x2a68`), loads selector/value (`0x2a6c`), and calls
relocated `FRC_WriteI2CData` at `0x2a70`. The relocation names the API module's
export at `tztv_frc_tcon_api.ko:0x9438`, not the distinct
`rosem_frc.ko:RosemFrc_WriteI2CData` at `0x618`. Copy failure returns the initialized
`-EFAULT` route. This is a positive write dispatch distinct from 6626.

The API export obtains its function table from API BSS `+0x618`; its write
callback is table slot `+0xf0` (240), analogous to the read slot +248. Static
pairing is positive: `rosem_frc` initializer `.init.text+0x1fc..0x204`
materializes `RosemFrc_WriteI2CData` and stores it to the RoseM table +0xf0;
the same initializer passes the table to `map_frc_functions`, whose API body
stores it in BSS +0x618. This is static initialization pairing, not proof it
was live during the incident.

`RosemFrc_WriteI2CData` at `.text+0x618` has a conditional cache path:
only when cached `m_pvcc_status` (BSS `+0x14`) is **zero** does it search
the selector table, provided value-array pointer `+0x100`, selector pointer
`+0x2a0` and count `+0x298` are nonzero. A match updates the value-array
word at `0x684` before the transfer gates. When cached PVCC is nonzero,
the branch at `0x63c` skips this cache search/store and reaches the ordinary
transfer gates directly. An absent table or unmatched selector also reaches
those gates; absence from the table does not suppress the immediate write.

Upgrade status `+0x44 == 1` or EW test `+0x6c == 1` skips the lower write
and returns zero. Otherwise `0x6a8..0x6b0` calls
`m_rosem_reg_write(selector,value)`. There is no equality suppression in
the reviewed selector-table update path, and no rollback of its cache store
if the later helper fails. This table is distinct from AVE's earlier
`siDimLvl` cache.

`m_rosem_reg_write` (`0x488`, 212 bytes) requires
`m_pvcc_status | m_outdoor_mode` (BSS `+0x14 | +0x19c`) to be nonzero.
When clear it returns zero without invoking the extension operation. When
set, it builds the 16-byte envelope `{0, value, selector, 1}` and invokes
the imported callback `tztv_frc_tcon_ext_cmd(2, &envelope, 16)` at
`0x4ac..0x4d0`. The final word one distinguishes this write envelope from
the [read envelope](frc-ioctl-6626-analysis.md), whose final word is zero.
An absent extension callback returns `-1`; otherwise the helper preserves
its callback return, including nonzero errors. Neither the envelope nor a
zero return proves physical bus activity or controller acceptance. The
bridge's subsequent dynamically resolved endpoint remains outside the
positive binding established here; the earlier read-ABI report describes
that additional boundary.

The base RoseMQD caller stores its AVE duty request cache before both
transports; this FRC write leg does not itself repair that ordering. Generic
kernel F3:0128 recovery replay is a separate mechanism. The positive FRC
table/replay evidence below is required to discuss this selector's restoration.

## Positive QD membership and conditional replay

`rosem_frc` rodata `uiRosemQDRegisterAddress` at `0xf00` holds nine u32
selectors; `0x42b48` is entry index 3 at `0xf0c`. In `RosemFrc_Initialize`,
the route with `m_ld_support` (BSS `+0xf4`) **not equal to one** tests
`m_oled_type` (`+0x1ac`); value one takes the QD path at `0x79f8`, stores
count nine at `0x79fc`, and, if the selector pointer is null, allocates and
copies those nine selectors at `0x7a34..0x7a84`. The value array is
allocated separately at `0x7904..0x7914` when needed, and this allocation
does not itself populate values or establish their validity. Existing nonnull
arrays can bypass allocation/copy. Other model values select different
tables. The model fields and table contents were not read, so this is not a
live table assertion. The copied static QD list is:

```text
4279c 427a0 41ec4 42b48 42618 40e70 47024 47028 4374c
```

`RosemFrc_Suspend` (`0x5dd8`, 424 bytes), after its upgrade/EW gates,
iterates the nonnull, nonempty table at `0x5e78..0x5ed4`. It calls
`m_rosem_reg_read(selector, &value_array[index])` at `0x5ec4` for every
entry. The loop does not check each helper return. The lower read can
return zero without writing a value, as previously established; therefore
this is a refresh attempt, not a guarantee of fresh or valid saved values.

`RosemFrc_Resume` (`0xd550`, 2532 bytes) also skips its ordinary body
when upgrade/EW status is one. On its ordinary route it first sets cached
PVCC to one at `0xd5e0`. Input **20 decimal** reaches the selector/value
loop through `0xd5f8..0xd638`; it loads
the count, selector and cached value at `0xd66c..0xd68c` and calls
`m_rosem_reg_write` at `0xd690`. It immediately loads a debug field rather
than accumulating that write return; per-entry replay errors do not contribute
to its saved aggregate result. There is no per-entry valid flag checked in
this loop. This audit establishes input 20's positive route, not that every
Resume input or every controller reset traverses it. Therefore if that QD
model table was initialized and this Resume
branch ran, the cached value for selector `0x42b48` reaches the lower register
write helper. This is static reachability only, not proof of resume, transfer,
acceptance, or panel output. Existing unobserved process-state captures did
not inspect these kernel tables.

## Review and reproduction scope

The initial agent draft and minimal verifier were corrected during parent
review: API and RoseM functions with nearby/similar identities had been
conflated, the exact write callback pairing and conditional cache store were
missing, and a local no-replay statement preceded the later positive result.
This final text incorporates the recovered initializer, exact QD membership,
Suspend refresh and Resume-20 replay. No earlier frozen evidence was edited.

The revised [reproducer](frc-duty-write-recovery-reproduce.py) pins the three
ELFs and the shared ELF-reading implementation in
`monitor-input-status-provenance.py`. It checks the PLT identity, ioctl
dispatch relocation, API callback slot, RoseM registration, cache gate, lower
write envelope, static QD table and lifecycle instruction landmarks. It
excludes the userspace wrapper's literal pool from instruction decoding and
compares a retained [bounded listing](frc-duty-write-recovery.disasm).
Manual control-flow/dataflow review is still required; passing landmarks
are not automatic proof of the complete binary or runtime behavior.

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/frc-duty-write-recovery-reproduce.py
```

No live observation, selector write, replay, suspend/resume, or workaround was
performed for this analysis. The finding narrows future measurements: an
incident must distinguish a failed immediate write, an unchanged/stale saved
value, a replay not reached, and a replay reached but ineffective downstream.
