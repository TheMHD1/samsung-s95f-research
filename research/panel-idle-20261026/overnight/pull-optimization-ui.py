#!/usr/bin/env python3
"""Read allowlisted installed UI binaries, with source/copy hash checks."""
from pathlib import Path
import base64
import hashlib
import json
import shlex
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]
ACCESS = BASE.parent / "root-access/s95f-access.py"
FILES = {
    "welcome-mode": "/usr/apps/org.tizen.welcome-mode/bin/welcome-mode",
    "NotificationApp.dll": "/usr/apps/com.samsung.tv.notification-app/bin/NotificationApp.dll",
    "NotificationServiceApp.dll": "/usr/apps/com.samsung.tv.notification-serviceapp/bin/NotificationServiceApp.dll",
    "org.tizen.menu.dll": "/usr/apps/org.tizen.menu/bin/org.tizen.menu.dll",
    "SelfDiagnosisTextResources.dll": "/opt/usr/apps/com.samsung.SelfDiagnosis/bin/SelfDiagnosisTextResources.dll",
    "SelfDiagnosis.dll": "/opt/usr/apps/com.samsung.SelfDiagnosis/bin/SelfDiagnosis.dll",
    "SelfDiagnosisData.dll": "/opt/usr/apps/com.samsung.SelfDiagnosis/bin/SelfDiagnosisData.dll",
    "SelfDiagnosisTextResources.xml": "/opt/usr/apps/com.samsung.SelfDiagnosis/bin/SelfDiagnosisTextResources.xml",
    "NotificationAppTextResources.dll": "/usr/apps/com.samsung.tv.notification-app/bin/NotificationAppTextResources.dll",
    "NotificationServiceAppTextResources.dll": "/usr/apps/com.samsung.tv.notification-serviceapp/bin/NotificationServiceAppTextResources.dll",
    "NotificationServiceAppTextResources.xml": "/usr/apps/com.samsung.tv.notification-serviceapp/bin/NotificationServiceAppTextResources.xml",
    "Reminder.dll": "/opt/usr/apps/com.samsung.tv.reminder/bin/Reminder.dll",
    "ReminderTextResources.dll": "/opt/usr/apps/com.samsung.tv.reminder/bin/ReminderTextResources.dll",
    "tv-viewer": "/usr/apps/org.tizen.tv-viewer/bin/tv-viewer",
    "tv-viewer-en-US.mo": "/usr/apps/org.tizen.tv-viewer/res/locale/en_US/LC_MESSAGES/tv-viewer.mo",
    "tv-viewer-en-GB.mo": "/usr/apps/org.tizen.tv-viewer/res/locale/en_GB/LC_MESSAGES/tv-viewer.mo",
    "app-control-service": "/usr/bin/app-control-service",
    "libnotification.so.0": "/usr/lib/libnotification.so.0",
    "data-provider-master": "/usr/bin/data-provider-master",
    "libpower-control-diagnosis.so": "/usr/lib/libpower-control-diagnosis.so",
    "libnotification-ex.so.1": "/usr/lib/libnotification-ex.so.1",
    "libppi-factory-api.so": "/usr/lib/libppi-factory-api.so",
    "libvideo-misc.so.0.1.0": "/usr/lib/libvideo-misc.so.0.1.0",
    "libvideo-ft-control-impl-sec.so.0.1.0": "/prd/usr/lib/libvideo-ft-control-impl-sec.so.0.1.0",
    "libnvram.so.0.1": "/usr/lib/libnvram.so.0.1",
    "libnvram-impl-sec.so.0.1": "/prd/usr/lib/libnvram-impl-sec.so.0.1",
    "libeeprom-map.so.0.1": "/prd/usr/lib/libeeprom-map.so.0.1",
}


def root(command):
    result = subprocess.run(["python3", str(ACCESS), "root", "--persistent-only", "--timeout", "25",
                             "--command", command], capture_output=True, text=True,
                            timeout=55, check=True)
    response = json.loads(result.stdout)
    item = response["commands"][0]
    if item["exit_code"] or item["timed_out"] or item["stderr"]:
        raise RuntimeError(item)
    assert response["uid"] == response["euid"] == 0
    return item["stdout"]


def main():
    selected = sys.argv[1:] or list(FILES)
    if any(name not in FILES for name in selected):
        raise SystemExit("only explicitly allowlisted binary names are accepted")
    manifest_path = BASE / "overnight/matching-optimization-ui-manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for name in selected:
        remote = FILES[name]
        path = shlex.quote(remote)
        metadata = root(f"wc -c {path}\nsha256sum {path}").split()
        size, expected = int(metadata[0]), metadata[2]
        size_limit = 8 * 1024 * 1024 if name == "tv-viewer" else 4 * 1024 * 1024
        assert 0 < size <= size_limit
        destination = BASE / "binaries" / name
        if destination.exists():
            data = destination.read_bytes()
        else:
            pieces = []
            for chunk in range((size + 131071) // 131072):
                encoded = root(f"dd if={path} bs=131072 skip={chunk} count=1 2>/dev/null | base64")
                pieces.append(base64.b64decode(encoded))
            data = b"".join(pieces)
            assert len(data) == size and hashlib.sha256(data).hexdigest() == expected
            destination.write_bytes(data)
        assert len(data) == size and hashlib.sha256(data).hexdigest() == expected
        assert root(f"sha256sum {path}").split()[0] == expected
        manifest[name] = {"remote": remote, "size": size, "sha256": expected,
                          "read_only_source_acquisition": True}
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        print(name, size, expected, flush=True)


if __name__ == "__main__":
    main()
