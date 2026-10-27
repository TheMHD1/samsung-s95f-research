# AZ: controller-output attribution and ordinary command mapping

Recorded 2026-10-27 UTC. This follow-up uses retained files and public vendor
documentation. No TV command, controller access, UI action, power operation,
register write, new target collector, firmware change or flash was performed.

## What the ordinary code adds

The [ordinary-use trace](ordinary-io-usage.md) finds positive uses of all four
hardware addresses outside the selector-0x10 emergency action. The selected
image's pre-loop initialization writes the same addresses, and three exact
emergency address/value pairs also occur there. The source also provides a
six-block indexed configuration/status interface spanning bases
0x40130000..0x40135000, with selected configuration nibbles and a selected
status bit.

This changes the interpretation of the emergency stores: they reuse a broader
control interface rather than identifying dedicated emergency-only registers.
It does not prove the stores are harmless, that the complete sequences are
equivalent, or that they preserve light. Initialization may itself run before
light is enabled. In particular, startup value8 and emergency value0x10 at
0x4013400c cannot be interpreted as replacing a state, setting a bit or
commanding a physical signal without the register contract.

Root independently replayed the ordinary-use checker and disassembled the
indexed status/configuration bodies and the relevant initialization stores.
The complete selected package is hash-pinned; these are selected-code facts,
not new live execution observations. The producer's normal and optimized
checker outputs are identical.

## What the hardware documentation adds

The [finite primary-source search](primary-map-assessment.md) did not find a
vendor register map satisfying both a matching multi-address layout and a
positive fitted-silicon identity. Partial address coincidences belong to
different documented layouts and cannot name this controller's registers.
The owner-photo board map identifies the boards and cables but provides no
readable silicon marking under the relevant shielding.

The four addresses therefore remain unnamed controller MMIO. The source's
banked structure is more concrete than the previous isolated-address view,
but it does not supply a panel-enable, reset, bias-rail, scan, timing or PWM
binding. GPIO-related text elsewhere in the image does not name the exact
helpers by proximity.

## Ordinary mute command: positive receiver mapping

The [ordinary mute receiver trace](ordinary-mute-receiver.md) follows the
existing host-wire correction into the selected image's parser. The exact
host read uses F3:00 with selector0x164, not the F3:80 small status table.
The preliminary concern about an unsupported selector is therefore rejected;
no controller-side prefix normalization is needed. Root independently
disassembled the host command construction at module text+0xcfa8 and the
selected getter, setter and small fixed-copy leaf.

The source read returns1 only when bits23:22 of word0x58200060 equal2. Raw
values0,1 and3 all return0. The reply is a normalized predicate, not the raw
two-bit state and not a measurement of panel light.

The selected setter is also different from a symmetric register write: zero
and one enter the routine with literal `Failmode:%d`, which changes the
derived MULTI/AP_EXCO object at+0x80. Both branches force bit2; one sets bit3,
while zero clears bit3, clears a separate RAM word, and copies two saved RAM
words to0x58300000 and0x58300018. There is no direct store to the getter's
word in this bounded setter chain. Its downstream staged-word consumer is
not established by this pass. These are source dataflows, not a proposal to
force either register block.

Root independently reused the hash-pinned W, AK and AW derived windows and
their cc-pointer gates. All three contain00000000 at derived+0x80. The
[retained-word record](retained-failmode-word.json) preserves file hashes,
pointer hashes, offsets and broad capture ordering. None contains the
setter's immediate bit2=1 pattern at that late time. This does not prove
that no setter ran: a consumer, another writer, initialization or an
unqualified executing-image difference could explain the late value. No new
target read was performed.

## Diagnostic consequence

The measured controller fault and reconstructed emergency path remain useful
evidence. They do not yet identify the final physical action that removes
light or show whether hardware collapse precedes a software response. The
ordinary use of the same addresses prevents assigning shutdown semantics
merely because the emergency path writes them.

The outstanding physical test remains a fresh RT observation paired with a
confirmed lit or black panel, followed by one annotated transition if a lit
control is available. A software screenshot, cached display-on value or old
clean RT sample cannot substitute for that observation. Neither the new
source evidence nor owner permission alone identifies a justified patch.

The source-based meaning of the ordinary mute reply is now narrower and more
precise. Future records must distinguish its normalized reply, staged-word
updates, transport completion and physical light. The next bounded source
lead is consumption of the staged+0x80 word; a late zero alone cannot provide
that execution evidence. Both source reproducers pass normal/optimized runs.
No runtime fix, prevention or physical recovery is established here.
