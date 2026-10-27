#!/usr/bin/env python3
"""Offline bounded string/XML evidence; never loads or executes TV assemblies."""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
EXPECTED = {
    "SelfDiagnosisTextResources.dll": "95d76c273d796ede8dfc4bc1a28987d6bfe2a12ddbdd84a06f6c8a8a38c3a4d7",
    "SelfDiagnosis.dll": "56ddbafd42e4d925cfca4ffbee5fc6c30e747457c2c691634251d76dc9bd71fc",
    "SelfDiagnosisData.dll": "6467b153417c665b1d5e61e5c8100e7bbd0507deba3fecb0daedb10deb48cc5d",
    "SelfDiagnosisTextResources.xml": "731b893998a55076e13576cb2c836c222203c816f85b6514b3d3f6df86f7e0bd",
}
PATTERN = re.compile(
    r"screen.?optim|pixel.?refresh|screen.?restor|clearer|el.?sensing|off.?sensing|"
    r"QDDisplayRequestELSensing|60.second|10.minute|ten.minute", re.I
)


def main():
    result = {
        "scope": "Four copied files; contiguous printable ASCII/UTF-16LE runs and XML members only",
        "limits": "A missing match does not exclude dynamic, compressed, localized, native, indirect or other-file implementation. No IL/control-flow or runtime proof.",
        "tv_action": "none; local files only",
        "files": [],
    }
    for name, expected in EXPECTED.items():
        data = (BASE / "binaries" / name).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != expected:
            raise ValueError("Unexpected source hash: " + name)
        entry = {"name": name, "bytes": len(data), "sha256": digest, "matches": []}
        if name.endswith(".xml"):
            for member in ET.fromstring(data).iter("member"):
                text = " ".join("".join(member.itertext()).split())
                key = member.attrib.get("name", "")
                if PATTERN.search(key + " " + text):
                    entry["matches"].append({"member": key, "summary": text})
        else:
            for encoding, expression in [("ascii", rb"[ -~]{6,}"),
                                         ("utf-16-le", rb"(?:[ -~]\x00){6,}")]:
                for match in re.finditer(expression, data):
                    text = match.group().decode(encoding)
                    if PATTERN.search(text):
                        entry["matches"].append({"offset": match.start(), "encoding": encoding, "text": text})
        result["files"].append(entry)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
