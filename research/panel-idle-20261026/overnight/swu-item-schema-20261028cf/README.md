This directory is the host-only CF schema/call-map checkpoint for the exact retained SWUCoreTV and the authenticated CE header. It does not contain a target runner and never loads the OEM ELF.

Read `schema-call-map.md` for the 21 recognized descriptor layouts, exact CryptoInfo candidate/copy chain, actual nine-item reconciliation, and separate ciphertext RSA/original-byte CRC scopes. `schema-evidence.json` pins 71 decisive ELF byte anchors. `item_schema.py` parses only the bounded signed OUIT span; its structural flags never assert authenticity or full policy validation.

`apply_authenticated_header.py` is a fixed-input host analysis of the already retained authenticated header, installed public PEM and original MSD. It verifies the header CRC/RSA, all nine encrypted section signatures and file hashes before writing the private plans. All data remains local. Its private outputs contain salts, signatures and lossless metadata, and are mode 0600 in a 0700 directory. They are excluded from any public export. Python storage is not wipe-qualified.

The private execution-plan input is `private/section-descriptors.json`: nine records in numeric directory order. Every record includes the actual name/ID, original and encrypted sizes, MSD offset, ciphertext SHA256, salt8, signature256/public-key ID, expected original-byte CRC and explicit scope, exact inherited CryptoInfo and command-0 parameters, fixed master/selector binding, and source file pins. `payload_plaintext_validated` and `execution_qualified` remain false. The first small candidates are sign.bin (1040 encrypted bytes; 1024 original) and ddr.init (166416 encrypted; 166400 original); a small whole-item success does not validate streaming larger items.

Verification commands, run on this host only:

```
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_item_schema
PYTHONDONTWRITEBYTECODE=1 python3 -O -m unittest -v test_item_schema
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/tcon-capstone python3 pin_evidence.py
PYTHONDONTWRITEBYTECODE=1 python3 apply_authenticated_header.py
```

Eleven synthetic parser test methods pass normally and with assertions optimized away. The fixed actual-input analysis independently verifies the selected 4027-byte envelope CRC, SHA512/PKCS1 header signature, complete 68-node tree, all nine numeric processed intervals, whole MSD and section hashes, and all nine ciphertext RSA signatures. Zero ciphertext CRCs match the original-item tag-18 CRC. No section plaintext is available to CF, so original-byte CRC/padding success is not claimed. `host-validation.json`, the test logs and safe `host-authentication.log` retain outcomes.

A centrally coordinated extraction test still needs the separately reviewed fixed-input adapter/engine, selector and library drift guards, original-capacity checks, exact output count, complete strict padding/CRC validation, bounded timeout, cleanup and wipe. This work implements no firmware update, flash, write bypass, plaintext key export, arbitrary TA command or retry. Signature authenticity is relative to the pinned installed 2048-bit key; ordinary CRC or wire structure is not signature authentication, and full metadata policy validation remains incomplete.
