# Firmware identity and acquisition work log

This directory continues the owner-authorized panel-blackout investigation.
Read progress.md first. The owner explicitly accepts protection changes and
flashing if needed, while asking to avoid bricking the TV. The current work
establishes the actual stored image and a reliable acquisition path before
choosing a patch. There is no verified permanent fix or physical recovery.

Completed so far:

- Six fixed512-byte reads, all exact and cleaned up, with raw root records.
- One fixed8192-byte prefix read, exact and cleaned up, repeating prior sectors.
- An instruction-bound current returned-code check, separate from the package.
- Offline full and32KiB-probe helpers, each45 tests and independently reviewed.
- Host retrieval/orchestration work, including finite/no-retry behavior and
  retaining the stage on any failure. Both multi-IN requests completed once.
- Earlier41/90/260-file manifests reverified unchanged.

The full5MiB helper is a single large protocol request. It is not the stock
backup's640 individual headers. Its first device transfer spans24576 bytes;
the host consumes three8192-byte reads before a continuation. The32KiB probe
must establish that first boundary before the full run.

Final checkpoint:145files /33,070,645bytes in
firmware-acquisition-evidence-manifest.json, SHA256
e1f11fe681fa6047ba995a796315b712428ff75c415b3e9042d7e52127960d0f.
All manifest entries are frozen; this README and CURRENT-INVESTIGATION.md
remain mutable navigation. Probe/full retrieval compatibility failures and
all recovery provenance are retained. The final5MiB image is
full-backup-recovered/fixeddata.bin, SHA256
f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562.
Both private stages are absent and no helper remains running.

If a request stops early, USB interface release/FD close does not abort the
controller transaction. Preserve the stage and all records; do not send a new
header or retry. Re-enumeration/reboot and state requalification are required
before later acquisition. A protocol timeout alone is not a reason to flash.

Native helper source/build artifacts are now immutable for review. Root owns
the directory-level audit/scripts and current navigation entry. Independent
reviewers make no TV calls. Source hashes, all raw transport responses, staged
upload reconstruction and extracted bytes are the authoritative evidence.
