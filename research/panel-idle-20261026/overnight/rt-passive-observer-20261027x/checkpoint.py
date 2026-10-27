#!/usr/bin/env python3
"""Publish once or verify the S--X evidence snapshot; local files only."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
MANIFEST = HERE / "evidence-manifest.json"
SCOPES = (
    "ap-exco-helper-inputs-20261027s", "rtp-action-causality-20261027t",
    "rtp-observer-feasibility-20261027u", "current-host-health-20261027v",
    "ap-exco-input-snapshot-20261027w", "rt-passive-observer-20261027x",
)
EXCLUDED = {str(MANIFEST.relative_to(BASE)),
            str((HERE / "checkpoint-review.md").relative_to(BASE))}
PARENTS = {
    "ap-exco-source-read-20261027m/ordinary-provenance-evidence-manifest.json":
        "26b5cc4faa8a3c03917b92ac48254ba359362bd201830cdf29fb229154b3dd0b",
    "code-map-qualified-followup-20261027n/code-view-evidence-manifest.json":
        "a365b51fe014af70d50697bdeefd0b5eac2d6abb342fda1c6d21ab6ec2b145d7",
    "ap-exco-callback-source-20261027o/callback-provenance-evidence-manifest.json":
        "c8876fcb5c6d2f5e41e21d2e202f35c4304629524c2f7cdc7bea94ed44c2d404",
}


def need(ok, why):
    if not ok:
        raise ValueError(why)


def fingerprint(path):
    need(path.is_file() and not path.is_symlink(), "regular file required")
    raw = path.read_bytes()
    return {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def parent_records():
    records = {}
    for name, expected in PARENTS.items():
        path = BASE / name
        need(fingerprint(path)["sha256"] == expected, "parent manifest hash")
        value = json.loads(path.read_bytes())
        root = (path.parent / value["path_base"]).resolve()
        size = 0
        for rel, row in value["files"].items():
            item = root / rel
            need(item.resolve().is_relative_to(root), "parent path escape")
            need(fingerprint(item) == row, "parent file changed: " + rel)
            size += row["size"]
        need(value["file_count"] == len(value["files"]) and
             value["total_bytes"] == size, "parent totals")
        records[name] = {"sha256": expected, "file_count": value["file_count"],
                         "total_bytes": size}
    return records


def inventory():
    result = {}
    for scope in SCOPES:
        root = BASE / scope
        need(root.is_dir() and not root.is_symlink(), "scope directory")
        for path in sorted(root.rglob("*")):
            need(not path.is_symlink(), "symlink in scope")
            if "__pycache__" in path.parts or path.suffix == ".pyc" or path.is_dir():
                continue
            rel = str(path.relative_to(BASE))
            if rel in EXCLUDED:
                continue
            need(path.resolve().is_relative_to(BASE), "scope path escape")
            result[rel] = fingerprint(path)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--publish", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.publish:
        need(not MANIFEST.exists(), "checkpoint already exists; never rewrite")
    parents = parent_records()
    files = inventory()
    if args.publish:
        value = {
            "schema": "ordinary-input-passive-observer-evidence-v1",
            "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "path_base": "..", "scope_roots": list(SCOPES),
            "excluded": sorted(EXCLUDED), "excluded_generated": ["__pycache__", "*.pyc"],
            "mutable_outside_scope": ["../../CURRENT-INVESTIGATION.md", "ordinary-fault-model-20261027.md"],
            "preservation_rule": "Never rewrite listed artifacts, even identically. Future work uses additive directories outside S--X.",
            "parent_manifests": parents, "file_count": len(files),
            "total_bytes": sum(row["size"] for row in files.values()), "files": files,
        }
        with MANIFEST.open("x") as output:
            output.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
    else:
        value = json.loads(MANIFEST.read_bytes())
        need(value["files"] == files and value["parent_manifests"] == parents,
             "snapshot inventory or parent mismatch")
        need(value["scope_roots"] == list(SCOPES) and value["excluded"] == sorted(EXCLUDED),
             "snapshot scope")
        need(value["file_count"] == len(files) and
             value["total_bytes"] == sum(row["size"] for row in files.values()), "totals")
    print(json.dumps({"verified": True, "target_operations": 0,
                      "file_count": value["file_count"], "total_bytes": value["total_bytes"],
                      "manifest_sha256": fingerprint(MANIFEST)["sha256"],
                      "unchanged_parent_file_entries": sum(v["file_count"] for v in parents.values())},
                     sort_keys=True))


if __name__ == "__main__":
    main()
