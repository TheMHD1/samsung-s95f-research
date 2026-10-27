# AC independent review closure

2026-10-27 UTC. Independent read-only instruction/math audit and final correction recheck PASS, no remaining material issues. The reviewer checked both consumer bodies, cap helpers, fixed input/source relationships, record bindings, filters, prefix/cap mapping, lane/bin tie rules, float-factor reuse, terminal-bin behavior and final output selection. No target/network/write action was made by the reviewer; root records the returned review here.

The initial report's live-domain subtraction wording was corrected: boundary subtraction wraps modulo2^32, relevant max/min/interval comparisons are unsigned, and a zero earlier live boundary can underflow even though the stored sequence avoids it. Fixtures now cover these underflows, fractional scale factors and host binary32 rounding. The host conversion model now rejects exceptional/out-of-range cases instead of silently masking them. The report explicitly distinguishes that limited model from ARM exceptional conversions and uncaptured live floating-point control.

Final verifier SHA-256 `95056ef66c853a107a9af9433ca780cb9d2fa44ac11eb7f272772660ac6060c7`; report `a1ee1f4653ea45979a266a22a2edaf2747aed36306612ff156facf0d9e018c57`. Normal/optimized outputs are identical SHA-256 `bd21c54cddab0c2245e68e34a68d952067a6f49c520f015bb089e4057988af0d`.

This proves selected-code numerical roles, not source units, live inputs, actual execution or physical causality. In particular, NPC_AP outputs+56/+58/+5a must not be conflated with the distinct NPC_AP+16/+18/+1a divisors read by the first AP_EXCO helper.
