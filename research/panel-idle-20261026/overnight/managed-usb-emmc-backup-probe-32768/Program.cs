using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;

internal static class Program
{
    const int ChunkLength = 8192, TotalLength = 0x8000, ChunkCount = TotalLength / ChunkLength;
    const int TimeoutMs = 2000, DeadlineMs = 15000;
    const string ExpectedBoot = "00000000-0000-4000-8000-000000000000";
    const string UsbRoot = "/sys/bus/usb/devices/7-1";
    const string DeviceHex = "12010002ef020140e8040120500201020301";
    const string AllDescriptorsHex = DeviceHex + "090262000301048032080b00020202010a09040000010202010a052400100105240100010424020205240600010705830308001009040100020a00000a07050102400010070581024000000904020002ff0000000705820200020007050202000200";
    static readonly byte[] Header = Convert.FromHexString("030200000000000000800000");

    readonly record struct Identity(int Bus, int Device)
    {
        public string Node => $"/dev/bus/usb/{Bus:D3}/{Device:D3}";
    }
    readonly record struct NativeResult(int Value, int Errno);
    sealed record Step(string Phase, int? Value = null, int? Errno = null, string? Error = null);
    sealed record Chunk(int Index, long StartElapsedMs, long EndElapsedMs, int Value, int Errno,
                        bool Stored, string? Sha256);
    sealed class Outcome
    {
        public string Stage { get; set; } = "preflight";
        public List<Step> Steps { get; } = new();
        public List<Chunk> Chunks { get; } = new();
        public bool Opened { get; set; }
        public bool Claimed { get; set; }
        public bool Released { get; set; } = true;
        public bool Closed { get; set; } = true;
        public bool SinkClosed { get; set; }
        public bool Accepted { get; set; }
        public int? OutCount { get; set; }
        public int InputTransfers { get; set; }
        public int CompletedChunks { get; set; }
        public int StoredBytes { get; set; }
        public long ElapsedMs { get; set; }
        public string? DataSha256 { get; set; }
        public string? Error { get; set; }
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
    interface IClock { long Milliseconds { get; } }
    interface IDataSink
    {
        void Write(byte[] data);
        void Close();
    }
    static void Need(bool ok, string message)
    {
        if (!ok) throw new InvalidOperationException(message);
    }

    static Outcome Run(IOps ops, IClock clock, IDataSink sink)
    {
        Outcome result = new();
        using IncrementalHash aggregate = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        int fd = -1;
        long origin = clock.Milliseconds;
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
            long beforeOut = clock.Milliseconds;
            Need(beforeOut >= origin, "monotonic clock reversed before header");
            Need(beforeOut - origin < DeadlineMs, "deadline before header");
            NativeResult write = ops.Bulk(fd, false, (byte[])Header.Clone());
            result.OutCount = write.Value;
            result.Steps.Add(new("out", write.Value, write.Errno));
            Need(write.Value == Header.Length, "header count not exact");

            long previousClock = beforeOut;
            for (int index = 0; index < ChunkCount; index++)
            {
                result.Stage = "in-" + index;
                long start = clock.Milliseconds;
                Need(start >= origin && start >= previousClock, "monotonic clock reversed before input");
                Need(start - origin < DeadlineMs, "deadline before input");
                byte[] data = new byte[ChunkLength];
                NativeResult read = ops.Bulk(fd, true, data);
                result.InputTransfers++;
                long end = clock.Milliseconds;
                bool exact = read.Value == ChunkLength;
                string? chunkSha = exact ? Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant() : null;
                result.Chunks.Add(new(index, start - origin, end - origin, read.Value, read.Errno, false, chunkSha));
                Need(end >= start, "monotonic clock reversed during input");
                previousClock = end;
                Need(exact, "response count not exact");
                sink.Write(data);
                aggregate.AppendData(data);
                result.Chunks[index] = result.Chunks[index] with { Stored = true };
                result.CompletedChunks++;
                result.StoredBytes += data.Length;
            }
            result.Stage = "complete";
        }
        catch (Exception e)
        {
            result.Error = e.GetType().Name + ": " + e.Message;
            result.Steps.Add(new(result.Stage, Error: result.Error));
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
            try
            {
                sink.Close();
                result.SinkClosed = true;
                result.Steps.Add(new("sink-close", 0, 0));
            }
            catch (Exception e) { result.Steps.Add(new("sink-close", Error: e.GetType().Name)); }
        }
        long finish = clock.Milliseconds;
        result.ElapsedMs = finish >= origin ? finish - origin : -1;
        result.DataSha256 = Convert.ToHexString(aggregate.GetHashAndReset()).ToLowerInvariant();
        result.Accepted = result.Stage == "complete" && result.OutCount == 12 &&
            result.InputTransfers == ChunkCount && result.CompletedChunks == ChunkCount &&
            result.StoredBytes == TotalLength && result.Released && result.Closed && result.SinkClosed;
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
    sealed class RealClock : IClock
    {
        readonly long origin = Stopwatch.GetTimestamp();
        public long Milliseconds => (Stopwatch.GetTimestamp() - origin) * 1000 / Stopwatch.Frequency;
    }
    sealed class RealSink : IDataSink
    {
        readonly FileStream stream;
        bool closed;
        public RealSink(string path)
        {
            stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None,
                                    ChunkLength, FileOptions.SequentialScan);
        }
        public void Write(byte[] data)
        {
            Need(!closed && data.Length == ChunkLength, "fixed sink write");
            stream.Write(data, 0, data.Length);
        }
        public void Close()
        {
            if (closed) return;
            stream.Flush(true);
            stream.Dispose();
            closed = true;
        }
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
            Need(input ? data.Length == ChunkLength : data.AsSpan().SequenceEqual(Header), "fixed transfer only");
            GCHandle pinned = GCHandle.Alloc(data, GCHandleType.Pinned);
            try
            {
                Transfer transfer = new() { Ep = input ? 0x82u : 0x02u, Length = (uint)data.Length, Timeout = TimeoutMs, Data = pinned.AddrOfPinnedObject() };
                return Result(ioctlTransfer(fd, BulkRequest, ref transfer));
            }
            finally { pinned.Free(); }
        }
    }

    sealed class FakeClock : IClock
    {
        public long Value;
        public int Reads;
        public int ReverseOnRead = -1;
        public long Milliseconds
        {
            get
            {
                Reads++;
                if (Reads == ReverseOnRead) Value--;
                return Value;
            }
        }
    }
    sealed class MemorySink : IDataSink
    {
        readonly IncrementalHash hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        public int Bytes { get; private set; }
        public bool Closed { get; private set; }
        public bool FailWrite;
        public bool FailClose;
        public string Hash = "";
        public void Write(byte[] data)
        {
            if (FailWrite) throw new IOException("injected sink write");
            Need(!Closed && data.Length == ChunkLength, "memory sink write");
            hash.AppendData(data);
            Bytes += data.Length;
        }
        public void Close()
        {
            if (FailClose) throw new IOException("injected sink close");
            if (Closed) return;
            Hash = Convert.ToHexString(hash.GetHashAndReset()).ToLowerInvariant();
            hash.Dispose();
            Closed = true;
        }
    }
    sealed class FakeOps : IOps
    {
        public List<string> Calls { get; } = new();
        public string? ThrowAt;
        public int OpenReturn = 9, ClaimReturn, OutReturn = 12, ReleaseReturn, CloseReturn;
        public int FailInput = -1, InputReturn = ChunkLength;
        public bool ChangeIdentity;
        public long ClaimAdvanceMs, OutAdvanceMs, InputAdvanceMs;
        public int ReverseAtInput = -1;
        public FakeClock Clock = new();
        int preflights, inputs;
        void Call(string phase) { Calls.Add(phase); if (ThrowAt == phase) throw new IOException("injected"); }
        public Identity Preflight() { Call("preflight"); preflights++; return new(7, ChangeIdentity && preflights == 2 ? 46 : 45); }
        public NativeResult Open(Identity id) { Call("open"); return new(OpenReturn, OpenReturn < 0 ? 5 : 0); }
        public void ValidateFd(int fd, Identity id) { Call("fd-validation"); }
        public NativeResult Claim(int fd) { Call("claim"); Clock.Value += ClaimAdvanceMs; return new(ClaimReturn, ClaimReturn < 0 ? 16 : 0); }
        public NativeResult Bulk(int fd, bool input, byte[] data)
        {
            Call(input ? "in" : "out");
            Need(input ? data.Length == ChunkLength : data.AsSpan().SequenceEqual(Header), "fake fixed data");
            if (!input) { Clock.Value += OutAdvanceMs; return new(OutReturn, OutReturn < 0 ? 5 : 0); }
            int current = inputs++;
            if (current == ReverseAtInput) Clock.Value--;
            else Clock.Value += InputAdvanceMs;
            Array.Fill(data, (byte)0x5a);
            int value = current == FailInput ? InputReturn : ChunkLength;
            return new(value, value < 0 ? 5 : 0);
        }
        public NativeResult Release(int fd) { Call("release"); return new(ReleaseReturn, ReleaseReturn < 0 ? 5 : 0); }
        public NativeResult Close(int fd) { Call("close"); return new(CloseReturn, CloseReturn < 0 ? 5 : 0); }
    }

    static int SelfTest()
    {
        int tests = 0;
        (Outcome, FakeOps, MemorySink) Execute(FakeOps ops, MemorySink? sink = null)
        {
            sink ??= new MemorySink();
            return (Run(ops, ops.Clock, sink), ops, sink);
        }
        void Case(string name, FakeOps ops, bool accepted, int chunks, MemorySink? sink = null, string? missing = null)
        {
            var item = Execute(ops, sink);
            Need(item.Item1.Accepted == accepted, name + " acceptance");
            Need(item.Item1.CompletedChunks == chunks && item.Item3.Bytes == chunks * ChunkLength, name + " extent");
            if (missing != null) Need(!item.Item2.Calls.Contains(missing), name + " forbidden later phase");
            if (item.Item1.Opened) Need(item.Item2.Calls.Contains("close"), name + " close attempted");
            if (item.Item1.Claimed) Need(item.Item2.Calls.Contains("release"), name + " release attempted");
            tests++;
        }
        var success = Execute(new FakeOps());
        Need(success.Item1.Accepted && success.Item1.Chunks.Count == ChunkCount && success.Item1.InputTransfers == ChunkCount, "success shape");
        Need(success.Item1.DataSha256 == success.Item3.Hash && success.Item1.StoredBytes == TotalLength, "success hash/extent");
        Need(success.Item1.DataSha256 == "b78aabbda3b7179baac5a4c9cfda66a6d6a40697bacc1eedf5c1935ca2491893",
             "known 32-KiB payload hash");
        tests++;
        Case("open-failure", new() { OpenReturn = -1 }, false, 0, missing: "claim");
        Case("claim-failure", new() { ClaimReturn = -1 }, false, 0, missing: "out");
        foreach (int n in new[] { -1, 0, 11, 13 }) Case("out-" + n, new() { OutReturn = n }, false, 0, missing: "in");
        foreach (int index in new[] { 0, ChunkCount / 2, ChunkCount - 1 })
            foreach (int n in new[] { -1, 0, ChunkLength - 1, ChunkLength + 1 })
                Case("in-" + index + "-" + n, new() { FailInput = index, InputReturn = n }, false, index);
        Case("deadline-before-header", new() { ClaimAdvanceMs = DeadlineMs }, false, 0, missing: "out");
        Case("deadline-before-first-in", new() { OutAdvanceMs = DeadlineMs }, false, 0, missing: "in");
        Case("deadline-middle", new() { InputAdvanceMs = 7500 }, false, 2);
        Case("reverse-clock", new() { ReverseAtInput = 3 }, false, 3);
        FakeOps crossReverse = new() { InputAdvanceMs = 10 };
        crossReverse.Clock.ReverseOnRead = 5;
        Case("reverse-clock-between-inputs", crossReverse, false, 1);
        Case("identity-change", new() { ChangeIdentity = true }, false, 0, missing: "claim");
        foreach (string phase in new[] { "preflight", "open", "fd-validation", "claim", "out", "in", "release", "close" })
            Case("exception-" + phase, new() { ThrowAt = phase }, false, phase == "release" || phase == "close" ? ChunkCount : 0);
        Case("release-error", new() { ReleaseReturn = -1 }, false, ChunkCount);
        Case("close-error", new() { CloseReturn = -1 }, false, ChunkCount);
        Case("sink-write-error", new(), false, 0, new MemorySink() { FailWrite = true });
        Case("sink-close-error", new(), false, ChunkCount, new MemorySink() { FailClose = true });
        Need(Convert.ToHexString(Header) == "030200000000000000800000", "fixed LE header");
        Need(Header.AsSpan(0, 4).SequenceEqual(BitConverter.GetBytes(0x203)) &&
             Header.AsSpan(4, 4).SequenceEqual(BitConverter.GetBytes(0)) &&
             Header.AsSpan(8, 4).SequenceEqual(BitConverter.GetBytes(TotalLength)), "header fields");
        Need(ChunkCount == 4 && ChunkCount * ChunkLength == TotalLength, "fixed extent");
        Need(Convert.FromHexString(AllDescriptorsHex).Length == 116, "descriptor extent");
        tests += 4;
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
        Console.WriteLine(JsonSerializer.Serialize(new { selfTestsPassed = tests, targetOperations = 0 }));
        return 0;
    }

    static int Main(string[] args)
    {
        if (args.Length == 0)
        {
            Console.WriteLine(JsonSerializer.Serialize(new { dryRun = true, targetOperations = 0,
                target = "0x203", address = "0x0", totalLength = TotalLength, chunkLength = ChunkLength,
                chunks = ChunkCount, deadlineMs = DeadlineMs, headerHex = Convert.ToHexString(Header),
                operation = "bounded-read-only-emmc-backup", interfaceNumber = 2 }));
            return 0;
        }
        if (args.Length == 1 && args[0] == "--self-test") return SelfTest();
        if (!(args.Length == 1 && args[0] == "--execute")) return 63;
        if (!RealOps.AbiReady) { Console.WriteLine("REFUSED_ARM32_ABI"); return 64; }
        string dataPath = Path.Combine(AppContext.BaseDirectory, "fixeddata.bin");
        string resultPath = Path.Combine(AppContext.BaseDirectory, "result.json");
        if (File.Exists(dataPath) || File.Exists(resultPath))
        {
            Console.WriteLine("REFUSED_OUTPUT_EXISTS");
            return 65;
        }
        Outcome outcome;
        using (RealSinkGuard guard = new(new RealSink(dataPath)))
        {
            outcome = Run(new RealOps(), new RealClock(), guard.Sink);
        }
        byte[] result = JsonSerializer.SerializeToUtf8Bytes(outcome, new JsonSerializerOptions { WriteIndented = true });
        using (FileStream stream = new(resultPath, FileMode.CreateNew, FileAccess.Write, FileShare.None))
        {
            stream.Write(result, 0, result.Length);
            stream.Flush(true);
        }
        Console.WriteLine(JsonSerializer.Serialize(new { outcome.Accepted, outcome.Stage, outcome.CompletedChunks,
            outcome.InputTransfers, outcome.StoredBytes, outcome.ElapsedMs, outcome.DataSha256,
            resultBytes = result.Length, dataFile = "fixeddata.bin", resultFile = "result.json" }));
        return outcome.Accepted ? 0 : 1;
    }

    sealed class RealSinkGuard : IDisposable
    {
        public RealSink Sink { get; }
        public RealSinkGuard(RealSink sink) { Sink = sink; }
        public void Dispose()
        {
            try { Sink.Close(); } catch { }
        }
    }
}
