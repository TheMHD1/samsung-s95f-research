#!/usr/bin/env python3
import base64,gzip,importlib.util,tempfile,unittest
from pathlib import Path
P=Path(__file__).with_name("parse-hdmi-kernel-snapshots.py");sp=importlib.util.spec_from_file_location("p",P);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
B="12345678-1234-1234-1234-123456789abc"
def block(n,raw): return f"@@ KERNEL_{n}\n{B}\n100.00 2.00\n".encode()+base64.b64encode(gzip.compress(raw))+f"\n@@ KERNEL_{n}_END\n".encode()
def art():return block("START",b"[  99.0] a\n[ 100.0] b\n")+block("END",b"[ 160.0] c\n[ 161.0] d\n")
class T(unittest.TestCase):
 def test_bracketed(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/"a";q=Path(d)/"q";a.write_bytes(art());q.write_text("CAPTURE_START utc=1 uptime=100.0\nCAPTURE_END utc=2 uptime=160.0\n")
   self.assertEqual(m.analyze(a,q)["requested_window_coverage"],"temporally_bracketed_not_proven_complete")
 def test_nonempty_not_coverage(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/"a";a.write_bytes(art());self.assertEqual(m.analyze(a)["requested_window_coverage"],"nonempty_only")
 def test_rejects_marker_and_integrity_errors(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/"a";a.write_bytes(block("START",b"x"))
   with self.assertRaisesRegex(ValueError,"END start marker"):m.analyze(a)
   a.write_bytes(art().replace(b"H4",b"XX",1))
   with self.assertRaisesRegex(ValueError,"integrity"):m.analyze(a)
 def test_one_sided_and_nonbracketed_meta(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/"a";q=Path(d)/"q";a.write_bytes(art());q.write_text("CAPTURE_START utc=1 uptime=100.0\n")
   with self.assertRaisesRegex(ValueError,"one-sided"):m.analyze(a,q)
   q.write_text("CAPTURE_START utc=1 uptime=1.0\nCAPTURE_END utc=2 uptime=200.0\n");self.assertEqual(m.analyze(a,q)["requested_window_coverage"],"nonempty_not_window_bracketed")
if __name__=="__main__":unittest.main()
