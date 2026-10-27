import importlib.util, pathlib, unittest, tempfile, json
from unittest.mock import patch
p=pathlib.Path(__file__).with_name('run-duty-read-v2.py');s=importlib.util.spec_from_file_location('r',p);r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
GOOD='''QD_TCON_DUTY_READ_V1\nARCH=Arm\nPTR_BYTES=4\nSTRUCT_BYTES=16\nENDIAN_LITTLE=1\nOPERATION_OFFSET=0\nOUTPUT_OFFSET=4\nCOMMAND_HIGH_OFFSET=8\nCOMMAND_LOW_OFFSET=12\nARGUMENT_COUNT=0\nUID=0\nEUID=0\nPID_LIBC=7\nPID_SYSCALL=7\nDEVICE=/dev/tztv_tcon\nOPEN_FLAGS=0x80002\nIOCTL_REQUEST=0xc010749f\nCOMMAND_U64=0x0000f30000000128\nWIRE_REQUEST_HEX=f30000000128\nEXPECTED_RESPONSE_BYTES=4\nPAYLOAD_BEFORE=00000013,a55a5aa5,0000f300,00000128\nOPEN_RETURN=3\nOPEN_ERRNO=0\nIOCTL_RETURN=0\nIOCTL_ERRNO=0\nPAYLOAD_AFTER=00000013,0000002a,0000f300,00000128\nCLOSE_RETURN=0\nCLOSE_ERRNO=0\nCLASSIFICATION=kernel_output_written\nRESULT_HEX=0x0000002a\nRESULT_U32=42\nPHYSICAL_BRIGHTNESS_INFERRED=0\nPACKAGED_RANGE_0_1023=1\nPROFILE_RANGE_CLASSIFICATION=within_packaged_low10_range\nREAD_COMPLETE'''
class T(unittest.TestCase):
 def test_positive(self): self.assertEqual(r.parse(GOOD,7)['duty_u32'],42)
 def test_unknown(self):
  with self.assertRaises(r.E): r.parse(GOOD.replace('READ_COMPLETE','X=1\nREAD_COMPLETE'),7)
 def test_deadline_lifecycle(self): self.assertTrue(r.dry(*r.contract())['all_commands_bounded'])
 def test_bad_outputs(self):
  mutations=[('OPEN_RETURN=3','OPEN_RETURN=-1'),('CLOSE_RETURN=0','CLOSE_RETURN=-1'),
   ('IOCTL_RETURN=0','IOCTL_RETURN=-1'),('PID_SYSCALL=7','PID_SYSCALL=8'),
   ('00000013,0000002a,0000f300,00000128','00000013,a55a5aa5,0000f300,00000128'),
   ('00000013,0000002a,0000f300,00000128','00000012,0000002a,0000f300,00000128'),
   ('READ_COMPLETE','UNKNOWN_BARE\nREAD_COMPLETE'),('RESULT_U32=42','RESULT_U32=43'),
   ('ARCH=Arm','ARCH=X64'),('READ_COMPLETE','UID=0\nREAD_COMPLETE')]
  for before,after in mutations:
   with self.subTest(after=after),self.assertRaises(r.E):r.parse(GOOD.replace(before,after),7)
 def fixture_run(self,managed=GOOD,cleanup_ok=True):
  x=r.mod(); calls=[]; boot='00000000-0000-0000-0000-000000000000'
  def root(command,record,output):
   calls.append(command)
   if 'echo PREFLIGHT_IDENTITY_MATCH' in command:
    return f'PREFLIGHT_BOOT={boot}\nPREFLIGHT_UTC=1\nPREFLIGHT_UPTIME=1.0\nPREFLIGHT_IDENTITY_MATCH\n'
   if 'echo EXECUTE_COMPLETE' in command:
    return f'HELPER_PID=7\nHELPER_START=1\nHELPER_DEADLINE_HIT=0\nHELPER_EXIT=0\nMANAGED_STDOUT_BEGIN\n{managed}\nMANAGED_STDOUT_END\nMANAGED_STDERR_BEGIN\nMANAGED_STDERR_END\nEXECUTE_BOOT={boot}\nEXECUTE_UTC=2\nEXECUTE_UPTIME=2.0\nEXECUTE_COMPLETE\n'
   if 'echo POSTFLIGHT_IDENTITY_MATCH' in command:return 'POSTFLIGHT_IDENTITY_MATCH\n'
   if 'echo PRIVATE_REMOVED' in command:return 'PRIVATE_REMOVED\n' if cleanup_ok else 'INCOMPLETE\n'
   if 'echo PRIVATE_CREATED' in command:return 'PRIVATE_CREATED\n'
   if 'echo STAGE_CHUNK_COMPLETE' in command:return 'STAGE_CHUNK_COMPLETE\n'
   raise AssertionError('unhandled lifecycle command')
  x.root=root
  with tempfile.TemporaryDirectory() as t,patch.object(r,'mod',return_value=x):
   dest=pathlib.Path(t)/'result.json'
   try:r.run_once(dest,*r.contract())
   except r.E:pass
   result=json.loads(dest.read_text())
  return result,calls
 def test_success_lifecycle_no_network(self):
  result,calls=self.fixture_run()
  self.assertTrue(result['accepted']);self.assertTrue(result['cleanup_confirmed'])
  self.assertEqual(result['schema'],'managed-tcon-duty-read-result-v1')
  self.assertEqual(result['execution']['result']['duty_u32'],42)
  self.assertEqual(sum('echo EXECUTE_COMPLETE' in c for c in calls),1)
  self.assertIn('ManagedTconDutyRead.dll',next(c for c in calls if 'echo EXECUTE_COMPLETE' in c))
 def test_bad_read_still_cleans(self):
  result,calls=self.fixture_run(GOOD.replace('RESULT_U32=42','RESULT_U32=99'))
  self.assertFalse(result['accepted']);self.assertTrue(result['cleanup_confirmed'])
  self.assertTrue(any('echo PRIVATE_REMOVED' in c for c in calls))
 def test_failed_cleanup_rejects(self):
  result,_=self.fixture_run(cleanup_ok=False)
  self.assertFalse(result['accepted']);self.assertFalse(result['cleanup_confirmed'])
if __name__=='__main__':unittest.main()
