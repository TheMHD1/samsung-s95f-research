#!/usr/bin/env python3
"""Create the fixed two-read native source from the frozen D5 64-byte reader."""

from pathlib import Path
import hashlib

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "managed-usb-secondary-root-read-once"
ROOT_ADAPTER = HERE.parent / "managed-usb-secondary-logger-onset-framing/root-with-margin.py"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def need(ok, why):
    if not ok:
        raise ValueError(why)


def replace_once(text, old, new):
    need(text.count(old) == 1, "replacement count: " + old[:50])
    return text.replace(old, new, 1)


def replace_span(text, start, end, replacement):
    a = text.index(start)
    b = text.index(end, a)
    return text[:a] + replacement + text[b:]


def main():
    source_raw = (PARENT / "Program.cs").read_bytes()
    project_raw = (PARENT / "ManagedUsbRtBlockReadOnce.csproj").read_bytes()
    adapter_raw = ROOT_ADAPTER.read_bytes()
    need(sha(source_raw) == "4a725f342237a848bd835ef090a9341ae30a80c70e9798a05236d108bbffe5e4", "parent source")
    need(sha(project_raw) == "05893d224110307cdce9838c9620aba3ed1326901288ad105279cfc9eed3f187", "parent project")
    need(sha(adapter_raw) == "bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a", "root adapter")
    text = source_raw.decode()
    text = replace_once(text,
        "    const int Length = 64, TimeoutMs = 2000;",
        "    const int ContextLength = 64, RtLength = 256, TimeoutMs = 2000;")
    text = replace_once(text,
        '    static readonly byte[] Header = Convert.FromHexString("01010000C004004740000000");',
        '    static readonly byte[] ContextHeader = Convert.FromHexString("01010000000F014740000000");\n'
        '    static readonly byte[] RtHeader = Convert.FromHexString("010100000024014700010000");')
    text = replace_once(text,
        "    sealed record Step(string Phase, int? Value = null, int? Errno = null, string? Error = null);",
        "    enum ProtocolPhase { ReadyForHeader, ExpectingContextIn, ExpectingRtIn, Unknown }\n"
        "    sealed record Step(string Name, string Direction, int Expected, int? Count = null, int? Errno = null, string? Error = null);")
    text = replace_span(text, "    sealed class Outcome\n", "    interface IOps\n", '''    sealed class Outcome
    {
        public string Schema { get; set; } = "managed-usb-rt-fault-context-read-v1";
        public string Stage { get; set; } = "preflight";
        public string ProtocolPhase { get; set; } = "ReadyForHeader";
        public List<Step> Steps { get; } = new();
        public bool Opened { get; set; }
        public bool Claimed { get; set; }
        public bool Released { get; set; } = true;
        public bool Closed { get; set; } = true;
        public bool Accepted { get; set; }
        public string? ContextBase64 { get; set; }
        public string? ContextSha256 { get; set; }
        public string? RtBase64 { get; set; }
        public string? RtSha256 { get; set; }
        public bool PhysicalPictureObserved { get; set; }
        public bool BusContentsAltered { get; set; }
    }
''')
    run = '''    static Outcome Run(IOps ops)
    {
        Outcome result = new();
        ProtocolPhase phase = ProtocolPhase.ReadyForHeader;
        int fd = -1;
        byte[] context = new byte[ContextLength];
        byte[] rt = new byte[RtLength];
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

            void Out(string name, byte[] header, ProtocolPhase next)
            {
                Need(phase == ProtocolPhase.ReadyForHeader, name + " phase");
                result.Stage = name;
                phase = ProtocolPhase.Unknown;
                NativeResult transfer = ops.Bulk(fd, false, (byte[])header.Clone());
                if (transfer.Value == header.Length) phase = next;
                result.Steps.Add(new(name, "OUT", header.Length, transfer.Value, transfer.Errno));
                Need(transfer.Value == header.Length, name + " count not exact");
            }
            void Input(string name, byte[] data, ProtocolPhase expected)
            {
                Need(phase == expected, name + " phase");
                result.Stage = name;
                phase = ProtocolPhase.Unknown;
                NativeResult transfer = ops.Bulk(fd, true, data);
                if (transfer.Value == data.Length) phase = ProtocolPhase.ReadyForHeader;
                result.Steps.Add(new(name, "IN", data.Length, transfer.Value, transfer.Errno));
                Need(transfer.Value == data.Length, name + " count not exact");
            }

            Out("context-header", ContextHeader, ProtocolPhase.ExpectingContextIn);
            Input("context-data", context, ProtocolPhase.ExpectingContextIn);
            result.ContextBase64 = Convert.ToBase64String(context);
            result.ContextSha256 = Convert.ToHexString(SHA256.HashData(context)).ToLowerInvariant();
            Out("rt-header", RtHeader, ProtocolPhase.ExpectingRtIn);
            Input("rt-data", rt, ProtocolPhase.ExpectingRtIn);
            result.RtBase64 = Convert.ToBase64String(rt);
            result.RtSha256 = Convert.ToHexString(SHA256.HashData(rt)).ToLowerInvariant();
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
            result.ContextBase64 != null && result.RtBase64 != null && result.Released && result.Closed;
        return result;
    }
'''
    text = replace_span(text, "    static Outcome Run(IOps ops)\n", "    // sysfs binary attributes", run)
    text = replace_once(text,
        "            Need(input ? data.Length == Length : data.AsSpan().SequenceEqual(Header), \"fixed transfer only\");",
        "            Need(input ? data.Length == ContextLength || data.Length == RtLength :\n"
        "                data.AsSpan().SequenceEqual(ContextHeader) || data.AsSpan().SequenceEqual(RtHeader), \"fixed transfer only\");")
    fake_start = text.index("    sealed class FakeOps : IOps\n")
    test_start = text.index("    static int SelfTest()\n", fake_start)
    fake = '''    sealed class FakeOps : IOps
    {
        public List<string> Calls { get; } = new();
        public string? ThrowAt;
        public int ThrowBulkAt = -1;
        public int OpenReturn = 9, ClaimReturn, ReleaseReturn, CloseReturn;
        public int[] BulkReturns = { 12, ContextLength, 12, RtLength };
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
            string name = index switch { 0 => "context-out", 1 => "context-in", 2 => "rt-out", 3 => "rt-in", _ => "extra-bulk" };
            Calls.Add(name);
            if (index == ThrowBulkAt) throw new IOException("injected bulk");
            Need(index < BulkReturns.Length, "fake bulk index");
            if (input)
            {
                byte seed = index == 1 ? (byte)0x40 : (byte)0x80;
                for (int i = 0; i < data.Length; i++) data[i] = (byte)(seed + i);
            }
            else Need(data.AsSpan().SequenceEqual(index == 0 ? ContextHeader : RtHeader), "fake fixed header");
            int value = BulkReturns[index];
            return new(value, value < 0 ? 5 : 0);
        }
        public NativeResult Release(int fd) { Call("release"); return new(ReleaseReturn, ReleaseReturn < 0 ? 5 : 0); }
        public NativeResult Close(int fd) { Call("close"); return new(CloseReturn, CloseReturn < 0 ? 5 : 0); }
    }
'''
    text = text[:fake_start] + fake + text[test_start:]
    tests = '''    static int SelfTest()
    {
        int tests = 0;
        void CheckCleanup(string name, FakeOps ops, Outcome result)
        {
            if (result.Opened) Need(ops.Calls.Contains("close"), name + " close attempted");
            if (result.Claimed) Need(ops.Calls.Contains("release"), name + " release attempted");
        }
        Outcome success = Run(new FakeOps());
        Need(success.Accepted && success.ProtocolPhase == "ReadyForHeader", "success accepted");
        Need(Convert.FromBase64String(success.ContextBase64!).Length == ContextLength, "context output");
        Need(Convert.FromBase64String(success.RtBase64!).Length == RtLength, "rt output");
        Need(success.Steps.Count == 8, "success steps");
        tests++;

        void BaseCase(string name, FakeOps ops, bool accepted, string? forbidden = null)
        {
            Outcome result = Run(ops);
            Need(result.Accepted == accepted, name + " acceptance");
            if (forbidden != null) Need(!ops.Calls.Contains(forbidden), name + " forbidden " + forbidden);
            CheckCleanup(name, ops, result);
            tests++;
        }
        BaseCase("open-failure", new() { OpenReturn = -1 }, false, "claim");
        BaseCase("claim-failure", new() { ClaimReturn = -1 }, false, "context-out");
        BaseCase("identity-change", new() { ChangeIdentity = true }, false, "claim");
        foreach (string phase in new[] { "preflight", "open", "fd-validation", "claim" })
            BaseCase("exception-" + phase, new() { ThrowAt = phase }, false, "context-out");

        int[] exact = { 12, ContextLength, 12, RtLength };
        string[] names = { "context-header", "context-data", "rt-header", "rt-data" };
        string?[] forbidden = { "context-in", "rt-out", "rt-in", null };
        for (int step = 0; step < 4; step++)
        {
            foreach (int value in new[] { -1, 0, exact[step] - 1, exact[step] + 1 })
            {
                int[] returns = (int[])exact.Clone();
                returns[step] = value;
                BaseCase(names[step] + "-count-" + value, new() { BulkReturns = returns }, false, forbidden[step]);
            }
            BaseCase(names[step] + "-exception", new() { ThrowBulkAt = step }, false, forbidden[step]);
        }
        BaseCase("release-error", new() { ReleaseReturn = -1 }, false);
        BaseCase("close-error", new() { CloseReturn = -1 }, false);
        Need(Convert.ToHexString(ContextHeader) == "01010000000F014740000000", "context header");
        Need(Convert.ToHexString(RtHeader) == "010100000024014700010000", "rt header");
        Need(Convert.FromHexString(AllDescriptorsHex).Length == 116, "descriptor extent");
        foreach (int length in new[] { 0, 115, 116 })
        {
            byte[] input = new byte[length];
            for (int i = 0; i < length; i++) input[i] = (byte)i;
            using PartialNonseekableStream stream = new(input);
            Need(ReadCachedDescriptors(stream).AsSpan().SequenceEqual(input), "partial stream " + length);
            tests++;
        }
        bool oversizedRejected = false;
        try
        {
            using PartialNonseekableStream stream = new(new byte[117]);
            ReadCachedDescriptors(stream);
        }
        catch (InvalidOperationException e) when (e.Message == "cached descriptors exceed 116 bytes")
        { oversizedRejected = true; }
        Need(oversizedRejected, "oversized descriptor rejection");
        tests++;
        Console.WriteLine(JsonSerializer.Serialize(new { selfTestsPassed = tests, targetOperations = 0 }));
        return 0;
    }
'''
    text = replace_span(text, "    static int SelfTest()\n", "    static int Main(string[] args)\n", tests)
    old_dry = '            Console.WriteLine(JsonSerializer.Serialize(new { dryRun = true, targetOperations = 0, address = "0x470004c0", operation = "opaque-secondary-root-and-gates-DMA-IN", headerHex = Convert.ToHexString(Header), inputLength = Length, timeoutMs = TimeoutMs, interfaceNumber = 2 }));'
    new_dry = '            Console.WriteLine(JsonSerializer.Serialize(new { schema = "managed-usb-rt-fault-context-read-dry-v1", dryRun = true, targetOperations = 0, contextAddress = "0x47010f00", contextHeaderHex = Convert.ToHexString(ContextHeader), contextLength = ContextLength, rtAddress = "0x47012400", rtHeaderHex = Convert.ToHexString(RtHeader), rtLength = RtLength, timeoutMs = TimeoutMs, interfaceNumber = 2, writes = 0, retries = 0 }));'
    text = replace_once(text, old_dry, new_dry)
    (HERE / "Program.cs").write_text(text)
    (HERE / "ManagedUsbRtBlockReadOnce.csproj").write_bytes(project_raw)
    (HERE / "root-with-margin.py").write_bytes(adapter_raw)
    print({"Program.cs": sha(text.encode()), "project": sha(project_raw), "root_adapter": sha(adapter_raw)})


if __name__ == "__main__":
    main()
