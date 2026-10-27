# Independent review: sleep evidence-index generator

Reviewed offline on 2026-10-27. This review examined the current
`sleep-evidence-index.py` at SHA-256
`fb16cb3ad5ff73857bf1bf4953ba2fd2344a4e82c1c5536f097eb627ae8d0c07`.
It ran only inventory and temporary-fixture verification checks. It did not
publish, create, replace, or verify a production manifest, and made no TV,
network, root, media, or controller call.

## Result: sound snapshot mechanics, one remaining root-symlink gap

The generator is appropriately fail-closed for ordinary evidence entries and
for manifest metadata/classification. It also includes the intended MODE2 raw
capture and helper artifacts in its inventory without overwriting any
manifest.

There is one narrow remaining discrepancy with the stated requirement that
an entry reject **any** symlink ancestor: `entry()` checks every ancestor
*below* `ROOT`, but not `ROOT` itself. A temporary fixture with `ROOT` set to
a symlink was accepted. A symlinked child ancestor was correctly rejected.
The current production root was not changed or published; this is a design
finding, not an assertion that it is currently symlinked.

## Verified behaviors

### Inventory only / no overwrite

Running the script without flags returned:

```json
{"candidate_files":259,"bytes":98273163,"published":false}
```

The default path therefore inventories only. `--publish` uses exclusive
creation (`open('x')`) after refusing any existing output path; `--verify`
only reads and validates the existing manifest. No production manifest existed
or was created by this review.

### Manifest metadata and classification guards

In an isolated temporary root, an otherwise valid one-entry manifest passed
only when all of the following were exact:

* schema `samsung-tv-sleep-evidence-v1`;
* manifest `root`, scope text, and exclusions list;
* `physical_recovery_confirmed: false`; and
* `whole_mode2_capture_accepted: false`.

The temporary verifier rejected an independently altered value for each of
`root`, `scope`, `exclusions`, `physical_recovery_confirmed`, and
`whole_mode2_capture_accepted`. Duplicate/empty entry and path-escape guards
are also present before per-entry byte/hash validation.

### Symlink behavior

`entry()` correctly rejects a regular-looking file reached through a symlinked
child directory. Its lexical loop checks `ROOT/<part>`, then each deeper
ancestor, before reading bytes.

The following fixture also demonstrates the remaining boundary condition:

```text
actual-root/ok                 -> accepted as ordinary file
actual-root/linked/x           -> rejected (symlink input or ancestor)
root-link -> actual-root
root-link/ok with ROOT=root-link -> accepted
```

Because `path.relative_to(ROOT).parts` excludes `ROOT`, the current predicate
does not call `ROOT.is_symlink()`. To meet the literal “any symlink ancestor”
rule, a future revision should reject a symlinked `ROOT` (and, if desired by
the policy, resolve/check its absolute parent chain) before accepting any
entry. This review does not modify the parent-owned script.

### Explicitly relevant retained evidence

The candidate inventory contains, among other required materials:

* `panel-idle-20261026/overnight/sleep-mode2-20261027a.onset/trace`,
  `record.json`, and `fds.txt` (raw capture/sidecars);
* `.../sleep-investigation-20261027a/stock-mode2-trial/outcome.json`
  (orchestrator outcome); and
* `.../sleep-investigation-20261027a/mode2-trial-client.stderr` and
  `stock-mode2-experiment.py` (helper/experiment record).

The script excludes mutable `README.md`, `diagnostic-next-tests.md`, and the
eventual manifest from the `HERE` scope. It includes its own generator bytes,
which is appropriate for a reproducible snapshot. The explicit mode2/onset,
managed-duty, managed-power, extra-capture, and static research scopes are
all represented in `SCOPES`, `EXTRA_NAMES`, and `STATIC_NAMES`.

The latest expanded source closure is also present: the original 60-second
HDMI capture source/tests, managed status-read and errpin helper directories,
the USB-reader erratum/branch-check artifacts, and the exact
`root-access/s95f-access.py` client are all explicit inventory inputs. The
production manifest remains absent. The count above includes this review
itself because it lies under the retained work-block scope; it is one more
than the parent’s pre-review dry count of 258.

## Conclusion

The two evidence-classification flags are pinned false, and no path in the
reviewed code can classify a whole MODE2 capture as accepted or physical
recovery as confirmed merely by publishing an index. The inventory mechanism
is suitable for a non-overwriting snapshot once the root-symlink edge is
fixed or explicitly ruled out by its launch environment.

This review remains separate from capture acceptance: it does not change the
rejected passive capture, helper results, physical annotations, or any fault
conclusion.

## Re-review addendum: root and absolute-parent symlink guard fixed

The earlier root-symlink gap is **not current**. I re-reviewed the latest
source at SHA-256
`e3c4eec9b3543511bd62d13850c303455ae7857ef9a548334e4181dd0cf79cf8`.
Before computing relative parts, `entry()` now rejects a symlink in `ROOT` or
in any absolute ancestor (`ROOT.parents`). It retains the original checks for
each in-root ancestor and the input path itself.

Fresh temporary-fixture results against these latest bytes were:

```text
child_symlink_rejected=true
root_symlink_rejected=true
```

The current dry inventory returned 260 files / 98,275,253 bytes and
`published:false`; the extra count relative to the parent’s 259-file
pre-addendum inventory is this review addendum plus the separately requested
reader-review acknowledgement. No manifest was created. The current source
therefore meets the stated root/ancestor symlink refusal requirement as well
as the metadata and false-classification checks above.
