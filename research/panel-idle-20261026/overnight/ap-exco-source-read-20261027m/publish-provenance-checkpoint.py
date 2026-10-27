#!/usr/bin/env python3
"""Publish once, or verify read-only, the completed H--M evidence checkpoint."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
MANIFEST = HERE / "ordinary-provenance-evidence-manifest.json"
ROOTS = [
    "executing-code-diagnostic-route-20261027h",
    "rtp-scan-input-origin-20261027i",
    "rtp-alternate-runtime-origin-20261027j",
    "rtp-baseline-live-comparison-20261027k",
    "rtp-packed-buffer-origin-20261027l",
    "ap-exco-source-read-20261027m",
]
EXTRAS = ["public-architecture-context-20261027.md",
          "finite-onset-logger-20261027g/external-code-map-search-followup.md"]
EXCLUDED = {MANIFEST, HERE / "checkpoint-review.md"}
PARENTS = {
    "runtime-evidence-manifest.json": "2d1d1427ea37c70e5b6ee37e301488027f6b2a0ff64f7d591884ca6faa252534",
    "fault-capture-evidence-manifest.json": "3bda86db80ddc3a0d5d6b0127e2dbc0ce6c1dcc19b15af3ad7b919bd29d12fb6",
    "diagnostic-followup-evidence-manifest.json": "4b93587a1062f2611fa0c2cdaeb6b0f7f0ef1fac637693d0003e0e0ed0bd33da",
}


def need(ok, why):
    if not ok:
        raise ValueError(why)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def row(path):
    need(path.is_file() and not path.is_symlink(), "regular file required: " + str(path))
    need(path.resolve().is_relative_to(BASE), "path escapes evidence base")
    raw = path.read_bytes()
    return {"size": len(raw), "sha256": digest(raw)}


def inventory():
    paths = []
    for name in ROOTS:
        root = BASE / name
        need(root.is_dir() and not root.is_symlink(), "scope root: " + name)
        for path in root.rglob("*"):
            need(not path.is_symlink(), "symlink in scope: " + str(path))
            if path.is_file() and path not in EXCLUDED and "__pycache__" not in path.parts and path.suffix != ".pyc":
                paths.append(path)
    paths += [BASE / name for name in EXTRAS]
    return {str(path.relative_to(BASE)): row(path) for path in sorted(paths)}


def parents():
    result = {}
    root = BASE / "finite-onset-logger-20261027g"
    for name, expected in PARENTS.items():
        path = root / name
        raw = path.read_bytes()
        need(digest(raw) == expected, "parent manifest changed: " + name)
        value = json.loads(raw)
        for relative, wanted in value["files"].items():
            need(row(path.parent / relative) == wanted, "parent file changed: " + relative)
        result[str(path.relative_to(BASE))] = {
            "sha256": expected, "file_count": len(value["files"]),
            "total_bytes": sum(item["size"] for item in value["files"].values()),
        }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    current, previous = inventory(), parents()
    if args.verify:
        value = json.loads(MANIFEST.read_bytes())
        need(value["files"] == current, "checkpoint byte/inventory mismatch")
        need(value["parent_manifests"] == previous, "parent checkpoint mismatch")
        need(value["file_count"] == len(current), "file count")
        need(value["total_bytes"] == sum(item["size"] for item in current.values()), "byte count")
    else:
        need(not MANIFEST.exists(), "refuse second publication")
        value = {
            "schema": "ordinary-provenance-evidence-checkpoint-v1",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "path_base": "..",
            "scope_roots": ROOTS,
            "scope_extra_files": EXTRAS,
            "excluded": [str(path.relative_to(BASE)) for path in sorted(EXCLUDED)],
            "excluded_generated": ["__pycache__", "*.pyc"],
            "mutable_outside_scope": ["../../CURRENT-INVESTIGATION.md", "ordinary-fault-model-20261027.md"],
            "future_work_outside_scope": ["code-map-qualified-followup-20261027n", "managed-usb-code-fingerprint-read"],
            "preservation_rule": "Never rewrite listed files, even identically. New work uses additive files outside scope.",
            "file_count": len(current),
            "total_bytes": sum(item["size"] for item in current.values()),
            "files": current,
            "parent_manifests": previous,
        }
        with MANIFEST.open("xb") as stream:
            stream.write((json.dumps(value, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps({"verified": args.verify, "file_count": value["file_count"],
                      "total_bytes": value["total_bytes"], "manifest_sha256": digest(MANIFEST.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
