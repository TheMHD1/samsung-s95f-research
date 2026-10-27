#!/usr/bin/env python3
"""One authorized stock MODE2 trial inside a finite passive 60s capture.

Dry by default. No picture annotations are manufactured. A technical capture
may pass while diagnostic_eligible remains false. Never retries a helper.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
B = HERE.parent
LABEL = "sleep-mode2-20261027a"
DEST = HERE / "stock-mode2-trial"
BOOT = "00000000-0000-4000-8000-000000000000"
PINS = {
    "observed-hdmi-onset-capture.py": "ab0a8d101bd1058ce4b25becb3ae5294cc29ac38a600ecf23c4dcf3658b886f3",
    "managed-tcon-status-read/run-status-read.py": "7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a",
    "managed-errpin-cdev/run-errpin-cdev-input-once.py": "cd0a34ffd719945bb369ecae16f4ca0672dbbaddea11be068e0f31465e185cde",
    "managed-tcon-duty-read/run-duty-read-v2.py": "5f0796be9ec36f7441ae248a1472cf61001a7417afd896d41057df45e0aad5c6",
    "managed-tcon-power-cycle-once/run-power-cycle-once.py": "5c7ec5d3581e349d7f91669977123497147777e573fbdefd8a9b6f96dcf3cb75",
}


def require(value, message):
    if not value:
        raise ValueError(message)


def identities():
    for name, expected in PINS.items():
        require(hashlib.sha256((B/name).read_bytes()).hexdigest() == expected,
                "source changed: " + name)


def load_status():
    path = B / "managed-tcon-status-read/run-status-read.py"
    spec = importlib.util.spec_from_file_location("mode2_transport", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def guarded_execute(command, end):
    """Guard the actual execute request after staging, not just helper launch."""
    if "echo EXECUTE_COMPLETE" not in command:
        return command
    private = "/sys/kernel/debug/tracing/instances/researcher-hdmi-onset-" + LABEL
    guard = f'''test "$(cat {private}/tracing_on)" = 1
awk -v e={end:.3f} '{{exit !($1+15<e)}}' /proc/uptime
'''
    # Full-line shell comments carry no execution semantics; remove them to
    # fit the added gate inside the authenticated transport's 8192B limit.
    compact = "\n".join(line for line in command.splitlines()
                        if not line.lstrip().startswith("#")) + "\n"
    require(compact.startswith("set -eu\n"), "unexpected execution shell")
    result = compact.replace("set -eu\n", "set -eu\n"+guard, 1)
    require(len(result.encode()) <= 8192, "guarded execute command too large")
    return result


def configure_transport(module, end):
    original = module.root
    def root(command, record, output):
        return original(guarded_execute(command, end), record, output)
    module.root = root
    return module


def helper(name, relative, end):
    output = DEST / (name + ".json")
    path = B/relative
    spec = importlib.util.spec_from_file_location("mode2_helper_"+name.replace("-","_"), path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    factory_name = next((key for key in ("lifecycle_module", "mod")
                         if hasattr(runner,key)), None)
    if factory_name:
        original_factory = getattr(runner,factory_name)
        setattr(runner,factory_name,lambda: configure_transport(original_factory(), end))
    else:
        configure_transport(runner,end)
    with (DEST/(name+".client.stdout")).open("x") as stdout, (DEST/(name+".client.stderr")).open("x") as stderr:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            runner.run_once(output,*runner.contract())
    record = json.loads(output.read_text())
    require(record.get("accepted") is True and record.get("cleanup_confirmed") is True,
            "helper result/cleanup rejected: " + name)
    require(record.get("execution", {}).get("boot_id") == BOOT,
            "helper Linux boot changed: " + name)
    require(record['execution']['execute_uptime'] < end,
            "helper completed outside capture; no further action: "+name)
    return record


def readiness(module, name):
    private = "/sys/kernel/debug/tracing/instances/researcher-hdmi-onset-" + LABEL
    command = f'''set -eu
test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}
test "$(cat {private}/tracing_on)" = 1
echo READY_UPTIME=$(cut -d ' ' -f1 /proc/uptime)
awk '/: CAPTURE_START / {{s++}} /: CAPTURE_END / {{e++}} END {{if(s!=1 || e!=0) exit 81; print "ACTIVE_CAPTURE_START_VERIFIED"}}' {private}/trace
'''
    text = module.root(command, {"calls": []}, DEST/(name+".json"))
    require(text.rstrip().endswith("ACTIVE_CAPTURE_START_VERIFIED"), "trace not ready")
    return float(module.marker(text, "READY_UPTIME", r"[0-9]+(?:\.[0-9]+)?"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--reviewed", action="store_true")
    args = parser.parse_args()
    identities()
    if not args.run:
        require(not args.reviewed, "reviewed requires run")
        print(json.dumps({"dry_run": True, "label": LABEL, "seconds": 60,
                          "physical_state": "unobserved; owner last reported black after For You",
                          "order": ["passive recorder", "verify active private window", "one pin sample",
                                    "one fixed MODE2 request", "post status", "post pin", "post drive"],
                          "source_pins": PINS, "retry": False}, indent=2))
        return
    require(args.reviewed, "exact reviewed run required")
    require(not (B/(LABEL+".onset")).exists(), "capture label already exists")
    DEST.mkdir(mode=0o700)
    intent = {"physical_state": "unobserved", "owner_last_state": "black after For You",
              "power_requests_planned": 1, "power_mode": 2, "boot_id": BOOT,
              "source_pins": PINS, "recovery_inferred": False}
    (DEST/"intent.json").write_text(json.dumps(intent, indent=2)+"\n")
    module = load_status()
    with (DEST/"capture.client.stdout").open("xb") as out, (DEST/"capture.client.stderr").open("xb") as err:
        capture = subprocess.Popen(["python3", str(B/"observed-hdmi-onset-capture.py"), LABEL,
                                    "--run", "--reviewed"], stdin=subprocess.DEVNULL,
                                   stdout=out, stderr=err)
        try:
            deadline = time.monotonic() + 55
            launch_path = B/(LABEL+".onset")/"launch-root-response.json"
            while True:
                require(capture.poll() is None, "capture stopped before experiment")
                require(time.monotonic() < deadline, "capture launch timeout")
                try:
                    launch = json.loads(launch_path.read_text())
                except (FileNotFoundError, json.JSONDecodeError):
                    launch = {}
                if launch:
                    command = launch['commands'][0]['command']
                    module.validate_response(launch, command)
                    targets = re.findall(r'-- ([0-9]+\.[0-9]+)\) >', command)
                    require(len(targets) == 1, "ambiguous collector target time")
                    target = float(targets[0])
                    # The frozen collector schedules twelve seconds ahead.
                    # This delay is only preparation; readiness is verified
                    # on the TV before any helper is requested.
                    time.sleep(13)
                    break
                time.sleep(.25)
            ready = readiness(module, "readiness-before-pin")
            require(target + 60 - ready > 35,
                    "insufficient private trace window")
            end = target+60
            pin = helper("pre-pin", "managed-errpin-cdev/run-errpin-cdev-input-once.py",end)
            require(pin['execution']['result']['value'] == 1,
                    "fault input is not asserted; MODE2 withheld")
            ready = readiness(module, "readiness-before-power")
            require(target + 60 - ready > 30, "power action would outlast bracket")
            helper("mode2", "managed-tcon-power-cycle-once/run-power-cycle-once.py",end)
            helper("post-status", "managed-tcon-status-read/run-status-read.py",end)
            helper("post-pin", "managed-errpin-cdev/run-errpin-cdev-input-once.py",end)
            helper("post-duty", "managed-tcon-duty-read/run-duty-read-v2.py",end)
        finally:
            # Allow the finite recorder to complete and run its own reviewed
            # cleanup even when a helper fails. No power retry is scheduled.
            capture.wait(timeout=180)
            (DEST/"capture-exit.json").write_text(json.dumps({"exit_code": capture.returncode})+"\n")
            final_path = B/(LABEL+".onset")/"record.json"
            final = json.loads(final_path.read_text())
            capture_ok = (capture.returncode == 0 and final.get('accepted') is True
                          and final.get('technical_capture_complete') is True
                          and final.get('cleanup_verified') is True)
            (DEST/"outcome.json").write_text(json.dumps({
                'capture_technically_accepted':capture_ok,
                'accepted_sequence':capture_ok and sys.exc_info()[0] is None,
                'sequence_completed':sys.exc_info()[0] is None,
                'physical_state':'unobserved', 'recovery_inferred':False,
                'diagnostic_eligible':final.get('diagnostic_eligible'),
            },indent=2)+"\n")
            require(capture_ok, "passive bracket rejected; preserve raw trial without recovery claim")
    print(json.dumps({"trial": str(DEST), "capture_exit": capture.returncode,
                      "recovery_inferred": False, "physical_state": "unobserved"}))


if __name__ == "__main__":
    main()
