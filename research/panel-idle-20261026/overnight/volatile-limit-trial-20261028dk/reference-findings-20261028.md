# Fixed-reference capture: narrower input evidence

The source-qualified DT reader actually completed a normal Apps baseline and a
separate postfault snapshot. Each accepted14exact read pairs/28bulks, with
ReadyForHeader, release, close and exact cleanup. Between them, the frozen DP
recorder completed its same unchanged40 Apps/header/one-Left trial: five clean
cycles, fault incycle6,48headers/96bulks. No threshold or controller-code write
occurred. These are software observations; physical light was not independently
verified while unattended.

Both baseline fixed-reference windows contained104zero bytes. After the fault,
the top and bottom windows contained different packed sample data. All41
source-compatible retained candidates had row-like2159/channel-like0 and unique
12-bit amplitude candidates B+Diff matching the later bottom buffer exactly.
None matched the corresponding later top value.

| Column-like x | New later bottom | New later top | Candidate records |
| --- | ---: | ---: | ---: |
|570 /571|1857|2168|6 /6|
|622 /623|454|2160|0 /0|
|624 /625|3053|2149|8 /7|
|632 /633|1717|2157|7 /7|

The previous DM-only fault capture had conditional amplitudes1861,550,3052,
1718 at those groups. In particular, the previously qualifying622/623 group
had B0 and implied amplitude550. Substituting454 with the same B0 gives a
difference454, below the strict500 threshold. More generally, for any low-band
B in0..499, abs(454-B)<=454 and cannot pass that difference test. This explains
why the new reference value is compatible with the group's absence. **The new
B values for absent lanes were not recorded**; high-band B, scheduling/masks or
other eligibility changes remain alternatives. The value alone does not prove
causation or exclusion.

The new DP last-clean A0 was28, not38 from the previous run. Postfault A0 was42;
last-clean source count2/history[0,2,0,2] changed to count0/history[2,0,2,0].
Ordinal0 changed32→41. Keep this run separate from the earlier38→42 run.
These are sequential sampled states, not the exact intervening dispatch trace.

The match materially supports the bottom-reference hypothesis. It still does
not directly log the historical selected-A pointer, B header, channel/epoch or
physical meaning of those packed units. The arrays lack type/epoch tags; the
later fixed buffer can change independently. DS maps exact potential execution
checkpoints for those missing facts, with explicit unresolved deployment and
rollback obligations. No executable hook was installed.

The controller remained on USB59 and continued answering the accepted postfault
reads. There is no re-enumeration in this captured software fault itself. The
state is compatible with a latched stop/gate closure rather than a required
controller reboot; it does not classify every earlier physical blackout or the
separate Screen Optimization maintenance cycle. Only the subsequent deliberate
stockMODE2 recovery disconnected59 and enumerated60.

After preserving the records, normalRight selected Apps and one separately
recorded bounded stockMODE2 request passed. USB60 cached identity/census was
retained. The next DM read verified clean stop0/fault0/gate1 and actual limit40,
with scan1. That immediate snapshot had aa0/ac1, alternate upper3161, normal
upper3200 and scaled diagnostic24: an initialization/other-mode context that
would fail the proposed mode1 writer guard. Shared diagnostics therefore cannot
be treated as proof that both endpoints are always simultaneously refreshed.
The static source-derived dynamic-profile model remains under review.

The parent checked a suspected review-file race. Actual saved readiness already
pins the final independent review validation and all referenced hashes match;
no readiness drift or rejection occurred. Both preliminary and final review
versions remain separately retained. See reference-baseline-provenance-consistency.json.

No persistent hook, boot/network modification, flash or prevention fix is
established. Latest target boundary is completed DM reference-recovered-clean-01
onUSB60, with no subsequent vendor operation at this report's creation.
