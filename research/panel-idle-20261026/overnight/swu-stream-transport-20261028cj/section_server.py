"""Single fixed-range, single-connection private raw-quarantine TLS server.
No imports start listeners. No secret or content diagnostics are emitted.
"""
from dataclasses import dataclass
import hashlib
import hmac
import ipaddress
import os
from pathlib import Path
import socket
import ssl
import stat
import struct
import threading
import time

CHUNK = 65536

@dataclass(frozen=True)
class ServerConfig:
    source_path: str
    source_offset: int
    cipher_bytes: int
    cipher_sha256: str
    maximum_output_bytes: int
    certificate_path: str
    private_key_path: str
    nonce: bytes
    output_directory: str
    bind_ipv4: str = '198.51.100.10'
    port: int = 0
    io_timeout_seconds: int = 10
    total_timeout_seconds: int = 90

class ProtocolError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__('transport_rejected')

def _identity(fd):
    s = os.fstat(fd)
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid,
            s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)

def _exact(sock, length, budget):
    data = bytearray(length)
    done = 0
    while done < length:
        budget(sock)
        n = sock.recv_into(memoryview(data)[done:])
        if n <= 0:
            raise ProtocolError(6)
        done += n
    return data

def _send(sock, data, budget):
    done = 0
    while done < len(data):
        budget(sock)
        n = sock.send(memoryview(data)[done:])
        if n <= 0:
            raise ProtocolError(6)
        done += n

def _write(fd, data):
    done = 0
    while done < len(data):
        n = os.write(fd, memoryview(data)[done:])
        if n <= 0:
            raise ProtocolError(7)
        done += n

def _ack(sock, op, count, budget):
    _send(sock, b'A' + op + struct.pack('>I', count), budget)

def _validate(c):
    ints = (c.source_offset, c.cipher_bytes, c.maximum_output_bytes, c.port,
            c.io_timeout_seconds, c.total_timeout_seconds)
    if (not all(type(x) is int for x in ints) or c.source_offset < 0 or
        not 16 <= c.cipher_bytes <= 2147483648 or c.cipher_bytes % 16 or
        not 1 <= c.maximum_output_bytes <= c.cipher_bytes or
        not 0 <= c.port <= 65535 or not 1 <= c.io_timeout_seconds <= 10 or
        not 1 <= c.total_timeout_seconds <= 7200 or
        type(c.nonce) is not bytes or len(c.nonce) != 32 or
        type(c.cipher_sha256) is not str or len(c.cipher_sha256) != 64 or
        any(ch not in '0123456789abcdef' for ch in c.cipher_sha256) or
        not all(Path(p).is_absolute() for p in (c.source_path, c.certificate_path,
                    c.private_key_path, c.output_directory))):
        raise ProtocolError(1)
    if ipaddress.ip_address(c.bind_ipv4).version != 4:
        raise ProtocolError(1)

def serve(config, ready_callback=None):
    """Prehash range, listen once, notify {'host','port'}, serve one nonce.

    Returned counts/status are transport evidence only. A completed output remains
    private raw quarantine. Config is local trusted state, never received on wire.
    Network I/O is bounded by per-call and total timers; regular-file kernel I/O
    cannot be forcibly cancelled by this Python thread.
    """
    c = config
    started = time.monotonic()
    source = out = None
    listener = connection = None
    timer = None
    handles = []
    result = dict(status='failed', error_code=0, cipher_bytes=0, raw_bytes=0,
                  raw_complete=False, payload_authenticity_validated=False,
                  full_schema_validated=False, connections_accepted=0)
    deadline = started + c.total_timeout_seconds if type(c.total_timeout_seconds) is int else started
    def budget(sock=None):
        left = deadline - time.monotonic()
        if left <= 0:
            raise ProtocolError(8)
        if sock is not None:
            sock.settimeout(min(c.io_timeout_seconds, left))
    def expire():
        # shutdown wakes blocking socket I/O; no TEEC operation/retry here.
        for item in list(handles):
            try: item.shutdown(socket.SHUT_RDWR)
            except OSError: pass
            try: item.close()
            except OSError: pass
    try:
        _validate(c)
        source = os.open(c.source_path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        identity = _identity(source)
        if not stat.S_ISREG(identity[2]) or identity[2] & 0o022 or c.source_offset+c.cipher_bytes > identity[6]:
            raise ProtocolError(2)
        key_stat = os.stat(c.private_key_path, follow_symlinks=False)
        if not stat.S_ISREG(key_stat.st_mode) or key_stat.st_uid != os.getuid() or key_stat.st_mode & 0o077:
            raise ProtocolError(2)
        digest = hashlib.sha256()
        cursor = 0
        while cursor < c.cipher_bytes:
            budget()
            data = os.pread(source, min(CHUNK, c.cipher_bytes-cursor), c.source_offset+cursor)
            if not data: raise ProtocolError(2)
            digest.update(data)
            cursor += len(data)
        if not hmac.compare_digest(digest.hexdigest(), c.cipher_sha256) or _identity(source) != identity:
            raise ProtocolError(2)
        parent = Path(c.output_directory).parent
        ps = parent.stat()
        if ps.st_uid != os.getuid() or ps.st_mode & 0o077:
            raise ProtocolError(2)
        os.mkdir(c.output_directory, 0o700) # exclusive fresh leaf, never reuse
        directory = os.stat(c.output_directory, follow_symlinks=False)
        if not stat.S_ISDIR(directory.st_mode) or directory.st_uid != os.getuid() or directory.st_mode & 0o077:
            raise ProtocolError(2)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(c.certificate_path, c.private_key_path)
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        handles.append(listener)
        listener.bind((c.bind_ipv4, c.port))
        listener.listen(1)
        timer = threading.Timer(max(0.001, deadline-time.monotonic()), expire)
        timer.daemon = True
        timer.start()
        if ready_callback is not None:
            ready_callback({'host': c.bind_ipv4, 'port': listener.getsockname()[1]})
        budget(listener)
        connection, _ = listener.accept()
        result['connections_accepted'] = 1
        handles.append(connection)
        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        listener.close()
        budget(connection)
        connection = context.wrap_socket(connection, server_side=True)
        handles.append(connection)
        hello = _exact(connection, 37, budget)
        try:
            if hello[:5] != b'HCGT1' or not hmac.compare_digest(hello[5:], c.nonce):
                raise ProtocolError(3)
        finally:
            hello[:] = b'\0'*len(hello)
        out = os.open(str(Path(c.output_directory)/'private.partial'),
                      os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
        _ack(connection, b'H', 0, budget)
        cursor = 0
        written = 0
        eof = False
        streamed = hashlib.sha256()
        frames = 0
        while True:
            frames += 1
            if frames > c.cipher_bytes+c.maximum_output_bytes+8:
                raise ProtocolError(4)
            op = bytes(_exact(connection, 1, budget))
            if op in (b'R', b'W'):
                count = struct.unpack('>I', _exact(connection, 4, budget))[0]
                if not 1 <= count <= CHUNK:
                    raise ProtocolError(4)
                if op == b'R':
                    if eof: raise ProtocolError(4)
                    n = min(count, c.cipher_bytes-cursor)
                    data = bytearray()
                    while len(data) < n:
                        budget()
                        part = os.pread(source, n-len(data), c.source_offset+cursor+len(data))
                        if not part: raise ProtocolError(2)
                        data.extend(part)
                    try:
                        if n == 0:
                            if not hmac.compare_digest(streamed.hexdigest(), c.cipher_sha256) or _identity(source) != identity:
                                raise ProtocolError(2)
                            eof = True
                        else: streamed.update(data)
                        _send(connection, b'D'+struct.pack('>i', n), budget)
                        _send(connection, data, budget)
                        cursor += n
                        result['cipher_bytes'] = cursor
                    finally: data[:] = b'\0'*len(data)
                else:
                    if count > c.maximum_output_bytes-written:
                        raise ProtocolError(5)
                    data = _exact(connection, count, budget)
                    try: _write(out, data)
                    finally: data[:] = b'\0'*len(data)
                    written += count
                    result['raw_bytes'] = written
                    _ack(connection, b'W', count, budget)
            elif op == b'C':
                if not eof or cursor != c.cipher_bytes or _identity(source) != identity:
                    raise ProtocolError(4)
                os.fsync(out)
                info = os.fstat(out)
                if info.st_size != written or info.st_mode & 0o077 or info.st_nlink != 1:
                    raise ProtocolError(7)
                os.close(out)
                out = None
                # Same fresh private directory; no public promotion or auth claim.
                os.rename(str(Path(c.output_directory)/'private.partial'), str(Path(c.output_directory)/'raw-complete.bin'))
                directory_fd = os.open(c.output_directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                try: os.fsync(directory_fd)
                finally: os.close(directory_fd)
                result.update(status='raw_complete', raw_complete=True)
                _ack(connection, b'C', 0, budget)
                return result
            elif op == b'F':
                os.close(out)
                out = None
                result['status'] = 'aborted'
                _ack(connection, b'F', 0, budget)
                return result
            else:
                raise ProtocolError(4)
    except Exception as exc:
        code = exc.code if isinstance(exc, ProtocolError) else 9
        result['error_code'] = code
        # If rename happened but its ACK was lost, host raw_complete may be true
        # while client reports failure. Never infer peer acceptance or retry.
        if connection is not None:
            try: _send(connection, b'E'+struct.pack('>H', code), budget)
            except Exception: pass
        return result
    finally:
        if timer is not None: timer.cancel()
        if out is not None: os.close(out)
        if source is not None: os.close(source)
        for item in handles:
            try: item.close()
            except OSError: pass
