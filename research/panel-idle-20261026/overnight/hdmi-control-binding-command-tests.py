#!/usr/bin/env python3
"""Execute the generated HDMI-binding shell only against local fake proc fixtures."""
from pathlib import Path
import importlib.util, os, struct, subprocess, tempfile, unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('binding_candidate',HERE/'read-hdmi-control-binding.py')
candidate=importlib.util.module_from_spec(spec); spec.loader.exec_module(candidate)

MAIN_HASH='067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410'
IMPL_HASH='5eaef7e92eac9468bf41073ccece56a64a70339c3056c3ca2b62391171f4d2a1'
MAINWORD,IMPLWORD=1148733441,4022383920
TABLE,CALLBACK=0x60000000,0x50008575

class CommandFixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='binding-command-fixture-')
        self.root=Path(self.temp.name); self.bin=self.root/'bin'; self.bin.mkdir()
        self.main=self.root/'main.so'; self.impl=self.root/'impl.so'; self.mem=self.root/'mem'; self.state=self.root/'dd-state'
        self.main.write_bytes(b'M'); self.impl.write_bytes(b'I'); self.mem.write_bytes(b'')
        self.maps=self.root/'maps'; self.maps.write_text(self.map_text())
        self.write_mocks()
    def tearDown(self): self.temp.cleanup()
    def map_text(self, *, duplicate=False, changed=False):
        mb='47d10000' if changed else '47e10000'
        rows=[f'{mb}-47e70000 r-xp 00000000 08:01 456 {self.main}',
              f'47e80000-47e90000 rw-p 00070000 08:01 456 {self.main}',
              f'50000000-50010000 r-xp 00000000 08:01 457 {self.impl}',
              '60000000-60001000 rw-p 00000000 00:00 0 [anon]']
        if duplicate: rows.insert(1,f'47e20000-47e70000 r-xp 00000000 08:01 456 {self.main}')
        return '\n'.join(rows)+'\n'
    def write(self, name, content):
        p=self.bin/name; p.write_text(content); p.chmod(0o755)
    def write_mocks(self):
        self.write('cat',f'''#!/bin/sh
case "$1" in
  /proc/sys/kernel/random/boot_id) if [ "${{FIXTURE_BAD_BOOT:-}}" ]; then echo bad-boot; else echo 00000000-0000-4000-8000-000000000000; fi;;
  /proc/uptime) echo '100.00 1.00';;
  /proc/706/stat) if [ "${{FIXTURE_BAD_START:-}}" ]; then echo '706 (avocd) S 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 604'; else echo '706 (avocd) S 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 603'; fi;;
  /proc/*) exit 97;;
  *) exec /bin/cat "$@";;
esac
''')
        self.write('readlink','#!/bin/sh\nif [ "${FIXTURE_BAD_EXE:-}" ]; then echo /usr/bin/other; else echo /usr/bin/avocd; fi\n')
        self.write('date','#!/bin/sh\necho 100\n')
        self.write('stat',f'''#!/bin/sh
case "$3" in {self.main}) if [ "${{FIXTURE_BAD_STAT:-}}" ]; then echo '2050 456'; else echo '2049 456'; fi;; {self.impl}) if [ "${{FIXTURE_BAD_IMPL_STAT:-}}" ]; then echo '2050 457'; else echo '2049 457'; fi;; *) exit 1;; esac
''')
        self.write('sha256sum',f'''#!/bin/sh
for x in "$@"; do case "$x" in {self.main}) if [ "${{FIXTURE_BAD_HASH:-}}" ]; then echo '0{MAIN_HASH[1:]}  {self.main}'; else echo '{MAIN_HASH}  {self.main}'; fi;; {self.impl}) echo '{IMPL_HASH}  {self.impl}';; *) exit 1;; esac; done
''')
        values=[MAINWORD,IMPLWORD,0x100,TABLE,CALLBACK]*2
        self.write('dd',f'''#!/usr/bin/env python3
from pathlib import Path
import os,struct,sys
root=Path({str(self.root)!r}); state=root/'dd-state'; n=int(state.read_text()) if state.exists() else 0
vals={values!r}; fail=os.environ.get('FIXTURE_DD_FAIL')
if os.environ.get('FIXTURE_ZERO_FLAG'): vals[2]=vals[7]=0
if os.environ.get('FIXTURE_EVEN_CALLBACK'): vals[4]=vals[9]-1
if os.environ.get('FIXTURE_WRONG_CALLBACK'): vals[4]=vals[9]=0x50008577
if os.environ.get('FIXTURE_CHANGE_END'): vals[7]=0x101
if fail is not None and n==int(fail): sys.exit(1)
if n>=len(vals): sys.exit(1)
blob=struct.pack('<I',vals[n]);
if os.environ.get('FIXTURE_DD_TRUNC') and n==int(os.environ['FIXTURE_DD_TRUNC']): blob=blob[:3]
sys.stdout.buffer.write(blob); state.write_text(str(n+1))
print('1+0 records in',file=sys.stderr);print('1+0 records out',file=sys.stderr);print('4 bytes (4 B) copied, 3.4413e-05 s, 116 kB/s',file=sys.stderr)
if n==4 and os.environ.get('FIXTURE_MAP_CHANGE'): (root/'maps').write_text({self.map_text(changed=True)!r})
''')
    def command(self):
        text=candidate.module.COMMAND
        text=text.replace('MAIN=/usr/lib/libhdmi-control.so.0.1',f'MAIN={self.main}')
        text=text.replace('IMPL=/prd/usr/lib/libhdmi-control-impl-sec.so.0.1',f'IMPL={self.impl}')
        text=text.replace('/proc/$P/maps',str(self.maps)).replace('/proc/$P/mem',str(self.mem))
        return text
    def invoke(self, **env):
        e=os.environ.copy(); e['PATH']=str(self.bin)+':'+e['PATH']; e.update(env)
        return subprocess.run(['bash','-c',self.command()],cwd=self.root,env=e,capture_output=True,text=True,timeout=5)
    def test_entire_generated_command_succeeds_in_local_fixture(self):
        r=self.invoke(); self.assertEqual(r.returncode,0,r.stderr); self.assertIn('@@ COMPLETE\nPASS_SAMPLED_BINDING_ONLY',r.stdout)
        self.assertEqual(r.stderr.count('1+0 records in'),10); self.assertNotIn('/proc/',r.stderr)
    def test_full_command_rejects_dd_and_snapshot_failures(self):
        for name,env in [('dd-error',{'FIXTURE_DD_FAIL':'2'}),('truncated',{'FIXTURE_DD_TRUNC':'3'}),('map-change',{'FIXTURE_MAP_CHANGE':'1'}),('changed-end',{'FIXTURE_CHANGE_END':'1'}),('zero-flag',{'FIXTURE_ZERO_FLAG':'1'}),('even-callback',{'FIXTURE_EVEN_CALLBACK':'1'}),('wrong-callback',{'FIXTURE_WRONG_CALLBACK':'1'}),('bad-start',{'FIXTURE_BAD_START':'1'}),('bad-stat',{'FIXTURE_BAD_STAT':'1'}),('bad-impl-stat',{'FIXTURE_BAD_IMPL_STAT':'1'}),('bad-hash',{'FIXTURE_BAD_HASH':'1'}),('bad-boot',{'FIXTURE_BAD_BOOT':'1'}),('bad-exe',{'FIXTURE_BAD_EXE':'1'})]:
            with self.subTest(name=name): self.assertNotEqual(self.invoke(**env).returncode,0)
    def test_full_command_rejects_duplicate_maps(self):
        self.maps.write_text(self.map_text(duplicate=True)); self.assertNotEqual(self.invoke().returncode,0)
    def test_full_command_rejects_source_and_range_failures(self):
        valid=self.map_text()
        cases={
            'storage-wrong-path':valid.replace(f'47e80000-47e90000 rw-p 00070000 08:01 456 {self.main}','47e80000-47e90000 rw-p 00070000 08:01 456 [anon]'),
            'storage-unreadable':valid.replace('47e80000-47e90000 rw-p','47e80000-47e90000 ---p'),
            'callback-nonexec':valid.replace('50000000-50010000 r-xp','50000000-50010000 r--p'),
            'callback-outside':valid.replace('50000000-50010000 r-xp','50000000-50008000 r-xp'),
            'table-crosses-map':valid.replace('60000000-60001000 rw-p','60000000-60000020 rw-p'),
            'table-unreadable':valid.replace('60000000-60001000 rw-p','60000000-60001000 ---p'),
            'malformed-map':valid.replace('60000000-60001000','6000000-60001000'),
        }
        for name,text in cases.items():
            with self.subTest(name=name):
                self.maps.write_text(text); self.assertNotEqual(self.invoke().returncode,0)
                self.maps.write_text(valid)
    def test_fixture_refuses_unexpected_real_proc_fallback(self):
        e=os.environ.copy(); e['PATH']=str(self.bin)+':'+e['PATH']
        r=subprocess.run(['bash','-c',self.command()+'\ncat /proc/self/status'],cwd=self.root,env=e,capture_output=True,text=True,timeout=5)
        self.assertEqual(r.returncode,97)

if __name__=='__main__': unittest.main()
