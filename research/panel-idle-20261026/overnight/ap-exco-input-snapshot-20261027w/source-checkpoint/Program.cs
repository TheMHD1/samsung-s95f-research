using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;

internal static class Program
{
    const int PointerLength = 32, OrdinaryLength = 824, DerivedLength = 1004, TimeoutMs = 2000;
    const string ExpectedBoot = "00000000-0000-4000-8000-000000000000";
    const string UsbRoot = "/sys/bus/usb/devices/7-1";
    const string DeviceHex = "12010002ef020140e8040120500201020301";
    const string AllDescriptorsHex = DeviceHex + "090262000301048032080b00020202010a09040000010202010a052400100105240100010424020205240600010705830308001009040100020a00000a07050102400010070581024000000904020002ff0000000705820200020007050202000200";
    static readonly byte[] PointerHeader = Convert.FromHexString("01010000C002004720000000");
    static readonly byte[] OrdinaryHeader = Convert.FromHexString("0101000014FF004538030000");
    static readonly byte[] DerivedHeader = Convert.FromHexString("01010000A8580145EC030000");
    readonly record struct Identity(int Bus, int Device)
    {
        public string Node => $"/dev/bus/usb/{Bus:D3}/{Device:D3}";
    }
    readonly record struct NativeResult(int Value, int Errno);
    enum ProtocolPhase { ReadyForHeader, ExpectingPointerIn, ExpectingOrdinaryIn, ExpectingDerivedIn, Unknown }
    sealed record Step(string Name, string Direction, int Expected, int? Count = null, int? Errno = null, string? Error = null);
    sealed class Outcome
    {
        public string Schema { get; set; } = "managed-usb-ap-exco-input-snapshot-v1";
        public string Stage { get; set; } = "preflight";
        public string ProtocolPhase { get; set; } = "ReadyForHeader";
        public List<Step> Steps { get; } = new();
        public bool Opened { get; set; }
        public bool Claimed { get; set; }
        public bool Released { get; set; } = true;
        public bool Closed { get; set; } = true;
        public bool Accepted { get; set; }
        public string? PointerBase64 { get; set; }
        public string? PointerSha256 { get; set; }
        public string? OrdinaryBase64 { get; set; }
        public string? OrdinarySha256 { get; set; }
        public string? DerivedBase64 { get; set; }
        public string? DerivedSha256 { get; set; }
        public uint? OrdinaryPointer { get; set; }
        public uint? DerivedPointer { get; set; }
        public bool PointerMatches { get; set; }
        public ushort? OrdinaryGateCa { get; set; }
        public ushort? OrdinaryGate116 { get; set; }
        public ushort? OrdinaryX10A { get; set; }
        public ushort? OrdinaryX10C { get; set; }
        public ushort? OrdinaryOutputE6 { get; set; }
        public ushort? OrdinaryOutput2Fc { get; set; }
        public ushort? OrdinaryCounter300 { get; set; }
        public ushort? OrdinaryCounter302 { get; set; }
        public byte? DerivedByteZero { get; set; }
        public byte? DerivedByteOne { get; set; }
        public byte? DerivedByte3D8 { get; set; }
        public bool InterpretationAccepted { get; set; }
        public string Interpretation { get; set; } = "not-decoded";
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
        byte[] pointer = new byte[PointerLength];
        byte[] ordinary = new byte[OrdinaryLength];
        byte[] derived = new byte[DerivedLength];
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
            Read("pointer", PointerHeader, pointer, ProtocolPhase.ExpectingPointerIn);
            result.PointerBase64 = Convert.ToBase64String(pointer);
            result.PointerSha256 = Convert.ToHexString(SHA256.HashData(pointer)).ToLowerInvariant();
            result.OrdinaryPointer = BitConverter.ToUInt32(pointer, 4);
            result.DerivedPointer = BitConverter.ToUInt32(pointer, 12);
            result.PointerMatches = result.OrdinaryPointer == 0x4500FF14u && result.DerivedPointer == 0x450158A8u;
            Need(result.PointerMatches, "pointer anchors mismatch");
            Read("ordinary", OrdinaryHeader, ordinary, ProtocolPhase.ExpectingOrdinaryIn);
            result.OrdinaryBase64 = Convert.ToBase64String(ordinary);
            result.OrdinarySha256 = Convert.ToHexString(SHA256.HashData(ordinary)).ToLowerInvariant();
            result.OrdinaryGateCa = BitConverter.ToUInt16(ordinary, 0xCA);
            result.OrdinaryGate116 = BitConverter.ToUInt16(ordinary, 0x116);
            result.OrdinaryX10A = BitConverter.ToUInt16(ordinary, 0x10A);
            result.OrdinaryX10C = BitConverter.ToUInt16(ordinary, 0x10C);
            result.OrdinaryOutputE6 = BitConverter.ToUInt16(ordinary, 0xE6);
            result.OrdinaryOutput2Fc = BitConverter.ToUInt16(ordinary, 0x2FC);
            result.OrdinaryCounter300 = BitConverter.ToUInt16(ordinary, 0x300);
            result.OrdinaryCounter302 = BitConverter.ToUInt16(ordinary, 0x302);
            Read("derived", DerivedHeader, derived, ProtocolPhase.ExpectingDerivedIn);
            result.DerivedBase64 = Convert.ToBase64String(derived);
            result.DerivedSha256 = Convert.ToHexString(SHA256.HashData(derived)).ToLowerInvariant();
            result.DerivedByteZero = derived[0]; result.DerivedByteOne = derived[1]; result.DerivedByte3D8 = derived[0x3D8];
            result.InterpretationAccepted = true;
            result.Interpretation = "pointer-gated-sequential-object-snapshot";
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
            result.PointerBase64 != null && result.OrdinaryBase64 != null && result.DerivedBase64 != null &&
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
            Need(input ? data.Length == PointerLength || data.Length == OrdinaryLength || data.Length == DerivedLength :
                data.AsSpan().SequenceEqual(PointerHeader) || data.AsSpan().SequenceEqual(OrdinaryHeader) ||
                data.AsSpan().SequenceEqual(DerivedHeader), "fixed transfer only");
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
        public int[] BulkReturns = { 12, PointerLength, 12, OrdinaryLength, 12, DerivedLength };
        public bool ChangeIdentity;
        public uint OrdinaryPointer = 0x4500FF14u, DerivedPointer = 0x450158A8u;
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
                0 => "pointer-out", 1 => "pointer-in", 2 => "ordinary-out",
                3 => "ordinary-in", 4 => "derived-out", 5 => "derived-in",
                _ => "extra-bulk"
            });
            if (index == ThrowBulkAt) throw new IOException("injected bulk");
            Need(index < BulkReturns.Length, "fake bulk index");
            if (input)
            {
                for (int i = 0; i < data.Length; i++) data[i] = (byte)(0x40 + i);
                if (index == 1) { BitConverter.GetBytes(OrdinaryPointer).CopyTo(data, 4); BitConverter.GetBytes(DerivedPointer).CopyTo(data, 12); }
                if (index == 3) { BitConverter.GetBytes((ushort)1).CopyTo(data, 0xCA); BitConverter.GetBytes((ushort)1).CopyTo(data, 0x116); BitConverter.GetBytes((ushort)9).CopyTo(data, 0x10A); BitConverter.GetBytes((ushort)10).CopyTo(data, 0x10C); BitConverter.GetBytes((ushort)1).CopyTo(data, 0xE6); BitConverter.GetBytes((ushort)2).CopyTo(data, 0x2FC); BitConverter.GetBytes((ushort)7).CopyTo(data, 0x300); BitConverter.GetBytes((ushort)8).CopyTo(data, 0x302); }
                if (index == 5) { data[0] = 3; data[1] = 10; data[0x3D8] = 1; }
            }
            else Need(data.AsSpan().SequenceEqual(index switch {
                0 => PointerHeader, 2 => OrdinaryHeader, 4 => DerivedHeader,
                _ => throw new InvalidOperationException("fake header index")
            }), "fake fixed header");
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
        Need(success.Accepted && success.InterpretationAccepted && success.PointerMatches &&
             success.OrdinaryPointer == 0x4500FF14u && success.DerivedPointer == 0x450158A8u &&
             success.OrdinaryGateCa == 1 && success.OrdinaryGate116 == 1 && success.OrdinaryX10A == 9 && success.OrdinaryX10C == 10 &&
             success.OrdinaryOutputE6 == 1 && success.OrdinaryOutput2Fc == 2 && success.OrdinaryCounter300 == 7 && success.OrdinaryCounter302 == 8 &&
             success.DerivedByteZero == 3 && success.DerivedByteOne == 10 && success.DerivedByte3D8 == 1 &&
             Convert.FromBase64String(success.PointerBase64!).Length == PointerLength && Convert.FromBase64String(success.OrdinaryBase64!).Length == OrdinaryLength &&
             Convert.FromBase64String(success.DerivedBase64!).Length == DerivedLength && success.Steps.Count == 10, "success"); tests++;
        Outcome mismatch = Run(new FakeOps { OrdinaryPointer = 0x12345678u });
        Need(!mismatch.Accepted && mismatch.PointerBase64 != null && mismatch.OrdinaryBase64 == null &&
             !mismatch.Steps.Exists(x => x.Name == "ordinary-header"), "ordinary pointer gate"); tests++;
        mismatch = Run(new FakeOps { DerivedPointer = 0x12345678u });
        Need(!mismatch.Accepted && mismatch.PointerBase64 != null && mismatch.DerivedBase64 == null &&
             !mismatch.Steps.Exists(x => x.Name == "ordinary-header"), "derived pointer gate"); tests++;
        Outcome baseShort = Run(new FakeOps { BulkReturns = new[] { 12, PointerLength, 12, OrdinaryLength - 1, 12, DerivedLength } });
        Need(!baseShort.Accepted && baseShort.PointerBase64 != null && baseShort.OrdinaryBase64 == null && baseShort.DerivedBase64 == null, "pointer retained"); tests++;
        Outcome tailShort = Run(new FakeOps { BulkReturns = new[] { 12, PointerLength, 12, OrdinaryLength, 12, DerivedLength - 1 } });
        Need(!tailShort.Accepted && tailShort.PointerBase64 != null && tailShort.OrdinaryBase64 != null && tailShort.DerivedBase64 == null, "prior retained"); tests++;
        Case("open-fail", new() { OpenReturn = -1 }, false, "claim");
        Case("claim-fail", new() { ClaimReturn = -1 }, false, "pointer-out");
        Case("identity", new() { ChangeIdentity = true }, false, "claim");
        foreach (string phase in new[] { "preflight", "open", "fd-validation", "claim" })
            Case("exception-" + phase, new() { ThrowAt = phase }, false, "pointer-out");
        for (int step = 0; step < 6; step++)
        {
            int[] exacts = { 12, PointerLength, 12, OrdinaryLength, 12, DerivedLength };
            int exact = exacts[step];
            foreach (int value in new[] { -1, 0, exact - 1, exact + 1 })
            {
                int[] returns = (int[])exacts.Clone();
                returns[step] = value;
                string? forbidden = step switch {
                    0 => "pointer-in", 1 => "ordinary-out", 2 => "ordinary-in",
                    3 => "derived-out", 4 => "derived-in", _ => null
                };
                Case("bulk-count", new() { BulkReturns = returns }, false, forbidden);
            }
            string? exceptionForbidden = step switch {
                0 => "pointer-in", 1 => "ordinary-out", 2 => "ordinary-in",
                3 => "derived-out", 4 => "derived-in", _ => null
            };
            Case("bulk-exception", new() { ThrowBulkAt = step }, false, exceptionForbidden);
        }
        Case("release", new() { ReleaseReturn = -1 }, false);
        Case("close", new() { CloseReturn = -1 }, false);
        Need(Convert.ToHexString(PointerHeader) == "01010000C002004720000000" &&
             Convert.ToHexString(OrdinaryHeader) == "0101000014FF004538030000" &&
             Convert.ToHexString(DerivedHeader) == "01010000A8580145EC030000", "headers");
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
                schema = "managed-usb-ap-exco-input-snapshot-dry-v1", dryRun = true, targetOperations = 0,
                requests = new[] {
                    new { address = "0x470002c0", headerHex = Convert.ToHexString(PointerHeader), length = PointerLength },
                    new { address = "0x4500ff14", headerHex = Convert.ToHexString(OrdinaryHeader), length = OrdinaryLength },
                    new { address = "0x450158a8", headerHex = Convert.ToHexString(DerivedHeader), length = DerivedLength }
                },
                timeoutMs = TimeoutMs, interfaceNumber = 2, writes = 0, retries = 0
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
