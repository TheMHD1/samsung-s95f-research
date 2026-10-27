"""Offline evidence-integrity tests, including real captured wire bytes."""
from pathlib import Path
import importlib.util,unittest
B=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('decoder',B/'decode-qd-trace.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
HEAD='# entries-in-buffer/entries-written: 3/3\n'
def line(pid,time,event,body):return f' worker-{pid} ( 706) [000] .... {time:.6f}: {event}: {body}\n'
def mute(pid=10,when=1,ret=2):return line(pid,when,'i2c_write','i2c-5 #0 a=076 f=0000 l=6 [f3-00-00-00-01-64]')+line(pid,when+.001,'i2c_write','i2c-5 #1 a=076 f=4000 l=4 [00-00-00-00]')+line(pid,when+.002,'i2c_result',f'i2c-5 n=2 ret={ret}')
class EvidenceIntegrity(unittest.TestCase):
 def test_real_capture(self):
  d=mod.decode((B/'passive-black-i2c.trace').read_text());self.assertTrue(d['ring_accounting_complete']);self.assertEqual(len(d['transfers']),4)
  self.assertTrue(all(t['structurally_complete'] for t in d['transfers']));self.assertEqual(d['transfers'][1]['qd']['selector_hex'],'0x174');self.assertEqual(d['transfers'][1]['qd']['write_payload_u32_be'],1);self.assertEqual(d['transfers'][3]['qd']['read_reply_hex'],'00000001');self.assertEqual(d['focus'],[])
 def test_unmute_is_observed_not_accepted(self):
  d=mod.decode(HEAD+mute());self.assertEqual(d['focus'][0]['name'],'panel-mute');self.assertEqual(d['focus'][0]['write_payload_u32_be'],0);self.assertNotIn('accepted',d['focus'][0])
 def test_linux_failure_preserved(self):
  d=mod.decode(HEAD+mute(ret=-121));self.assertEqual(d['transfers'][0]['ret'],-121);self.assertEqual(d['focus'][0]['transport_outcome'],'short-or-failed-transfer')
 def test_overflow_blocks_semantic_pairing(self):
  d=mod.decode(HEAD.replace('3/3','3/7')+mute());self.assertFalse(d['ring_accounting_complete']);self.assertEqual(d['focus'],[])
 def test_truncated_export_cannot_claim_complete_ring(self):
  d=mod.decode(HEAD.replace('3/3','739/739')+mute());self.assertFalse(d['ring_accounting_complete']);self.assertEqual(d['focus'],[])
 def test_missing_reply_and_result(self):
  text=HEAD.replace('3/3','2/2')+line(10,1,'i2c_write','i2c-5 #0 a=076 f=0000 l=6 [f3-80-00-00-01-64]')+line(10,1.001,'i2c_read','i2c-5 #1 a=076 f=0001 l=4')
  d=mod.decode(text);self.assertFalse(d['transfers'][0]['structurally_complete']);self.assertNotIn('qd',d['transfers'][0])
 def test_other_threads_cannot_supply_payload(self):
  rows=mute().splitlines(True);d=mod.decode(HEAD.replace('3/3','6/6')+rows[0]+mute(pid=11,when=1.0001)+rows[1]+rows[2]);self.assertEqual(len(d['focus']),2);self.assertEqual({r['pid'] for r in d['focus']},{10,11})
 def test_filtered_message_and_length_mismatch(self):
  d=mod.decode(HEAD+mute().replace('a=076 f=4000 l=4 [00-00-00-00]','a=076 f=4000 l=5 [00-00-00-00]'));self.assertFalse(d['transfers'][0]['structurally_complete']);self.assertEqual(d['focus'],[])
 def test_missing_write_payload_does_not_crash(self):
  d=mod.decode(HEAD+mute().replace(' [00-00-00-00]',''));self.assertEqual(d['focus'],[])
 def test_malformed_known_i2c_event_blocks_semantics(self):
  text=HEAD.replace('3/3','4/4')+mute()+line(10,2,'i2c_write','unsupported-body')
  d=mod.decode(text);self.assertTrue(d['ring_accounting_complete']);self.assertFalse(d['semantic_capture_complete']);self.assertEqual(len(d['parse_errors']),1);self.assertEqual(d['focus'],[])
 def test_write_opcode_with_read_payload_is_not_named(self):
  text=HEAD.replace('3/3','4/4')+line(10,1,'i2c_write','i2c-5 #0 a=076 f=0000 l=6 [f3-00-00-00-01-64]')+line(10,1.001,'i2c_read','i2c-5 #1 a=076 f=0001 l=4')+line(10,1.002,'i2c_reply','i2c-5 #1 a=076 f=0001 l=4 [00-00-00-00]')+line(10,1.003,'i2c_result','i2c-5 n=2 ret=2')
  d=mod.decode(text);self.assertTrue(d['transfers'][0]['structurally_complete']);self.assertFalse(d['transfers'][0]['qd_semantic_shape_valid']);self.assertNotIn('qd',d['transfers'][0]);self.assertEqual(d['focus'],[])
 def test_read_opcode_with_write_payload_is_not_named(self):
  d=mod.decode(HEAD+mute().replace('f3-00-00-00-01-64','f3-80-00-00-01-64'));self.assertFalse(d['transfers'][0]['qd_semantic_shape_valid']);self.assertEqual(d['focus'],[])
 def test_reply_flags_must_match_request(self):
  text=HEAD.replace('3/3','4/4')+line(10,1,'i2c_write','i2c-5 #0 a=076 f=0000 l=6 [f3-80-00-00-01-64]')+line(10,1.001,'i2c_read','i2c-5 #1 a=076 f=0001 l=4')+line(10,1.002,'i2c_reply','i2c-5 #1 a=076 f=0000 l=4 [00-00-00-00]')+line(10,1.003,'i2c_result','i2c-5 n=2 ret=2')
  d=mod.decode(text);self.assertFalse(d['transfers'][0]['structurally_complete']);self.assertEqual(d['focus'],[])
 def test_sensing_commands_are_control_evidence_not_active_state(self):
  for suffix,name in [('01-80','off-sensing-control'),('01-a0','EL-sensing-control')]:
   text=HEAD+mute().replace('01-64',suffix).replace('[00-00-00-00]','[00-00-00-01]')
   d=mod.decode(text);self.assertEqual(d['focus'],[]);item=d['maintenance_focus'][0];self.assertEqual(item['name'],name);self.assertEqual(item['write_payload_u32_be'],1);self.assertNotIn('active',item);self.assertNotIn('accepted',item)
 def test_dimming_requests_preserve_scalar_without_light_inference(self):
  for suffix,name,value in [('01-28','dimming-level-request',51),('00-c4','screen-saver-brightness',7)]:
   text=HEAD+mute().replace('01-64',suffix).replace('[00-00-00-00]',f'[00-00-00-{value:02x}]')
   d=mod.decode(text);self.assertEqual(d['focus'],[]);self.assertEqual(d['maintenance_focus'],[])
   item=d['dimming_focus'][0];self.assertEqual(item['name'],name);self.assertEqual(item['write_payload_u32_be'],value);self.assertNotIn('luminance',item);self.assertNotIn('accepted',item)
 def test_incomplete_dimming_request_is_not_semantic_evidence(self):
  text=HEAD.replace('3/3','3/8')+mute().replace('01-64','01-28')
  d=mod.decode(text);self.assertEqual(d['dimming_focus'],[]);self.assertNotIn('qd',d['transfers'][0])
if __name__=='__main__':unittest.main()
