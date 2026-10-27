using System;
using System.Collections.Generic;
using System.IO;
using System.Diagnostics;
using System.Threading;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;

internal static class Program
{
    const int Length = 256, TimeoutMs = 2000;
    const int MaxSamples = 20, PeriodMs = 250, LatestStartMs = 5500;
    const string ExpectedBoot = "00000000-0000-4000-8000-000000000000";
    const string UsbRoot = "/sys/bus/usb/devices/7-1";
    const string DeviceHex = "12010002ef020140e8040120500201020301";
    const string AllDescriptorsHex = DeviceHex + "090262000301048032080b00020202010a09040000010202010a052400100105240100010424020205240600010705830308001009040100020a00000a07050102400010070581024000000904020002ff0000000705820200020007050202000200";
    static readonly byte[] Header = Convert.FromHexString("010100000024014700010000");
    readonly record struct Identity(int Bus, int Device)
    {
        public string Node => $"/dev/bus/usb/{Bus:D3}/{Device:D3}";
    }
    readonly record struct NativeResult(int Value, int Errno);
    sealed record Step(string Phase, int? Value = null, int? Errno = null, string? Error = null);
    sealed class Outcome
    {
        public string Stage { get; set; } = "preflight";
        public List<Step> Steps { get; } = new();
        public bool Opened { get; set; }
        public bool Claimed { get; set; }
        public bool Released { get; set; } = true;
        public bool Closed { get; set; } = true;
        public bool Accepted { get; set; }
        public int? OutCount { get; set; }
        public int? InCount { get; set; }
        public string? DataBase64 { get; set; }
        public string? DataSha256 { get; set; }
    }
    interface IOps
    {
        Identity Preflight();
        NativeResult Open(Identity id);
        void ValidateFd(int fd, Identity id);
        NativeResult Claim(int fd);
        NativeResult Bulk(int fd, bool input, byte[] data);
        NativeResult Release(int fd);
        NativeResult Close(int fd);
    }
    static void Need(bool ok, string message)
    {
        if (!ok) throw new InvalidOperationException(message);
    }
    static Outcome Run(IOps ops)
    {
        Outcome result = new();
        int fd = -1;
        byte[]? data = null;
        try
        {
            Identity id = ops.Preflight();
            result.Stage = "open";
            NativeResult opened = ops.Open(id);
            result.Steps.Add(new("open", opened.Value, opened.Errno));
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
            result.Steps.Add(new("claim", claim.Value, claim.Errno));
            Need(claim.Value == 0, "claim failed");
            result.Claimed = true;
            result.Released = false;
            result.Stage = "out";
            NativeResult write = ops.Bulk(fd, false, (byte[])Header.Clone());
            result.OutCount = write.Value;
            result.Steps.Add(new("out", write.Value, write.Errno));
            Need(write.Value == Header.Length, "header count not exact");
            result.Stage = "in";
            data = new byte[Length];
            NativeResult read = ops.Bulk(fd, true, data);
            result.InCount = read.Value;
            result.Steps.Add(new("in", read.Value, read.Errno));
            Need(read.Value == Length, "response count not exact");
            result.DataBase64 = Convert.ToBase64String(data);
            result.DataSha256 = Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();
            result.Stage = "complete";
        }
        catch (Exception e)
        {
            result.Steps.Add(new(result.Stage, Error: e.GetType().Name + ": " + e.Message));
        }
        finally
        {
            if (result.Claimed)
            {
                try
                {
                    NativeResult release = ops.Release(fd);
                    result.Released = release.Value == 0;
                    result.Steps.Add(new("release", release.Value, release.Errno));
                }
                catch (Exception e) { result.Steps.Add(new("release", Error: e.GetType().Name)); }
            }
            if (fd >= 0)
            {
                try
                {
                    NativeResult close = ops.Close(fd);
                    result.Closed = close.Value == 0;
                    result.Steps.Add(new("close", close.Value, close.Errno));
                }
                catch (Exception e) { result.Steps.Add(new("close", Error: e.GetType().Name)); }
            }
        }
        result.Accepted = result.Stage == "complete" && result.OutCount == 12 &&
            result.InCount == Length && result.Released && result.Closed;
        return result;
    }
    // sysfs binary attributes can advertise a length larger than their content.
    // Consume a bounded stream; never infer bytes to read from Stream.Length.
    static byte[] ReadCachedDescriptors(Stream stream)
    {
        byte[] data = new byte[117];
        int used = 0;
        while (used < data.Length)
        {
            int count = stream.Read(data, used, data.Length - used);
            if (count == 0) return data.AsSpan(0, used).ToArray();
            Need(count > 0 && count <= data.Length - used, "descriptor stream count");
            used += count;
        }
        throw new InvalidOperationException("cached descriptors exceed 116 bytes");
    }
    static byte[] ReadCachedDescriptors(string path)
    {
        using FileStream stream = File.OpenRead(path);
        return ReadCachedDescriptors(stream);
    }
    sealed class PartialNonseekableStream : Stream
    {
        readonly byte[] data;
        int position;
        public PartialNonseekableStream(byte[] data) { this.data = data; }
        public override bool CanRead => true;
        public override bool CanSeek => false;
        public override bool CanWrite => false;
        public override long Length => throw new InvalidOperationException("Length must not be used");
        public override long Position { get => throw new NotSupportedException(); set => throw new NotSupportedException(); }
        public override int Read(byte[] buffer, int offset, int count)
        {
            int available = Math.Min(Math.Min(count, 7), data.Length - position);
            Array.Copy(data, position, buffer, offset, available);
            position += available;
            return available;
        }
        public override void Flush() => throw new NotSupportedException();
        public override long Seek(long offset, SeekOrigin origin) => throw new NotSupportedException();
        public override void SetLength(long value) => throw new NotSupportedException();
        public override void Write(byte[] buffer, int offset, int count) => throw new NotSupportedException();
    }
    sealed class RealOps : IOps
    {
        const uint ClaimRequest = 0x8004550f, ReleaseRequest = 0x80045510, BulkRequest = 0xc0105502;
        [StructLayout(LayoutKind.Sequential, Pack = 4)]
        internal struct Transfer { public uint Ep, Length, Timeout; public IntPtr Data; }
        [DllImport("libc.so.6", SetLastError = true)] static extern int open(string path, int flags);
        [DllImport("libc.so.6", SetLastError = true)] static extern int close(int fd);
        [DllImport("libc.so.6", EntryPoint = "ioctl", SetLastError = true)] static extern int ioctlNumber(int fd, uint request, ref uint data);
        [DllImport("libc.so.6", EntryPoint = "ioctl", SetLastError = true)] static extern int ioctlTransfer(int fd, uint request, ref Transfer data);
        [DllImport("libc.so.6", SetLastError = true)] static extern IntPtr read(int fd, [Out] byte[] data, UIntPtr count);
        [DllImport("libc.so.6", SetLastError = true)] static extern int statx(int dirfd, string path, int flags, uint mask, [Out] byte[] data);
        static NativeResult Result(int value) => new(value, value < 0 ? Marshal.GetLastWin32Error() : 0);
        static string Text(string name) => File.ReadAllText(UsbRoot + "/" + name).Trim();
        public static bool AbiReady => IntPtr.Size == 4 && Marshal.SizeOf<Transfer>() == 16 && BitConverter.IsLittleEndian;
        public Identity Preflight()
        {
            Need(File.ReadAllText("/proc/sys/kernel/random/boot_id").Trim() == ExpectedBoot, "boot changed");
            Need(Text("power/runtime_status") == "active", "USB not already active");
            Need(Text("idVendor") == "04e8" && Text("idProduct") == "2001", "USB IDs");
            Need(Text("bConfigurationValue") == "1" && Text("authorized") == "1", "configuration/authorization");
            Need(Convert.ToHexString(ReadCachedDescriptors(UsbRoot + "/descriptors")).Equals(AllDescriptorsHex, StringComparison.OrdinalIgnoreCase), "cached full descriptors");
            string intf = UsbRoot + ":1.2/";
            Need(!Directory.Exists(intf + "driver") && !File.Exists(intf + "driver") &&
                new DirectoryInfo(intf + "driver").LinkTarget == null, "interface already bound");
            Need(File.ReadAllText(intf + "bInterfaceNumber").Trim() == "02" &&
                File.ReadAllText(intf + "bAlternateSetting").Trim() == "0" &&
                File.ReadAllText(intf + "bInterfaceClass").Trim() == "ff" &&
                File.ReadAllText(intf + "bInterfaceSubClass").Trim() == "00" &&
                File.ReadAllText(intf + "bInterfaceProtocol").Trim() == "00", "vendor interface");
            Need(int.TryParse(Text("busnum"), out int bus) && bus == 7, "bus");
            Need(int.TryParse(Text("devnum"), out int device) && device >= 1 && device <= 127, "device address");
            return new(bus, device);
        }
        // ARM EABI overrides generic O_NOFOLLOW: octal 0100000 = 0x8000.
        public NativeResult Open(Identity id) => Result(open(id.Node, 2 | 0x80000 | 0x8000));
        public void ValidateFd(int fd, Identity id)
        {
            byte[] status = new byte[256];
            int ret = statx(fd, "", 0x1000, 1, status);
            int errno = ret < 0 ? Marshal.GetLastWin32Error() : 0;
            Need(ret == 0, "statx failed errno=" + errno);
            Need((BitConverter.ToUInt32(status, 0) & 1) == 1, "statx type unavailable");
            Need((BitConverter.ToUInt16(status, 28) & 0xf000) == 0x2000, "FD not a character device");
            Need(BitConverter.ToUInt32(status, 128) == 189 &&
                BitConverter.ToUInt32(status, 132) == (uint)((id.Bus - 1) * 128 + id.Device - 1), "FD USB device number");
            byte[] descriptor = new byte[18];
            long count = read(fd, descriptor, (UIntPtr)18).ToInt64();
            errno = count < 0 ? Marshal.GetLastWin32Error() : 0;
            Need(count == 18, "FD cached descriptor count=" + count + " errno=" + errno);
            Need(Convert.ToHexString(descriptor).Equals(DeviceHex, StringComparison.OrdinalIgnoreCase), "FD cached descriptor identity");
        }
        public NativeResult Claim(int fd) { uint iface = 2; return Result(ioctlNumber(fd, ClaimRequest, ref iface)); }
        public NativeResult Release(int fd) { uint iface = 2; return Result(ioctlNumber(fd, ReleaseRequest, ref iface)); }
        public NativeResult Close(int fd) => Result(close(fd));
        public NativeResult Bulk(int fd, bool input, byte[] data)
        {
            Need(AbiReady, "bulk ABI");
            Need(input ? data.Length == Length : data.AsSpan().SequenceEqual(Header), "fixed transfer only");
            GCHandle pinned = GCHandle.Alloc(data, GCHandleType.Pinned);
            try
            {
                Transfer transfer = new() { Ep = input ? 0x82u : 0x02u, Length = (uint)data.Length, Timeout = TimeoutMs, Data = pinned.AddrOfPinnedObject() };
                return Result(ioctlTransfer(fd, BulkRequest, ref transfer));
            }
            finally { pinned.Free(); }
        }
    }
    sealed class FakeOps : IOps
    {
        public List<string> Calls { get; } = new();
        public string? ThrowAt;
        public int OpenReturn = 9, ClaimReturn, OutReturn = 12, InReturn = Length, ReleaseReturn, CloseReturn;
        public bool ChangeIdentity;
        public byte RtFlag;
        public Action<string>? OnCall;
        int preflights;
        void Call(string phase) { Calls.Add(phase); OnCall?.Invoke(phase); if (ThrowAt == phase) throw new IOException("injected"); }
        public Identity Preflight() { Call("preflight"); preflights++; return new(7, ChangeIdentity && preflights == 2 ? 46 : 45); }
        public NativeResult Open(Identity id) { Call("open"); return new(OpenReturn, OpenReturn < 0 ? 5 : 0); }
        public void ValidateFd(int fd, Identity id) { Call("fd-validation"); }
        public NativeResult Claim(int fd) { Call("claim"); return new(ClaimReturn, ClaimReturn < 0 ? 16 : 0); }
        public NativeResult Bulk(int fd, bool input, byte[] data)
        {
            Call(input ? "in" : "out");
            Need(input ? data.Length == Length : data.AsSpan().SequenceEqual(Header), "fake fixed data");
            if (input) { Array.Fill(data, (byte)0x5a); data[10] = RtFlag; }
            return new(input ? InReturn : OutReturn, 0);
        }
        public NativeResult Release(int fd) { Call("release"); return new(ReleaseReturn, ReleaseReturn < 0 ? 5 : 0); }
        public NativeResult Close(int fd) { Call("close"); return new(CloseReturn, CloseReturn < 0 ? 5 : 0); }
    }
    interface ISeriesClock
    {
        long Milliseconds { get; }
        long UtcMilliseconds { get; }
        string Uptime { get; }
        void Delay(int milliseconds);
    }
    sealed class SeriesClock : ISeriesClock
    {
        public long Milliseconds => (long)(Stopwatch.GetTimestamp() * (1000.0 / Stopwatch.Frequency));
        public long UtcMilliseconds => DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        public string Uptime => File.ReadAllText("/proc/uptime").Trim();
        public void Delay(int milliseconds) => Thread.Sleep(milliseconds);
    }
    sealed class FakeClock : ISeriesClock
    {
        public long Now = 1000000;
        public bool ReverseDelay;
        public long Milliseconds => Now;
        public long UtcMilliseconds => 1700000000000 + Now;
        public string Uptime => FormattableString.Invariant($"{Now / 1000.0:F3} 0.00");
        public void Delay(int milliseconds) { Need(milliseconds >= 0, "negative delay"); Now += ReverseDelay ? -milliseconds : milliseconds; }
    }
    sealed record Sample(string Type, int Index, long StartMilliseconds, long EndMilliseconds,
        long StartElapsedMs, long UtcStartMs, string UptimeBefore, string UptimeAfter,
        Outcome Transport, int? RtFlagHalfword);
    sealed class SeriesResult
    {
        public string Type { get; set; } = "rt_block_summary";
        public string Reason { get; set; } = "internal_error";
        public bool Accepted { get; set; }
        public int SamplesCompleted { get; set; }
        public int SamplesTransportAccepted { get; set; }
        public long ElapsedMs { get; set; }
        public string? Error { get; set; }
    }
    static SeriesResult RunSeries(Func<int, IOps> factory, ISeriesClock clock, Action<Sample> emit)
    {
        SeriesResult summary = new();
        long start = 0, previousEnd = 0, due = 0;
        try
        {
            start = clock.Milliseconds;
            previousEnd = due = start;
            for (int index = 0; index < MaxSamples; index++)
            {
                long now = clock.Milliseconds;
                Need(now >= previousEnd, "monotonic clock moved backwards");
                if (now < due) clock.Delay(checked((int)(due - now)));
                long began = clock.Milliseconds;
                Need(began >= previousEnd && began >= due, "invalid delayed clock");
                if (began - start > LatestStartMs) { summary.Reason = "deadline"; break; }
                string uptimeBefore = clock.Uptime;
                long utc = clock.UtcMilliseconds;
                Outcome outcome = Run(factory(index));
                long ended = clock.Milliseconds;
                Need(ended >= began, "clock moved backwards during transfer");
                string uptimeAfter = clock.Uptime;
                int? flag = null;
                if (outcome.Accepted)
                {
                    byte[] bytes = Convert.FromBase64String(outcome.DataBase64!);
                    Need(bytes.Length == Length, "sample payload extent");
                    flag = BitConverter.ToUInt16(bytes, 10);
                    summary.SamplesTransportAccepted++;
                }
                summary.SamplesCompleted++;
                emit(new("rt_block_sample", index + 1, began, ended, began - start,
                    utc, uptimeBefore, uptimeAfter, outcome, flag));
                previousEnd = ended;
                due = began + PeriodMs;
                if (!outcome.Accepted) { summary.Reason = "transport_failure"; break; }
                if ((flag!.Value & 1) != 0) { summary.Reason = "rt_flag_set"; break; }
                if (index + 1 == MaxSamples) summary.Reason = "sample_limit";
            }
            summary.ElapsedMs = clock.Milliseconds - start;
            summary.Accepted = (summary.Reason == "sample_limit" || summary.Reason == "rt_flag_set") &&
                summary.SamplesCompleted == summary.SamplesTransportAccepted && summary.SamplesCompleted > 0;
        }
        catch (Exception e)
        {
            summary.Reason = "internal_error";
            summary.Error = e.GetType().Name + ": " + e.Message;
            summary.Accepted = false;
        }
        return summary;
    }
    static int SeriesSelfTests()
    {
        int tests = 0;
        SeriesResult Test(Func<int, FakeClock, FakeOps> make, string reason, bool accepted,
            int count, bool backwards = false, bool emitFailure = false)
        {
            FakeClock clock = new() { ReverseDelay = backwards };
            List<FakeOps> ops = new();
            List<Sample> samples = new();
            SeriesResult result = RunSeries(index => { FakeOps op = make(index, clock); ops.Add(op); return op; }, clock,
                sample =>
                {
                    Need(ops[ops.Count - 1].Calls.Contains("close") || !sample.Transport.Opened,
                        "sample emitted before cleanup");
                    samples.Add(sample);
                    if (emitFailure && samples.Count == 2) throw new IOException("injected output failure");
                });
            Need(result.Reason == reason && result.Accepted == accepted && result.SamplesCompleted == count,
                "series expected reason/count " + reason);
            Need(samples.Count == count, "series emitted sample count");
            Need(ops.Count <= MaxSamples, "series maximum attempts");
            for (int i = 1; i < samples.Count; i++)
                Need(samples[i].StartMilliseconds - samples[i - 1].StartMilliseconds >= PeriodMs,
                    "series catch-up burst");
            tests++;
            return result;
        }
        Test((i, c) => new(), "sample_limit", true, 20);
        Test((i, c) => new() { RtFlag = i == 2 ? (byte)1 : (byte)0 }, "rt_flag_set", true, 3);
        Test((i, c) => new() { OutReturn = i == 1 ? 11 : 12 }, "transport_failure", false, 2);
        Test((i, c) => new() { ThrowAt = "preflight" }, "transport_failure", false, 1);
        Test((i, c) => new() { OnCall = phase => { if (phase == "in") c.Now += 3000; } }, "deadline", false, 2);
        Test((i, c) => new(), "internal_error", false, 1, backwards: true);
        Test((i, c) => new(), "internal_error", false, 2, emitFailure: true);
        Test((i, c) => new() { ReleaseReturn = i == 1 ? -1 : 0 }, "transport_failure", false, 2);
        FakeClock clock = new();
        int created = 0, emitted = 0;
        SeriesResult failedFactory = RunSeries(i => { created++; throw new IOException("injected factory"); }, clock, s => emitted++);
        Need(!failedFactory.Accepted && failedFactory.Reason == "internal_error" && created == 1 && emitted == 0,
            "series factory exception stops");
        tests++;
        return tests;
    }
    static int SelfTest()
    {
        int tests = 0;
        void Case(string name, FakeOps ops, bool accepted, string? missing = null)
        {
            Outcome r = Run(ops);
            Need(r.Accepted == accepted, name + " acceptance");
            if (missing != null) Need(!ops.Calls.Contains(missing), name + " forbidden later phase");
            if (r.Opened) Need(ops.Calls.Contains("close"), name + " close attempted");
            if (r.Claimed) Need(ops.Calls.Contains("release"), name + " release attempted");
            tests++;
        }
        Case("success", new(), true);
        Case("open-failure", new() { OpenReturn = -1 }, false, "claim");
        Case("claim-failure", new() { ClaimReturn = -1 }, false, "out");
        foreach (int n in new[] { -1, 0, 11, 13 }) Case("out-" + n, new() { OutReturn = n }, false, "in");
        foreach (int n in new[] { -1, 0, Length - 1, Length + 1 }) Case("in-" + n, new() { InReturn = n }, false);
        Case("identity-change", new() { ChangeIdentity = true }, false, "claim");
        foreach (string phase in new[] { "preflight", "open", "fd-validation", "claim", "out", "in", "release", "close" })
            Case("exception-" + phase, new() { ThrowAt = phase }, false);
        Case("release-error", new() { ReleaseReturn = -1 }, false);
        Case("close-error", new() { CloseReturn = -1 }, false);
        Need(Convert.ToHexString(Header) == "010100000024014700010000", "fixed LE header");
        Need(Convert.FromHexString(AllDescriptorsHex).Length == 116, "descriptor extent");
        foreach (int length in new[] { 0, 115, 116 })
        {
            byte[] input = new byte[length];
            for (int i = 0; i < length; i++) input[i] = (byte)i;
            using PartialNonseekableStream stream = new(input);
            Need(ReadCachedDescriptors(stream).AsSpan().SequenceEqual(input), "partial nonseekable stream " + length);
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
        Need(oversizedRejected, "oversized cached descriptor rejection");
        tests++;

        int seriesTests = SeriesSelfTests();
        Console.WriteLine(JsonSerializer.Serialize(new { selfTestsPassed = tests + seriesTests, seriesTestsPassed = seriesTests, targetOperations = 0 }));
        return 0;
    }
    static int Main(string[] args)
    {
        if (args.Length == 0)
        {
            Console.WriteLine(JsonSerializer.Serialize(new { dryRun = true, targetOperations = 0, address = "0x47012400", operation = "bounded-RT-block-samples", headerHex = Convert.ToHexString(Header), inputLength = Length, maxSamples = MaxSamples, periodMs = PeriodMs, latestStartMs = LatestStartMs, timeoutMs = TimeoutMs, interfaceNumber = 2 }));
            return 0;
        }
        if (args.Length == 1 && args[0] == "--self-test") return SelfTest();
        if (!(args.Length == 1 && args[0] == "--execute")) return 63;
        if (!RealOps.AbiReady) { Console.WriteLine("REFUSED_ARM32_ABI"); return 64; }
        Console.WriteLine(JsonSerializer.Serialize(new { type = "rt_block_start", maxSamples = MaxSamples,
            periodMs = PeriodMs, latestStartMs = LatestStartMs, inputLength = Length,
            address = "0x47012400", headerHex = Convert.ToHexString(Header) }));
        SeriesResult outcome = RunSeries(i => new RealOps(), new SeriesClock(),
            sample => Console.WriteLine(JsonSerializer.Serialize(sample)));
        Console.WriteLine(JsonSerializer.Serialize(outcome));
        return outcome.Accepted ? 0 : 1;
    }
}
