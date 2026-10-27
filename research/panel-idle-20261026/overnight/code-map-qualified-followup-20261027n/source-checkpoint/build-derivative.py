#!/usr/bin/env python3
"""Build the fixed code-fingerprint source from the reviewed three-read helper."""

from pathlib import Path
import hashlib
import re
import shutil

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "managed-usb-ap-exco-source-read"
PARENT_MANIFEST_SHA = "3222c56b1b80749123a2b360ebae9ffbf44779cf748061737774c93fc153fa51"
PARENT_PROGRAM_SHA = "99fe549a5b4c408e6c83a44675cdd7c5f975231f2495e07b1bc9481939d6dc60"
PARENT_WRAPPER_SHA = "79341a52a0c69031a2d489d35c80997997b80b75661814637f6de27836221106"

EXPECTED_A = "[encoded-payload-omitted]"
EXPECTED_B = "APCQ+X8cEC//9M2uAL+35nQEACD8qAAgHKkAIHgEACA8qQAgfKsAIAFIAGhwRwAAzAIAIABIcEcABQAgAUgAaA=="
EXPECTED_C = "[encoded-payload-omitted]"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(ok, why):
    if not ok:
        raise RuntimeError(why)


def one(text, old, new):
    need(text.count(old) == 1, "replacement cardinality: " + old[:80])
    return text.replace(old, new)


need(sha(PARENT / "build-manifest.json") == PARENT_MANIFEST_SHA, "parent manifest pin")
need(sha(PARENT / "Program.cs") == PARENT_PROGRAM_SHA, "parent Program pin")
need(sha(PARENT / "run-once.py") == PARENT_WRAPPER_SHA, "parent wrapper pin")

for name in ("ManagedUsbRtBlockReadOnce.csproj", "NuGet.Config", "root-with-margin.py"):
    shutil.copyfile(PARENT / name, HERE / name)

p = (PARENT / "Program.cs").read_text()
p = one(p,
'''    const int PointerLength = 32, BaseLength = 16, TailLength = 32, TimeoutMs = 2000;
    const string ExpectedBoot = "00000000-0000-4000-8000-000000000000";
    const string UsbRoot = "/sys/bus/usb/devices/7-1";
    const string DeviceHex = "12010002ef020140e8040120500201020301";
    const string AllDescriptorsHex = DeviceHex + "090262000301048032080b00020202010a09040000010202010a052400100105240100010424020205240600010705830308001009040100020a00000a07050102400010070581024000000904020002ff0000000705820200020007050202000200";
    static readonly byte[] PointerHeader = Convert.FromHexString("01010000C002004720000000");
    static readonly byte[] BaseHeader = Convert.FromHexString("0101000014FF004510000000");
    static readonly byte[] TailHeader = Convert.FromHexString("01010000E002014520000000");
''',
f'''    const int WindowALength = 512, WindowBLength = 64, WindowCLength = 576, TimeoutMs = 2000;
    const string ExpectedBoot = "00000000-0000-4000-8000-000000000000";
    const string UsbRoot = "/sys/bus/usb/devices/7-1";
    const string DeviceHex = "12010002ef020140e8040120500201020301";
    const string AllDescriptorsHex = DeviceHex + "090262000301048032080b00020202010a09040000010202010a052400100105240100010424020205240600010705830308001009040100020a00000a07050102400010070581024000000904020002ff0000000705820200020007050202000200";
    static readonly byte[] WindowAHeader = Convert.FromHexString("01010000601E004600020000");
    static readonly byte[] WindowBHeader = Convert.FromHexString("01010000C038004640000000");
    static readonly byte[] WindowCHeader = Convert.FromHexString("0101000060BB014640020000");
    static readonly byte[] ExpectedWindowA = Convert.FromBase64String("{EXPECTED_A}");
    static readonly byte[] ExpectedWindowB = Convert.FromBase64String("{EXPECTED_B}");
    static readonly byte[] ExpectedWindowC = Convert.FromBase64String("{EXPECTED_C}");
''')
p = one(p, 'enum ProtocolPhase { ReadyForHeader, ExpectingPointerIn, ExpectingBaseIn, ExpectingTailIn, Unknown }',
           'enum ProtocolPhase { ReadyForHeader, ExpectingWindowAIn, ExpectingWindowBIn, ExpectingWindowCIn, Unknown }')
old_outcome = re.search(r'    sealed class Outcome\n    \{.*?\n    \}\n    interface IOps', p, re.S).group(0)
new_outcome = '''    sealed class Outcome
    {
        public string Schema { get; set; } = "managed-usb-code-fingerprint-read-v1";
        public string Stage { get; set; } = "preflight";
        public string ProtocolPhase { get; set; } = "ReadyForHeader";
        public List<Step> Steps { get; } = new();
        public bool Opened { get; set; }
        public bool Claimed { get; set; }
        public bool Released { get; set; } = true;
        public bool Closed { get; set; } = true;
        public bool Accepted { get; set; }
        public string? WindowABase64 { get; set; }
        public string? WindowASha256 { get; set; }
        public bool WindowAMatchesSelected { get; set; }
        public string? WindowBBase64 { get; set; }
        public string? WindowBSha256 { get; set; }
        public bool WindowBMatchesSelected { get; set; }
        public string? WindowCBase64 { get; set; }
        public string? WindowCSha256 { get; set; }
        public bool WindowCMatchesSelected { get; set; }
        public bool AllWindowsMatchSelected { get; set; }
        public string ContentComparison { get; set; } = "not-compared";
        public bool PhysicalPictureObserved { get; set; }
        public bool BusContentsAltered { get; set; }
        public bool ExecutingCodeIdentityProved { get; set; }
        public bool WholeImageIdentityInferred { get; set; }
    }
    interface IOps'''
p = one(p, old_outcome, new_outcome)
p = one(p, '''        byte[] pointer = new byte[PointerLength];
        byte[] sourceBase = new byte[BaseLength];
        byte[] sourceTail = new byte[TailLength];''', '''        byte[] windowA = new byte[WindowALength];
        byte[] windowB = new byte[WindowBLength];
        byte[] windowC = new byte[WindowCLength];''')
start = p.index('            Read("pointer",')
end = p.index('            result.Stage = "complete";', start) + len('            result.Stage = "complete";')
p = p[:start] + '''            Read("window-a", WindowAHeader, windowA, ProtocolPhase.ExpectingWindowAIn);
            result.WindowABase64 = Convert.ToBase64String(windowA);
            result.WindowASha256 = Convert.ToHexString(SHA256.HashData(windowA)).ToLowerInvariant();
            result.WindowAMatchesSelected = windowA.AsSpan().SequenceEqual(ExpectedWindowA);
            Read("window-b", WindowBHeader, windowB, ProtocolPhase.ExpectingWindowBIn);
            result.WindowBBase64 = Convert.ToBase64String(windowB);
            result.WindowBSha256 = Convert.ToHexString(SHA256.HashData(windowB)).ToLowerInvariant();
            result.WindowBMatchesSelected = windowB.AsSpan().SequenceEqual(ExpectedWindowB);
            Read("window-c", WindowCHeader, windowC, ProtocolPhase.ExpectingWindowCIn);
            result.WindowCBase64 = Convert.ToBase64String(windowC);
            result.WindowCSha256 = Convert.ToHexString(SHA256.HashData(windowC)).ToLowerInvariant();
            result.WindowCMatchesSelected = windowC.AsSpan().SequenceEqual(ExpectedWindowC);
            result.AllWindowsMatchSelected = result.WindowAMatchesSelected && result.WindowBMatchesSelected && result.WindowCMatchesSelected;
            result.ContentComparison = result.AllWindowsMatchSelected ?
                "all-windows-match-selected-package" : "one-or-more-window-mismatch";
            result.Stage = "complete";''' + p[end:]
p = one(p, '''            result.PointerBase64 != null && result.BaseBase64 != null && result.TailBase64 != null &&
            result.Released && result.Closed;''', '''            result.WindowABase64 != null && result.WindowBBase64 != null && result.WindowCBase64 != null &&
            result.Released && result.Closed;''')
p = one(p, '''            Need(input ? data.Length == PointerLength || data.Length == BaseLength || data.Length == TailLength :
                data.AsSpan().SequenceEqual(PointerHeader) || data.AsSpan().SequenceEqual(BaseHeader) ||
                data.AsSpan().SequenceEqual(TailHeader), "fixed transfer only");''', '''            Need(input ? data.Length == WindowALength || data.Length == WindowBLength || data.Length == WindowCLength :
                data.AsSpan().SequenceEqual(WindowAHeader) || data.AsSpan().SequenceEqual(WindowBHeader) ||
                data.AsSpan().SequenceEqual(WindowCHeader), "fixed transfer only");''')
fake_start = p.index('    sealed class FakeOps')
main_start = p.index('    static int Main(', fake_start)
fake_tests = '''    sealed class FakeOps : IOps
    {
        public List<string> Calls { get; } = new();
        public string? ThrowAt;
        public int ThrowBulkAt = -1, CorruptWindow = -1;
        public int OpenReturn = 9, ClaimReturn, ReleaseReturn, CloseReturn;
        public int[] BulkReturns = { 12, WindowALength, 12, WindowBLength, 12, WindowCLength };
        public bool ChangeIdentity;
        int preflights, bulkIndex;
        void Call(string phase) { Calls.Add(phase); if (ThrowAt == phase) throw new IOException("injected"); }
        public Identity Preflight() { Call("preflight"); preflights++; return new(7, ChangeIdentity && preflights == 2 ? 46 : 45); }
        public NativeResult Open(Identity id) { Call("open"); return new(OpenReturn, OpenReturn < 0 ? 5 : 0); }
        public void ValidateFd(int fd, Identity id) { Call("fd-validation"); }
        public NativeResult Claim(int fd) { Call("claim"); return new(ClaimReturn, ClaimReturn < 0 ? 16 : 0); }
        public NativeResult Bulk(int fd, bool input, byte[] data)
        {
            int index = bulkIndex++;
            Calls.Add(index switch { 0 => "window-a-out", 1 => "window-a-in", 2 => "window-b-out",
                3 => "window-b-in", 4 => "window-c-out", 5 => "window-c-in", _ => "extra-bulk" });
            if (index == ThrowBulkAt) throw new IOException("injected bulk");
            Need(index < BulkReturns.Length, "fake bulk index");
            if (input)
            {
                byte[] expected = index switch { 1 => ExpectedWindowA, 3 => ExpectedWindowB, 5 => ExpectedWindowC,
                    _ => throw new InvalidOperationException("fake input index") };
                expected.CopyTo(data, 0);
                if (CorruptWindow == index / 2) data[data.Length / 2] ^= 0x80;
            }
            else Need(data.AsSpan().SequenceEqual(index switch { 0 => WindowAHeader, 2 => WindowBHeader,
                4 => WindowCHeader, _ => throw new InvalidOperationException("fake header index") }), "fake fixed header");
            int value = BulkReturns[index];
            return new(value, value < 0 ? 5 : 0);
        }
        public NativeResult Release(int fd) { Call("release"); return new(ReleaseReturn, ReleaseReturn < 0 ? 5 : 0); }
        public NativeResult Close(int fd) { Call("close"); return new(CloseReturn, CloseReturn < 0 ? 5 : 0); }
    }
    static int SelfTest()
    {
        int tests = 0;
        void Case(string name, FakeOps ops, bool accepted, string? forbidden = null)
        {
            Outcome result = Run(ops);
            Need(result.Accepted == accepted, name + " acceptance");
            if (forbidden != null) Need(!ops.Calls.Contains(forbidden), name + " forbidden");
            if (result.Opened) Need(ops.Calls.Contains("close"), name + " close");
            if (result.Claimed) Need(ops.Calls.Contains("release"), name + " release");
            tests++;
        }
        Outcome success = Run(new FakeOps());
        Need(success.Accepted && success.AllWindowsMatchSelected && success.WindowAMatchesSelected &&
             success.WindowBMatchesSelected && success.WindowCMatchesSelected && success.Steps.Count == 10 &&
             Convert.FromBase64String(success.WindowABase64!).Length == WindowALength &&
             Convert.FromBase64String(success.WindowBBase64!).Length == WindowBLength &&
             Convert.FromBase64String(success.WindowCBase64!).Length == WindowCLength, "success");
        tests++;
        for (int which = 0; which < 3; which++)
        {
            Outcome mismatch = Run(new FakeOps { CorruptWindow = which });
            Need(mismatch.Accepted && !mismatch.AllWindowsMatchSelected &&
                 mismatch.ContentComparison == "one-or-more-window-mismatch" &&
                 mismatch.WindowABase64 != null && mismatch.WindowBBase64 != null && mismatch.WindowCBase64 != null,
                 "content mismatch retains accepted transport");
            tests++;
        }
        int[] exacts = { 12, WindowALength, 12, WindowBLength, 12, WindowCLength };
        for (int stop = 1; stop < 6; stop += 2)
        {
            int[] returns = (int[])exacts.Clone(); returns[stop]--;
            Outcome shortRead = Run(new FakeOps { BulkReturns = returns });
            Need(!shortRead.Accepted && (stop < 3 || shortRead.WindowABase64 != null) &&
                 (stop < 5 || shortRead.WindowBBase64 != null), "prior raw retained before short read");
            tests++;
        }
        Case("open-fail", new() { OpenReturn = -1 }, false, "claim");
        Case("claim-fail", new() { ClaimReturn = -1 }, false, "window-a-out");
        Case("identity", new() { ChangeIdentity = true }, false, "claim");
        foreach (string phase in new[] { "preflight", "open", "fd-validation", "claim" })
            Case("exception-" + phase, new() { ThrowAt = phase }, false, "window-a-out");
        for (int step = 0; step < 6; step++)
        {
            int exact = exacts[step];
            foreach (int value in new[] { -1, 0, exact - 1, exact + 1 })
            {
                int[] returns = (int[])exacts.Clone(); returns[step] = value;
                string? forbidden = step switch { 0 => "window-a-in", 1 => "window-b-out", 2 => "window-b-in",
                    3 => "window-c-out", 4 => "window-c-in", _ => null };
                Case("bulk-count", new() { BulkReturns = returns }, false, forbidden);
            }
            string? exceptionForbidden = step switch { 0 => "window-a-in", 1 => "window-b-out", 2 => "window-b-in",
                3 => "window-c-out", 4 => "window-c-in", _ => null };
            Case("bulk-exception", new() { ThrowBulkAt = step }, false, exceptionForbidden);
        }
        Case("release", new() { ReleaseReturn = -1 }, false);
        Case("close", new() { CloseReturn = -1 }, false);
        Need(Convert.ToHexString(WindowAHeader) == "01010000601E004600020000" &&
             Convert.ToHexString(WindowBHeader) == "01010000C038004640000000" &&
             Convert.ToHexString(WindowCHeader) == "0101000060BB014640020000", "headers");
        Need(ExpectedWindowA.Length == 512 && ExpectedWindowB.Length == 64 && ExpectedWindowC.Length == 576 &&
             Convert.ToHexString(SHA256.HashData(ExpectedWindowA)).ToLowerInvariant() == "8be303fddfa4aefd0f2d307f05c7522213f8017ae15b374a4fd7178aeca2bb49" &&
             Convert.ToHexString(SHA256.HashData(ExpectedWindowB)).ToLowerInvariant() == "0483a632a5e65f8eba8bd623411d6f955705d012c831eac9347e7f9564d944cb" &&
             Convert.ToHexString(SHA256.HashData(ExpectedWindowC)).ToLowerInvariant() == "035d13a7c17ac9b303ee5739a421a84d0ceec46167d6efce13f4723fc701d9b8", "expected windows");
        Need(Convert.FromHexString(AllDescriptorsHex).Length == 116, "descriptor extent");
        foreach (int length in new[] { 0, 115, 116 })
        {
            byte[] input = new byte[length];
            for (int i = 0; i < length; i++) input[i] = (byte)i;
            using PartialNonseekableStream stream = new(input);
            Need(ReadCachedDescriptors(stream).AsSpan().SequenceEqual(input), "descriptor " + length);
            tests++;
        }
        bool rejected = false;
        try { using PartialNonseekableStream stream = new(new byte[117]); ReadCachedDescriptors(stream); }
        catch (InvalidOperationException e) when (e.Message == "cached descriptors exceed 116 bytes") { rejected = true; }
        Need(rejected, "descriptor oversize"); tests++;
        Console.WriteLine(JsonSerializer.Serialize(new { selfTestsPassed = tests, targetOperations = 0 }));
        return 0;
    }
'''
p = p[:fake_start] + fake_tests + p[main_start:]
old_main = re.search(r'        if \(args.Length == 0\)\n        \{.*?\n        \}', p, re.S).group(0)
new_main = '''        if (args.Length == 0)
        {
            Console.WriteLine(JsonSerializer.Serialize(new {
                schema = "managed-usb-code-fingerprint-read-dry-v1", dryRun = true, targetOperations = 0,
                requests = new[] {
                    new { address = "0x46001e60", headerHex = Convert.ToHexString(WindowAHeader), length = WindowALength },
                    new { address = "0x460038c0", headerHex = Convert.ToHexString(WindowBHeader), length = WindowBLength },
                    new { address = "0x4601bb60", headerHex = Convert.ToHexString(WindowCHeader), length = WindowCLength }
                },
                timeoutMs = TimeoutMs, interfaceNumber = 2, writes = 0, retries = 0
            }));
            return 0;
        }'''
p = one(p, old_main, new_main)
need(not re.search(r'Pointer|SourceByte|InterpretationAccepted|PointerLength|BaseLength|TailLength', p), "old semantics remain")
(HERE / "Program.cs").write_text(p)

w = (PARENT / "run-once.py").read_text()
w = one(w, '"""Stage and execute the fixed three-read AP_EXCO helper; dry by default."""',
           '"""Stage and execute the fixed three-window code fingerprint reader; dry by default."""')
w = one(w, 'SCHEMA = "managed-usb-ap-exco-source-read-build-v1"',
           'SCHEMA = "managed-usb-code-fingerprint-read-build-v1"')
w = one(w, '''                "run-once.py", "test-wrapper.py", "root-with-margin.py", "README.md"}''',
           '''                "run-once.py", "test-wrapper.py", "root-with-margin.py", "README.md", "source-note.md"}''')
w = one(w, 'MAX_NATIVE_STDERR = 2048\n', f'''MAX_NATIVE_STDERR = 2048
EXPECTED_A = base64.b64decode("{EXPECTED_A}", validate=True)
EXPECTED_B = base64.b64decode("{EXPECTED_B}", validate=True)
EXPECTED_C = base64.b64decode("{EXPECTED_C}", validate=True)
EXPECTED = (EXPECTED_A, EXPECTED_B, EXPECTED_C)
''')
w = one(w, 'spec = importlib.util.spec_from_file_location("ap_exco_source_root_transport", ROOT_ADAPTER)',
           'spec = importlib.util.spec_from_file_location("code_fingerprint_root_transport", ROOT_ADAPTER)')
w = one(w, '{"selfTestsPassed": 47, "targetOperations": 0}',
           '{"selfTestsPassed": 50, "targetOperations": 0}')
parse_start = w.index('def parse_native(text):')
parse_end = w.index('\n\ndef parse_envelope(text):', parse_start)
new_parse = '''def parse_native(text):
    rows, gc = parse_lines_with_gc(text)
    need(len(rows) == 1 and isinstance(rows[0], dict), "one native outcome")
    value = rows[0]
    need(value.get("Schema") == "managed-usb-code-fingerprint-read-v1", "native schema")
    need(value.get("Stage") == "complete" and value.get("ProtocolPhase") == "ReadyForHeader",
         "native terminal phase")
    for key in ("Opened", "Claimed", "Released", "Closed", "Accepted"):
        need(value.get(key) is True, "native " + key)
    need(value.get("PhysicalPictureObserved") is False and
         value.get("BusContentsAltered") is False and
         value.get("ExecutingCodeIdentityProved") is False and
         value.get("WholeImageIdentityInferred") is False, "native bounded claims")
    raw = []
    match = []
    for letter, expected in zip("ABC", EXPECTED):
        data = base64.b64decode(value.get("Window" + letter + "Base64", ""), validate=True)
        need(len(data) == len(expected) and sha(data) == value.get("Window" + letter + "Sha256"),
             "window " + letter + " raw artifact")
        equals = data == expected
        need(value.get("Window" + letter + "MatchesSelected") is equals,
             "window " + letter + " comparison")
        raw.append(data)
        match.append(equals)
    all_match = all(match)
    need(value.get("AllWindowsMatchSelected") is all_match, "aggregate comparison")
    need(value.get("ContentComparison") ==
         ("all-windows-match-selected-package" if all_match else "one-or-more-window-mismatch"),
         "comparison label")
    steps = value.get("Steps")
    need(isinstance(steps, list) and len(steps) == 10, "native step count")
    expected_steps = [("open", "LOCAL", 0), ("claim", "LOCAL", 0),
                      ("window-a-header", "OUT", 12), ("window-a-data", "IN", 512),
                      ("window-b-header", "OUT", 12), ("window-b-data", "IN", 64),
                      ("window-c-header", "OUT", 12), ("window-c-data", "IN", 576),
                      ("release", "LOCAL", 0), ("close", "LOCAL", 0)]
    for row, (name, direction, count) in zip(steps, expected_steps):
        need(row.get("Name") == name and row.get("Direction") == direction and
             row.get("Expected") == count and row.get("Error") is None,
             "native step " + name)
        if direction in ("OUT", "IN") or name in ("claim", "release", "close"):
            need(row.get("Count") == count and row.get("Errno") == 0, "native exact " + name)
        else:
            need(isinstance(row.get("Count"), int) and not isinstance(row.get("Count"), bool) and
                 row.get("Count") >= 0 and row.get("Errno") == 0, "native open")
    return value, raw[0], raw[1], raw[2], gc
'''
w = w[:parse_start] + new_parse + w[parse_end:]
old_dry = '''        print(json.dumps({"schema": "managed-usb-ap-exco-source-wrapper-dry-v1",
                          "target_operations": 0,
                          "requests": [{"target": "0x101", "address": "0x470002c0", "length": 32},
                                       {"target": "0x101", "address": "0x4500ff14", "length": 16},
                                       {"target": "0x101", "address": "0x450102e0", "length": 32}],
                          "writes": 0, "retries": 0}, separators=(",", ":")))'''
new_dry = '''        print(json.dumps({"schema": "managed-usb-code-fingerprint-wrapper-dry-v1",
                          "target_operations": 0,
                          "requests": [{"target": "0x101", "address": "0x46001e60", "length": 512},
                                       {"target": "0x101", "address": "0x460038c0", "length": 64},
                                       {"target": "0x101", "address": "0x4601bb60", "length": 576}],
                          "writes": 0, "retries": 0}, separators=(",", ":")))'''
w = one(w, old_dry, new_dry)
w = one(w, 'stage = "/tmp/researcher-ap-exco-source-" + uuid.uuid4().hex',
           'stage = "/tmp/researcher-code-fingerprint-" + uuid.uuid4().hex')
w = one(w, '''record = {"schema": "managed-usb-ap-exco-source-wrapper-record-v1",''',
           '''record = {"schema": "managed-usb-code-fingerprint-wrapper-record-v1",''')
old_requests = '''              "requests": [{"target": "0x101", "address": "0x470002c0", "length": 32},
                           {"target": "0x101", "address": "0x4500ff14", "length": 16},
                           {"target": "0x101", "address": "0x450102e0", "length": 32}]}'''
new_requests = '''              "requests": [{"target": "0x101", "address": "0x46001e60", "length": 512},
                           {"target": "0x101", "address": "0x460038c0", "length": 64},
                           {"target": "0x101", "address": "0x4601bb60", "length": 576}]}'''
w = one(w, old_requests, new_requests)
w = one(w, '''    native, pointer, source_base, source_tail, gc = parse_native(native_stdout.decode("utf-8"))
    (args.output / "pointer-window.bin").write_bytes(pointer)
    (args.output / "source-base-window.bin").write_bytes(source_base)
    (args.output / "source-tail-window.bin").write_bytes(source_tail)''', '''    native, window_a, window_b, window_c, gc = parse_native(native_stdout.decode("utf-8"))
    (args.output / "window-a.bin").write_bytes(window_a)
    (args.output / "window-b.bin").write_bytes(window_b)
    (args.output / "window-c.bin").write_bytes(window_c)''')
result_start = w.index('    pointer_matches = native["PointerMatches"] is True')
result_end = w.index('    save(args.output / "result.json", result)', result_start)
new_result = '''    match = [native["Window" + letter + "MatchesSelected"] is True for letter in "ABC"]
    result = {"schema": "managed-usb-code-fingerprint-wrapper-result-v1",
              "transport_accepted": True,
              "manifest_sha256": sha(manifest_raw), "record": str(record_path),
              "windows": [
                  {"address": "0x46001e60", "length": len(window_a), "sha256": sha(window_a),
                   "matches_selected_package": match[0]},
                  {"address": "0x460038c0", "length": len(window_b), "sha256": sha(window_b),
                   "matches_selected_package": match[1]},
                  {"address": "0x4601bb60", "length": len(window_c), "sha256": sha(window_c),
                   "matches_selected_package": match[2]}],
              "all_windows_match_selected_package": all(match),
              "content_comparison": native["ContentComparison"],
              "content_mismatch_is_not_transport_failure": True,
              "windows_sequential_not_atomic": True,
              "executing_code_identity_proved": False,
              "whole_image_identity_inferred": False,
              "native_gc_lines": len(gc), "cleanup": "STAGE_ABSENT",
              "bus_contents_altered": False, "physical_picture_observed": False} 
'''
w = w[:result_start] + new_result + w[result_end:]
need('0x470002c0' not in w and 'PointerMatches' not in w and 'SourceByte' not in w, "old wrapper semantics remain")
(HERE / "run-once.py").write_text(w)
print("generated Program.cs", hashlib.sha256(p.encode()).hexdigest())
print("generated run-once.py", hashlib.sha256(w.encode()).hexdigest())
