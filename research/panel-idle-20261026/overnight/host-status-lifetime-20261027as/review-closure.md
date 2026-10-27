# Independent review closure

Reviewed read-only on 2026-10-27 UTC. No TV, network, USB, root-agent,
firmware, UI, or instrumentation operation was made by this review.

## Final reviewed pins

- `status-lifetime.md`: SHA-256
  `3bc6c3c41b9e331af55f6271ebf3ad263fb5dc14e074839fbe4554efe9ee9d51`
- `verify-status-lifetime.py`: SHA-256
  `67fcfd86f287ed552dd4f3b2b06141d26817b74a62f1aa0aeafd42e7c642a486`
- normal and optimized verifier output: identical, SHA-256
  `bfddca54a077656edd49ec1ba8a8fd1106a2623fe79b90a28d4d243bae715785`

## Result

PASS within the report's stated bounded, packaged-code scope. This is not a
formal whole-firmware semantic or mutation-completeness result.

Independent byte and instruction checks confirm:

- the fixed accessor returns CPU `0x2000f0e0`, so status `+0x10` is
  `0x2000f0f0`;
- reset scatter row 11 has destination extent
  `[0x20000f4c,0x20017384)`, which contains both status bytes;
- the `AP` registry row, type-4 metadata, zero source halfword, and direct
  startup-wrapper -> type-4 enumerator -> loader chain are internally
  consistent;
- the successful first-copy path takes the smaller first length, gates the
  copy on lower-read result zero, constructs the destination using the table
  base plus record offset, and calls the copy helper;
- setter `0x2b764` replaces the complete low 16 bits and has the one recovered
  direct caller inside common entry `0xb660`;
- the four immediate selector-zero calls and their strings are exactly the
  reported INA/PMIC sites; and
- main startup's direct calls have the reported lexical order. That order
  does not prove a common-handler return or that a pre-loop selector-`0x10`
  execution and the later PMIC zero site can coexist in one startup.

Normal and `-O` runs reproduced identical output with ten focused mutation
rejections and `target_operations=0`.

## Review corrections retained

The initial report/verifier had four material review findings:

1. It described the accessor census as conservatively merging branch paths,
   but the implementation is a linear instruction-order walk. The final
   report now says it can both miss feasible paths and overapproximate
   infeasible sequences.
2. It implied the later PMIC zero path could overwrite an earlier pre-loop
   `0x10` based on static call order alone. The final wording makes this
   conditional on `0x10` still being retained when the zero site actually
   reaches the setter and explicitly disclaims co-occurrence/return proof.
3. With package identity disabled for mutation testing, changing the type-4
   gate at VA `0x756a` or the copy call at VA `0x6258` to NOPs was initially
   accepted. The final verifier pins the dispatch, first-length minimum,
   successful-read gate, destination/copy slice, and targets, and rejects
   those mutations.
4. The first corrected revision still accepted removal of the wrapper's
   `BL 0x7544` at VA `0x7492`, disconnecting startup from the type-4
   enumerator. The final verifier pins that edge and rejects the corresponding
   mutation.

The final claim remains deliberately limited. The 223 values are
decoder-recognized accessor callsites, the ten `+0x10` candidates come from a
bounded linear heuristic, and the 62 apparent call escapes are not an
exhaustive escape list. Computed aliases, indirect calls, bulk copies, DMA,
missed control-flow paths, and external agents remain outside the proof. The
packaged reset/configuration paths do not prove current-boot execution or
runtime load success, and the setter is not established as the global sole
writer.

The report also correctly confines the earlier unproved zero statement to
the stock selector-8 getter. It does not promote the separately audited raw
RAM zero, establish a raw zero-to-`0x10` transition, identify a writer, or
claim physical panel state.
