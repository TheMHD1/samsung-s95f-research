#!${S95F_EVIDENCE_ROOT}/venv/bin/python
"""Reuse the approved S95F identity. No daemon, auto-wake, or pairing loop."""
import argparse
import fcntl
import json
import logging
import os
from pathlib import Path
import socket
import stat
import subprocess
import sys
import time
import urllib.request

logging.disable(logging.CRITICAL)  # Upstream INFO logging includes auth tokens.

BASE = Path('${S95F_EVIDENCE_ROOT}')
TOKEN = BASE / 'private/s95f.token'
HOST = '198.51.100.20'
CONTROLLER = '198.51.100.10'
MODEL = 'QN77S95FAFXZC'
NAME = 'researcher TV Control'
DIAGNOSTICS_URL = 'http://198.51.100.10:8851/'
BROWSER_ID = 'org.tizen.browser'
KEYS = ('KEY_UP', 'KEY_DOWN', 'KEY_LEFT', 'KEY_RIGHT', 'KEY_ENTER',
        'KEY_RETURN', 'KEY_HOME', 'KEY_MENU', 'KEY_INFO', 'KEY_SOURCE',
        'KEY_VOLUP', 'KEY_VOLDOWN', 'KEY_MUTE', 'KEY_PLAY', 'KEY_PAUSE',
        'KEY_STOP', 'KEY_FF', 'KEY_REWIND', 'KEY_POWER')


def classify_receipt(response):
    """Retain fixed protocol categories only, never raw messages or token data."""
    if not isinstance(response, dict):
        return 'malformed-event'
    event = response.get('event')
    if event == 'ms.channel.unauthorized':
        return 'unauthorized'
    if event == 'ms.error':
        data = response.get('data')
        message = data.get('message') if isinstance(data, dict) else None
        if isinstance(message, str) and 'unrecognized method' in message.lower():
            return 'method-rejected'
        return 'server-error'
    if event in {'ms.channel.connect', 'ms.channel.clientConnect',
                 'ms.channel.clientDisconnect', 'ed.apps.launch',
                 'ed.installedApp.get', 'ms.remote.imeStart', 'ms.remote.imeEnd'}:
        return event
    return 'other-event'


def collect_receipts(tv, duration=3):
    """Observe a bounded response window. Silence is not an execution ACK."""
    if not 0 < duration <= 3:
        raise ValueError('Receipt window must be at most three seconds')
    connection = tv.connection
    if connection is None:
        raise RuntimeError('No established control channel')
    from websocket import WebSocketTimeoutException
    previous_timeout = connection.gettimeout()
    end = time.monotonic() + duration
    receipts = []
    try:
        while len(receipts) < 16:
            remaining = end - time.monotonic()
            if remaining <= 0:
                break
            connection.settimeout(remaining)
            try:
                payload = connection.recv()
            except (WebSocketTimeoutException, TimeoutError):
                break
            if not payload:
                receipts.append('channel-closed')
                break
            try:
                receipt = classify_receipt(json.loads(payload))
            except (ValueError, TypeError):
                receipt = 'malformed-event'
            receipts.append(receipt)
            if receipt in {'unauthorized', 'method-rejected', 'server-error', 'malformed-event'}:
                break
    finally:
        connection.settimeout(previous_timeout)
    return receipts


def send_allowed_key(tv, key, mode):
    if key not in KEYS or mode not in {'click', 'press-release'}:
        raise ValueError('Unsupported key or input mode')
    if mode == 'press-release':
        # A short ordinary key press, not a factory sequence or long power hold.
        if key == 'KEY_POWER':
            raise ValueError('Power is excluded from alternate input tests')
        tv.send_key(key, cmd='Press', key_press_delay=0)
        try:
            time.sleep(0.15)
        finally:
            tv.send_key(key, cmd='Release', key_press_delay=0)
    else:
        tv.send_key(key)


def read_token(path=TOKEN):
    flags = os.O_RDONLY | os.O_NOFOLLOW
    fd = os.open(path, flags)
    with os.fdopen(fd) as file:
        metadata = os.fstat(file.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid():
            raise RuntimeError('Token ownership is invalid')
        if stat.S_IMODE(metadata.st_mode) != 0o600:
            raise RuntimeError('Token must have mode 0600')
        token = file.read(1025).strip()
        if not token or len(token) > 1024 or not token.isascii() or not token.isdigit():
            raise RuntimeError('Approval token is missing or invalid')
        return token


def check_model(info):
    if info.get('device', {}).get('modelName') != MODEL:
        raise RuntimeError('TV model mismatch')


def require_reported_browser(apps):
    if not isinstance(apps, list) or not any(
        isinstance(app, dict) and app.get('appId') == BROWSER_ID for app in apps
    ):
        raise RuntimeError('TV did not report the expected installed browser')


def require_sdk_browser(output):
    # Exact TV-reported application entry, not a guessed ID or a cached declaration.
    if '[exit:0]' not in output.splitlines() or not any(
        line.split() == ["'Internet'", "'org.tizen.browser'"] for line in output.splitlines()
    ):
        raise RuntimeError('SDK query did not verify the installed Internet browser')


def verify_sdk_browser():
    result = subprocess.run(
        (str(BASE / 'root-access/s95f-access.py'), 'sdk', '--timeout', '10',
         '--command', 'app_launcher --list | grep -F "\'org.tizen.browser\'"; true'),
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError('Bounded SDK browser verification failed')
    require_sdk_browser(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--key', choices=KEYS, help='Explicitly send one normal remote key; omitted means connection test only')
    action.add_argument('--list-apps', action='store_true', help='Query installed apps; report only browser availability')
    action.add_argument('--open-diagnostics', action='store_true', help='Open only the fixed local diagnostic page after browser verification; no pattern starts automatically')
    parser.add_argument('--browser-check', choices=('ws', 'sdk'), default='ws',
                        help='SDK is an explicit alternative installed-app query, not an automatic retry; requires the exact-build access guard')
    parser.add_argument('--key-mode', choices=('click', 'press-release'), default='click',
                        help='Explicit alternate short key test; no fallback or repeated input')
    args = parser.parse_args()
    if args.browser_check == 'sdk' and not (args.list_apps or args.open_diagnostics):
        parser.error('--browser-check sdk requires an explicit browser action')
    if args.key_mode != 'click' and (not args.key or args.key == 'KEY_POWER'):
        parser.error('--key-mode press-release requires a normal non-power key')
    os.umask(0o077)
    from samsungtvws import SamsungTVWS
    with (BASE / 'private/s95f-remote.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        token = read_token()  # Fail before connecting rather than silently re-pairing.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as route:
            route.connect((HOST, 8002))
            if route.getsockname()[0] != CONTROLLER:
                raise RuntimeError('Controller route changed')
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://{HOST}:8001/api/v2/', timeout=5) as response:
            info = json.load(response)
        check_model(info)
        if args.open_diagnostics:
            if info.get('device', {}).get('PowerState') != 'on':
                raise RuntimeError('TV must already be on; no automatic wake')
            with opener.open(DIAGNOSTICS_URL + 'status', timeout=3) as response:
                if json.load(response).get('diagnostic_only') is not True:
                    raise RuntimeError('Diagnostic preview is unavailable')
        if args.browser_check == 'sdk':
            verify_sdk_browser()
        tv = SamsungTVWS(host=HOST, port=8002, name=NAME, token=token, timeout=10)
        try:
            tv.open()
            if args.key:
                if args.key_mode == 'press-release':
                    time.sleep(1)  # One explicit connection-settling test, not a retry loop.
                send_allowed_key(tv, args.key, args.key_mode)
            result = {'connected': True, 'model': MODEL,
                      'key_sent': args.key, 'key_mode': args.key_mode,
                      'authorization': 'saved-token'}
            if args.list_apps or args.open_diagnostics:
                if args.browser_check == 'ws':
                    apps = tv.app_list()
                    require_reported_browser(apps)
                result['browser_reported'] = BROWSER_ID
                result['browser_check'] = args.browser_check
            if args.open_diagnostics:
                tv.open_browser(DIAGNOSTICS_URL)
                result['browser_launch_sent'] = DIAGNOSTICS_URL
                result['visual_confirmation_required'] = True
            if args.key or args.open_diagnostics:
                result['protocol_receipts'] = collect_receipts(tv)
                result['execution_confirmed'] = False
                if any(receipt in {'unauthorized', 'method-rejected', 'server-error',
                                   'malformed-event', 'channel-closed'}
                       for receipt in result['protocol_receipts']):
                    result['control_error'] = True
                    print(json.dumps(result))
                    return 1
            print(json.dumps(result))
            return 0
        finally:
            tv.close()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        # Never print raw WebSocket exceptions, URLs, messages, or tokens.
        print('Connection stopped: ' + type(error).__name__ +
              '. Check TV availability, saved permission, and reserved addresses; no automatic pairing or wake attempted.', file=sys.stderr)
        sys.exit(1)
