#!/usr/bin/env python3
"""Derive the fixed 68-byte mode reader from the reviewed two-window engine."""

from pathlib import Path
import hashlib

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "managed-usb-rt-fault-context-read"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def need(ok, why):
    if not ok:
        raise ValueError(why)


def once(text, old, new):
    need(text.count(old) == 1, "replacement: " + old[:60])
    return text.replace(old, new, 1)


def span(text, start, end, replacement):
    a, b = text.index(start), text.index(end, text.index(start))
    return text[:a] + replacement + text[b:]


def main():
    source = (PARENT / "Program.cs").read_bytes()
    project = (PARENT / "ManagedUsbRtBlockReadOnce.csproj").read_bytes()
    adapter = (PARENT / "root-with-margin.py").read_bytes()
    wrapper = (PARENT / "run-once.py").read_bytes()
    need(sha(source) == "f7418df841af9b616c198958b5b725dd7fc2434c92f5b360b65989c9da66b6a0", "parent source")
    need(sha(project) == "05893d224110307cdce9838c9620aba3ed1326901288ad105279cfc9eed3f187", "project")
    need(sha(adapter) == "bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a", "adapter")
    need(sha(wrapper) == "93af800b0e4103a03d268680cb13b6ea6ed3c2d4ceeead79625f75b10b584c1a", "parent wrapper")
    text = source.decode()
    text = once(text, "    const int ContextLength = 64, RtLength = 256, TimeoutMs = 2000;",
                "    const int ModeLength = 68, AltLength = 16, TimeoutMs = 2000;")
    text = once(text,
        '    static readonly byte[] ContextHeader = Convert.FromHexString("01010000000F014740000000");\n'
        '    static readonly byte[] RtHeader = Convert.FromHexString("010100000024014700010000");',
        '    static readonly byte[] ModeHeader = Convert.FromHexString("01010000A004004744000000");\n'
        '    static readonly byte[] AltHeader = Convert.FromHexString("01010000C00B004710000000");')
    text = once(text,
        "    enum ProtocolPhase { ReadyForHeader, ExpectingContextIn, ExpectingRtIn, Unknown }",
        "    enum ProtocolPhase { ReadyForHeader, ExpectingModeIn, ExpectingAltIn, Unknown }")
    outcome = '''    sealed class Outcome
    {
        public string Schema { get; set; } = "managed-usb-rt-mode-read-v1";
        public string Stage { get; set; } = "preflight";
        public string ProtocolPhase { get; set; } = "ReadyForHeader";
        public List<Step> Steps { get; } = new();
        public bool Opened { get; set; }
        public bool Claimed { get; set; }
        public bool Released { get; set; } = true;
        public bool Closed { get; set; } = true;
        public bool Accepted { get; set; }
        public string? DataBase64 { get; set; }
        public string? DataSha256 { get; set; }
        public string? AlternateBase64 { get; set; }
        public string? AlternateSha256 { get; set; }
        public ushort? ModeAa { get; set; }
        public ushort? ModeAc { get; set; }
        public ushort? MirrorCandidate { get; set; }
        public ushort? EnableCandidate { get; set; }
        public uint? RootWord { get; set; }
        public bool RootMatches { get; set; }
        public bool InterpretationAccepted { get; set; }
        public string Interpretation { get; set; } = "not-decoded";
        public bool PhysicalPictureObserved { get; set; }
        public bool BusContentsAltered { get; set; }
    }
'''
    text = span(text, "    sealed class Outcome\n", "    interface IOps\n", outcome)
    run = '''    static Outcome Run(IOps ops)
    {
        Outcome result = new();
        ProtocolPhase phase = ProtocolPhase.ReadyForHeader;
        int fd = -1;
        byte[] data = new byte[ModeLength];
        byte[] alternate = new byte[AltLength];
        try
        {
            Identity id = ops.Preflight();
            result.Stage = "open";
            NativeResult opened = ops.Open(id);
            result.Steps.Add(new("open", "LOCAL", 0, opened.Value, opened.Errno));
            Need(opened.Value >= 0, "open failed");
            fd = opened.Value;
            result.Opened = true;
            result.Closed = false;
            result.Stage = "fd-validation";
            ops.ValidateFd(fd, id);
            result.Stage = "identity-recheck";
            Need(ops.Preflight() == id, "USB identity changed");
            result.Stage = "claim";
            NativeResult claim = ops.Claim(fd);
            result.Steps.Add(new("claim", "LOCAL", 0, claim.Value, claim.Errno));
            Need(claim.Value == 0, "claim failed");
            result.Claimed = true;
            result.Released = false;

            void Read(string prefix, byte[] headerBytes, byte[] output, ProtocolPhase expected)
            {
                Need(phase == ProtocolPhase.ReadyForHeader, prefix + " header phase");
                result.Stage = prefix + "-header";
                phase = ProtocolPhase.Unknown;
                NativeResult header = ops.Bulk(fd, false, (byte[])headerBytes.Clone());
                if (header.Value == headerBytes.Length) phase = expected;
                result.Steps.Add(new(prefix + "-header", "OUT", headerBytes.Length, header.Value, header.Errno));
                Need(header.Value == headerBytes.Length, prefix + " header count not exact");
                Need(phase == expected, prefix + " input phase");
                result.Stage = prefix + "-data";
                phase = ProtocolPhase.Unknown;
                NativeResult input = ops.Bulk(fd, true, output);
                if (input.Value == output.Length) phase = ProtocolPhase.ReadyForHeader;
                result.Steps.Add(new(prefix + "-data", "IN", output.Length, input.Value, input.Errno));
                Need(input.Value == output.Length, prefix + " input count not exact");
            }
            Read("mode", ModeHeader, data, ProtocolPhase.ExpectingModeIn);
            Read("alternate", AltHeader, alternate, ProtocolPhase.ExpectingAltIn);

            result.DataBase64 = Convert.ToBase64String(data);
            result.DataSha256 = Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();
            result.AlternateBase64 = Convert.ToBase64String(alternate);
            result.AlternateSha256 = Convert.ToHexString(SHA256.HashData(alternate)).ToLowerInvariant();
            result.ModeAa = BitConverter.ToUInt16(data, 0x0A);
            result.ModeAc = BitConverter.ToUInt16(data, 0x0C);
            result.MirrorCandidate = BitConverter.ToUInt16(data, 0x22);
            result.EnableCandidate = BitConverter.ToUInt16(data, 0x24);
            result.RootWord = BitConverter.ToUInt32(data, 0x40);
            result.RootMatches = result.RootWord == 0x20010000u;
            result.InterpretationAccepted = result.RootMatches;
            result.Interpretation = result.RootMatches ? "conditional-image1-mode-sample" : "root-anchor-mismatch";
            result.Stage = "complete";
        }
        catch (Exception e)
        {
            if (phase != ProtocolPhase.ReadyForHeader) phase = ProtocolPhase.Unknown;
            try { result.Steps.Add(new(result.Stage, "NONE", 0, Error: e.GetType().Name + ": " + e.Message)); }
            catch { }
        }
        finally
        {
            if (result.Claimed)
            {
                try
                {
                    NativeResult release = ops.Release(fd);
                    result.Released = release.Value == 0;
                    result.Steps.Add(new("release", "LOCAL", 0, release.Value, release.Errno));
                }
                catch (Exception e)
                {
                    result.Released = false;
                    try { result.Steps.Add(new("release", "LOCAL", 0, Error: e.GetType().Name)); } catch { }
                }
            }
            if (fd >= 0)
            {
                try
                {
                    NativeResult close = ops.Close(fd);
                    result.Closed = close.Value == 0;
                    result.Steps.Add(new("close", "LOCAL", 0, close.Value, close.Errno));
                }
                catch (Exception e)
                {
                    result.Closed = false;
                    try { result.Steps.Add(new("close", "LOCAL", 0, Error: e.GetType().Name)); } catch { }
                }
            }
        }
        result.ProtocolPhase = phase.ToString();
        result.Accepted = result.Stage == "complete" && phase == ProtocolPhase.ReadyForHeader &&
            result.DataBase64 != null && result.AlternateBase64 != null && result.Released && result.Closed;
        return result;
    }
'''
    text = span(text, "    static Outcome Run(IOps ops)\n", "    // sysfs binary attributes", run)
    text = once(text,
        "            Need(input ? data.Length == ContextLength || data.Length == RtLength :\n"
        "                data.AsSpan().SequenceEqual(ContextHeader) || data.AsSpan().SequenceEqual(RtHeader), \"fixed transfer only\");",
        "            Need(input ? data.Length == ModeLength || data.Length == AltLength :\n"
        "                data.AsSpan().SequenceEqual(ModeHeader) || data.AsSpan().SequenceEqual(AltHeader), \"fixed transfer only\");")
    fake = '''    sealed class FakeOps : IOps
    {
        public List<string> Calls { get; } = new();
        public string? ThrowAt;
        public int ThrowBulkAt = -1;
        public int OpenReturn = 9, ClaimReturn, ReleaseReturn, CloseReturn;
        public int[] BulkReturns = { 12, ModeLength, 12, AltLength };
        public bool ChangeIdentity;
        public uint RootValue = 0x20010000u;
        public ushort Aa = 1, Ac = 0;
        int preflights, bulkIndex;
        void Call(string phase) { Calls.Add(phase); if (ThrowAt == phase) throw new IOException("injected"); }
        public Identity Preflight() { Call("preflight"); preflights++; return new(7, ChangeIdentity && preflights == 2 ? 46 : 45); }
        public NativeResult Open(Identity id) { Call("open"); return new(OpenReturn, OpenReturn < 0 ? 5 : 0); }
        public void ValidateFd(int fd, Identity id) { Call("fd-validation"); }
        public NativeResult Claim(int fd) { Call("claim"); return new(ClaimReturn, ClaimReturn < 0 ? 16 : 0); }
        public NativeResult Bulk(int fd, bool input, byte[] data)
        {
            int index = bulkIndex++;
            Calls.Add(index switch { 0 => "mode-out", 1 => "mode-in", 2 => "alternate-out", 3 => "alternate-in", _ => "extra-bulk" });
            if (index == ThrowBulkAt) throw new IOException("injected bulk");
            Need(index < BulkReturns.Length, "fake bulk index");
            if (input)
            {
                for (int i = 0; i < data.Length; i++) data[i] = (byte)(0x40 + i);
                if (data.Length == ModeLength)
                {
                    BitConverter.GetBytes(Aa).CopyTo(data, 0x0A);
                    BitConverter.GetBytes(Ac).CopyTo(data, 0x0C);
                    BitConverter.GetBytes(RootValue).CopyTo(data, 0x40);
                }
            }
            else Need(data.AsSpan().SequenceEqual(index == 0 ? ModeHeader : AltHeader), "fake fixed header");
            int value = BulkReturns[index];
            return new(value, value < 0 ? 5 : 0);
        }
        public NativeResult Release(int fd) { Call("release"); return new(ReleaseReturn, ReleaseReturn < 0 ? 5 : 0); }
        public NativeResult Close(int fd) { Call("close"); return new(CloseReturn, CloseReturn < 0 ? 5 : 0); }
    }
'''
    text = span(text, "    sealed class FakeOps : IOps\n", "    static int SelfTest()\n", fake)
    tests = '''    static int SelfTest()
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
        Need(success.Accepted && success.InterpretationAccepted && success.RootMatches &&
             success.ModeAa == 1 && success.ModeAc == 0 && success.RootWord == 0x20010000u &&
             Convert.FromBase64String(success.DataBase64!).Length == ModeLength &&
             Convert.FromBase64String(success.AlternateBase64!).Length == AltLength && success.Steps.Count == 8,
             "success");
        tests++;
        Outcome mismatch = Run(new FakeOps { RootValue = 0x12345678u });
        Need(mismatch.Accepted && !mismatch.InterpretationAccepted && !mismatch.RootMatches &&
             mismatch.Interpretation == "root-anchor-mismatch" && mismatch.DataBase64 != null,
             "root mismatch retains accepted transport");
        tests++;
        Case("open-fail", new() { OpenReturn = -1 }, false, "claim");
        Case("claim-fail", new() { ClaimReturn = -1 }, false, "mode-out");
        Case("identity", new() { ChangeIdentity = true }, false, "claim");
        foreach (string phase in new[] { "preflight", "open", "fd-validation", "claim" })
            Case("exception-" + phase, new() { ThrowAt = phase }, false, "mode-out");
        for (int step = 0; step < 4; step++)
        {
            int[] exacts = { 12, ModeLength, 12, AltLength };
            int exact = exacts[step];
            foreach (int value in new[] { -1, 0, exact - 1, exact + 1 })
            {
                int[] returns = (int[])exacts.Clone();
                returns[step] = value;
                string? forbidden = step switch { 0 => "mode-in", 1 => "alternate-out", 2 => "alternate-in", _ => null };
                Case("bulk-count", new() { BulkReturns = returns }, false, forbidden);
            }
            string? exceptionForbidden = step switch { 0 => "mode-in", 1 => "alternate-out", 2 => "alternate-in", _ => null };
            Case("bulk-exception", new() { ThrowBulkAt = step }, false, exceptionForbidden);
        }
        Case("release", new() { ReleaseReturn = -1 }, false);
        Case("close", new() { CloseReturn = -1 }, false);
        Need(Convert.ToHexString(ModeHeader) == "01010000A004004744000000" &&
             Convert.ToHexString(AltHeader) == "01010000C00B004710000000", "headers");
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
        Need(rejected, "descriptor oversize");
        tests++;
        Console.WriteLine(JsonSerializer.Serialize(new { selfTestsPassed = tests, targetOperations = 0 }));
        return 0;
    }
'''
    text = span(text, "    static int SelfTest()\n", "    static int Main(string[] args)\n", tests)
    old = '            Console.WriteLine(JsonSerializer.Serialize(new { schema = "managed-usb-rt-fault-context-read-dry-v1", dryRun = true, targetOperations = 0, contextAddress = "0x47010f00", contextHeaderHex = Convert.ToHexString(ContextHeader), contextLength = ContextLength, rtAddress = "0x47012400", rtHeaderHex = Convert.ToHexString(RtHeader), rtLength = RtLength, timeoutMs = TimeoutMs, interfaceNumber = 2, writes = 0, retries = 0 }));'
    new = '            Console.WriteLine(JsonSerializer.Serialize(new { schema = "managed-usb-rt-mode-read-dry-v1", dryRun = true, targetOperations = 0, modeAddress = "0x470004a0", modeHeaderHex = Convert.ToHexString(ModeHeader), modeLength = ModeLength, alternateAddress = "0x47000bc0", alternateHeaderHex = Convert.ToHexString(AltHeader), alternateLength = AltLength, timeoutMs = TimeoutMs, interfaceNumber = 2, writes = 0, retries = 0 }));'
    text = once(text, old, new)
    (HERE / "Program.cs").write_text(text)
    (HERE / "ManagedUsbRtBlockReadOnce.csproj").write_bytes(project)
    (HERE / "root-with-margin.py").write_bytes(adapter)
    host = wrapper.decode()
    host = once(host, 'SCHEMA = "managed-usb-rt-fault-context-read-build-v1"',
                'SCHEMA = "managed-usb-rt-mode-read-build-v1"')
    host = once(host,
        '    expected = {"Program.cs", "ManagedUsbRtBlockReadOnce.csproj", "build-derivative.py", "build-offline.py",\n'
        '                "run-once.py", "test-wrapper.py", "root-with-margin.py", "README.md"}',
        '    expected = {"Program.cs", "ManagedUsbRtBlockReadOnce.csproj", "NuGet.Config", "build-derivative.py", "build-offline.py",\n'
        '                "run-once.py", "test-wrapper.py", "root-with-margin.py", "README.md"}')
    parsers = '''def parse_selftest(text):
    rows, _ = parse_lines_with_gc(text)
    need(len(rows) == 1 and rows[0] == {"selfTestsPassed": 35, "targetOperations": 0},
         "self-test contract")


def parse_native(text):
    rows, gc = parse_lines_with_gc(text)
    need(len(rows) == 1 and isinstance(rows[0], dict), "one native outcome")
    value = rows[0]
    need(value.get("Schema") == "managed-usb-rt-mode-read-v1", "native schema")
    need(value.get("Stage") == "complete" and value.get("ProtocolPhase") == "ReadyForHeader",
         "native terminal phase")
    for key in ("Opened", "Claimed", "Released", "Closed", "Accepted"):
        need(value.get(key) is True, "native " + key)
    need(value.get("PhysicalPictureObserved") is False and
         value.get("BusContentsAltered") is False, "native bounded claims")
    data = base64.b64decode(value.get("DataBase64", ""), validate=True)
    need(len(data) == 68 and sha(data) == value.get("DataSha256"), "raw artifact")
    alternate = base64.b64decode(value.get("AlternateBase64", ""), validate=True)
    need(len(alternate) == 16 and sha(alternate) == value.get("AlternateSha256"), "alternate raw artifact")
    aa, ac = int.from_bytes(data[0x0A:0x0C], "little"), int.from_bytes(data[0x0C:0x0E], "little")
    root_word = int.from_bytes(data[0x40:0x44], "little")
    mirror = int.from_bytes(data[0x22:0x24], "little")
    enable = int.from_bytes(data[0x24:0x26], "little")
    root_matches = root_word == 0x20010000
    need(value.get("ModeAa") == aa and value.get("ModeAc") == ac and
         value.get("RootWord") == root_word and value.get("MirrorCandidate") == mirror and
         value.get("EnableCandidate") == enable, "decoded raw offsets")
    need(value.get("RootMatches") is root_matches and
         value.get("InterpretationAccepted") is root_matches, "interpretation gate")
    need(value.get("Interpretation") ==
         ("conditional-image1-mode-sample" if root_matches else "root-anchor-mismatch"),
         "interpretation label")
    steps = value.get("Steps")
    need(isinstance(steps, list) and len(steps) == 8, "native step count")
    expected = [("open", "LOCAL", 0), ("claim", "LOCAL", 0),
                ("mode-header", "OUT", 12), ("mode-data", "IN", 68),
                ("alternate-header", "OUT", 12), ("alternate-data", "IN", 16),
                ("release", "LOCAL", 0), ("close", "LOCAL", 0)]
    for row, (name, direction, count) in zip(steps, expected):
        need(row.get("Name") == name and row.get("Direction") == direction and
             row.get("Expected") == count and row.get("Error") is None,
             "native step " + name)
        if direction in ("OUT", "IN") or name in ("claim", "release", "close"):
            need(row.get("Count") == count and row.get("Errno") == 0, "native exact " + name)
        else:
            need(isinstance(row.get("Count"), int) and row.get("Count") >= 0 and
                 row.get("Errno") == 0, "native open")
    return value, data, alternate, gc


'''
    host = span(host, "def parse_selftest(text):\n", "def parse_envelope(text):\n", parsers)
    host = once(host,
        '        print(json.dumps({"schema": "managed-usb-rt-fault-context-wrapper-dry-v1",\n'
        '                          "target_operations": 0,\n'
        '                          "requests": [{"target": "0x101", "address": "0x47010f00", "length": 64},\n'
        '                                       {"target": "0x101", "address": "0x47012400", "length": 256}],\n'
        '                          "writes": 0, "retries": 0}, separators=(",", ":")))',
        '        print(json.dumps({"schema": "managed-usb-rt-mode-wrapper-dry-v1",\n'
        '                          "target_operations": 0,\n'
        '                          "requests": [{"target": "0x101", "address": "0x470004a0", "length": 68},\n'
        '                                       {"target": "0x101", "address": "0x47000bc0", "length": 16}],\n'
        '                          "writes": 0, "retries": 0}, separators=(",", ":")))')
    host = once(host, '    stage = "/tmp/researcher-rt-fault-context-" + uuid.uuid4().hex',
                '    stage = "/tmp/researcher-rt-mode-" + uuid.uuid4().hex')
    host = once(host, '    record = {"schema": "managed-usb-rt-fault-context-wrapper-record-v1",',
                '    record = {"schema": "managed-usb-rt-mode-wrapper-record-v1",')
    host = once(host,
        '              "requests": [{"target": "0x101", "address": "0x47010f00", "length": 64},\n'
        '                           {"target": "0x101", "address": "0x47012400", "length": 256}]}',
        '              "requests": [{"target": "0x101", "address": "0x470004a0", "length": 68},\n'
        '                           {"target": "0x101", "address": "0x47000bc0", "length": 16}]}')
    host = once(host,
        '    native, context, rt, gc = parse_native(native_stdout.decode("utf-8"))\n'
        '    (args.output / "context.bin").write_bytes(context)\n'
        '    (args.output / "rt.bin").write_bytes(rt)\n'
        '    record["target_operations"] = 2',
        '    native, data, alternate, gc = parse_native(native_stdout.decode("utf-8"))\n'
        '    (args.output / "mode-window.bin").write_bytes(data)\n'
        '    (args.output / "alternate-window.bin").write_bytes(alternate)\n'
        '    record["target_operations"] = 2')
    old_result = '''    result = {"schema": "managed-usb-rt-fault-context-wrapper-result-v1",
              "accepted": True, "manifest_sha256": sha(manifest_raw),
              "record": str(record_path), "context_sha256": sha(context),
              "rt_sha256": sha(rt), "native_gc_lines": len(gc),
              "cleanup": "STAGE_ABSENT", "bus_contents_altered": False,
              "physical_picture_observed": False, "interpretation_deferred": True}
'''
    new_result = '''    root_matches = native["RootMatches"] is True
    result = {"schema": "managed-usb-rt-mode-wrapper-result-v1",
              "transport_accepted": True, "interpretation_accepted": root_matches,
              "interpretation": native["Interpretation"],
              "manifest_sha256": sha(manifest_raw), "record": str(record_path),
              "raw_sha256": sha(data), "raw_length": len(data),
              "alternate_raw_sha256": sha(alternate), "alternate_raw_length": len(alternate),
              "alternate_interpretation": "candidate-bus-bytes-only",
              "candidate_mode_aa_raw": native["ModeAa"],
              "candidate_mode_ac_raw": native["ModeAc"],
              "mirror_candidate_raw": native["MirrorCandidate"],
              "enable_candidate_raw": native["EnableCandidate"],
              "alternate_byte_7_raw": alternate[7],
              "mirror_alternate_numeric_consistent": native["MirrorCandidate"] == alternate[7],
              "consistency_promotes_alternate_cpu_alias": False,
              "root_word_raw": native["RootWord"], "native_gc_lines": len(gc),
              "cleanup": "STAGE_ABSENT", "bus_contents_altered": False,
              "physical_picture_observed": False,
              "late_state_not_v6_event_time": True}
'''
    host = once(host, old_result, new_result)
    (HERE / "run-once.py").write_text(host)
    print({"source": sha(text.encode()), "wrapper": sha(host.encode()),
           "project": sha(project), "adapter": sha(adapter)})


if __name__ == "__main__":
    main()
