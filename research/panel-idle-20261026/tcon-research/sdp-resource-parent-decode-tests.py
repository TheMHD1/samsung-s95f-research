#!/usr/bin/env python3
"""Mutation checks for the offline SDP DT-parent decoder."""
from pathlib import Path
import importlib.util
import shutil
import tempfile

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("decoder", HERE / "sdp-resource-parent-decode.py")
decoder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(decoder)
SOURCE = decoder.CAPTURE


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def copied_capture(root):
    target = root / "capture"
    shutil.copytree(SOURCE, target)
    return target


def raw(capture):
    return (capture / "remote-stdout.txt").read_text()


def expect_rejected(label, mutate, raw_only=False):
    with tempfile.TemporaryDirectory() as temp:
        capture = copied_capture(Path(temp))
        if raw_only:
            altered = mutate(raw(capture))
            require(altered != raw(capture), label + " made no mutation")
            try:
                decoder.decode(altered)
            except ValueError:
                return
        else:
            mutate(capture)
            try:
                decoder.build_report(capture)
            except ValueError:
                return
    raise RuntimeError(label + " was accepted")


def replace_once(text, old, new):
    require(old in text, "test fixture text absent")
    return text.replace(old, new, 1)


def main():
    report = decoder.build_report()
    require(report["translated_resource"]["translated_start"] == 0xB90000, "baseline translation")
    expect_rejected("prefix", lambda value: "JUNK\\n" + value, raw_only=True)
    expect_rejected("interstitial", lambda value: replace_once(value, "@@ PROPERTY ranges\\n", "NOISE\\n@@ PROPERTY ranges\\n"), raw_only=True)
    expect_rejected("trailing", lambda value: value + "TRAIL\\n", raw_only=True)
    expect_rejected("reordered", lambda value: replace_once(value, "@@ PROPERTY #address-cells\\n", "@@ PROPERTY #size-cells\\n"), raw_only=True)
    expect_rejected("reversed uptime", lambda value: replace_once(value, "63565.30 237740.39", "63565.20 237740.20"), raw_only=True)
    expect_rejected("remote stdout sidecar", lambda capture: (capture / "remote-stdout.txt").write_text(raw(capture) + "x"))
    expect_rejected("client stderr sidecar", lambda capture: (capture / "client-stderr.txt").write_text("unexpected"))
    print("PASS: baseline plus prefix/interstitial/trailing/reordered/reversed-time and sidecar mutations rejected.")


if __name__ == "__main__":
    main()
