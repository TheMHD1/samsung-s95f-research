using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;

internal static class Program
{
    const int TimeoutMs = 2000, HoldMs = 3000, ArmDeadlineMs = 10000;
    const int WholeDeadlineMs = 20000, MinimumArmBudgetMs = 18000;
    const int RingLength = 15372, RtLength = 64, CallbackLength = 64;
    const string ExpectedBoot = "00000000-0000-4000-8000-000000000000";
    const string UsbRoot = "/sys/bus/usb/devices/7-1";
    const string DeviceHex = "12010002ef020140e8040120500201020301";
    const string AllDescriptorsHex = DeviceHex + "090262000301048032080b00020202010a09040000010202010a052400100105240100010424020205240600010705830308001009040100020a00000a07050102400010070581024000000904020002ff0000000705820200020007050202000200";
    static readonly byte[] CallbackReadHeader = Convert.FromHexString("010100008005004540000000");
    static readonly byte[] RingReadHeader = Convert.FromHexString("01010000000020200C3C0000");
    static readonly byte[] RtReadHeader = Convert.FromHexString("010100000024014740000000");
    static readonly byte[] GateWriteHeader = Convert.FromHexString("020100000624014702000000");
    static readonly byte[] ArmPayload = { 1, 0 }, RestorePayload = { 0, 0 };
    static readonly uint[] PackagedCallbacks = { 0x2945d, 0x293d1, 0x294fb, 0, 0, 0x28b85, 0x28cf1, 0x294f5 };
    static readonly JsonSerializerOptions JsonOptions = new()
    {
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    enum Phase { ReadyForHeader, ExpectingWritePayload, ExpectingReadIn, Unknown }
    readonly record struct Identity(int Bus, int Device)
    {
        public string Node => $"/dev/bus/usb/{Bus:D3}/{Device:D3}";
    }
    readonly record struct NativeResult(int Value, int Errno);
    sealed record Step(string Name, long AtMs, string Direction, int Expected,
                       int? Count, int? Errno, string Before, string After,
                       string? Error = null);
    sealed record Marker(string Name, long AtMs, string Phase);

    sealed class Outcome
    {
        public string Stage { get; set; } = "preflight";
        public string ProtocolPhase { get; set; } = "ReadyForHeader";
        public List<Step> Steps { get; } = new();
        public List<Marker> Markers { get; } = new();
        public List<string> Errors { get; } = new();
        public bool Opened { get; set; }
        public bool Claimed { get; set; }
        public bool Released { get; set; } = true;
        public bool Closed { get; set; } = true;
        public bool ArmAttempted { get; set; }
        public bool ArmTransportComplete { get; set; }
        public bool ArmVerified { get; set; }
        public bool ObservationCompleted { get; set; }
        public bool RestoreAttempted { get; set; }
        public bool RestoreTransportComplete { get; set; }
        public bool RestoreVerified { get; set; }
        public bool RestoreUnverified { get; set; }
        public bool LogFlagMayRemainChanged { get; set; }
        public bool DeadlineViolation { get; set; }
        public bool Accepted { get; set; }
        public bool PhysicalPictureObserved { get; set; }
        public bool RepairEstablished { get; set; }
        public uint? BaselineWriteCursor { get; set; }
        public uint? BaselineReadCursor { get; set; }
        public uint? BaselineFlag { get; set; }
        public ushort? PreArmGate { get; set; }
        public ushort? ArmedGate { get; set; }
        public ushort? RestoredGate { get; set; }
        public string? CallbackBase64 { get; set; }
        public string? CallbackSha256 { get; set; }
        public string? BaselineRingBase64 { get; set; }
        public string? BaselineRingSha256 { get; set; }
        public string? PreArmRtBase64 { get; set; }
        public string? ArmedRtBase64 { get; set; }
        public string? RestoredRtBase64 { get; set; }
        public string? PostRingBase64 { get; set; }
        public string? PostRingSha256 { get; set; }
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
    interface IClock
    {
        long NowMs { get; }
        void Hold(int milliseconds);
    }
    static void Need(bool ok, string message)
    {
        if (!ok) throw new InvalidOperationException(message);
    }
    static string Sha(byte[] data) => Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();
    static string B64(byte[] data) => Convert.ToBase64String(data);
    static string PhaseName(Phase phase) => phase.ToString();

    sealed class Controller
    {
        readonly IOps ops;
        readonly IClock clock;
        readonly Outcome result;
        readonly int fd;
        readonly long wholeDeadline;
        long? armDeadline;
        long lastTime = -1;
        Phase phase = Phase.ReadyForHeader;

        public Controller(IOps ops, IClock clock, Outcome result, int fd,
                          long operationDeadline)
        {
            this.ops = ops;
            this.clock = clock;
            this.result = result;
            this.fd = fd;
            Time();
            wholeDeadline = operationDeadline;
        }
        long Time()
        {
            long now = clock.NowMs;
            Need(now >= lastTime, "monotonic clock moved backwards");
            lastTime = now;
            return now;
        }
        long UrgentTime()
        {
            try
            {
                long now = clock.NowMs;
                if (now >= lastTime) lastTime = now;
            }
            catch { }
            return Math.Max(0, lastTime);
        }
        void SetPhase(Phase value)
        {
            phase = value;
            result.ProtocolPhase = PhaseName(value);
        }
        public bool Ready => phase == Phase.ReadyForHeader;
        public void Mark(string name) => result.Markers.Add(new(name, Time(), PhaseName(phase)));
        void NeedReady() => Need(phase == Phase.ReadyForHeader, "new header outside ready phase");
        void NeedTransactionBudget(long deadline, int transferCount, string name)
        {
            Need(Time() + (long)transferCount * TimeoutMs <= deadline,
                 name + " lacks bounded transfer budget");
        }
        NativeResult Transfer(string name, bool input, byte[] data, int expected,
                              Phase afterExact, bool urgent = false)
        {
            string before = PhaseName(phase);
            long at;
            try { at = urgent ? UrgentTime() : Time(); }
            catch (Exception e)
            {
                if (phase != Phase.ReadyForHeader) SetPhase(Phase.Unknown);
                result.Errors.Add(name + "-clock: " + e.GetType().Name + ": " + e.Message);
                throw;
            }
            NativeResult native;
            try
            {
                native = ops.Bulk(fd, input, data);
            }
            catch (Exception e)
            {
                SetPhase(Phase.Unknown);
                result.Steps.Add(new(name, at, input ? "IN" : "OUT", expected,
                                     null, null, before, PhaseName(phase),
                                     e.GetType().Name + ": " + e.Message));
                throw;
            }
            if (native.Value == expected) SetPhase(afterExact);
            else SetPhase(Phase.Unknown);
            result.Steps.Add(new(name, at, input ? "IN" : "OUT", expected,
                                 native.Value, native.Errno, before, PhaseName(phase)));
            Need(native.Value == expected, name + " count not exact");
            return native;
        }
        public byte[] Read(string name, byte[] header, int length, long? deadline = null)
        {
            NeedReady();
            long bound = deadline ?? wholeDeadline;
            NeedTransactionBudget(bound, 2, name);
            Transfer(name + "-header", false, (byte[])header.Clone(), 12,
                     Phase.ExpectingReadIn);
            byte[] data = new byte[length];
            Transfer(name + "-data", true, data, length, Phase.ReadyForHeader);
            return data;
        }
        public void Write(string name, byte[] payload, long? deadline = null)
        {
            NeedReady();
            long bound = deadline ?? wholeDeadline;
            NeedTransactionBudget(bound, 2, name);
            Transfer(name + "-header", false, (byte[])GateWriteHeader.Clone(), 12,
                     Phase.ExpectingWritePayload);
            // After an exact header, the payload is mandatory. No intervening
            // deadline refusal may strand the device expecting payload bytes.
            Transfer(name + "-payload", false, (byte[])payload.Clone(), 2,
                     Phase.ReadyForHeader);
        }
        public void WriteUrgentRestore()
        {
            NeedReady();
            Transfer("restore-header", false, (byte[])GateWriteHeader.Clone(), 12,
                     Phase.ExpectingWritePayload, urgent: true);
            Transfer("restore-payload", false, (byte[])RestorePayload.Clone(), 2,
                     Phase.ReadyForHeader, urgent: true);
        }
        public void NeedArmBudget()
        {
            NeedReady();
            Need(Time() + MinimumArmBudgetMs <= wholeDeadline,
                 "insufficient whole-operation budget before arm");
        }
        public void StartArmDeadline()
        {
            armDeadline = checked(Time() + ArmDeadlineMs);
        }
        public bool CanVerifyArmAndRestore()
        {
            Need(armDeadline.HasValue, "arm deadline absent");
            return Time() + 4L * TimeoutMs <= armDeadline.GetValueOrDefault();
        }
        public bool CanHoldAndRestore()
        {
            Need(armDeadline.HasValue, "arm deadline absent");
            return Time() + HoldMs + 2L * TimeoutMs <= armDeadline.GetValueOrDefault();
        }
        public long ArmDeadline
        {
            get { Need(armDeadline.HasValue, "arm deadline absent"); return armDeadline!.Value; }
        }
        public bool RestoreInsideLogicalDeadlines()
        {
            if (!armDeadline.HasValue) return false;
            long now = Time();
            return now + 2L * TimeoutMs <= armDeadline.GetValueOrDefault() &&
                   now + 2L * TimeoutMs <= wholeDeadline;
        }
        public bool CanReadInsideWholeDeadline()
        {
            return Time() + 2L * TimeoutMs <= wholeDeadline;
        }
        public void Observe()
        {
            NeedReady();
            long start = Time();
            long end = checked(start + HoldMs);
            Need(end + 2L * TimeoutMs <= ArmDeadline, "hold lacks restore reserve");
            result.Markers.Add(new("observe-start", start, PhaseName(phase)));
            while (true)
            {
                long remaining = end - Time();
                if (remaining <= 0) break;
                int slice = (int)Math.Min(50, remaining);
                Need(slice >= 1 && slice <= 50, "bounded hold slice");
                clock.Hold(slice);
                Need(Time() <= ArmDeadline - 2L * TimeoutMs,
                     "arm deadline reserve exhausted during hold");
            }
            result.Markers.Add(new("observe-end", Time(), PhaseName(phase)));
        }
    }

    static ushort Gate(byte[] rt)
    {
        Need(rt.Length == RtLength, "RT extent");
        return BitConverter.ToUInt16(rt, 6);
    }
    static void ValidateCallbacks(byte[] data)
    {
        Need(data.Length == CallbackLength, "callback extent");
        for (int i = 0; i < PackagedCallbacks.Length; i++)
            Need(BitConverter.ToUInt32(data, 12 + i * 4) == PackagedCallbacks[i],
                 "callback tuple mismatch at word " + i);
    }
    static void ValidateRing(byte[] data, Outcome result)
    {
        Need(data.Length == RingLength, "ring extent");
        uint write = BitConverter.ToUInt32(data, 0);
        uint read = BitConverter.ToUInt32(data, 4);
        uint flag = BitConverter.ToUInt32(data, 8);
        Need(write <= 0x3c00 && read <= 0x3c00, "ring cursor bounds");
        Need(flag <= 1, "ring flag bounds");
        result.BaselineWriteCursor = write;
        result.BaselineReadCursor = read;
        result.BaselineFlag = flag;
    }

    static Outcome Run(IOps ops, IClock clock)
    {
        Outcome result = new();
        int fd = -1;
        Controller? controller = null;
        bool mutationMayHaveStarted = false;
        bool failure = false;
        long operationDeadline = checked(clock.NowMs + WholeDeadlineMs);
        try
        {
            Identity id = ops.Preflight();
            result.Stage = "open";
            NativeResult opened = ops.Open(id);
            Need(opened.Value >= 0, "open failed errno=" + opened.Errno);
            fd = opened.Value;
            result.Opened = true;
            result.Closed = false;
            result.Stage = "fd-validation";
            ops.ValidateFd(fd, id);
            result.Stage = "identity-recheck";
            Need(ops.Preflight() == id, "USB identity changed");
            result.Stage = "claim";
            NativeResult claimed = ops.Claim(fd);
            Need(claimed.Value == 0, "claim failed errno=" + claimed.Errno);
            result.Claimed = true;
            result.Released = false;
            controller = new(ops, clock, result, fd, operationDeadline);

            result.Stage = "callbacks";
            byte[] callbacks = controller.Read("callbacks", CallbackReadHeader, CallbackLength);
            result.CallbackBase64 = B64(callbacks);
            result.CallbackSha256 = Sha(callbacks);
            ValidateCallbacks(callbacks);
            controller.Mark("callbacks-validated");

            result.Stage = "baseline-ring";
            byte[] baseline = controller.Read("baseline-ring", RingReadHeader, RingLength);
            result.BaselineRingBase64 = B64(baseline);
            result.BaselineRingSha256 = Sha(baseline);
            ValidateRing(baseline, result);
            controller.Mark("baseline-validated");

            result.Stage = "fresh-prearm-rt";
            byte[] preRt = controller.Read("prearm-rt", RtReadHeader, RtLength);
            result.PreArmRtBase64 = B64(preRt);
            result.PreArmGate = Gate(preRt);
            Need(result.PreArmGate == 0, "fresh complete gate halfword is not zero");
            controller.Mark("prearm-zero-validated");
            controller.NeedArmBudget();

            result.Stage = "arm";
            result.ArmAttempted = true;
            result.RestoreUnverified = true;
            result.LogFlagMayRemainChanged = true;
            controller.Write("arm", ArmPayload);
            result.ArmTransportComplete = true;
            controller.StartArmDeadline();

            result.Stage = "armed-readback";
            if (!controller.CanVerifyArmAndRestore())
                throw new InvalidOperationException("insufficient arm-deadline reserve for readback and restore");
            byte[] armedRt = controller.Read("armed-rt", RtReadHeader, RtLength,
                                             controller.ArmDeadline);
            result.ArmedRtBase64 = B64(armedRt);
            result.ArmedGate = Gate(armedRt);
            result.ArmVerified = result.ArmedGate == 1;
            if (!result.ArmVerified)
                throw new InvalidOperationException("armed readback was not exact halfword one");
            controller.Mark("arm-verified");

            result.Stage = "observe";
            if (!controller.CanHoldAndRestore())
                throw new InvalidOperationException("insufficient arm-deadline reserve for fixed hold and restore");
            controller.Observe();
            result.ObservationCompleted = true;
        }
        catch (Exception e)
        {
            failure = true;
            result.Errors.Add(result.Stage + ": " + e.GetType().Name + ": " + e.Message);
        }
        mutationMayHaveStarted = result.Steps.Exists(step => step.Name == "arm-header");

        // Restoration is deliberately structured, not a blind finally packet.
        // It is mandatory only after mutation may have started and the exact
        // protocol boundary is positively known to be header-ready.
        if (mutationMayHaveStarted && controller != null && controller.Ready)
        {
            try
            {
                result.Stage = "restore";
                result.RestoreAttempted = true;
                bool insideDeadline;
                try { insideDeadline = controller.RestoreInsideLogicalDeadlines(); }
                catch (Exception e)
                {
                    insideDeadline = false;
                    result.Errors.Add("restore-deadline: " + e.GetType().Name + ": " + e.Message);
                }
                if (!insideDeadline)
                {
                    failure = true;
                    result.DeadlineViolation = true;
                    result.Errors.Add("restore priority overrode logical deadline at known ready boundary");
                }
                controller.WriteUrgentRestore();
                result.RestoreTransportComplete = true;
                if (!controller.CanReadInsideWholeDeadline())
                    throw new InvalidOperationException("whole-operation budget exhausted after urgent restore");
                result.Stage = "restore-readback";
                byte[] restoredRt = controller.Read("restored-rt", RtReadHeader, RtLength);
                result.RestoredRtBase64 = B64(restoredRt);
                result.RestoredGate = Gate(restoredRt);
                Need(result.RestoredGate == 0, "restored readback was not exact halfword zero");
                result.RestoreVerified = true;
                result.RestoreUnverified = false;
                result.LogFlagMayRemainChanged = false;
                controller.Mark("restore-verified");

                result.Stage = "post-ring";
                if (!controller.CanReadInsideWholeDeadline())
                    throw new InvalidOperationException("whole-operation budget exhausted before post ring");
                byte[] post = controller.Read("post-ring", RingReadHeader, RingLength);
                result.PostRingBase64 = B64(post);
                result.PostRingSha256 = Sha(post);
                controller.Mark("post-ring-collected");
            }
            catch (Exception e)
            {
                failure = true;
                result.Errors.Add(result.Stage + ": " + e.GetType().Name + ": " + e.Message);
            }
        }
        else if (mutationMayHaveStarted)
        {
            failure = true;
            result.RestoreUnverified = true;
            result.LogFlagMayRemainChanged = true;
            result.Errors.Add("restore forbidden: protocol phase is not positively header-ready");
        }

        try
        {
            if (result.Claimed)
            {
                NativeResult released = ops.Release(fd);
                result.Released = released.Value == 0;
                if (!result.Released) result.Errors.Add("release failed errno=" + released.Errno);
            }
        }
        catch (Exception e) { result.Released = false; result.Errors.Add("release: " + e.GetType().Name); }
        try
        {
            if (fd >= 0)
            {
                NativeResult closed = ops.Close(fd);
                result.Closed = closed.Value == 0;
                if (!result.Closed) result.Errors.Add("close failed errno=" + closed.Errno);
            }
        }
        catch (Exception e) { result.Closed = false; result.Errors.Add("close: " + e.GetType().Name); }

        result.ProtocolPhase = controller == null ? result.ProtocolPhase : controller.Ready ? "ReadyForHeader" : result.ProtocolPhase;
        result.Accepted = !failure && result.ArmVerified && result.ObservationCompleted &&
            result.RestoreVerified && result.PostRingBase64 != null &&
            result.Released && result.Closed && result.ProtocolPhase == "ReadyForHeader";
        result.Stage = result.Accepted ? "complete" : "rejected";
        return result;
    }

    // sysfs binary attributes can advertise a length larger than their content.
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
        readonly Stopwatch stopwatch = Stopwatch.StartNew();
        public long NowMs => stopwatch.ElapsedMilliseconds;
        public void Hold(int milliseconds)
        {
            Need(milliseconds >= 1 && milliseconds <= 50, "native hold slice range");
            Thread.Sleep(milliseconds);
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
            bool allowed = input ? data.Length == CallbackLength || data.Length == RtLength || data.Length == RingLength
                : data.AsSpan().SequenceEqual(CallbackReadHeader) || data.AsSpan().SequenceEqual(RingReadHeader) ||
                  data.AsSpan().SequenceEqual(RtReadHeader) || data.AsSpan().SequenceEqual(GateWriteHeader) ||
                  data.AsSpan().SequenceEqual(ArmPayload) || data.AsSpan().SequenceEqual(RestorePayload);
            Need(allowed, "fixed transfers only");
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
        public bool ThrowOnHold;
        public bool ThrowNextNow;
        public int NowAdvanceMs;
        public int HoldExtraMs;
        public long NowMs
        {
            get
            {
                if (ThrowNextNow) { ThrowNextNow = false; throw new IOException("clock injected"); }
                long current = Value;
                Value += NowAdvanceMs;
                return current;
            }
        }
        public void Hold(int milliseconds)
        {
            if (ThrowOnHold) { ThrowOnHold = false; throw new IOException("hold injected"); }
            Need(milliseconds >= 1 && milliseconds <= 50, "fake hold slice range");
            Value += milliseconds + HoldExtraMs;
        }
    }
    sealed class Plan
    {
        public int Count;
        public byte[]? Fill;
        public bool Throw;
        public bool ThrowClockAfter;
        public int AdvanceMs;
        public Plan(int count, byte[]? fill = null) { Count = count; Fill = fill; }
        public Plan Clone() => new(Count, Fill == null ? null : (byte[])Fill.Clone()) { Throw = Throw, ThrowClockAfter = ThrowClockAfter, AdvanceMs = AdvanceMs };
    }
    sealed class FakeOps : IOps
    {
        readonly FakeClock clock;
        public List<Plan> Plans;
        public int BulkCalls;
        public int OpenReturn = 9, ClaimReturn, ReleaseReturn, CloseReturn;
        public bool ChangeIdentity;
        public string? ThrowAt;
        int preflights;
        public FakeOps(FakeClock clock, List<Plan>? plans = null)
        {
            this.clock = clock;
            Plans = plans ?? SuccessPlans();
        }
        void Maybe(string name) { if (ThrowAt == name) throw new IOException("injected " + name); }
        public Identity Preflight() { Maybe("preflight"); preflights++; return new(7, ChangeIdentity && preflights == 2 ? 46 : 45); }
        public NativeResult Open(Identity id) { Maybe("open"); return new(OpenReturn, OpenReturn < 0 ? 5 : 0); }
        public void ValidateFd(int fd, Identity id) { Maybe("fd-validation"); }
        public NativeResult Claim(int fd) { Maybe("claim"); return new(ClaimReturn, ClaimReturn < 0 ? 16 : 0); }
        public NativeResult Bulk(int fd, bool input, byte[] data)
        {
            Need(BulkCalls < Plans.Count, "unexpected later bulk traffic");
            Plan plan = Plans[BulkCalls++];
            clock.Value += plan.AdvanceMs;
            if (plan.Throw) throw new IOException("bulk injected");
            if (input && plan.Fill != null)
            {
                Need(plan.Fill.Length == data.Length, "fake fill extent");
                plan.Fill.CopyTo(data, 0);
            }
            if (plan.ThrowClockAfter) clock.ThrowNextNow = true;
            return new(plan.Count, plan.Count < 0 ? 5 : 0);
        }
        public NativeResult Release(int fd) { Maybe("release"); return new(ReleaseReturn, ReleaseReturn < 0 ? 5 : 0); }
        public NativeResult Close(int fd) { Maybe("close"); return new(CloseReturn, CloseReturn < 0 ? 5 : 0); }
    }

    static byte[] CallbackFixture(bool valid = true)
    {
        byte[] data = new byte[CallbackLength];
        for (int i = 0; i < PackagedCallbacks.Length; i++)
            BitConverter.GetBytes(PackagedCallbacks[i]).CopyTo(data, 12 + i * 4);
        if (!valid) data[12] ^= 1;
        return data;
    }
    static byte[] RingFixture(uint write = 0, uint read = 0, uint flag = 0)
    {
        byte[] data = new byte[RingLength];
        BitConverter.GetBytes(write).CopyTo(data, 0);
        BitConverter.GetBytes(read).CopyTo(data, 4);
        BitConverter.GetBytes(flag).CopyTo(data, 8);
        return data;
    }
    static byte[] RtFixture(ushort gate)
    {
        byte[] data = new byte[RtLength];
        BitConverter.GetBytes(gate).CopyTo(data, 6);
        return data;
    }
    static List<Plan> SuccessPlans()
    {
        return new()
        {
            new(12), new(64, CallbackFixture()),
            new(12), new(RingLength, RingFixture()),
            new(12), new(64, RtFixture(0)),
            new(12), new(2),
            new(12), new(64, RtFixture(1)),
            new(12), new(2),
            new(12), new(64, RtFixture(0)),
            new(12), new(RingLength, RingFixture(4, 4, 0))
        };
    }
    static List<Plan> ClonePlans()
    {
        List<Plan> result = new();
        foreach (Plan plan in SuccessPlans()) result.Add(plan.Clone());
        return result;
    }
    static Outcome FakeRun(FakeOps ops, FakeClock clock) => Run(ops, clock);

    static int SelfTest()
    {
        int baseline = 0, state = 0;
        int successOutputBytes = 0;
        void BaselineCase(string name, FakeOps ops, FakeClock clock, bool accepted, int? bulkCalls = null)
        {
            Outcome r = FakeRun(ops, clock);
            Need(r.Accepted == accepted, name + " acceptance");
            if (bulkCalls.HasValue) Need(ops.BulkCalls == bulkCalls.Value, name + " bulk count");
            baseline++;
        }
        {
            FakeClock c = new(); FakeOps o = new(c); BaselineCase("success", o, c, true, 16);
        }
        {
            FakeClock c = new(); FakeOps o = new(c) { OpenReturn = -1 }; BaselineCase("open-failure", o, c, false, 0);
        }
        {
            FakeClock c = new(); FakeOps o = new(c) { ClaimReturn = -1 }; BaselineCase("claim-failure", o, c, false, 0);
        }
        foreach (int n in new[] { -1, 0, 11, 13 })
        {
            FakeClock c = new(); List<Plan> p = ClonePlans(); p[0].Count = n;
            BaselineCase("first-out-" + n, new(c, p), c, false, 1);
        }
        foreach (int n in new[] { -1, 0, 63, 65 })
        {
            FakeClock c = new(); List<Plan> p = ClonePlans(); p[1].Count = n;
            BaselineCase("first-in-" + n, new(c, p), c, false, 2);
        }
        {
            FakeClock c = new(); FakeOps o = new(c) { ChangeIdentity = true };
            BaselineCase("identity-change", o, c, false, 0);
        }
        foreach (string phaseName in new[] { "preflight", "open", "fd-validation", "claim", "release", "close" })
        {
            FakeClock c = new(); FakeOps o = new(c) { ThrowAt = phaseName };
            BaselineCase("exception-" + phaseName, o, c, false,
                         phaseName == "release" || phaseName == "close" ? 16 : 0);
        }
        for (int index = 0; index < 2; index++)
        {
            FakeClock c = new(); List<Plan> p = ClonePlans(); p[index].Throw = true;
            BaselineCase("exception-first-bulk-" + index, new(c, p), c, false, index + 1);
        }
        {
            FakeClock c = new(); FakeOps o = new(c) { ReleaseReturn = -1 };
            BaselineCase("release-error", o, c, false, 16);
        }
        {
            FakeClock c = new(); FakeOps o = new(c) { CloseReturn = -1 };
            BaselineCase("close-error", o, c, false, 16);
        }
        foreach (int length in new[] { 0, 115, 116 })
        {
            byte[] input = new byte[length];
            for (int i = 0; i < length; i++) input[i] = (byte)i;
            using PartialNonseekableStream stream = new(input);
            Need(ReadCachedDescriptors(stream).AsSpan().SequenceEqual(input), "descriptor stream " + length);
            baseline++;
        }
        bool oversized = false;
        try { using PartialNonseekableStream stream = new(new byte[117]); ReadCachedDescriptors(stream); }
        catch (InvalidOperationException e) when (e.Message == "cached descriptors exceed 116 bytes") { oversized = true; }
        Need(oversized, "oversized descriptor rejection"); baseline++;
        Need(baseline == 26, "retained baseline test count");

        void StateCase(string name, Action<List<Plan>, FakeClock, FakeOps> change,
                       Func<Outcome, bool> check, int expectedBulks)
        {
            FakeClock c = new(); List<Plan> p = ClonePlans(); FakeOps o = new(c, p);
            change(p, c, o);
            Outcome r = FakeRun(o, c);
            Need(check(r), name + " outcome");
            Need(o.BulkCalls == expectedBulks, name + " no later bulk traffic");
            state++;
        }
        StateCase("callback-mismatch", (p, c, o) => p[1].Fill = CallbackFixture(false),
                  r => !r.ArmAttempted && r.ProtocolPhase == "ReadyForHeader", 2);
        StateCase("bad-cursors", (p, c, o) => p[3].Fill = RingFixture(0x3c01, 0, 0),
                  r => !r.ArmAttempted && r.ProtocolPhase == "ReadyForHeader", 4);
        StateCase("precondition-gate-one", (p, c, o) => p[5].Fill = RtFixture(1),
                  r => !r.ArmAttempted && r.PreArmGate == 1, 6);

        for (int index = 0; index < 16; index++)
        {
            int capture = index;
            StateCase("short-" + index, (p, c, o) => p[capture].Count = Math.Max(0, p[capture].Count - 1),
                      r => !r.Accepted && r.ProtocolPhase == "Unknown", index + 1);
        }
        for (int index = 0; index < 16; index++)
        {
            int capture = index;
            StateCase("error-" + index, (p, c, o) => p[capture].Throw = true,
                      r => !r.Accepted && r.ProtocolPhase == "Unknown", index + 1);
        }
        StateCase("armed-read-logic-failure", (p, c, o) => p[9].Fill = RtFixture(2),
                  r => !r.ArmVerified && r.RestoreVerified && !r.ObservationCompleted && r.PostRingBase64 != null, 16);
        StateCase("hold-exception-restores", (p, c, o) => c.ThrowOnHold = true,
                  r => r.ArmVerified && !r.ObservationCompleted && r.RestoreVerified && r.PostRingBase64 != null, 16);
        StateCase("clock-advances-between-samples", (p, c, o) => c.NowAdvanceMs = 1,
                  r => r.Accepted && r.RestoreVerified && !r.DeadlineViolation, 16);
        StateCase("hold-oversleep-urgent-restore", (p, c, o) => c.HoldExtraMs = 8000,
                  r => !r.Accepted && r.ArmVerified && !r.ObservationCompleted &&
                       r.RestoreTransportComplete && r.RestoreVerified && r.DeadlineViolation, 16);
        StateCase("post-arm-clock-fault-urgent-restore", (p, c, o) =>
                  { p[7].ThrowClockAfter = true; p.RemoveRange(8, 2); },
                  r => !r.Accepted && r.ArmTransportComplete && !r.ArmVerified &&
                       r.RestoreTransportComplete && r.RestoreVerified && r.DeadlineViolation, 14);
        StateCase("restore-payload-partial", (p, c, o) => p[11].Count = 1,
                  r => r.RestoreAttempted && !r.RestoreTransportComplete && !r.RestoreVerified && r.ProtocolPhase == "Unknown", 12);
        StateCase("postrestore-read-failure", (p, c, o) => p[13].Throw = true,
                  r => r.RestoreTransportComplete && !r.RestoreVerified && r.PostRingBase64 == null, 14);
        StateCase("budget-before-arm", (p, c, o) => { for (int i = 0; i < 6; i++) p[i].AdvanceMs = 1100; },
                  r => !r.ArmAttempted && r.PreArmGate == 0 && r.ProtocolPhase == "ReadyForHeader", 6);
        foreach ((string name, Action<FakeOps> change) in new (string, Action<FakeOps>)[]
        {
            ("release-nonzero", o => o.ReleaseReturn = -1),
            ("close-nonzero", o => o.CloseReturn = -1),
            ("release-throws", o => o.ThrowAt = "release"),
            ("close-throws", o => o.ThrowAt = "close")
        })
            StateCase(name, (p, c, o) => change(o), r => !r.Accepted, 16);

        {
            FakeClock c = new(); FakeOps o = new(c); Outcome r = FakeRun(o, c);
            byte[] json = JsonSerializer.SerializeToUtf8Bytes(r, JsonOptions);
            Need(json.Length <= 55000, "native output size budget");
            successOutputBytes = json.Length;
            Need(r.Steps.Count == 16 && r.Steps.TrueForAll(s => s.Count.HasValue), "all bulk steps retained");
            Need(r.BaselineRingBase64 != null && Convert.FromBase64String(r.BaselineRingBase64).Length == RingLength, "baseline artifact extent");
            Need(r.PostRingBase64 != null && Convert.FromBase64String(r.PostRingBase64).Length == RingLength, "post artifact extent");
            state++;
        }
        Console.WriteLine(JsonSerializer.Serialize(new { selfTestsPassed = baseline + state,
            baselineTestsPassed = baseline, stateMachineTestsPassed = state,
            successOutputBytes,
            targetOperations = 0 }, JsonOptions));
        return 0;
    }

    static int Main(string[] args)
    {
        if (args.Length == 0)
        {
            Console.WriteLine(JsonSerializer.Serialize(new {
                dryRun = true, targetOperations = 0, variant = "arm-verified",
                fixedSequence = "callbacks64,baseline15372,preRT64,arm2,armedRT64,hold3s,restore2,restoredRT64,post15372",
                writeHeaderHex = Convert.ToHexString(GateWriteHeader),
                armPayloadHex = Convert.ToHexString(ArmPayload),
                restorePayloadHex = Convert.ToHexString(RestorePayload),
                timeoutMs = TimeoutMs, hardArmDeadlineMs = ArmDeadlineMs,
                wholeDeadlineMs = WholeDeadlineMs, interfaceNumber = 2
            }, JsonOptions));
            return 0;
        }
        if (args.Length == 1 && args[0] == "--self-test") return SelfTest();
        if (!(args.Length == 1 && args[0] == "--execute")) return 63;
        if (!RealOps.AbiReady) { Console.WriteLine("REFUSED_ARM32_ABI"); return 64; }
        Outcome outcome = Run(new RealOps(), new RealClock());
        string json = JsonSerializer.Serialize(outcome, JsonOptions);
        if (Encoding.UTF8.GetByteCount(json) > 55000)
        {
            Console.WriteLine(JsonSerializer.Serialize(new { Stage = "output-size-refused",
                Accepted = false, RestoreVerified = outcome.RestoreVerified,
                RestoreUnverified = outcome.RestoreUnverified,
                LogFlagMayRemainChanged = outcome.LogFlagMayRemainChanged,
                ProtocolPhase = outcome.ProtocolPhase }, JsonOptions));
            return 2;
        }
        Console.WriteLine(json);
        return outcome.Accepted ? 0 : 1;
    }
}
