#!${S95F_EVIDENCE_ROOT}/venv/bin/python
"""Keep authenticated S95F root available; reacquire when this host sees the TV.

This is host-assisted persistence, not an untethered TV boot modification.
The only control endpoint is an owner-only Unix socket. No power-on is sent.
"""
from __future__ import annotations
import argparse
import asyncio
import dataclasses
import fcntl
import json
import os
from pathlib import Path
import runpy
import secrets
import signal
import socket
import struct
import sys
import tempfile
import time
from urllib.request import ProxyHandler, build_opener

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / 'source/src'))
from samsung_tv_root import archive_root as ar
from samsung_tv_root.discovery import SsdpPresenceDiscovery
from samsung_tv_root.root_agent import RootAgentServer, generate_secret
from samsung_tv_root.sdb import SdbClient, route_callback_host

GUARD = runpy.run_path(str(BASE / 's95f-access.py'), run_name='s95f_guard')
TV, CONTROLLER = GUARD['TV'], GUARD['CONTROLLER']
STATE = BASE / 'persistent'
SOCKET = STATE / 'control.sock'
STATUS = STATE / 'status.json'

def check_tv() -> None:
    if route_callback_host(TV) != CONTROLLER:
        raise RuntimeError('Controller source changed')
    import subprocess
    result = subprocess.run(['sudo', '-n', '/usr/sbin/nft', 'list', 'table', 'inet', 'samsung_sdb_guard'], capture_output=True, text=True, timeout=5)
    if result.returncode or 'tcp dport 26099' not in result.stdout or 'drop' not in result.stdout:
        raise RuntimeError('SDB guard unavailable')
    with build_opener(ProxyHandler({})).open(f'http://{TV}:8001/api/v2/', timeout=4) as response:
        device = json.load(response)['device']
    GUARD['check_identity'](device)
    if str(device.get('PowerState', '')).lower() != 'on':
        raise RuntimeError('TV is not on')

class Controller:
    def __init__(self):
        self.connection = None
        self.agent_server = None
        self.client = SdbClient(GUARD['SDB'], TV, timeout=10)
        self.package = None
        self.hashes = None
        self.wake = asyncio.Event()
        self.stop = asyncio.Event()
        self.gate = asyncio.Lock()
        self.last_attempt = 0.0

    def status(self, state, **extra):
        value = dict(state=state, updated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), host=TV, controller=CONTROLLER, persistence='host-assisted', **extra)
        temporary = STATUS.with_suffix('.new')
        temporary.write_text(json.dumps(value, indent=2)+'\n')
        temporary.replace(STATUS)
        print(json.dumps({k:v for k,v in value.items() if k not in ('package',)}), flush=True)

    async def acquire(self):
        self.last_attempt = time.monotonic()
        await asyncio.to_thread(check_tv)
        with (BASE.parent / 'private/s95f-access.lock').open('a') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.status('acquiring')
            assessment = await asyncio.to_thread(ar._check_target, self.client)
            fingerprint = await asyncio.to_thread(self.client.capture, 'cat /etc/tizen-release', timeout=15)
            GUARD['check_build'](fingerprint.output)
            self.hashes = assessment.original_hashes
            self.package = 'archive-root-' + secrets.token_hex(8)
            self.agent_server = RootAgentServer(CONTROLLER, 0, TV, generate_secret(), require_root=True)
            await self.agent_server.start()
            with tempfile.TemporaryDirectory(prefix='s95f-persistent-', dir=STATE) as temporary:
                directory = Path(temporary)
                ar._prepare_artifacts(directory, assessment.runtime, self.package, CONTROLLER, self.agent_server.listening_port, self.agent_server.secret)
                await asyncio.to_thread(ar._stage, self.client, directory, BASE / 'payloads', self.package)
            stage = ar.STAGING_ROOT / self.package
            command = f'( nohup /usr/bin/dotnet {stage}/SamsungTvArchiveRoot.dll {self.package} >{stage}/outer.log 2>&1 </dev/null 3>&- & )'
            launched = await asyncio.to_thread(self.client.capture, command, callback_host=CONTROLLER, bind_host=CONTROLLER, timeout=15)
            if '[exit:0]' not in launched.output:
                raise RuntimeError('Background launcher failed')
            self.connection = await self.agent_server.accept(25)
            identity = await self.connection.ping()
            # These hashes are read through the original SDK mount namespace.
            observed = await asyncio.to_thread(ar._capture, self.client, ar.SYSTEM_HASH_COMMAND)
            if observed != self.hashes:
                raise RuntimeError('Global system file hashes changed')
            boot = await self.connection.execute('cat /proc/sys/kernel/random/boot_id', 5)
            if boot.exit_code or boot.timed_out:
                raise RuntimeError('Boot identity unreadable')
            self.status('ready', uid=identity.uid, euid=identity.euid, pid=identity.pid, smack=identity.smack_label.strip(), boot_id=boot.stdout.strip(), system_files_unchanged=True, package=self.package)

    async def release(self):
        if self.connection:
            try:
                await self.connection.shutdown(timeout=3)
            except Exception:
                await self.connection.close()
        self.connection = None
        if self.agent_server:
            await self.agent_server.close()
        self.agent_server = None
        if self.package:
            # Cleanup is confined to this session's random package.
            try:
                await asyncio.to_thread(ar._cleanup, self.client, self.package)
            except Exception:
                pass  # TV may already be powered off; no power-on is sent.
        self.package = None

    async def presence(self, discovery):
        while not self.stop.is_set():
            event = await discovery.receive()
            if event.available:
                self.wake.set()

    async def handle(self, reader, writer):
        try:
            peer = writer.get_extra_info('socket').getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
            if struct.unpack('3i', peer)[1] != os.getuid():
                raise PermissionError('Owner-only endpoint')
            request = json.loads(await asyncio.wait_for(reader.readline(), 5))
            if request.get('operation') == 'status':
                response = json.loads(STATUS.read_text())
            else:
                command = request.get('command')
                timeout = request.get('timeout', 30)
                if not isinstance(command, str) or not command.strip() or len(command.encode()) > 8192 or not isinstance(timeout, int) or not 1 <= timeout <= 120:
                    raise ValueError('Invalid command or timeout')
                async with self.gate:
                    if self.connection is None:
                        raise RuntimeError('Root unavailable; waiting for TV')
                    result = await self.connection.execute(command, timeout)
                    response = dict(authenticated=True, uid=self.connection.identity.uid, euid=self.connection.identity.euid, persistence='host-assisted', **dataclasses.asdict(result))
            writer.write((json.dumps(response)+'\n').encode())
            await writer.drain()
        except Exception as error:
            writer.write((json.dumps({'error':type(error).__name__})+'\n').encode())
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def run(self):
        discovery = SsdpPresenceDiscovery((TV,))
        await discovery.start()
        SOCKET.unlink(missing_ok=True)
        server = await asyncio.start_unix_server(self.handle, path=SOCKET, limit=65536)
        os.chmod(SOCKET, 0o600)
        watcher = asyncio.create_task(self.presence(discovery))
        self.wake.set()
        try:
            while not self.stop.is_set():
                if self.connection:
                    try:
                        await asyncio.wait_for(self.stop.wait(), 30)
                    except TimeoutError:
                        try:
                            async with self.gate:
                                await self.connection.ping(timeout=5)
                        except Exception:
                            async with self.gate:
                                await self.release()
                            self.status('waiting-for-tv')
                    continue
                wake_task = asyncio.create_task(self.wake.wait())
                stop_task = asyncio.create_task(self.stop.wait())
                _, pending = await asyncio.wait((wake_task, stop_task), return_when=asyncio.FIRST_COMPLETED)
                for task in pending:
                    task.cancel()
                if self.stop.is_set():
                    break
                self.wake.clear()
                delay = 30 - (time.monotonic() - self.last_attempt)
                if delay > 0:
                    try:
                        await asyncio.wait_for(self.stop.wait(), delay)
                        break
                    except TimeoutError:
                        pass
                try:
                    async with self.gate:
                        await self.acquire()
                except Exception as error:
                    (STATE / 'last-error.txt').write_text(str(error)+'\n')
                    async with self.gate:
                        await self.release()
                    self.status('waiting-for-tv', reason=type(error).__name__)
        finally:
            server.close()
            await server.wait_closed()
            watcher.cancel()
            await discovery.close()
            async with self.gate:
                await self.release()
            SOCKET.unlink(missing_ok=True)
            self.status('stopped')

async def call(operation, command=None, timeout=30):
    reader, writer = await asyncio.open_unix_connection(SOCKET, limit=4*1024*1024)
    try:
        writer.write((json.dumps(dict(operation=operation, command=command, timeout=timeout))+'\n').encode())
        await writer.drain()
        result = json.loads(await asyncio.wait_for(reader.readline(), timeout+10))
        print(json.dumps(result, indent=2))
        return 0 if 'error' not in result and result.get('exit_code', 0) == 0 and not result.get('timed_out', False) else 1
    finally:
        writer.close()
        await writer.wait_closed()

async def main(args):
    if args.operation != 'daemon':
        return await call(args.operation, args.command, args.timeout)
    controller = Controller()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, controller.stop.set)
    await controller.run()
    return 0

if __name__ == '__main__':
    os.umask(0o077)
    os.environ['SDB'] = str(GUARD['SDB'])
    STATE.mkdir(mode=0o700, exist_ok=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('daemon', 'status', 'exec'))
    parser.add_argument('--command')
    parser.add_argument('--timeout', type=int, default=30)
    arguments = parser.parse_args()
    if arguments.operation == 'exec' and not arguments.command:
        parser.error('exec requires --command')
    try:
        if arguments.operation == 'daemon':
            with (STATE / 'daemon.lock').open('a') as daemon_lock:
                fcntl.flock(daemon_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                raise SystemExit(asyncio.run(main(arguments)))
        raise SystemExit(asyncio.run(main(arguments)))
    except Exception as error:
        print(f'S95F persistent root: {type(error).__name__}', file=sys.stderr)
        raise SystemExit(1)
