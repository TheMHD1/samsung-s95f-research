"""Synthetic localhost tests only. No TV, root, TEE, firmware or network peers."""
import dataclasses
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import queue
import socket
import ssl
import struct
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import section_server as server

HERE = Path(__file__).resolve().parent
DOTNET = '${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet'
CLIENT = HERE/'bin/Release/net6.0/ClientTests.dll'

class FragmentSocket:
    def __init__(self, data=b''):
        self.data = bytearray(data)
        self.sent = bytearray()
    def recv_into(self, dest):
        n = min(len(dest),len(self.data),3)
        dest[:n]=self.data[:n]
        del self.data[:n]
        return n
    def send(self, data):
        n=min(2,len(data));self.sent.extend(data[:n]);return n

class Tests(unittest.TestCase):
    cases = 0
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.base=Path(cls.temp.name)
        cls.key=cls.base/'key.pem';cls.cert=cls.base/'cert.pem'
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-sha256','-nodes','-days','1','-subj','/CN=localhost','-keyout',str(cls.key),'-out',str(cls.cert)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        cls.key.chmod(0o600)
        cls.pin=hashlib.sha256(ssl.PEM_cert_to_DER_cert(cls.cert.read_text())).hexdigest()
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def setUp(self):
        type(self).cases+=1
        self.private=self.base/str(type(self).cases);self.private.mkdir(mode=0o700)
    def config(self, count=1040, **updates):
        data=bytes((i*17+3)%256 for i in range(count))
        source=self.private/'whole-msd.synthetic';source.write_bytes(b'outside-prefix'+data+b'outside-suffix');source.chmod(0o600)
        c=server.ServerConfig(str(source),14,count,hashlib.sha256(data).hexdigest(),count,str(self.cert),str(self.key),b'N'*32,str(self.private/'output'),bind_ipv4='127.0.0.1',total_timeout_seconds=5)
        return dataclasses.replace(c,**updates)
    def start(self,c):
        ready=queue.Queue();done=queue.Queue()
        t=threading.Thread(target=lambda:done.put(server.serve(c,ready.put)),daemon=True);t.start()
        return ready.get(timeout=4),done,t
    def client(self,c,ready,mode='complete',**updates):
        d=dict(host='127.0.0.1',port=ready['port'],certificate_sha256=self.pin,nonce=c.nonce.hex(),cipher_bytes=c.cipher_bytes,cipher_sha256=c.cipher_sha256,maximum_output_bytes=c.maximum_output_bytes,io_timeout_seconds=2,total_timeout_seconds=5,mode=mode)
        d.update(updates);p=self.private/'client.json';p.write_text(json.dumps(d));p.chmod(0o600)
        return subprocess.run([DOTNET,str(CLIENT),str(p)],capture_output=True,text=True,timeout=9)
    def connect(self,c,ready):
        ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);ctx.check_hostname=False;ctx.verify_mode=ssl.CERT_NONE
        sock=ctx.wrap_socket(socket.create_connection(('127.0.0.1',ready['port']),timeout=2),server_hostname='localhost')
        sock.sendall(b'HCGT1'+c.nonce)
        self.assertEqual(self.recv(sock,6),b'AH\0\0\0\0')
        return sock
    @staticmethod
    def recv(sock,n):
        b=bytearray()
        while len(b)<n:
            x=sock.recv(n-len(b))
            if not x:break
            b.extend(x)
        return bytes(b)
    def test_fragment_helpers(self):
        fake=FragmentSocket(b'abcdefghijk');self.assertEqual(server._exact(fake,11,lambda _:None),b'abcdefghijk')
        server._send(fake,b'123456789',lambda _:None);self.assertEqual(fake.sent,b'123456789')
        pieces=[]
        def partial(fd,data):pieces.append(bytes(data[:2]));return min(2,len(data))
        with patch.object(server.os,'write',partial):server._write(99,b'abcdefg')
        self.assertEqual(b''.join(pieces),b'abcdefg')
        with self.assertRaises(server.ProtocolError):server._exact(FragmentSocket(),1,lambda _:None)
    def test_cross_language_small(self):
        self.success(1040)
    def test_cross_language_many_chunks(self):
        self.success(166416)
    def success(self,count):
        c=self.config(count);ready,done,t=self.start(c);p=self.client(c,ready)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertEqual(p.stdout,'raw_complete\n')
        r=done.get(timeout=3);t.join(1)
        self.assertEqual(r['status'],'raw_complete');self.assertEqual(r['cipher_bytes'],count);self.assertEqual(r['raw_bytes'],count)
        self.assertFalse(r['payload_authenticity_validated']);self.assertFalse(r['full_schema_validated'])
        output=Path(c.output_directory)/'raw-complete.bin';self.assertEqual(output.stat().st_mode & 0o777,0o600);self.assertEqual(output.read_bytes(),b'\xa5'*count)
        self.assertFalse((output.parent/'private.partial').exists());self.assertEqual(r['connections_accepted'],1)
    def test_wrong_certificate(self):
        c=self.config();ready,done,t=self.start(c);p=self.client(c,ready,certificate_sha256='0'*64)
        self.assertEqual(p.returncode,1);r=done.get(timeout=3);self.assertFalse(r['raw_complete']);self.assertFalse((Path(c.output_directory)/'private.partial').exists())
    def test_wrong_nonce(self):
        c=self.config();ready,done,t=self.start(c);p=self.client(c,ready,nonce='00'*32)
        self.assertEqual(p.returncode,1);r=done.get(timeout=3);self.assertEqual(r['error_code'],3);self.assertFalse((Path(c.output_directory)/'private.partial').exists())
    def test_abort_retains_partial(self):
        c=self.config();ready,done,t=self.start(c);p=self.client(c,ready,mode='abort')
        self.assertEqual(p.returncode,0);r=done.get(timeout=3);self.assertEqual(r['status'],'aborted');self.assertEqual((Path(c.output_directory)/'private.partial').read_bytes(),b'\xa5'*16);self.assertFalse((Path(c.output_directory)/'raw-complete.bin').exists())
    def test_early_completion_rejected_client(self):
        c=self.config();ready,done,t=self.start(c);p=self.client(c,ready,mode='early_complete')
        self.assertEqual(p.returncode,1);r=done.get(timeout=3);self.assertFalse(r['raw_complete']);self.assertTrue((Path(c.output_directory)/'private.partial').exists())
    def test_client_overflow_rejected_without_second_write(self):
        c=self.config();ready,done,t=self.start(c);p=self.client(c,ready,mode='overflow')
        self.assertEqual(p.returncode,1);r=done.get(timeout=3);self.assertEqual(r['raw_bytes'],1040);self.assertFalse(r['raw_complete'])
    def test_bad_prehash_never_ready(self):
        c=self.config(cipher_sha256='0'*64);called=[];r=server.serve(c,called.append)
        self.assertEqual(called,[]);self.assertEqual(r['error_code'],2);self.assertFalse(Path(c.output_directory).exists())
    def test_server_rejects_frame_lengths(self):
        for bad in (0,65537,0xffffffff):
            directory=self.private/str(bad);directory.mkdir(mode=0o700)
            c=dataclasses.replace(self.config(),output_directory=str(directory/'out'))
            ready,done,t=self.start(c);sock=self.connect(c,ready);sock.sendall(b'R'+struct.pack('>I',bad));self.assertEqual(self.recv(sock,3),b'E\0\4');sock.close();self.assertEqual(done.get(timeout=3)['error_code'],4)
    def test_server_rejects_write_overflow(self):
        c=self.config(maximum_output_bytes=16);ready,done,t=self.start(c);sock=self.connect(c,ready);sock.sendall(b'W'+struct.pack('>I',17));self.assertEqual(self.recv(sock,3),b'E\0\5');sock.close();self.assertEqual(done.get(timeout=3)['raw_bytes'],0)
    def test_server_rejects_early_commit(self):
        c=self.config();ready,done,t=self.start(c);sock=self.connect(c,ready);sock.sendall(b'C');self.assertEqual(self.recv(sock,3),b'E\0\4');sock.close();self.assertFalse(done.get(timeout=3)['raw_complete'])
    def test_source_mutation_fails_completion(self):
        c=self.config();ready,done,t=self.start(c);sock=self.connect(c,ready)
        sock.sendall(b'R'+struct.pack('>I',1040));self.assertEqual(self.recv(sock,5),b'D'+struct.pack('>i',1040));self.assertEqual(len(self.recv(sock,1040)),1040)
        with open(c.source_path,'r+b') as f:f.seek(c.source_offset);f.write(b'X')
        sock.sendall(b'R'+struct.pack('>I',1));self.assertEqual(self.recv(sock,3),b'E\0\2');sock.close();self.assertEqual(done.get(timeout=3)['error_code'],2)
    def test_total_timeout_before_handshake(self):
        c=self.config(total_timeout_seconds=1);ready,done,t=self.start(c)
        raw=socket.create_connection(('127.0.0.1',ready['port']),timeout=2)
        start=time.monotonic();r=done.get(timeout=3);raw.close();self.assertLess(time.monotonic()-start,2.5);self.assertFalse(r['raw_complete'])
    def test_invalid_config_no_listener(self):
        c=self.config()
        for updates in ({'source_offset':-1},{'cipher_bytes':15},{'maximum_output_bytes':1041},{'nonce':b'x'},{'port':True},{'io_timeout_seconds':11},{'total_timeout_seconds':7201}):
            called=[];r=server.serve(dataclasses.replace(c,**updates),called.append);self.assertEqual(called,[]);self.assertEqual(r['error_code'],1)
    def malicious_peer(self, reply, total_timeout=5):
        c=self.config();ready=queue.Queue();done=queue.Queue()
        def peer():
            listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1)
            ready.put({'port':listener.getsockname()[1]})
            conn=None
            try:
                raw,_=listener.accept();raw.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
                ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.load_cert_chain(self.cert,self.key)
                conn=ctx.wrap_socket(raw,server_side=True);conn.settimeout(3)
                if len(self.recv(conn,37))!=37:raise RuntimeError()
                for x in b'AH\0\0\0\0':conn.sendall(bytes([x]))
                request=self.recv(conn,5)
                if reply is None:
                    # Client total timer must close blocked Read, not wait for us.
                    self.recv(conn,1)
                else:
                    for x in reply:conn.sendall(bytes([x]))
                done.put(request)
            except Exception:done.put(b'peer_error')
            finally:
                if conn is not None:conn.close()
                listener.close()
        t=threading.Thread(target=peer,daemon=True);t.start();r=ready.get(timeout=2)
        start=time.monotonic();p=self.client(c,r,total_timeout_seconds=total_timeout)
        self.assertEqual(p.returncode,1);self.assertEqual(done.get(timeout=4)[:1],b'R');t.join(1)
        return time.monotonic()-start
    def test_client_rejects_negative_reply(self):
        self.malicious_peer(b'D'+struct.pack('>i',-1))
    def test_client_rejects_oversized_reply(self):
        self.malicious_peer(b'D'+struct.pack('>i',1041))
    def test_client_rejects_premature_eof(self):
        self.malicious_peer(b'D'+struct.pack('>i',0))
    def test_client_total_deadline_interrupts_read(self):
        elapsed=self.malicious_peer(None,total_timeout=1);self.assertLess(elapsed,2.5)
    def test_fresh_output_only(self):
        c=self.config();Path(c.output_directory).mkdir(mode=0o700);r=server.serve(c,lambda _:self.fail('must not listen'));self.assertFalse(r['raw_complete'])

if __name__=='__main__':unittest.main()
