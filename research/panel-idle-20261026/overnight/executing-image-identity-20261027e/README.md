# Live controller identity and CPU/DMA namespace investigation

The complete 5 MiB storage reply is retained and frozen in
`../firmware-fingerprint-20261027d`. Its first image reports build241205A,
whereas the selected packaged image reports241230A. Storage content does not
by itself identify code executing on this boot. The storage read leaf also
does not expose its underlying fresh-read status.

## Actual live reads

1. A single target0x101/address0x20000580/length64 read completed with exact
   transport and cleanup, but returned all zeros. It used the CPU namespace,
   not the USB DMA alias. It is inconclusive; it does not show that the
   CPU callback table is zero. Raw evidence is in `callback-read-once/`.
2. A separately reviewed single read at DMA address0x45000580 completed with
   exact OUT12/IN64 and cleanup. Its eight callback words at offset+0x0c are
   `2945d 293d1 294fb 0 0 28b85 28cf1 294f5`. All six nonzero discriminators
   match the packaged241230A initializer, and differ from the stored241205A
   initializer. Raw evidence is in `callback-alias-read-once/`.

`verify-callback-initializers.py` reconstructs both initializers.
`verify-dma-alias.py` verifies the mapper and storage-to-USB buffer dataflow.
`audit-callback-reads.py` authenticates envelopes, reconstructs uploads,
replays the exact deployment commands offline, and checks transport, returned
bytes, expected callback words and cleanup. `callback-runtime-audit.json`
records the results. No second read or reset was needed for either run.

The running RAM callback generation is package-compatible at this observed
location. This is not a proof that every running code byte equals the package,
that the complete stored image is correct, or that the panel is physically lit.
Tracing must keep active callback evidence separate from stored-code offsets.

## Next fault-state discrimination

Read-only fixed-address candidates target known RAM objects: the secondary
root/gates and the main controller common-error object. They are intended to
distinguish an emergency-loop hypothesis from ordinary servicing; field values
alone cannot prove the instantaneous program counter or the blackout cause.
No candidate runs until its exact address, length and native helper are checked.

No protection bypass, flash, EEPROM write, kernel modification, new reset or
physical repair was performed in this block. Owner authorization now permits
considering such interventions, but no specific firmware repair is established.

## Frozen evidence milestone

`live-controller-evidence-manifest.json` freezes167 files /13,379,142 bytes.
SHA-256: `63162c7d8c44e6090a9b2c2d8646811152b6fb1d19db6a6d1770ea0ba0464fd6`.
Publication and optimized verification passed. Parent D4 and D3 snapshots
were verified unchanged immediately before publication. Only this README
and the root CURRENT-INVESTIGATION.md remain mutable summaries.

Use `evidence-index.py --verify` for read-only validation. Do not rerun the
audit/checker scripts which rewrite reports inside this frozen snapshot.
Further logger implementation and experiments belong in
`../volatile-logger-qualification-20261027f`; no volatile logger write or
physical repair is established by the D5 snapshot.
