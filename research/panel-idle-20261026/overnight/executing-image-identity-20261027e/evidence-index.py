#!/usr/bin/env python3
"""Publish once, or verify the explicitly recorded controller-access evidence."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT / "panel-idle-20261026"
OUTPUT = HERE / "live-controller-evidence-manifest.json"
HELPERS = ("managed-usb-current-callbacks-read-once", "managed-usb-current-callbacks-alias-read-once",
           "managed-usb-common-error-guard-read-once", "managed-usb-secondary-root-read-once",
           "managed-usb-main-event-log-read-once", "managed-usb-main-log-index-read-once",
           "managed-usb-secondary-log-header-read-once", "managed-usb-secondary-event-log-read-once",
           "managed-tcon-status-read")
REPORTS = ()


def need(ok, why):
    if not ok:
        raise ValueError(why)


def row(path):
    need(path.is_file() and not path.is_symlink(), "Missing/nonregular evidence: " + str(path))
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def collect():
    files = {p for p in HERE.rglob("*") if p.is_file()
             and p != OUTPUT and p != HERE / "README.md"
             and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    for name in HELPERS:
        helper = BASE / "overnight" / name
        files.update(p for p in helper.iterdir() if p.is_file() and p.suffix in (".cs", ".csproj", ".json", ".py", ".md", ".bin", ".txt"))
        files.update(p for p in (helper / "bin/Release/net6.0").iterdir()
                     if p.is_file() and p.suffix in (".dll", ".json"))
    files.update(BASE / "tcon-research" / name for name in REPORTS)
    files.add(BASE / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin")
    files.add(BASE / "overnight/managed-tcon-status-read/run-status-read.py")
    files.add(BASE / "overnight/rt-onset-memory-20261027c/audit-runtime.py")
    files.add(BASE / "overnight/rt-onset-memory-20261027c/emmc-sector-read-once/returned-sector.bin")
    files.add(BASE / "overnight/rt-onset-memory-20261027c/rt-recorder-evidence-manifest.json")
    files.add(BASE / "overnight/firmware-fingerprint-20261027d/firmware-acquisition-evidence-manifest.json")
    files.add(BASE / "overnight/firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin")
    return [row(p) for p in sorted(files, key=lambda p: str(p.relative_to(ROOT)))]


def verify(manifest):
    need(manifest["schema"] == "samsung-live-controller-evidence-v1", "Schema")
    names = [entry["path"] for entry in manifest["entries"]]
    need(names == sorted(set(names)), "Unique sorted inventory")
    for entry in manifest["entries"]:
        path = ROOT / entry["path"]
        need(path.resolve().is_relative_to(ROOT.resolve()), "Evidence path escape")
        need(row(path) == entry, "Evidence changed: " + entry["path"])
    return len(names), sum(entry["bytes"] for entry in manifest["entries"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--publish", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.publish:
        need(not OUTPUT.exists(), "Snapshot already published")
        manifest = {"schema": "samsung-live-controller-evidence-v1",
                    "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "root": str(ROOT), "entries": collect(),
                    "exclusions": ["Mutable follow-up README and CURRENT-INVESTIGATION.md", "__pycache__/pyc and helper obj files", "Additional files created after publication"],
                    "physical_recovery_confirmed": False,
                    "active_usb_reads": ["one raw CPU64 negative control", "one corrected DMA callback64", "one main common64", "one secondary root64", "one main log3072", "one main index64", "one secondary header64", "one secondary full-ring15372"],
                    "additional_host_queries": ["one existing QDF status getter", "one nonclearing bounded kernel-log read"],
                    "flash_or_protection_change_performed": False,
                    "volatile_logger_write_performed": False,
                    "preceding_firmware_manifest_sha256": "e1f11fe681fa6047ba995a796315b712428ff75c415b3e9042d7e52127960d0f"}
        verify(manifest)
        with OUTPUT.open("x") as stream:
            stream.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    manifest = json.loads(OUTPUT.read_text())
    count, size = verify(manifest)
    print(json.dumps({"verified_files": count, "bytes": size,
                      "manifest_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
