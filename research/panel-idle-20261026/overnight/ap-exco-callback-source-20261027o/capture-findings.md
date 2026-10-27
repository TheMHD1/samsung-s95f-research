# Corrected callback-source read: pointer and numeric fields corroborated

Recorded2026-10-27 UTC. One independently reviewed invocation used final
manifest48b202a87cd714dab866a32cb36cb716a65cdec6745519463a346bab9d35f00a.
It completed on boot34f419d2-6256-4e1f-a7a9-8d46b875857d with terminal
uptime123267.81. Its19 authenticated root calls retain the preceding47-case
native self-test, one native execution, six exact bulk transfers, terminal
ReadyForHeader, successful release/close and STAGE_ABSENT cleanup. No retry,
UI action, reset, firmware/code/configuration write or physical observation
occurred. A separate runtime review is retained in this directory.

| fixed bus window | bytes | SHA256 |
| --- | ---: | --- |
| 470002c0 | 32 | 7634f63e1eace3b6da5f287655f1b1ef3ebdb81b22909605a467c2472af43cd3 |
| 450158a8 | 16 | 21f2234ff842c398b65210295a7a5e15220503bc73240a0eb68e4b897929db47 |
| 45015c70 | 32 | eb1b55a1e4f19a403134f7ddc3a4f7f3853f50ef06cb9b9e74a5659f6183323f |

The pointer word at the first window's offset0c is450158a8, matching the
corrected distinct-registry AP_EXCO object. The complete pointer window is
identical to the earlier M capture. Transport and the conditional local
pointer binding are both accepted. This is not a whole-core or PC proof.

The source16 bytes are:

```text
030a1100000000000000010000010000
```

The source tail32 bytes are:

```text
f00093239223fe000a00fa000700000001010001000000000200000000000000
```

Exact raw decoding yields:

| source field | returned position | value | selected callback use |
| --- | --- | ---: | --- |
| object+0 | base[0] | 3 | copies to context+6c8 |
| object+1 | base[1] | 10 | separately loads r8; field meaning unassigned |
| object+3d8 | tail[10 hex] | 1 | copies to context+6c7 |

The tail starts at object+3c8, so its offset10hex is object+3d8. The
previous inherited offset0c is not used. All bytes fit inside the positively
recorded3ec-byte object. Root independently recomputed hashes and offsets
from the raw files, rather than trusting only native decode fields.

The3/1 source values agree numerically with the earlier saved candidate
context pair, acquired at terminal uptime119358.55. That context sample was
3909.26seconds earlier; the source read is not an atomic source/mirror tuple
and does not prove that a callback copied these bytes at either instant.
V6 ended at115907.45,7360.36seconds before this terminal sample. No exact
V6 compare operand, selected limit or physical blackout timestamp is recovered.

This closes the narrow ordinary source-object interpretation: the relevant
callback source is the distinct AP_EXCO object, not the ordinary raw blocks
whose selected bytes were20/0. No ordinary-object default comparison is made
or required. The newer N code-view fingerprints corroborate the exact getter,
predicate and startup bodies, without proving a corePC or writable code.

The current numeric hypothesis remains a limit crossing in the reconstructed
stateful count calculation. This capture does not establish the electrical
meaning of sampled lanes, why a count crossed its limit, a software repair,
or a physical recovery/prevention result. No helper remains running.
