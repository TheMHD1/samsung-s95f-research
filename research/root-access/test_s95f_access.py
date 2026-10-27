import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location("s95f_access", Path(__file__).with_name("s95f-access.py"))
access = importlib.util.module_from_spec(spec)
spec.loader.exec_module(access)


def test_identity_accepts_exact_owner_tv():
    access.check_identity({"modelName": access.MODEL, "developerMode": "1", "developerIP": access.CONTROLLER})


@pytest.mark.parametrize("changes", [
    {"modelName": "another-tv"}, {"developerMode": "0"}, {"developerIP": "198.51.100.10"},
])
def test_identity_rejects_changes(changes):
    device = {"modelName": access.MODEL, "developerMode": "1", "developerIP": access.CONTROLLER}
    device.update(changes)
    with pytest.raises(RuntimeError):
        access.check_identity(device)


def test_build_accepts_exact_build():
    access.check_build(f"BUILD_ID={access.BUILD}\n[exit:0]\n")


@pytest.mark.parametrize("output", [
    "BUILD_ID=other\n[exit:0]\n", f"BUILD_ID={access.BUILD}\n[exit:1]\n", "",
])
def test_build_rejects_changed_or_failed_build(output):
    with pytest.raises(RuntimeError):
        access.check_build(output)


@pytest.mark.parametrize("mode,command_exit", [("sdk", 0), ("root", 0), ("root", 1)])
def test_main_uses_real_release_file_and_scoped_sdb(monkeypatch, tmp_path, mode, command_exit):
    base = tmp_path / "root-access"
    base.mkdir()
    (tmp_path / "private").mkdir()
    monkeypatch.setattr(access, "BASE", base)
    monkeypatch.setattr(access.sys, "argv", ["s95f-access", mode, "--command", "id"])
    monkeypatch.setattr(access, "route_callback_host", lambda tv: access.CONTROLLER)
    monkeypatch.setattr(access.subprocess, "run", lambda *args, **kw: SimpleNamespace(
        returncode=0, stdout="tcp dport 26099 drop"))
    device = {"modelName": access.MODEL, "developerMode": "1", "developerIP": access.CONTROLLER}
    monkeypatch.setattr(access, "build_opener", lambda *args: SimpleNamespace(
        open=lambda *a, **kw: io.BytesIO(json.dumps({"device": device}).encode())))

    class Client:
        def __init__(self, *args, **kw):
            assert args[0] == access.SDB

        def connect(self):
            pass

        def require_device(self):
            pass

        def capture(self, command, **kw):
            assert kw["bind_host"] == access.CONTROLLER
            if command == "cat /etc/tizen-release":
                return SimpleNamespace(output=f"BUILD_ID={access.BUILD}\n[exit:0]\n")
            assert command == "id"
            return SimpleNamespace(output="uid=901(sdk)\n[exit:0]\n")

    async def fake_probe(*args, **kw):
        assert access.os.environ["SDB"] == str(access.SDB)
        assert kw["payloads"] == base / "payloads"
        assert kw["commands"] == ("id",)
        return {"commands": [{"exit_code": command_exit, "timed_out": False}]}

    monkeypatch.setattr(access, "SdbClient", Client)
    monkeypatch.setattr(access, "probe", fake_probe)
    assert access.main() == command_exit


@pytest.mark.parametrize("command_exit", [0, 7])
def test_persistent_root_uses_authenticated_session_without_second_execution(monkeypatch, tmp_path, command_exit, capsys):
    base = tmp_path / 'root-access'
    (base / 'persistent').mkdir(parents=True)
    (base / 'persistent/control.sock').touch()
    (tmp_path / 'private').mkdir()
    monkeypatch.setattr(access, 'BASE', base)
    monkeypatch.setattr(access.sys, 'argv', ['s95f-access', 'root', '--command', 'owner-command'])
    monkeypatch.setattr(access, 'route_callback_host', lambda tv: access.CONTROLLER)
    monkeypatch.setattr(access.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout='tcp dport 26099 drop'))
    device = dict(modelName=access.MODEL, developerMode='1', developerIP=access.CONTROLLER)
    monkeypatch.setattr(access, 'build_opener', lambda *a: SimpleNamespace(open=lambda *a, **k: io.BytesIO(json.dumps({'device':device}).encode())))
    calls = []
    def request(value, timeout=15):
        calls.append(value)
        if value['operation'] == 'status':
            return dict(state='ready', system_files_unchanged=True)
        if value['command'] == 'cat /etc/tizen-release':
            return dict(uid=0, euid=0, exit_code=0, timed_out=False, stdout=f'BUILD_ID={access.BUILD}\n')
        assert value['command'] == 'owner-command'
        return dict(uid=0, euid=0, exit_code=command_exit, timed_out=False, stdout='result', stderr='')
    monkeypatch.setattr(access, 'persistent_request', request)
    def no_sdk(*a, **k):
        pytest.fail('Persistent execution must not fall back to a second SDK root execution')
    monkeypatch.setattr(access, 'SdbClient', no_sdk)
    assert access.main() == (0 if command_exit == 0 else 1)
    assert [c.get('command') for c in calls].count('owner-command') == 1
    result = json.loads(capsys.readouterr().out)
    assert result['commands'][0]['exit_code'] == command_exit


def test_persistent_transport_error_is_not_retried(monkeypatch, tmp_path):
    class Channel:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def settimeout(self, value): pass
        def connect(self, value): pass
        def sendall(self, value):
            submitted.append(value)
        def makefile(self, mode):
            return io.BytesIO(b'')
    submitted = []
    monkeypatch.setattr(access.socket, 'socket', lambda *a: Channel())
    with pytest.raises(RuntimeError):
        access.persistent_request({'operation':'exec', 'command':'owner-command'})
    assert len(submitted) == 1
