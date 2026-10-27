#!/usr/bin/env python3
"""Hash-gated, offline extraction of installed tv-viewer English messages."""
import gettext
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SOURCES = {
    "tv-viewer-en-US.mo": "8a7dbbe95e34aaa3d2e86fb11fa7079f0269b8c92b94c2537e491d48679eb66c",
    "tv-viewer-en-GB.mo": "b151f1451c438c9652c819f08deed6813a2ede91aed65e1b05f5e7cc819b1b0f",
}
KEYS = [
    "TV_SID_QD_CBSEP_INFO_MSG_SCREEN_RESTORATION_CLEARER",
    "TV_SID_QD_CBSEP_INFO_MSG_SCREEN_TURN_OFF_RUN_SCREEN_RESTORATION",
    "TV_SID_QD_CBSEP_SCREEN_RESTORATION",
    "TV_SID_QD_CBSEP_SCREEN_RESTORATION_COMPLETE",
    "TV_SID_QD_CBSEP_SCREEN_RESTORATION_NOT_COMPLETE",
    "TV_SID_SETTINGS_CBSEP_PIXEL_REFRESH",
    "TV_SID_SETTINGS_CBSEP_PIXEL_REFRESH_STARTS_MSG",
]


def main():
    records = []
    for name, expected in SOURCES.items():
        path = BASE / "binaries" / name
        data = path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise SystemExit(f"source hash mismatch: {name}")
        with path.open("rb") as stream:
            catalog = gettext.GNUTranslations(stream)
        messages = {}
        for key in KEYS:
            value = catalog.gettext(key)
            if value == key:
                raise SystemExit(f"missing message: {name}: {key}")
            messages[key] = value
        records.append({"source": str(path.relative_to(BASE)), "bytes": len(data),
                        "sha256": actual, "messages": messages})
    result = {
        "scope": "Installed English gettext catalogs; text identity only, not countdown/caller execution or blackout attribution",
        "tv_actions": "none; offline source reads and host JSON write",
        "sources": records,
    }
    output = BASE / "idle-research" / "tv-viewer-optimization-text.json"
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"PASS: {len(records)} hash-checked catalogs, {len(KEYS)} exact keys each; {output.name}")


if __name__ == "__main__":
    main()
