# UID `0x506e` / value `6`: off-sensing route coverage

## Result

The copied `deviced` binary proves one narrow effect for the factory item
`UID 0x506e` (`Offsensing TEST Period`): a successful factory read whose
integer value is exactly `6` makes
`OledDevice::OffSensingDisabledInFactoryMenu()` true.  The one recovered
consumer is the normal QD display-state classifier.  On its eligible path,
that true result returns classifier state `0`, thereby suppressing a *new*
normal/force off-sensing notification from that classifier invocation.

This is **not** an all-route maintenance disable.  It does not have a recovered
guard edge into the direct user-request, standby/power-suspend, existing
notification-countdown, reinforce-timer, or EL/Pixel Refresh routes.  Some of
those bodies have been bounded and contain no direct call to the known
predicate; that is useful scope evidence, but cannot establish global
exclusion through untraced virtual, higher-level, data-driven, or unacquired
paths.

No FactoryService request, storage write, PPI request, D-Bus request, power
operation, or TV action was made for this audit.

## Exact predicate and its only recovered direct caller

The copied factory definition identifies item `200802` as UID `0x506e`, label
`Offsensing TEST Period`, with storage-key string
`db/factory/FC_STORE_LEVEL_EER_B/OFFSENSING_TEST_PERIOD`.  In exact copied
`binaries/deviced` (SHA-256
`2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2`),
ARM `OledDevice::OffSensingDisabledInFactoryMenu()` at `0x7ad00`:

```text
0x7ad04  materialize UID 0x506e
0x7ad34  factory_get_data(0x506e, &value)
0x7ad38  require return == 1
...       return (value == 6)
```

Thus a failed read and every successfully read value other than `6` evaluate
false.  This says nothing about the physical meaning or safety of values 0–5.
The global wrapper `off_sensing_is_disabled_in_factory_menu` at `0x769cc`
dispatches through the selected off-sensing object.  The bounded
mapping-symbol-aware scan in the existing factory audit found one direct
caller of that wrapper: `qd_get_state` at `0x71688`.  The virtual edge from
the wrapper to `OledDevice` explains why the predicate itself is not a direct
branch target.

The factory setter is intentionally out of scope as a control recommendation:
its copied route can enter real PPI dispatches and conditionally reach factory
storage, while daemon reload/application timing is unproved.  See
`factory-off-sensing-transmit-target.md` for that separate risk boundary.

## Coverage matrix

| Route under review | Linked predicate coverage | What value `6` can establish | What it cannot establish |
|---|---|---|---|
| (a) Normal startup QD classifier | **Proven**, conditional | On the eligible `qd_get_state` path, return `0` rather than a newly classified normal/force result | No cancellation of existing UI/timer, no assertion about earlier saved-result/EL branches, no physical sensing result |
| (b) Normal/force popup and force countdown | **Only upstream new-popup suppression** through (a) | Startup classifier state `0` is not mapped to the normal/force notification events | No stop/cancel of a countdown already created; no coverage of reinforce timer |
| (c) `RequestOffSensing` mode 0 / `startByUser` | **No recovered guard edge** | Nothing beyond the bounded absence of a direct call in named user-start/start bodies | Not proof that every user request bypasses the predicate through all indirect paths |
| (d) Standby power-suspend `needSensing` / `start` | **No recovered guard edge** | Nothing beyond the bounded absence of a direct call in named suspend/start bodies | Not proof that all automatic standby sensing ignores the predicate |
| (e) EL / Pixel Refresh | **No recovered link** to UID `0x506e` predicate | The audited EL request/state paths remain distinct | Not proof that the setting cannot affect an unacquired/higher EL policy; no EL disable effect is shown |

### (a) Normal startup classifier: proven narrow suppression

`qd_get_state` begins at ARM `0x71520`.  Its early saved-result branches can
return lifecycle values before the factory check.  On the later ordinary
classification path it computes an EL-related comparison result in `r4`:

```text
0x71674..0x71684  derive r4; a greater EL condition branches to return 7
0x71688            off_sensing_is_disabled_in_factory_menu()
0x7168c            compare result with zero
0x71690            nonzero -> 0x71728
0x71728..0x71768  log then return r4
0x716fc..0x71714  only false predicate: compare off-time and return 2, 1, or 0
```

The nonzero predicate branch is reached only after the greater-EL condition
has not taken its return-7 branch; at that point `r4` is zero.  Therefore an
eligible successful `value == 6` predicate produces classifier result **0**.
The false-predicate path is the one that maps off-time `>= 0x2d0` to `2`,
`> 0xef` to `1`, and otherwise to `0`.

`app-control-service` `CheckQdDisplayState` sends states 1 and 2 through its
normal/force notification mapper, while state 0 has no corresponding
normal/force output.  This links the narrow result as:

```text
factory_get_data(0x506e) == success/value 6
  -> qd_get_state eligible ordinary branch returns 0
  -> no newly mapped normal_off_sensing_required / force_off_sensing_required
     from that classifier invocation
```

The classifier is not a passive observation API: some other result branches
can save/acknowledge outcomes.  No live query was issued.  The exact result is
also conditional on support, ready, and preceding classifier gates; it is not
a blanket return-0 override.

### (b) Popup/countdown versus reinforce: bounded separation

The forced popup's automatic route is in `tv-viewer`: its local 60-update
progress handler calls `RequestQdDisplayOffSensing()` at `0x26d5b2` when the
counter expires.  The factory predicate is not in that viewer code.  It can
prevent a *future classifier-produced* state-1/2 popup only through section
(a); it has no recovered edge that destroys a popup already shown or the
progress timer it already created.

Reinforce is separately scheduled by
`CReinforceOffSensingTimer::t_ProcessTimeout()` in `app-control-service`.
Its policy uses the adaptive-off-sensing feature, power state, software-upgrade
state, and reinforce/cancel keys.  No UID `0x506e` factory-predicate call was
recovered on that timer route.  Accordingly value `6` must not be described
as a reinforce-warning or countdown cancellation control.

### (c) User request mode 0: no linked coverage

The `libdeviced` convenience call
`qd_display_request_off_sensing()` explicitly sets mode `0` and reaches the
daemon GDBus handler `gdbus_request_off_sensing` at `0x5dee0`.  A decoded zero
request branches at `0x5dfe0` to `off_sensing_request_start_by_user` at
`0x76700`, which selects legacy `startByUser` `0x79368` or Y23 `startByUser`
`0x80374`.

Both bounded start-by-user bodies check local state and power state, then call
their generation's `start(2)` (`0x794b8` / `0x804b4`).  The recovered start
bodies (`0x774e0` / `0x7eee0`) likewise contain no direct call to
`off_sensing_is_disabled_in_factory_menu` or the UID predicate.  This proves
no direct known-predicate edge in these bounded bodies, not that every
possible virtual/higher call chain is insensitive to the factory value.

### (d) Standby/power-suspend policy: no linked coverage

Legacy `OffSensing::onPowerSuspend` (`0x78ab8`) and Y23
`OffSensingY23::onPowerSuspend` (`0x7fba4`) require event state 1, reject
event type 6, and require sensing state 0.  Their non-`0x2a` branches call the
generation-specific `needSensing()` helper before `start`; the documented call
regions are legacy `0x78de0..0x78f2c` and Y23 `0x7fde0..0x7fe58`.

Neither bounded handler nor the named start bodies supplies a direct branch to
the known factory-disable wrapper.  The `needSensing()` helper and virtual
operations are separate boundaries; without a proven predicate-to-helper edge,
the correct classification is **coverage not established**, rather than
“value 6 does not affect standby sensing.”

### (e) EL / Pixel Refresh: distinct, unlinked policy

The EL families are `ELSensing` / `ELSensingY23`, not `OffSensing`. Their
`pixelRefreshRequestByUser()` methods (`0x73d50` / `0x7c650`) read
`db/sysman/el_sensing_poweroff`; their start methods issue the distinct
`ppi_displaypanel_set_elsensing` request only after EL-specific state and
standby guards.  No recovered call connects these paths to
`OffSensingDisabledInFactoryMenu`, UID `0x506e`, or the factory wrapper.

Do not confuse the user-request consumer's check `getPowerOffType() != 6`
with factory value `6`: it compares a power-off type code, not the factory
item's integer.  This distinction rules out treating the same numeral as
evidence of EL coverage.

## Decision boundary

The evidence supports only a future candidate hypothesis: if a factory value
of 6 were successfully supplied to the daemon's predicate, it would suppress
eligible *new classifier-based* normal/force off-sensing notifications. It
does not establish blackout repair, existing-countdown cancellation, standby
or user-request bypass, EL/Pixel Refresh suppression, persistent application,
or hardware safety. The current observed factory service value was 0 and the
named storage key was absent; neither is a safe rollback baseline for a write.

## Inputs

This report links only existing, hash-qualified offline analyses:

- `binaries/deviced` —
  `2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2`
- `binaries/libdeviced.so.1.0.3` —
  `ea3ddbe08dbad2eb3d969d0df434be23afe69eb00921a7969191646e2d1bcb1a`
- `binaries/tv-viewer` —
  `d32fbb420d26a27845cbb23ab216de23706c6aeb6376e4107849f74ec5a1883f`
- `binaries/app-control-service` —
  `f2adcb0ab496e555f6c2b40c854240956860d84909daf83be9fc6017bb7001c6`

The existing `factory-off-sensing-test-period-reproduce.py` validates the
predicate and direct-wrapper caller inventory. The existing
`deviced-off-sensing-policy-reproduce.py` and
`deviced-el-sensing-policy-reproduce.py`, plus the linked reports, provide the
bounded route evidence. No new live control or diagnostic procedure follows
from this coverage map.
