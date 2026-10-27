# Independent review: controller follow-up predicates and CAD route split

## Scope and outcome

This is a bounded offline cross-review of two new conclusions against the
exact copied binaries and retained disassembly.  I made no TV, root, network,
GPIO, I2C, update, power-control, or payload-application call.

No material blocker was found:

1. The two operation-2 sites in the QD monitor have the reported distinct
   predicates.  The no-current-ERR branch at `0x269ae0` requires the exact
   retry value one.  The current-ERR branch at `0x269b26` is downstream of
   `isProductionMode != 1` and the three terminal-retry comparisons.
2. The QDF CAD caller takes the non-SE operation-`0x20` route through the
   dynamically resolved name `tcon_ex_proc`.  It does not take the separately
   recovered SE operation-9/SDP loader route in this build.  The copied-module
   set does not contain an export named exactly `tcon_ex_proc`, so the actual
   CAD consumer remains unresolved.

Both conclusions are static and conditional.  They establish neither live
callback binding nor incident execution and do not authorize a recovery,
firmware-update, payload, or controller command.

## Pinned inputs

| Artifact | SHA-256 |
| --- | --- |
| `binaries/libave.so.0.1` | `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` |
| `overnight/errdet-libave.disasm.txt` | `9a5dfbd37e4a376a1ab8873a04854ab2138e7527836a2598e34b3145885772bb` |
| `qd-monitor-exact-recovery-predicates.md` | `2cab8b090de232224a4d9b5ceb6c2ecf576d5a5a17bcbc8aa046ced116c87a1d` |
| `qd-cad-command9-consumer.md` | `19b3f88815cff664b7452115d242a52b3626e46fbadc09422d399d5663986d6a` |
| `qd-cad-command9-consumer-reproduce.py` | `056839aad8cf8d85d64bc47f68c610eccae48800980468206b02af55a8c052e6` |
| corrected current `qd-firmware-resolver-exact-paths.md` | `6606a013d45ce746db041a667e5a2d916cb1f3ce0b755fcebd43d85d37cfae83` |
| archived prior resolver report | `631e2e9ef0c29d1e2aeb67b42b94a8ff4b890c4bf3d66f6d677849fde25cd0a9` |

The complete 1,928-byte Thumb body at `libave` address `0x2695fc` hashes to
`299e1de0bf303b4c3e6ed87db990e4269aa2b85354c8595cf21ef1ae742b1c87`.
The CAD checker passed in normal mode against all six pinned AArch64 modules.
Its PASS proves hashes and selected landmarks; the control-flow statements
below were checked manually rather than inferred merely from that result.

## QD monitor predicates

### No-current-ERR operation two

The result of `ave_tcon_qd_err_detect_check` is copied to `r4`.  Initial zero
branches at `0x26967a` to `0x2696d6`; a later zero after the retry loop also
falls through from `0x2696d4` to that same block.  At `0x2696d6`:

```text
ldr.w r3,[pc,#0x58c]
add   r3,pc
ldr   r3,[r3,#0x48]
cmp   r3,#1
beq.w 0x269ab8
```

The literal at `0x269c64` is `0x00356542`.  With the Thumb PC value at the
`add`, it resolves to state base `0x5bfc20`; offset `+0x48` is the symbolized
`err_det_reboot_try` at `0x5bfc68`.  The equality branch reaches
`0x269ab8`, and `0x269ade..0x269ae0` executes `movs r0,#2` followed by the
power-control call.  It then returns to `0x2696e4`.  Therefore this site is
selected by **no current ERR predicate plus `err_det_reboot_try == 1`**, not
by status bit `0x10` and not by a broad nonzero retry test.

### Current-ERR operation two

At the common classification path, `0x26971e` compares the retained current
ERR result in `r4`; zero diverts to `0x2699aa`, while nonzero reaches
`0x269724`.  The literal at `0x269c78` is `0x003442c4`; the add at
`0x269728` resolves base `0x5ad9f0`, and the load at base `+8` is the exact
local symbol `isProductionMode` at `0x5ad9f8`.  Equality with one branches to
`0x269bc0`; only a value other than one continues to the retry checks.

The terminal tests are then exact:

- `err_det_reboot_try > 1` at `0x269738..0x26973c`;
- `vdd_det_reboot_try > 3` at `0x26973e..0x269742`; and
- `elvdd_i2c_reboot_try > 3` at `0x269ae6..0x269aea`.

Any true terminal comparison reaches operation zero at `0x26977a` and the
`qd_tcon_off=1` store at `0x269786`.  If none is true, the path logs/decodes
status at `0x269b20`, loads literal operation two at `0x269b24`, calls at
`0x269b26`, and branches to `0x269788`, past the latch store.  Thus the
operation-2 path itself does not set `qd_tcon_off`.

This path also depends on the earlier entry, stale-latch, one-time-execution,
and common-classification gates documented in the source report.  Saying a
fresh nonzero ERR result *can* reach it is accurate; saying every such sample
does would not be.  “ERR” here denotes the function's returned predicate,
which can include the previously documented driver/debug behavior; it is not
independent proof of a raw electrical transition.  No live counter,
production-mode value, or execution of either site was captured here.

## CAD and extension-command routes

### Actual QDF CAD caller

In `m_tcon_upgrade_data_cad` (`qdf_tcon.ko+0x13298`), the block at
`0x13394..0x133a4` calls `m_get_tcon_update_command`, loads the resulting
command word, supplies the composed pathname, and directly calls
`m_tcon_flash_upgrade` at `0x12218`.  Within that complete pinned function,
the update call at `0x1262c` targets `m_tcon_update_send_cmd` at `0x9630`;
there is no call to the SE helper at `0x3f98`.

The non-SE helper loads the imported callback variable
`tztv_tcon_ext_cmd`.  Its call site at `0x99ec..0x99fc` passes a 48-byte
envelope and literal operation `0x20`.  The bridge `_tztv_tcon_ext_cmd`
constructs/resolves the exact string `tcon_ex_proc`, caches the returned
pointer, and calls it conditionally.  A symbol-table check across the six
pinned modules finds no global function exported with that exact name;
`sdp_tcon_ex_proc` is a distinct export and cannot be substituted by name.
This is a bounded missing-provider result, not a claim that no installed or
unacquired module can provide it.

### Separate SE command-9 route

The distinct `m_tcon_update_send_cmd_se` body uses imported
`tztv_frc_tcon_ext_cmd` and, at `0x40bc..0x40c8`, passes a 32-byte request and
literal operation 9.  The copied bridge/SDP modules statically support the
reported conditional chain through `sdp_display_ex_proc`, SDP FRC mediation,
the dynamically resolved exact name `sdp_tcon_ex_proc`, and the SDP TCON
update loader/packer.  Null callback and initialization paths remain, so
this static chain is not proof of live forwarding or success.

The selected SDP pathname loader reads a supplied path and length, clears a
`0x30000` update-image region, opens the path, derives a file length, requests
that many bytes, ignores the `fio_fread` return, and closes.  The packer later
copies exactly `0x30000` bytes into its outgoing message.  The loader has no
explicit pathname-count bound against its 150-byte local area and no explicit
file-length bound against the `0x30000` destination.  Those are static safety
observations, not an invocation proposal.

The normal checker confirms that neither byte order of `0xa5a55a5a` appears
literally in the six complete copied modules and that the selected loader and
packer contain no asserted magic-parser landmark.  This is only a finite
literal/body result: it cannot exclude computed comparisons, a parser in the
missing `tcon_ex_proc` provider, or another unacquired component.  In
particular, the nine 5 MiB CAD files must not inherit the SDP command-9
loader's `0x30000` semantics merely because that separate route was found.

## Final boundaries

- The QD predicate result does not establish that operation two is safe,
  effective, or appropriate to call directly.
- The current live values of the monitor counters, production-mode local,
  route pointers, and CAD key are not proven by static code.
- The real CAD provider, its 5 MiB format/parser, checksum policy, and final
  controller endpoint remain unresolved.
- No negative literal/symbol census is a global runtime-absence proof.
- Nothing reviewed here explains or clears the observed protection bit or
  authorizes a protection bypass, power operation, flash/update, or I2C read.

