#!/usr/bin/env python3
"""Bounded read-only avocd memory snapshot. Default prints the contract only.

Never sends a TV key, ioctl, D-Bus call, memory write, ptrace, or service action.
Physical labels are observer annotations, never derived from software values.
"""
from pathlib import Path
import argparse
import base64
import datetime
import hashlib
import json
import re
import subprocess

BASE = Path(__file__).resolve().parents[1]
SOURCE = "/prd/usr/lib/libave.so.0.1"
SHA = "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777"
ACCESS = BASE.parent / "root-access/s95f-access.py"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def blocks(text):
    result = {}
    name = None
    for line in text.splitlines():
        if line.startswith("@@ "):
            name = line[3:]
            require(name not in result, "Duplicate section: " + name)
            result[name] = []
        else:
            require(name is not None, "Unframed output")
            result[name].append(line)
    return {k: "\n".join(v).strip() for k, v in result.items()}


def maps(text):
    result = []
    for line in text.splitlines():
        fields = line.split(None, 5)
        require(len(fields) >= 5, "Malformed mapping")
        start, end = (int(x, 16) for x in fields[0].split("-"))
        result.append((start, end, fields[1], int(fields[2], 16),
                       fields[5] if len(fields) == 6 else ""))
    require(bool(result), "Empty maps")
    return result


def check_range(mapping, address, words):
    require(isinstance(address, int) and 0 < address < 2**32 and address % 4 == 0,
            "Unaligned/invalid 32-bit address")
    require(isinstance(words, int) and 1 <= words <= 6, "Read length out of bounds")
    require(any(start <= address and address + 4 * words <= end and "r" in perms
                for start, end, perms, _, _ in mapping), "Unmapped/unreadable target")


def decode(text, count):
    raw = base64.b64decode("".join(text.split()), validate=True)
    require(len(raw) == count * 4, "Incomplete memory read")
    return [int.from_bytes(raw[i:i + 4], "little") for i in range(0, len(raw), 4)]


def check_dd_stderr(text):
    expressions = [r"[0-9]+\+[0-9]+ records (in|out)",
                   r"[0-9]+ bytes \([^()]+\) copied, [0-9.e+-]+ s, [0-9.]+ [kMGT]?B/s"]
    require(all(any(re.fullmatch(pattern, line) for pattern in expressions)
                for line in text.splitlines()), "Unexpected remote stderr")


def identity(fields, suffix=""):
    pid = fields["PID" + suffix]
    boot = fields["BOOT" + suffix]
    require(re.fullmatch(r"[1-9][0-9]*", pid), "Expected one process")
    require(re.fullmatch(r"[0-9a-f-]{36}", boot), "Malformed boot ID")
    require(fields["EXE" + suffix] == "/usr/bin/avocd", "Unexpected executable")
    stat = fields["STAT" + suffix]
    require(stat.startswith(pid + " (avocd) "), "Unexpected process stat")
    tail = stat.rsplit(") ", 1)[1].split()
    require(len(tail) >= 20 and tail[19].isdigit(), "Missing start time")
    require(fields["HASH" + suffix].split() == [SHA, SOURCE], "Source hash mismatch")
    return {"pid": int(pid), "boot_id": boot, "start_ticks": int(tail[19])}


def metadata(suffix=""):
    return [
        f"echo '@@ BOOT{suffix}'", "cat /proc/sys/kernel/random/boot_id",
        f"echo '@@ PID{suffix}'", "pidof avocd",
        f"echo '@@ EXE{suffix}'", 'readlink "/proc/$tv_pid/exe"',
        f"echo '@@ STAT{suffix}'", 'cat "/proc/$tv_pid/stat"',
        f"echo '@@ HASH{suffix}'", "sha256sum " + SOURCE,
        f"echo '@@ UPTIME{suffix}'", "cat /proc/uptime",
        f"echo '@@ MAPS{suffix}'", 'cat "/proc/$tv_pid/maps"',
    ]


class Capture:
    def __init__(self, destination, physical_label):
        self.path = destination
        self.record = {
            "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "physical_label": physical_label,
            "physical_label_source": "caller annotation; not verified by this tool",
            "atomic": False, "accepted": False, "source_hash_is_live_text_hash": False,
            "actions": "process/source-file reads only", "stages": [],
        }
        self.expected_identity = None
        self.expected_bias = None
        self.mapping = None

    def save(self):
        self.path.write_text(json.dumps(self.record, indent=2) + "\n")

    def stage(self, name, requests):
        require(all(re.fullmatch(r"[a-z][a-z0-9_]*", k) for k in requests), "Invalid read label")
        if self.mapping is not None:
            for address, count in requests.values():
                check_range(self.mapping, address, count)
        command = ["set -eu", 'tv_pid=$(pidof avocd)',
                   'case "$tv_pid" in \'\'|*[!0-9]*) exit 31;; esac']
        if self.expected_identity is not None:
            expected = self.expected_identity
            command += [f'test "$tv_pid" = {expected["pid"]}',
                        f'test "$(cat /proc/sys/kernel/random/boot_id)" = {expected["boot_id"]}',
                        'test "$(readlink /proc/$tv_pid/exe)" = /usr/bin/avocd',
                        'test "$(awk \'{print $22}\' /proc/$tv_pid/stat)" = '
                        + str(expected["start_ticks"])]
        command += ["echo '@@ UTC'", "date -u"] + metadata()
        for label, (address, count) in requests.items():
            command += [f"echo '@@ READ_{label}'",
                        f'dd if="/proc/$tv_pid/mem" bs=4 skip={address // 4} count={count} | base64']
        command += metadata("_END")
        text = "\n".join(command) + "\n"
        require(len(text.encode()) < 7500, "Command too large")
        entry = {"name": name, "command": text,
                 "requests": {k: {"address": hex(v[0]), "words": v[1]} for k, v in requests.items()}}
        self.record["stages"].append(entry)
        self.save()
        proc = subprocess.run(["python3", str(ACCESS), "root", "--persistent-only", "--timeout", "25",
                               "--command", text], text=True, capture_output=True, timeout=55)
        entry.update({"transport_exit": proc.returncode, "transport_stderr": proc.stderr})
        try:
            response = json.loads(proc.stdout)
            entry["response"] = response
        except ValueError:
            entry["unparsed_stdout"] = proc.stdout
            self.save()
            raise
        self.save()
        require(proc.returncode == 0, "Root transport failed")
        require(response.get("authenticated") is True and response.get("uid") == 0
                and response.get("euid") == 0 and response.get("model") == "QN77S95FAFXZC",
                "Unexpected root identity")
        require(response.get("root_persistence") == "host-assisted", "Unexpected access path")
        require(response.get("global_system_files_unchanged_at_acquisition") is True,
                "Controller source-system invariant failed")
        require(len(response["commands"]) == 1, "Unexpected command count")
        item = response["commands"][0]
        require(item["exit_code"] == 0 and not item["timed_out"], "Remote command failed")
        # dd success summaries are allowed; every byte count is checked separately.
        check_dd_stderr(item["stderr"])
        fields = blocks(item["stdout"])
        expected_sections = {"UTC"} | {
            k + suffix for k in ["BOOT", "PID", "EXE", "STAT", "HASH", "UPTIME", "MAPS"]
            for suffix in ["", "_END"]} | {"READ_" + k for k in requests}
        require(set(fields) == expected_sections, "Unexpected/missing framed section")
        ident = identity(fields)
        require(ident == identity(fields, "_END"), "Process identity changed during read")
        if self.expected_identity is None:
            self.expected_identity = ident
        require(ident == self.expected_identity, "Process identity changed between stages")
        require(fields["MAPS"] == fields["MAPS_END"], "Maps changed during stage")
        mapping = maps(fields["MAPS"])
        load = [start for start, _, perms, offset, path in mapping
                if path == SOURCE and offset == 0 and "x" in perms]
        require(len(load) == 1, "Ambiguous exact-library load bias")
        if self.expected_bias is None:
            self.expected_bias = load[0]
        require(load[0] == self.expected_bias, "Library load bias changed between stages")
        decoded = {}
        for label, (address, count) in requests.items():
            check_range(mapping, address, count)
            decoded[label] = decode(fields["READ_" + label], count)
        entry["decoded"] = decoded
        entry["identity"] = ident
        entry["memory_bytes"] = sum(4 * v[1] for v in requests.values())
        entry["uptime"] = [fields["UPTIME"], fields["UPTIME_END"]]
        self.mapping = mapping
        self.save()
        return decoded


def collect(capture):
    capture.stage("source_and_maps", {})
    load = [start for start, _, perms, offset, path in capture.mapping
            if path == SOURCE and offset == 0 and "x" in perms]
    require(len(load) == 1, "Ambiguous exact-library load bias")
    bias = load[0]  # Hash-gated ELF first PT_LOAD has p_vaddr=0.
    capture.record["bias"] = hex(bias)
    roots = {"got": (bias + 0x5A69EC, 1), "global": (bias + 0x5BE2A4, 1),
             "cache": (bias + 0x5AB958, 1)}
    first = capture.stage("root_pointers", roots)
    require(first["got"] == [bias + 0x5BE2A4], "Unexpected relocated GOT")
    panel = first["global"][0]
    outer = {"header": (panel, 2), "interfaces": (panel + 0xC, 2),
             "ready": (panel + 0x18, 1)}
    second = capture.stage("outer_object", {**roots, **outer})
    require(second["got"] == first["got"] and second["global"] == first["global"],
            "Root pointer changed")
    require(second["header"][0] == bias + 0x59F2E8, "Unsupported active QD object")
    inner = second["header"][1]
    vendor, backend = second["interfaces"]
    require(vendor != 0 and backend != 0, "Missing interface")
    children = {"backend_vptr": (backend, 1), "vendor_vptr": (vendor, 1)}
    third = capture.stage("interface_types", {**roots, **outer, **children})
    for key in ["got", "global", "header", "interfaces"]:
        require(third[key] == second[key], "Object chain changed")
    require(third["backend_vptr"] == [bias + 0x5A152C], "Unsupported backend type")
    require(third["vendor_vptr"] == [bias + 0x59FA7C], "Unsupported vendor type")
    fields = {**roots, **outer, **children,
              "backend_slot": (bias + 0x5A1604, 1),
              "duty": (inner + 0xA8, 2), "gate_38": (inner + 0x38, 1),
              "gate_5c": (inner + 0x5C, 1), "gate_1b4": (inner + 0x1B4, 1),
              "control": (inner + 0x18C, 1), "autodim": (inner + 0x2A8, 1),
              "vendor_gate": (inner, 1),
              "monitor_counters": (bias + 0x5BFC5C, 6),
              "monitor_latch_context": (bias + 0x5BFC74, 6),
              "monitor_previous": (bias + 0x5BFCD0, 1),
              "monitor_restart_on": (bias + 0x5BFCE8, 2)}
    requests = {k + "_before": v for k, v in fields.items()}
    requests.update({k + "_after": v for k, v in reversed(list(fields.items()))})
    final = capture.stage("paired_fields", requests)
    pairs = {k: final[k + "_before"] == final[k + "_after"] for k in fields}
    capture.record["matching_pairs"] = pairs
    require(all(pairs.values()), "Nonmatching paired fields; raw sample retained")
    for key in ["got", "global", "header", "interfaces", "backend_vptr", "vendor_vptr"]:
        require(final[key + "_before"] == third[key], "Object chain changed at final read")
    require(final["backend_slot_before"] == [bias + 0x1C6275], "Unexpected live output slot")
    capture.record["summary"] = {
        "cache": final["cache_before"][0], "working_duty": final["duty_before"],
        "autodim_raw": final["autodim_before"][0],
        "monitor_fault_counts": dict(zip(["err_det", "vdd_det", "elvdd_i2c"],
                                          final["monitor_counters_before"][:3])),
        "monitor_retry_counts": dict(zip(["err_det", "vdd_det", "elvdd_i2c"],
                                          final["monitor_counters_before"][3:])),
        "monitor_history_latch": final["monitor_latch_context_before"][1],
        "monitor_restart_on": final["monitor_restart_on_before"],
        "monitor_previous": final["monitor_previous_before"][0],
        "physical_output_or_failure": "not determined by memory fields",
    }
    capture.record["accepted"] = True
    capture.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label", help="Unique local capture label")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--physical-label", choices=["unobserved", "apps-visible", "black-audio"],
                        default="unobserved")
    args = parser.parse_args()
    require(re.fullmatch(r"[a-z][a-z0-9-]{0,50}", args.label), "Invalid label")
    require(hashlib.sha256((BASE / "binaries/libave.so.0.1").read_bytes()).hexdigest() == SHA,
            "Unexpected local input binary")
    if not args.run:
        print(json.dumps({"mode": "dry-run; no TV call", "stages": ["source_and_maps", "root_pointers",
              "outer_object", "interface_types", "paired_fields"],
              "source_sha256": SHA, "physical_label": args.physical_label,
              "actions": "bounded process-memory/source reads only"}, indent=2))
        return
    destination = BASE / "overnight" / (args.label + ".json")
    require(not destination.exists(), "Existing capture refused")
    # Exclusive local creation, even if another invocation races this check.
    with destination.open("x"):
        pass
    capture = Capture(destination, args.physical_label)
    try:
        collect(capture)
    except Exception as error:
        capture.record["error"] = type(error).__name__ + ": " + str(error)
        capture.save()
        raise
    print(json.dumps({"path": str(destination), "accepted": True,
                      "physical_label": args.physical_label, "summary": capture.record["summary"]}))


if __name__ == "__main__":
    main()
