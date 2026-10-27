#!${S95F_EVIDENCE_ROOT}/venv/bin/python
"""Owner-authorized, on-demand S95F diagnostics; no TV boot persistence."""
from __future__ import annotations

import argparse
import asyncio
import fcntl
import json
import os
from pathlib import Path
import subprocess
import socket
import sys
from urllib.request import ProxyHandler, build_opener

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / "source" / "src"))
from samsung_tv_root.archive_root import probe
from samsung_tv_root.sdb import SdbClient, route_callback_host

TV = "198.51.100.20"
CONTROLLER = "198.51.100.10"
MODEL = "QN77S95FAFXZC"
BUILD = "T-RSMFAKUC-0090-REL-202607141953"
SDB = BASE.parent / "devtools" / "sdb"


def check_identity(device: dict[str, object]) -> None:
    if device.get("modelName") != MODEL:
        raise RuntimeError("TV model changed; refusing execution")
    if str(device.get("developerMode")) != "1":
        raise RuntimeError("TV developer mode is not enabled")
    if device.get("developerIP") != CONTROLLER:
        raise RuntimeError("TV developer host changed; review addressing first")


def check_build(output: str) -> None:
    lines = output.splitlines()
    if "[exit:0]" not in lines or f"BUILD_ID={BUILD}" not in lines:
        raise RuntimeError("TV build changed or was unreadable; re-audit before execution")


def persistent_request(request: dict, timeout: int = 15) -> dict:
    """An execution request is never retried after being submitted."""
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel:
        channel.settimeout(timeout)
        channel.connect(str(BASE / 'persistent/control.sock'))
        channel.sendall((json.dumps(request)+'\n').encode())
        with channel.makefile('rb') as stream:
            line = stream.readline(4 * 1024 * 1024 + 1)
        if not line or len(line) > 4 * 1024 * 1024:
            raise RuntimeError('Persistent controller response missing or oversized')
        response = json.loads(line)
        if 'error' in response:
            raise RuntimeError('Persistent root unavailable; request was not retried')
        return response


def main() -> int:
    os.umask(0o077)
    os.environ["SDB"] = str(SDB)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("sdk", "root"))
    parser.add_argument("--command", required=True)
    parser.add_argument("--timeout", type=int, default=30, choices=range(1, 121), metavar="1..120")
    parser.add_argument("--persistent-only", action="store_true",
                        help="Require the existing root controller; never stage or bootstrap access")
    args = parser.parse_args()
    if args.persistent_only and args.mode != "root":
        parser.error("--persistent-only requires root mode")
    if not args.command.strip() or len(args.command.encode()) > 8192:
        parser.error("command must be nonempty and at most 8192 UTF-8 bytes")
    lock_path = BASE.parent / "private" / "s95f-access.lock"
    with lock_path.open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        guard = subprocess.run(
            ("sudo", "-n", "/usr/sbin/nft", "list", "table", "inet", "samsung_sdb_guard"),
            capture_output=True, text=True, timeout=5,
        )
        if guard.returncode != 0 or "tcp dport 26099" not in guard.stdout or "drop" not in guard.stdout:
            raise RuntimeError("SDB LAN firewall guard unavailable; refusing to start bridge")
        if route_callback_host(TV) != CONTROLLER:
            raise RuntimeError("Controller source address changed; review addressing first")
        opener = build_opener(ProxyHandler({}))
        with opener.open(f"http://{TV}:8001/api/v2/", timeout=5) as response:
            check_identity(json.load(response)["device"])
        if args.mode == 'root' and (BASE / 'persistent/control.sock').exists():
            status = persistent_request({'operation':'status'})
            if status.get('state') == 'ready':
                fingerprint = persistent_request({'operation':'exec', 'command':'cat /etc/tizen-release', 'timeout':10})
                if fingerprint.get('uid') != 0 or fingerprint.get('euid') != 0 or fingerprint.get('exit_code') != 0 or fingerprint.get('timed_out') or f'BUILD_ID={BUILD}' not in fingerprint.get('stdout','').splitlines():
                    raise RuntimeError('Persistent build or root identity check failed')
                result = persistent_request({'operation':'exec', 'command':args.command, 'timeout':args.timeout}, args.timeout + 15)
                print(json.dumps(dict(model=MODEL, host=TV, authenticated=True, uid=result['uid'], euid=result['euid'], root_persistence='host-assisted', global_system_files_unchanged_at_acquisition=status['system_files_unchanged'], commands=[dict(command=args.command, **{k:result[k] for k in ('exit_code','timed_out','stdout','stderr')})]), indent=2))
                return 0 if result['exit_code'] == 0 and not result['timed_out'] else 1
        if args.persistent_only:
            raise RuntimeError('Existing persistent root is unavailable; bootstrapping refused')
        client = SdbClient(SDB, TV, timeout=10)
        client.connect()
        client.require_device()
        fingerprint = client.capture(
            "cat /etc/tizen-release", callback_host=CONTROLLER,
            bind_host=CONTROLLER, timeout=15,
        )
        check_build(fingerprint.output)
        if args.mode == "sdk":
            result = client.capture(
                args.command, callback_host=CONTROLLER, bind_host=CONTROLLER,
                timeout=args.timeout,
            )
            print(result.output, end="")
            return 0 if "[exit:0]" in result.output.splitlines() else 1
        evidence = asyncio.run(probe(
            TV, model=MODEL, callback_host=CONTROLLER, bind_host=CONTROLLER,
            sdb_timeout=10, accept_timeout=20, command_timeout=args.timeout,
            payloads=BASE / "payloads", commands=(args.command,),
        ))
        print(json.dumps(evidence, indent=2))
        return 0 if all(
            item["exit_code"] == 0 and not item["timed_out"]
            for item in evidence.get("commands", [])
        ) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        # Suppress library exception details that might include command text.
        print(f"S95F access failed: {type(error).__name__}; no automatic retry", file=sys.stderr)
        raise SystemExit(1)
