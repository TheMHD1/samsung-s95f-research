using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;

internal static class Program
{
    const int DataLength = 8, TimeoutMs = 2000;
    const string ExpectedBoot = "00000000-0000-4000-8000-000000000000";
    const string UsbRoot = "/sys/bus/usb/devices/7-1";
    const string DeviceHex = "12010002ef020140e8040120500201020301";
    const string AllDescriptorsHex = DeviceHex + "090262000301048032080b00020202010a09040000010202010a052400100105240100010424020205240600010705830308001009040100020a00000a07050102400010070581024000000904020002ff0000000705820200020007050202000200";
    static readonly byte[] Header = Convert.FromHexString("0101000030D7004508000000");
    readonly record struct Identity(int Bus, int Device)
    {
        public string Node => $"/dev/bus/usb/{Bus:D3}/{Device:D3}";
    }
    readonly record struct NativeResult(int Value, int Errno);
    enum ProtocolPhase { ReadyForHeader, ExpectingDataIn, Unknown }
    sealed record Step(string Name, string Direction, int Expected, int? Count = null, int? Errno = null, string? Error = null);
    sealed class Outcome
    {
        public string Schema { get; set; } = "managed-usb-npc-ap-divisor-read-v1";
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
        public string? PartialDataBase64 { get; set; }
        public int? PartialDataLength { get; set; }
        public ushort? Context14 { get; set; }
        public ushort? Divisor16 { get; set; }
        public ushort? Divisor18 { get; set; }
        public ushort? Divisor1A { get; set; }
        public string Interpretation { get; set; } = "not-sampled";
        public bool PointerIdentityGateUsed { get; set; }
        public bool StoredDefaultsUsedAsIdentity { get; set; }
        public long TimestampFrequency { get; set; } = Stopwatch.Frequency;
        public long? ReadStartTicks { get; set; }
        public long? ReadEndTicks { get; set; }
        public bool PhysicalPictureObserved { get; set; }
        public bool BusContentsAltered { get; set; }
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
        ProtocolPhase phase = ProtocolPhase.ReadyForHeader;
        int fd = -1;
        byte[] data = new byte[DataLength];
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
                NativeResult input;
                try { input = ops.Bulk(fd, true, output); }
                finally { result.ReadEndTicks = Stopwatch.GetTimestamp(); }
                if (input.Value > 0 && input.Value <= output.Length)
                {
                    result.PartialDataLength = input.Value;
                    result.PartialDataBase64 = Convert.ToBase64String(output, 0, input.Value);
                }
                if (input.Value == output.Length) phase = ProtocolPhase.ReadyForHeader;
                result.Steps.Add(new(prefix + "-data", "IN", output.Length, input.Value, input.Errno));
                Need(input.Value == output.Length, prefix + " input count not exact");
            }
            result.ReadStartTicks = Stopwatch.GetTimestamp();
            Read("npc", Header, data, ProtocolPhase.ExpectingDataIn);
            result.DataBase64 = Convert.ToBase64String(data);
            result.DataSha256 = Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();
            result.Context14 = BitConverter.ToUInt16(data, 0);
            result.Divisor16 = BitConverter.ToUInt16(data, 2);
            result.Divisor18 = BitConverter.ToUInt16(data, 4);
            result.Divisor1A = BitConverter.ToUInt16(data, 6);
            result.Interpretation = "conditional-selector0-npc-ap-object-offsets-14-through-1b";
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
            result.DataBase64 != null && result.DataSha256 != null &&
            result.Released && result.Closed;
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
            Need(input ? data.Length == DataLength : data.AsSpan().SequenceEqual(Header),
                "fixed transfer only");
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
        public int ThrowBulkAt = -1;
        public int OpenReturn = 9, ClaimReturn, ReleaseReturn, CloseReturn;
        public int[] BulkReturns = { 12, DataLength };
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
            Calls.Add(index switch {
                0 => "npc-out", 1 => "npc-in",
                _ => "extra-bulk"
            });
            if (index == ThrowBulkAt) throw new IOException("injected bulk");
            Need(index < BulkReturns.Length, "fake bulk index");
            if (input)
            {
                ushort[] values = { 100, 490, 491, 1024 };
                for (int i = 0; i < values.Length; i++)
                    BitConverter.GetBytes(values[i]).CopyTo(data, i * 2);
            }
            else Need(index == 0 && data.AsSpan().SequenceEqual(Header), "fake fixed header");
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
        byte[] raw = Convert.FromBase64String(success.DataBase64!);
        Need(success.Accepted && success.ProtocolPhase == "ReadyForHeader" &&
             success.Interpretation == "conditional-selector0-npc-ap-object-offsets-14-through-1b" &&
             !success.PointerIdentityGateUsed && !success.StoredDefaultsUsedAsIdentity &&
             success.Context14 == 100 && success.Divisor16 == 490 &&
             success.Divisor18 == 491 && success.Divisor1A == 1024 &&
             raw.Length == DataLength && success.DataSha256 ==
             Convert.ToHexString(SHA256.HashData(raw)).ToLowerInvariant() &&
             success.PartialDataLength == DataLength &&
             Convert.FromBase64String(success.PartialDataBase64!).AsSpan().SequenceEqual(raw) &&
             success.ReadStartTicks.HasValue && success.ReadEndTicks >= success.ReadStartTicks &&
             success.TimestampFrequency > 0 && success.Steps.Count == 6, "success"); tests++;
        Outcome partial = Run(new FakeOps { BulkReturns = new[] { 12, 4 } });
        Need(!partial.Accepted && partial.ProtocolPhase == "Unknown" &&
             partial.DataBase64 == null && partial.DataSha256 == null &&
             partial.PartialDataLength == 4 &&
             Convert.FromBase64String(partial.PartialDataBase64!).AsSpan().SequenceEqual(
                 new byte[] { 100, 0, 234, 1 }) &&
             partial.ReadEndTicks >= partial.ReadStartTicks,
             "short input prefix retention"); tests++;
        Outcome overlong = Run(new FakeOps { BulkReturns = new[] { 12, DataLength + 1 } });
        Need(!overlong.Accepted && overlong.PartialDataLength == null &&
             overlong.PartialDataBase64 == null && overlong.DataBase64 == null,
             "overlong input untrusted"); tests++;
        Case("open-fail", new() { OpenReturn = -1 }, false, "claim");
        Case("claim-fail", new() { ClaimReturn = -1 }, false, "npc-out");
        Case("identity", new() { ChangeIdentity = true }, false, "claim");
        foreach (string phase in new[] { "preflight", "open", "fd-validation", "claim" })
            Case("exception-" + phase, new() { ThrowAt = phase }, false, "npc-out");
        for (int step = 0; step < 2; step++)
        {
            int[] exacts = { 12, DataLength };
            int exact = exacts[step];
            foreach (int value in new[] { -1, 0, exact - 1, exact + 1 })
            {
                int[] returns = (int[])exacts.Clone();
                returns[step] = value;
                string? forbidden = step == 0 ? "npc-in" : "extra-bulk";
                Case("bulk-count", new() { BulkReturns = returns }, false, forbidden);
            }
            string? exceptionForbidden = step == 0 ? "npc-in" : "extra-bulk";
            Case("bulk-exception", new() { ThrowBulkAt = step }, false, exceptionForbidden);
        }
        Case("release", new() { ReleaseReturn = -1 }, false);
        Case("close", new() { CloseReturn = -1 }, false);
        Need(Convert.ToHexString(Header) == "0101000030D7004508000000", "header");
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
    static int Main(string[] args)
    {
        if (args.Length == 0)
        {
            Console.WriteLine(JsonSerializer.Serialize(new {
                schema = "managed-usb-npc-ap-divisor-read-dry-v1", dryRun = true, targetOperations = 0,
                requests = new[] {
                    new { address = "0x4500d730", headerHex = Convert.ToHexString(Header), length = DataLength }
                },
                timeoutMs = TimeoutMs, interfaceNumber = 2, writes = 0, retries = 0,
                interpretation = "conditional-selector0-npc-ap-object-offsets-14-through-1b",
                pointerIdentityGate = false, storedDefaultsIdentityGate = false
            }));
            return 0;
        }
        if (args.Length == 1 && args[0] == "--self-test") return SelfTest();
        if (!(args.Length == 1 && args[0] == "--execute")) return 63;
        if (!RealOps.AbiReady) { Console.WriteLine("REFUSED_ARM32_ABI"); return 64; }
        Outcome outcome = Run(new RealOps());
        Console.WriteLine(JsonSerializer.Serialize(outcome));
        return outcome.Accepted ? 0 : 1;
    }
}
