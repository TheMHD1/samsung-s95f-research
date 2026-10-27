# Future first-header phase after the recovered BI replay

Recorded 2026-10-27 UTC. This is a bounded offline review of retained source
and records. It made no TV, network, root, USB, I2C, UI, reset, power,
firmware, controller, or collector request. It does not retroqualify BI's
rejected recorder, clear a new vendor header, or relax any existing parser.

## Result

The BI `F3:01` failure does **not by itself make the USB vendor parser phase
ambiguous**. It occurred after USB device 49 had enumerated and configuration
1 had been reported. The failed operation was the post-check for the already
completed `F3:00:000330 = 000000c0` setting write. Stock QDF retried that
check once, obtained the exact expected checksum `e6`, advanced to setting
`000334`, and completed 199 further I2C transfers. The bounded QDF path handles
that error by an I2C re-read; no reviewed edge from this retry writes the
vendor parser state or issues vendor bulk traffic.

That conclusion is deliberately narrower than BI's scientific acquisition
contract. The predeclared requirement that every action-PID I2C transfer
return `2` was a useful criterion for calling the entire replay complete and
using the rejected recorder as a causal bracket. It is **not** a recovered
invariant of the independent USB OUT parser. BO's checksum proof narrows the
one I2C defect, but it does not repair BI's forced-vlog/export failure and does
not retroactively make the collector or a delayed X result eligible.

The retained evidence still does not prove an unconditional fresh
`ReadyForHeader` state for a future first USB header. It supports a narrower,
conditional **no-prior-payload premise**:

1. if the same vendor implementation's configuration callback executed on
   the newly configured USB instance;
2. if its state stores completed before any host vendor OUT; and
3. if the bounded closed-world lineage contains no intervening vendor OUT,

then the first fixed target-`0x101` read header cannot be consumed as an old
operation-2 write payload. The callback stores operation `6`, remaining `0`,
and the header pointer before attempting the exact 12-byte receive.

The source does **not** prove that the endpoint controller accepted that
receive. The rearm helper's submission return is discarded and the
configuration callback returns zero regardless. Host configuration value 1,
same device identity, unbound interfaces, and zero observed usbfs holders do
not directly expose that queue state. Therefore this review does not issue a
new execution clearance.

## Three different acceptance questions

The evidence becomes consistent once these questions are kept separate:

| question | present answer | reason |
| --- | --- | --- |
| Was BI a complete scientific stock-lifecycle recording under its predeclared contract? | **No.** | The forced vlog/export stop independently rejects it, and its action replay contains one `ret=-6` transfer. BO's later decode does not change the original contract. |
| Does the recovered `ret=-6`/retry sequence itself imply that the USB parser left header phase? | **No positive evidence of that.** | It is an I2C post-check retry after USB configuration; QDF obtains `e6`, advances, and has no reviewed vendor-bulk/parser-state edge in this path. |
| Is the fresh vendor endpoint positively proved to have an active 12-byte header receive? | **No.** | The firmware queues that receive by intent, but ignores the submission return; no retained live descriptor/queue observation binds acceptance. |

Thus “all physical I2C transfers returned 2” is stricter than the actual
known USB parser invariant. Dropping it for this phase analysis does not drop
the independent requirements of a fresh initialization premise, exclusive
vendor-OUT lineage, and fail-closed first transaction.

## Positive USB initialization control flow

The selected package is 5,242,880 bytes, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Image 0 uses `FILE = linked VA + 0x200`.

The source-backed normal path is:

1. startup VA `0x39a16` calls vendor initializer `0x2490c`;
2. the initializer installs endpoints `0x82` and `0x02` and registers the
   class table;
3. USB core broadcaster `0x28448` invokes slot `+0` of active class tables;
4. the vendor table's slot `+0` points to configuration callback `0x2945c`;
5. that callback installs the header pointer, stores state `+0x08 = 0`
   (remaining) and `+0x0c = 6` (idle/completed operation), then calls rearm
   helper `0x29500`; and
6. the rearm helper checks `6/0` and asks the OUT scheduler for exactly 12
   bytes on endpoint `0x02`.

The corresponding decisive slice hashes are:

| role | VA / size | SHA-256 |
| --- | --- | --- |
| startup window | `0x39a00 / 0x1a` | `1be8eb4f97bb2028d3ffe93a61dc0566e5021eeaae5044dd55af294752dbe722` |
| vendor initializer | `0x2490c / 0x58` | `fe0614e38e5ba9a93ea7b9e7f6713407c9f2abdc4fcce28d11448c8baee41ae2` |
| class broadcaster | `0x28448 / 0x4a` | `c4f064a989b3b50c08d280832b60792021494ac45e7b1ec65691a7981c46ff3b` |
| vendor configuration | `0x2945c / 0x88` | `7d0acce7e777be885ce0e87c205580f21a204dc38800d1d58a633405dda25748` |
| header rearm | `0x29500 / 0x34` | `19b640cf59ed8e61dbefe6e4d59ce3188f4d20be75e9d8d432bd483ada39561f` |

The packaged 18-byte USB device descriptor exactly matches the retained
`04e8:2001`, revision `0250`, one-configuration descriptor. Historical live
RAM also matched all six nonzero selected-generation vendor callback
pointers, including `0x2945d` and OUT completion `0x28cf1`. These are strong
identity/generation correlations. They are not a measurement that device
49 executed the callback or that endpoint `0x02` retained its descriptor.

## BI chronology and the recovered I2C defect

The retained BI lower chronology is:

| uptime | event | bounded consequence |
| ---: | --- | --- |
| `157460.889006..157460.914656` | USB device 48 disconnects | host observes disappearance of the old instance |
| `157462.402935..157462.551467` | USB device 49 enumerates with the same detailed identity and configuration 1 | fresh host control-plane configuration boundary |
| `157462.752223` | MODE2 PID 31720 begins its I2C tail | stock on-tail proceeds after enumeration |
| `157462.986311..157462.987034` | first `F3:01` post-check after setting `000330/c0` has no reply, `ret=-6` | one incomplete Linux I2C read; no USB operation is identified |
| `157463.000065..157463.000430` | stock retry returns `0000e604`, `ret=2` | exact expected checksum `e6` is recovered |
| `157463.000432..157463.000781` | ordinary pre-read succeeds, then setting `000334` begins | replay rejoins its normal command sequence |
| through `157463.071046` | 199 further PID-31720 transfers succeed | bounded recovery/continuation of this I2C sequence |

The checksum identity is exact:

```text
(f3 + 00 + 00 + 00 + 03 + 30 + 00 + 00 + 00 + c0) & ff = e6
```

The QDF retry is generic to a mismatching/incomplete post-check; BO correctly
does not assign a controller-internal meaning to Linux result `-6`.

The finite actor/source separation is also positive but bounded. The copied
QDF module's reviewed undefined-symbol census contains its four QDF I2C
entry points and no undefined name containing `usb`, `ssb`, or `bulk`. The
MODE2 record identifies PID 31720's failed and recovered transactions as
I2C bus 5/address `0x76`. No retained row identifies an SSB/vendor-bulk
client in that tail. This proves the recovered error path is not a *known*
vendor parser actor. It is not a whole-firmware theorem that an internal
controller fault can never reset a USB endpoint.

## What a controller I2C error can and cannot establish about phase

No reviewed source path makes a failed QDF I2C post-check decrement vendor
remaining length, install a write destination, or call the USB OUT completion
handler. On the retained execution, there is also no second host-observed USB
disconnect/re-enumeration after the failed post-check. The retry succeeds and
the stock replay continues. Consequently the one failure supplies no positive
reason to replace the post-configuration idle/header premise with an
operation-2 payload premise.

Two residual possibilities cannot be excluded from these records:

- an unproved internal coupling could reset or disturb the USB endpoint
  without a retained host disconnect; or
- the initial callback could have attempted the receive but the endpoint
  scheduler could have rejected or lost it, because its return is discarded.

The first is an unresolved global coupling, not evidence observed in BI. The
second is a concrete local source limitation and is the decisive reason that
active endpoint liveness is not proved.

## Closed-world lineage: useful but not self-authenticating

A fresh host ownership snapshot can establish same identity, configuration
1, unbound interfaces, and zero enumerated usbfs FD holders at a bounded
instant. The serialized action ledger can establish that **the reviewed
helpers** sent no vendor OUT after re-enumeration. Together they are relevant
to the no-intervening-OUT premise.

They do not establish a continuous global absence theorem. The FD census is
racy, an unrecorded privileged actor is not disproved, and process/driver
absence cannot reveal firmware queue state. A future decision must therefore
state the premise as “no vendor OUT in the recorded closed-world lineage,”
not “nothing could have touched the endpoint.”

BI's collector rejection does not erase the concrete USB48-to-49 kernel
chronology or the individually recovered I2C transaction. Conversely, those
narrow facts do not repair the collector's forced-stop/export invariant or
turn its unobserved portions into a global actor census.

## Exact remaining fact and safe route

For a strict, independently proved *pre-header* `ReadyForHeader` premise, the
missing fact remains one of:

1. a live read-only endpoint/descriptor observation showing endpoint `0x02`
   owns the active 12-byte receive at the header buffer on the fresh instance;
   or
2. positive live binding that the same-image configuration callback executed,
   plus a source/transport observation that its receive submission succeeded;
   or
3. an exact completed vendor transaction on that fresh instance whose
   terminal callback rearmed the next 12-byte header, followed by a carried
   closed-world no-transfer lineage.

No retained artifact supplies item 1 or 2. Item 3 proves the boundary only
after the first transaction; it cannot make that first transaction a passive
probe.

Without new instrumentation, the narrower risk-managed route already
identified in the reviewed stock-lifecycle decision remains the only bounded
route: require a fresh same-identity disconnect/re-enumeration/configuration,
fresh unbound/no-holder samples, a serialized no-vendor-OUT action lineage,
and then at most one unchanged fixed read. Its first OUT is justified only by
the conditional no-prior-payload premise, not by proof of endpoint liveness.
Any short count, timeout, error, identity change, owner/binding, or unknown
lineage is a terminal stop with no retry and no later header. Only an exact
OUT/IN pair plus modeled completion may establish the subsequent host
`ReadyForHeader` boundary.

This is a safe-route description, **not clearance for a current invocation**.
A future review must bind the actual post-reset instance, current closed-world
lineage, and unchanged helper. Fresh metadata alone is insufficient.

## Evidence pins

| retained source/evidence | SHA-256 |
| --- | --- |
| `stock-lifecycle-followup-20261027au/vendor-ready-boundary.md` | `f7352c2d26f9b61bed84409146dc45df998a4f4514c8c3884eefe22557273d8a` |
| `stock-lifecycle-followup-20261027au/practical-test-decision.md` | `9924085fdab24b5272db7916b5ecd662f3f2c7d6cba554343830c3d6e262e9cc` |
| `owner-repeat-recovery-20261027bi/lifecycle-review.md` | `78c90f141d75fd5b0da4cf2a5fba27f4eb69df2e4d42972936d66fae757def3f` |
| `stock-error-propagation-20261027bo/driver-error-review.md` | `117b1a814a125e6a342883fc9e8a4ac9d7eb630345bb6d41c79de44aec6b1dd4` |
| `stock-rt-lifecycle-trial-20261027av/baseline-and-lifecycle-audit.md` | `f3756c82257e8b0afcb327c4fc9a5436990cb55ea959a999859d00d9cdbb1088` |
| `tcon-research/qd-usb-device-descriptor-scatter-match-20261027.md` | `ec6d1c4edf55b4d7738422ecfbf2f141ac2ae6f35dcb3a00e2c861dec527ff64` |
| `tcon-research/ssb-device-read-protocol-20261027.md` | `6bafcfb45e95b18a3646b71e5da37a43df4a863e6368e57dfb808e139da7021c` |

