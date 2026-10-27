# Offline reproduction

Python 3.10+ and a C11 compiler are sufficient for the publication checks and minimal SWU host mock. The exported research uses other optional packages and .NET SDK versions as declared in its individual projects. Private OEM fixtures and target access are not bundled.

```sh
python3 -m unittest discover -s tests -v
python3 tools/verify_public.py
mkdir -p /tmp/s95f-public-host-test
cc -std=c11 -Wall -Wextra -Werror -Wpedantic -O1 -g \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  research/research-20261027-external/sources/minimal-swu-helper/test_host.c \
  -o /tmp/s95f-public-host-test/swu-host-test
/tmp/s95f-public-host-test/swu-host-test
```

This mock exercises a supplied operation storage layout and a fake backend, command sequence 0/1/2, failure cleanup, output-capacity bounds and plaintext quarantine. It does not load a vendor library, invoke TEEC or contact a trusted application. The legacy `offline_validate.py` in the retained helper directory needs omitted acquisition fixtures, so a fresh clone cannot run its original `make check` in full. No target acceptance is inferred from the C host test.

To inspect a report's lineage, find its `public_path` in `manifests/source-dispositions.json`. `source_sha256` identifies retained pre-redaction bytes; `public_sha256` identifies public bytes. Original hash assertions inside retained scripts refer to the original acquisition and will not necessarily match redacted public artifacts. Do not update those assertions merely to make a live experiment run.
