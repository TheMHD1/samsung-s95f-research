#!/usr/bin/env python3
from pathlib import Path
import hashlib
D=Path(__file__).resolve().parent;Q=D.parent/'volatile-limit-native-binding-20261028dq/Program.cs';raw=Q.read_bytes()
if hashlib.sha256(raw).hexdigest()!='c589815120878e619458e98c558a81962b9318a7dd6bd76dd48cdd39eef770a7':raise ValueError('frozen DQ native pin')
s=raw.decode();s=s[s.index('    sealed class RealClock'):s.index('    sealed class FakeClock')]
a='if (input) Need(data.Length == length && (length == 64 || length == 256 || length == 68 || length == 16), "fixed input length");\n            else Need((length == 12 && AllowedHeader(data)) || (length == 2 && data.Length == 2 && (Half(data,0) == 40 || Half(data,0) == 200)), "fixed OUT only");'
b='if (input) Need(data.Length == 256 && IsInputLength(length), "fixed input length");\n            else Need(length == 12 && data.Length == 12 && FindHeader(data) != null, "fixed read headers only");'
if s.count(a)!=1:raise ValueError('fixed USB allowlist anchor')
s=s.replace(a,b)
(D/'NativeBinding.cs').write_text('using System;\nusing System.IO;\nusing System.Collections.Generic;\nusing System.Diagnostics;\nusing System.Runtime.InteropServices;\nusing System.Threading;\ninternal static partial class Program\n{\n'+s+'}\n')
