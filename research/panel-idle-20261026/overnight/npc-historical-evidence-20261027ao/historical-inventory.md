# Historical NPC_AP and F3 evidence inventory

Recorded 2026-10-27 UTC. An independent read-only inventory and root recheck
scanned71 files named record.json under overnight. The scope is explicit
request/requests metadata with fixed addresses; it is not an exhaustive
analysis of every binary, free-form command, log, indirect address or absent
record. No target, network, USB or new instrumentation operation occurred.

Eight records declare target101 reads in the selector-zero0x45 address
domain. Their ranges are below; all paths are relative to overnight.

| Record | Declared 0x45 ranges, start/bytes |
| --- | --- |
| ap-exco-callback-source-20261027o/capture-once/record.json | 450158a8/16;45015c70/32 |
| ap-exco-input-snapshot-20261027w/capture-once/record.json | 4500ff14/824;450158a8/1004 |
| ap-exco-source-read-20261027m/capture-once/record.json | 4500ff14/16;450102e0/32 |
| executing-image-identity-20261027e/callback-alias-read-once/record.json | 45000580/64 |
| executing-image-identity-20261027e/common-error-guard-read-once/record.json | 4500f0c0/64 |
| executing-image-identity-20261027e/main-log-index-read-once/record.json | 45000e20/64 |
| npc-ap-divisor-snapshot-20261027ak/capture-once/record.json | 4500d730/8 |
| npc-ap-divisor-snapshot-20261027ak/capture-ordinary-after/record.json | 4500ff14/824;450158a8/1004 |

Only AK's eight-byte read intersects the qualified NPC_AP allocation
[4500d71c,4500dc5c). No broader accepted live NPC_AP operand/control capture
was found in this bounded inventory. This does not prove universal absence.
Different0x47-core views are not promoted into selector-zero NPC aliases, and
packaged NPC0x5843 data/type4 NPC_AP defaults are not live RAM observations.
Some historical records have rejected or corrected semantic interpretations;
listing a declared range does not upgrade their acceptance status.

## Two historical F3:128 readings

Two accepted/read-usable records preserve operation19 fixed selector128
results on boot34f419d2-6256-4e1f-a7a9-8d46b875857d:

| File | Execute uptime | Recorded result |
| --- | ---: | --- |
| sleep-investigation-20261027a/controller-duty-once.json | 93210.81 | kernel_output_written;207 |
| sleep-investigation-20261027a/stock-mode2-trial/post-duty.json | 94430.42 | kernel_output_written;207 |

Both preserve PAYLOAD_AFTER=00000013,000000cf,0000f300,00000128 and
close0/errno0. File SHA-256 values are respectively
`4944dd3fe9f47b3d15ca5618b0fc4a203271b0edd5910049d11c6a6d4f8231cc`
and `b3a2e6939efe8ff8ca4198c4bab6874b51e7ae15288463604371327ecaebf299`.

The later reading precedes AK's native read start131155.397966259 by
36724.977966259seconds (about10.20hours). It is a same-boot historical
host/controller scalar result, not a raw NPC_AP+a6 RAM sample or proof the
selected store executed. Combining historical207 with AK118 cannot establish
an active factor, nonlinear transfer curve, branch choice or fault-time cause.

The accompanying inventory.json retains the exact eight record hashes and
parsed ranges from the root recheck. It is a descriptive census at this time,
not a publication/freeze of the entire evidence corpus.
