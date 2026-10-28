# Offline reproduction

Python 3.10+, Git and a C11 compiler are sufficient for the publication checks and minimal SWU host mock. The exported research uses other optional packages and .NET SDK versions as declared in its individual projects. Private OEM fixtures and target access are not bundled.

```sh
python3 -m unittest discover -s tests -v
python3 tools/verify_public.py --check-git
python3 tools/verify_onset.py
python3 -O tools/verify_onset.py
mkdir -p /tmp/s95f-public-host-test
cc -std=c11 -Wall -Wextra -Werror -Wpedantic -O1 -g \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  research/research-20261027-external/sources/minimal-swu-helper/test_host.c \
  -o /tmp/s95f-public-host-test/swu-host-test
/tmp/s95f-public-host-test/swu-host-test
```

This mock exercises a supplied operation storage layout and a fake backend, command sequence 0/1/2, failure cleanup, output-capacity bounds and plaintext quarantine. It does not load a vendor library, invoke TEEC or contact a trusted application. The legacy `offline_validate.py` in the retained helper directory needs omitted acquisition fixtures, so a fresh clone cannot run its original `make check` in full. No target acceptance is inferred from the C host test.

The optional `--check-git` release check requires a Git clone or staged release checkout. It verifies complete manifest membership and exact staged bytes, including files a global ignore might otherwise hide. An unpacked source archive without Git can run `verify_public.py` without that option, but cannot establish Git packaging completeness.

To inspect a report's lineage, find its `public_path` in `manifests/source-dispositions.json`. `source_sha256` identifies retained pre-redaction bytes; `public_sha256` identifies public bytes. Original hash assertions inside retained scripts refer to the original acquisition and will not necessarily match redacted public artifacts. Do not update those assertions merely to make a live experiment run.

The public CB verifier consumes only `fixtures/onset-cb.json`. It independently decodes the six retained R windows, checks all 18 exact controller-window hashes and lengths, verifies fixed read addresses/transfer times, and reconstructs the counter and key-ordering facts. Eleven damaged/overclaimed variants are rejected by the publication tests. It does not import retained deployment tools, require credentials, or reauthenticate private root records. Its scope and physical-timing limitations are documented in the [evidence update](update-20261028.md).

The firmware acquisition/inspection tools under `research/firmware-acquisition-20261028/` require an independently acquired official archive/MSD input. Hashes and official source URLs are provided, while OEM bytes are excluded. Acquisition is an explicit network operation and is never invoked by publication checks.

## Bounded RTP scientific fixtures

`python3 tools/verify_rtp.py` reproduces the first unchanged-limit40 DP score and DM record observations. `python3 tools/verify_reference_rtp.py` verifies the separate later DT baseline/onset/fault reference comparison. `python3 tools/verify_limit_rtp.py` checks the distinct reversible set200/restore40 experiment and its two clean observations. All work from a fresh clone without original firmware, authentication or device tooling. Their raw subsets contain only bounded controller arrays, compact checkpoints, monotonic scientific times and source provenance; original transport/readiness acceptance is not reauthenticated. Repeat with `python3 -O` and run `python3 -m unittest discover -s tests -v` for damaged-evidence and privacy-schema refusals. Read the [scope and findings](rtp-records-20261028.md) before interpreting a match as historical branch execution, physical causation or prevention.


## Pure reference-refresh models

The [reference-refresh guide](reference-refresh-20261028.md) lists four original pure-model suites for selector edges, two-event copy counting, table arithmetic/lifetime and mock coordination. `tests/test_refresh_models.py` runs them from the public tree in normal and optimized Python without private acquisition inputs or a target adapter. Source-audit and actual-capture replay scripts retain their original private-input requirements; successful public model tests do not establish runtime call coverage.

The [reference-event guide](reference-events-20261028.md) adds two pure host-model suites to the publication tests: EK single-lane design ownership/phase boundaries and EQ stock gate/trainer controls. They run normally and with `-O` without OEM images or a target adapter. Their passing models do not qualify a deployed writer. Actual-capture analyzers retain private input dependencies and are not claimed to replay from the public tree.
