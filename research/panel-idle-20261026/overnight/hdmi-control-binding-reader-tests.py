#!/usr/bin/env python3
"""Local-only malformed-response fixtures for the unrun HDMI binding reader."""
from pathlib import Path
import copy, importlib.util, unittest

HERE=Path(__file__).resolve().parent
def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/name)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
reader=load('read-hdmi-control-binding.py'); parser=load('parse-hdmi-control-binding.py')

def identity():
    return [parser.BOOT,parser.EXE,'706 603',f'{parser.MAIN_HASH}  {parser.MAIN}',f'{parser.IMPL_HASH}  {parser.IMPL}',
            f'2049 456 08:01 {parser.MAIN}',f'2049 457 08:01 {parser.IMPL}']
def fixture():
    maps=['47e10000-47e70000 r-xp 00000000 08:01 456 '+parser.MAIN,
          '47e80000-47e90000 rw-p 00070000 08:01 456 '+parser.MAIN,
          '50000000-50010000 r-xp 00000000 08:01 457 '+parser.IMPL,
          '60000000-60001000 rw-p 00000000 00:00 0 [anon]']
    values='256 1610612736 1342211445 1148733441 4022383920'
    out=['@@ TIME_START','100','100.00 1.00','@@ ID_START',*identity(),'@@ BASES','0 1342177280 1206400252 1342211445','@@ MAPS_START',*maps,'@@ VALUES_START',values,'@@ VALUES_END',values,'@@ MAPS_END',*maps,'@@ ID_END',*identity(),'@@ TIME_END','101','101.00 1.00','@@ COMPLETE','PASS_SAMPLED_BINDING_ONLY']
    dd='\n'.join(['1+0 records in','1+0 records out','4 bytes (4 B) copied, 3.4413e-05 s, 116 kB/s']*10)+'\n'
    client={'model':parser.MODEL,'host':'198.51.100.20','authenticated':True,'uid':0,'euid':0,'root_persistence':'host-assisted','global_system_files_unchanged_at_acquisition':True,'commands':[{'command':reader.module.COMMAND,'exit_code':0,'timed_out':False,'stderr':dd,'stdout':'\n'.join(out)+'\n'}]}
    client_path=parser.CLIENT
    intent={'command':reader.module.COMMAND,'command_sha256':parser.COMMAND_SHA,'client_sha256':parser.CLIENT_SHA,
            'argv':['python3',str(client_path),'root','--persistent-only','--timeout','25','--command',reader.module.COMMAND],
            'purpose':reader.__doc__,'retry':False,'physical_state':'unobserved','started_utc':'2026-10-26T00:00:00+00:00'}
    return client,'',{'returncode':0,'host_timeout':False,'finished_utc':'2026-10-26T00:00:01+00:00'},intent

class BindingReaderTests(unittest.TestCase):
    def reject(self, mutate):
        c,e,r,i=fixture(); mutate(c,e,r,i)
        with self.assertRaises(ValueError): parser.validate_response(c,e,r,i)

    def test_valid_fixture(self):
        c,e,r,i=fixture(); self.assertEqual(parser.validate_response(c,e,r,i)['dd_reads'],10)

    def test_rejects_transport_and_authority_mutations(self):
        cases=[
            ('command',lambda c,e,r,i:(i.update(command=i['command']+'\n:'),i.update(command_sha256=__import__('hashlib').sha256(i['command'].encode()).hexdigest()),c['commands'][0].update(command=i['command']))),
            ('client-hash',lambda c,e,r,i:i.update(client_sha256='0'*64)),
            ('argv-persistence',lambda c,e,r,i:i['argv'].remove('--persistent-only')),
            ('purpose',lambda c,e,r,i:i.update(purpose='different')),
            ('retry',lambda c,e,r,i:i.update(retry=True)),
            ('physical',lambda c,e,r,i:i.update(physical_state='observed')),
            ('started-syntax',lambda c,e,r,i:i.update(started_utc='not-a-time')),
            ('finished-syntax',lambda c,e,r,i:r.update(finished_utc='not-a-time')),
            ('host-order',lambda c,e,r,i:r.update(finished_utc='2026-10-25T23:59:59+00:00')),
            ('result-extra',lambda c,e,r,i:r.update(extra=True)),
            ('host',lambda c,e,r,i:c.update(host='192.0.2.1')),
            ('global-state',lambda c,e,r,i:c.update(global_system_files_unchanged_at_acquisition=False)),
            ('client-extra',lambda c,e,r,i:c.update(extra=True)),
            ('command-extra',lambda c,e,r,i:c['commands'][0].update(extra=True)),
            ('host-stderr',lambda c,e,r,i:None),
        ]
        for name,mutate in cases:
            with self.subTest(name=name):
                c,e,r,i=fixture(); mutate(c,e,r,i)
                if name=='host-stderr': e='unexpected\n'
                with self.assertRaises(ValueError): parser.validate_response(c,e,r,i)

    def test_rejects_framing_identity_and_result_mutations(self):
        for name, mutate in [
            ('duplicate-marker',lambda c,e,r,i:c['commands'][0].update(stdout=c['commands'][0]['stdout'].replace('@@ COMPLETE','@@ VALUES_START\n0 0 0 0 0\n@@ COMPLETE'))),
            ('maps-invalid',lambda c,e,r,i:c['commands'][0].update(stdout=c['commands'][0]['stdout'].replace('r-xp 00000000','z-xp 00000000',1))),
            ('wrong-device',lambda c,e,r,i:c['commands'][0].update(stdout=c['commands'][0]['stdout'].replace('08:01 '+parser.MAIN,'08:02 '+parser.MAIN))),
            ('zero-flag',lambda c,e,r,i:c['commands'][0].update(stdout=c['commands'][0]['stdout'].replace('256 1610612736 1342211445','0 1610612736 1342211445'))),
            ('even-callback',lambda c,e,r,i:c['commands'][0].update(stdout=c['commands'][0]['stdout'].replace('1610612736 1342211445','1610612736 1342211444'))),
            ('wrong-codeword',lambda c,e,r,i:c['commands'][0].update(stdout=c['commands'][0]['stdout'].replace('1148733441','1'))),
            ('changed-snapshot',lambda c,e,r,i:c['commands'][0].update(stdout=c['commands'][0]['stdout'].replace('@@ VALUES_END\n256 1610612736 1342211445','@@ VALUES_END\n2 1610612736 1342211445'))),
            ('changed-boot',lambda c,e,r,i:c['commands'][0].update(stdout=c['commands'][0]['stdout'].replace(parser.BOOT,'x'+parser.BOOT,1))),
            ('extra-remote-stderr',lambda c,e,r,i:c['commands'][0].update(stderr=c['commands'][0]['stderr']+'unexpected\n')),
            ('bad-result',lambda c,e,r,i:r.update(returncode=1)),
        ]:
            with self.subTest(name=name):
                c,e,r,i=fixture()
                mutate(c,e,r,i)
                with self.assertRaises(ValueError): parser.validate_response(c,e,r,i)

    def test_rejects_source_map_and_derived_address_mutations(self):
        def stdout(c): return c['commands'][0]['stdout']
        def change(c,old,new): c['commands'][0]['stdout']=stdout(c).replace(old,new)
        cases=[
            ('second-main-row-identity',lambda c,e,r,i:change(c,'47e80000-47e90000 rw-p 00070000 08:01 456 '+parser.MAIN,'47e80000-47e90000 rw-p 00070000 08:02 456 '+parser.MAIN)),
            ('stat-device-encoding',lambda c,e,r,i:change(c,'2049 456 08:01 '+parser.MAIN,'2049 456 08:02 '+parser.MAIN)),
            ('duplicate-main-load',lambda c,e,r,i:change(c,'@@ VALUES_START','47e20000-47e70000 r-xp 00000000 08:01 456 '+parser.MAIN+'\n@@ VALUES_START')),
            ('storage-wrong-path',lambda c,e,r,i:change(c,'47e80000-47e90000 rw-p 00070000 08:01 456 '+parser.MAIN,'47e80000-47e90000 rw-p 00070000 08:01 456 /other')),
            ('storage-unreadable',lambda c,e,r,i:change(c,'47e80000-47e90000 rw-p','47e80000-47e90000 ---p')),
            ('callback-nonexec',lambda c,e,r,i:change(c,'50000000-50010000 r-xp','50000000-50010000 r--p')),
            ('table-crosses-end',lambda c,e,r,i:change(c,'60000000-60001000 rw-p','60000000-60000020 rw-p')),
            ('table-unreadable',lambda c,e,r,i:change(c,'60000000-60001000 rw-p','60000000-60001000 ---p')),
            ('unaligned-map',lambda c,e,r,i:change(c,'60000000-60001000','60000001-60001000')),
            ('wrong-main-bias',lambda c,e,r,i:change(c,'@@ BASES\n0 1342177280','@@ BASES\n4096 1342177280')),
        ]
        for name,mutate in cases:
            with self.subTest(name=name): self.reject(mutate)

    def test_rejects_nonfinite_unbounded_or_reversed_times(self):
        cases=[
            ('uptime-infinity',lambda c,e,r,i:c['commands'][0].update(stdout=c['commands'][0]['stdout'].replace('101.00 1.00','9'*400+' 1.00'))),
            ('uptime-too-long',lambda c,e,r,i:c['commands'][0].update(stdout=c['commands'][0]['stdout'].replace('101.00 1.00','127.00 1.00'))),
            ('wall-too-long',lambda c,e,r,i:c['commands'][0].update(stdout=c['commands'][0]['stdout'].replace('@@ TIME_END\n101','@@ TIME_END\n127'))),
            ('idle-reversed',lambda c,e,r,i:c['commands'][0].update(stdout=c['commands'][0]['stdout'].replace('101.00 1.00','101.00 0.50'))),
        ]
        for name,mutate in cases:
            with self.subTest(name=name): self.reject(mutate)

    def test_rejects_ungrounded_or_nonfinite_dd_summaries(self):
        cases=[('unit','116 ERROR/s'),('nan-rate','nan kB/s'),('infinite-duration','9'*400+' s, 116 kB/s'),('diagnostic','116 kB/s dd:error')]
        for name,replacement in cases:
            with self.subTest(name=name):
                c,e,r,i=fixture()
                if name=='infinite-duration': old='3.4413e-05 s, 116 kB/s'
                elif name=='nan-rate': old='116 kB/s'
                elif name=='diagnostic': old='116 kB/s'
                else: old='116 kB/s'
                c['commands'][0]['stderr']=c['commands'][0]['stderr'].replace(old,replacement,1)
                with self.assertRaises(ValueError): parser.validate_response(c,e,r,i)
    def test_rejects_missing_truncated_or_extra_dd_accounting(self):
        c,e,r,i=fixture()
        original=c['commands'][0]['stderr']
        for bad in ('',original.rsplit('\n',4)[0]+'\n',original+'x\n'):
            with self.subTest(length=len(bad)):
                c2=copy.deepcopy(c); c2['commands'][0]['stderr']=bad
                with self.assertRaises(ValueError): parser.validate_response(c2,'',copy.deepcopy(r),copy.deepcopy(i))

if __name__=='__main__': unittest.main()
