# Complete main firmware extraction — 2026-10-28

All nine sections of the official T-RSMFAKUC-0090 main firmware were decrypted and retained privately: platform.img, uImage, factory_peq.img, secos.bin, seret.bin, secos_drv.bin, dtb.bin, ddr.init and sign.bin. Their original sizes total 1,493,534,000 bytes. Every section's complete ciphertext RSA signature was independently verified using the pinned installed public key; each decoded section passed exact original size, canonical sixteen-byte PKCS7 padding and the authenticated tag18 original-byte CRC. The companion TB-RSWF4AKUC package is acquired but its cryptography and payloads remain unqualified.

## Final platform run

CX02 used the pinned CX portable managed helper, CG streaming core, CJ certificate-pinned/nonce-authenticated TLS transport and CW prepared-inline lifetime adapter. The native sequence ran command0 once, 22,209 command1 updates, and command2 once. Full ciphertext/raw output: 1,455,423,504 bytes. Original platform image after padding removal: 1,455,423,488 bytes. Native elapsed555190ms; 22,215 guards, input SHA256/EOF and exact output counts passed. Session closed, three shared buffers released, context finalized, owned buffers wiped; zero backend exceptions, uncertain ownership or cleanup failures. Supervisor exit0, no deadline, one native launch, zero native retries. The host bulk channel accepted one connection and one raw completion.

## Original wrapper rejection and separate reconciliation

The original DA wrapper rejected its status parse. It must not be reported as having passed. A runtime garbage-collection print was interrupted by the complete native status row: the byte sequence `[GC_INFO] GC_` preceded the status; `Start #3012...` followed its terminating newline. The exact-prefix GC line filter hid the native status, leaving the trailing GC fragment. This happened after successful native exit and complete raw transport.

A separate bounded, authenticated root read recovered and hash-checked the immutable 345471-byte raw stdout. It contains exactly one complete 385-byte native status row at byte interval [344064,344449). The reconciliation extracted these exact bytes and applied the unchanged strict DA native-field validator. Removing just that row including its newline restores every remaining byte as 3020 complete GC Start/End pairs, with exact sequential IDs, matching generations and nondecreasing timestamps. No arbitrary output was discarded and no decryption command was rerun.

The independent host original-byte validator then checked strict16-byte padding, exact size and authenticated CRC and copied the accepted original privately. Reconciled result explicitly records `original_driver_accepted=false`, `reconciled_native_receipt=true`, `native_reinvoked=false`. All exact job files and the target CX stage were subsequently removed through two guarded cleanup calls. Private raw logs, authentication receipts and OEM output hashes stay outside the public release.

## Rejected startup attempts retained

CR/CM01 never reached its supervisor/child/native marker: Samsung UEP refused `/bin/sh worker.sh` as an unsigned script file. The host saw zero TCP connections and a positive UEP rejection. A fixed-argv process census was empty. The failed CR stage remains retained as diagnostic evidence.

CX/CV01 never dispatched the inline worker. Its stored script hash checks refused a root transport quoting change: child length1280→1281 and worker2882→2884 because printf newline escapes were doubled inside nested single-quoted data. The root-agent source at SamsungTvRootAgent.cs343/601–603 explains this QuoteArgument behavior. Parent recovered exact failed bytes and hashes and removed only the three known prelaunch files after closed-world guards; the five pinned helper inputs remained. The changed CW implementation prepared the same scripts through four bounded Base64 data writes, checked byte counts/hashes, then launched the short fixed inline command once. This was a new explicitly changed and reconciled preparation path, not automatic repetition of an ambiguous native operation.

## Reproduction and further work

The original foreground and background runners, source manifests, code ancestry, mock/native failure tests and separate reconciliation script are retained. They are fixed to this model/build/boot and local private configuration; they require rebuilding and review for another target. Future long helpers should write an exclusive private structured status file or dedicated descriptor after cleanup, independent of runtime stdout, to prevent GC interleaving from becoming an evidence problem.

No firmware was installed, flashed, modified or executed as downloaded code. No controller vendor USB, UI/power action, watchdog/protection change, kernel patch or permanent root change was part of this extraction. The content-dependent blackout root cause and permanent prevention remain open. Next work is offline partition/filesystem extraction, comparison against installed artifacts, and identification of controller firmware/configuration and missing producer paths. `firmware-kernel-analysis-20261028cs` already proves exact kernel identity and provides candidate DTB wiring evidence; `firmware-platform-analysis-20261028db` and `vdfs-reader-research-20261028dc` cover the separate GPT/VDFS stages.
