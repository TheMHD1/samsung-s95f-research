using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;

internal static partial class Program
{
    static string Sha(byte[] b)=>Convert.ToHexString(SHA256.HashData(b)).ToLowerInvariant();
    static int ExpectedDevice;
    const int TimeoutMs = 2000;
    const int OutputLimit = 24576;
    const string ExpectedBoot = "00000000-0000-4000-8000-000000000000";
    const string UsbRoot = "/sys/bus/usb/devices/7-1";
    const string DeviceHex = "12010002ef020140e8040120500201020301";
    const string AllDescriptorsHex = DeviceHex + "090262000301048032080b00020202010a09040000010202010a052400100105240100010424020205240600010705830308001009040100020a00000a07050102400010070581024000000904020002ff0000000705820200020007050202000200";

    sealed record WindowSpec(string Name, uint Address, int Length, byte[] Header, string HeaderStep, string DataStep);
    static WindowSpec Spec(string name, uint address, int length) =>
        new(name, address, length, Header(address, length), name + "-header", name + "-data");
    static byte[] Header(uint address, int length)
    {
        byte[] value = new byte[12];
        BitConverter.GetBytes(0x101u).CopyTo(value, 0);
        BitConverter.GetBytes(address).CopyTo(value, 4);
        BitConverter.GetBytes((uint)length).CopyTo(value, 8);
        return value;
    }

    static readonly WindowSpec R = Spec("R", 0x47012400, 256);
    static readonly WindowSpec M = Spec("M", 0x470004a0, 68);
    static readonly WindowSpec C = Spec("C", 0x47000bc0, 16);
    static readonly WindowSpec[] AllSpecs = { R, M, C };
    static readonly byte[] LoggerHeader = Convert.FromHexString("020100000624014702000000");
    static WindowSpec? FindHeader(byte[] data)
    {
        foreach (WindowSpec spec in AllSpecs) if (spec.Header.AsSpan().SequenceEqual(data)) return spec;
        return null;
    }
    static bool IsInputLength(int length)
    {
        foreach (WindowSpec spec in AllSpecs) if (spec.Length == length) return true;
        return false;
    }

    readonly record struct Identity(int Bus, int Device)
    {
        public string Node => $"/dev/bus/usb/{Bus:D3}/{Device:D3}";
    }
    readonly record struct NativeResult(int Value, int Errno);
    enum ProtocolPhase { ReadyForHeader, ExpectingIn, ExpectingPayload, Unknown }
    enum PairResult { Complete, Deadline, TransportFailure, ClockFailure }
    enum RtState { Clean, Faulted, Unexpected, Quiescent }

    sealed class Config
    {
        public long DurationUs = 2_000_000;
        public int MaxCycles = 56;
        public long PeriodUs = 25_000;
    }

    struct TransferRecord
    {
        public string Name;
        public string Direction;
        public int Expected;
        public int? Count;
        public int? Errno;
        public long? BeforeUs;
        public long? AfterUs;
        public string? Error;
    }

    sealed class WindowCapture
    {
        public readonly byte[] Buffer;
        public WindowCapture(int size=256){Buffer=new byte[size];}
        public WindowSpec? Spec;
        public int Count = -1;
        public bool Used;
        public void Reset() { Spec = null; Count = -1; Used = false; Array.Clear(Buffer, 0, Buffer.Length); }
        public void CopyFrom(WindowCapture other)
        {
            Reset(); Spec = other.Spec; Count = other.Count; Used = other.Used;
            if (other.Count > 0) Array.Copy(other.Buffer, Buffer, Math.Min(other.Count, Buffer.Length));
        }
    }

    sealed class Capture
    {
        public readonly WindowCapture[] Windows = new WindowCapture[8];
        public readonly TransferRecord[] Transfers = new TransferRecord[16];
        public int TransferCount;
        public int WindowCount;
        public int CycleIndex;
        public string Role = "unused";
        public bool Present;
        public Capture(int size=256) { for (int i = 0; i < Windows.Length; i++) Windows[i] = new(size); }
        public void Begin(string role, int cycleIndex)
        {
            Present = true; Role = role; CycleIndex = cycleIndex; TransferCount = 0; WindowCount = 0;
            Array.Clear(Transfers, 0, Transfers.Length);
            foreach (WindowCapture window in Windows) window.Reset();
        }
        public void Clear()
        {
            Present = false; Role = "unused"; CycleIndex = 0; TransferCount = 0; WindowCount = 0;
            Array.Clear(Transfers, 0, Transfers.Length);
            foreach (WindowCapture window in Windows) window.Reset();
        }
        public WindowCapture AddWindow(WindowSpec spec)
        {
            Need(WindowCount < Windows.Length, "window capacity");
            WindowCapture window = Windows[WindowCount++]; window.Reset(); window.Spec = spec; window.Used = true; return window;
        }
        public void AddTransfer(TransferRecord record)
        {
            Need(TransferCount < Transfers.Length, "transfer capacity"); Transfers[TransferCount++] = record;
        }
        public void CopyFrom(Capture other, string role)
        {
            Begin(role, other.CycleIndex); TransferCount = other.TransferCount; WindowCount = other.WindowCount;
            Array.Copy(other.Transfers, Transfers, other.TransferCount);
            for (int i = 0; i < other.WindowCount; i++) Windows[i].CopyFrom(other.Windows[i]);
        }
    }

    sealed class Buffers
    {
        // All raw response and transfer-retention capacity is allocated before USB preflight/open.
        public readonly Capture Current = new();
        public readonly Capture LastClean = new();
        public readonly Capture Transition = new();
        public readonly Capture PostFault = new();
        public readonly Capture Initial = new();
        public readonly Capture TriggerBaseline = new();
    }

    sealed class Outcome
    {
        public string Schema { get; set; } = "logger-gate-reconciliation-fm-v1";
        public int Device{get;set;}
        public bool BindingQualified{get;set;}
        public List<BindingCheck>? BindingChecks{get;set;}
        public bool? ObservationAccepted { get; set; }
        public string Stage { get; set; } = "preflight";
        public string TerminalReason { get; set; } = "NotStarted";
        public string ProtocolPhase { get; set; } = "ReadyForHeader";
        public bool Opened { get; set; }
        public bool Claimed { get; set; }
        public bool Released { get; set; } = true;
        public bool Closed { get; set; } = true;
        public bool Accepted { get; set; }
        public bool OnsetObserved { get; set; }
        public bool OnsetMissed { get; set; }
        public bool PhysicalPictureObserved { get; set; }
        public bool BusContentsAltered { get; set; }
        public int Writes { get; set; }
        public int Retries { get; set; }
        public int CyclesStarted { get; set; }
        public int CleanCyclesCompleted { get; set; }
        public int QuiescentCyclesCompleted { get; set; }
        public int CleanCyclesDiscarded { get; set; }
        public int BulkTransfers { get; set; }
        public int HeadersSent { get; set; }
        public int InputsCompleted { get; set; }
        public long? StartUs { get; set; }
        public long? DeadlineUs { get; set; }
        public long? EndUs { get; set; }
        public long? OvershootUs { get; set; }
        public string RetentionPolicy { get; set; } = "last-completed-clean-or-quiescent+transition+one-postfault-set+current-partial";
        public string? Error { get; set; }
        public List<CaptureDto> Retained { get; set; } = new();
    }

    sealed class CaptureDto
    {
        public string Role { get; set; } = "";
        public int CycleIndex { get; set; }
        public List<WindowDto> Windows { get; set; } = new();
        public List<TransferDto> Transfers { get; set; } = new();
    }
    sealed class WindowDto
    {
        public string Name { get; set; } = "";
        public string Address { get; set; } = "";
        public int Expected { get; set; }
        public int? Count { get; set; }
        public bool Complete { get; set; }
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] public string? RawBase64 { get; set; }
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] public string? Sha256 { get; set; }
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] public RtDto? ObservedRtState { get; set; }
    }
    sealed class TransferDto
    {
        public string Name { get; set; } = "";
        public string Direction { get; set; } = "";
        public int Expected { get; set; }
        public int? Count { get; set; }
        public int? Errno { get; set; }
        public long? BeforeUs { get; set; }
        public long? AfterUs { get; set; }
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] public string? Error { get; set; }
    }
    sealed class RtDto
    {
        public int Stop { get; set; }
        public int Fault { get; set; }
        public int OrdinaryGate { get; set; }
        public string Classification { get; set; } = "";
    }

    interface IOps
    {
        IReadOnlyList<BindingCheck> BindingChecks{get;}
        void Revalidate(Identity id);
        Identity Preflight();
        NativeResult Open(Identity id);
        void ValidateFd(int fd, Identity id);
        NativeResult Claim(int fd);
        NativeResult Bulk(int fd, bool input, byte[] data, int length);
        NativeResult Release(int fd);
        NativeResult Close(int fd);
    }
    interface IClock
    {
        long NowUs();
        void SleepUs(long microseconds);
    }

    static void Need(bool ok, string message) { if (!ok) throw new InvalidOperationException(message); }
    static string ShortError(Exception e)
    {
        string value = e.GetType().Name + ": " + e.Message;
        if(value.Length>240)value=value.Substring(0,240);
        while(System.Text.Encoding.UTF8.GetByteCount(JsonSerializer.Serialize(value))>128)value=value.Substring(0,value.Length-1);
        return value;
    }
    static int Half(byte[] value, int offset) => value[offset] | value[offset + 1] << 8;
    static RtState ClassifyRt(byte[] value)
    {
        if(Half(value,0xc4)!=40)return RtState.Unexpected;
        int stop = Half(value, 0), fault = Half(value, 0x0a), gate = Half(value, 0x0e);
        if (stop == 0 && fault == 0 && gate == 1) return RtState.Clean;
        if (stop == 1 && fault == 0x1001 && gate == 0) return RtState.Faulted;
        if (stop == 0 && fault == 0 && gate == 0 && Half(value, 0xc4) == 40) return RtState.Quiescent;
        return RtState.Unexpected;
    }

    static long? Stamp(IClock clock, ref string? clockError)
    {
        try { return clock.NowUs(); }
        catch (Exception e) { clockError ??= ShortError(e); return null; }
    }

    static PairResult ReadPair(IOps ops, IClock clock, Outcome result, Capture capture,
        WindowSpec spec, int fd, ref ProtocolPhase phase, long deadlineUs, bool enforceDeadline)
    {
        string? clockError = null;
        long? beforeHeader = Stamp(clock, ref clockError);
        if (clockError != null) { result.Error = clockError; return PairResult.ClockFailure; }
        if (enforceDeadline && beforeHeader!.Value >= deadlineUs) return PairResult.Deadline;

        WindowCapture window = capture.AddWindow(spec);
        result.Stage = spec.HeaderStep;
        phase = ProtocolPhase.Unknown;
        NativeResult headerResult;
        string? headerException = null;
        try { headerResult = ops.Bulk(fd, false, spec.Header, 12); }
        catch (Exception e) { headerResult = new(-1, 0); headerException = ShortError(e); }
        result.BulkTransfers++; result.HeadersSent++;
        long? afterHeader = Stamp(clock, ref clockError);
        capture.AddTransfer(new TransferRecord { Name = spec.HeaderStep, Direction = "OUT", Expected = 12,
            Count = headerException == null ? headerResult.Value : null, Errno = headerResult.Errno,
            BeforeUs = beforeHeader, AfterUs = afterHeader, Error = headerException });
        if (headerException != null || headerResult.Value != 12)
        {
            result.Error = headerException ?? $"{spec.Name} header count={headerResult.Value} errno={headerResult.Errno}";
            return PairResult.TransportFailure;
        }
        phase = ProtocolPhase.ExpectingIn;

        // An accepted header creates a pending IN. Clock/deadline faults are recorded,
        // but cannot prevent the one exact matching IN from being attempted.
        long? beforeInput = Stamp(clock, ref clockError);
        result.Stage = spec.DataStep;
        phase = ProtocolPhase.Unknown;
        NativeResult inputResult;
        string? inputException = null;
        try { inputResult = ops.Bulk(fd, true, window.Buffer, spec.Length); }
        catch (Exception e) { inputResult = new(-1, 0); inputException = ShortError(e); }
        result.BulkTransfers++;
        long? afterInput = Stamp(clock, ref clockError);

        // Preserve the transport's actual count.  ToDto separately clamps the
        // raw prefix copied into JSON, so an overlong/negative return remains
        // visible without ever reading outside the fixed response buffer.
        window.Count = inputException == null ? inputResult.Value : -1;
        capture.AddTransfer(new TransferRecord { Name = spec.DataStep, Direction = "IN", Expected = spec.Length,
            Count = inputException == null ? inputResult.Value : null, Errno = inputResult.Errno,
            BeforeUs = beforeInput, AfterUs = afterInput, Error = inputException });
        if (inputException == null && inputResult.Value == spec.Length)
        {
            phase = ProtocolPhase.ReadyForHeader; result.InputsCompleted++;
            if (clockError != null) { result.Error = clockError; return PairResult.ClockFailure; }
            return PairResult.Complete;
        }
        result.Error = inputException ?? $"{spec.Name} data count={inputResult.Value} errno={inputResult.Errno}";
        return PairResult.TransportFailure;
    }

    static PairResult ReadSet(IOps ops, IClock clock, Outcome result, Capture capture,
        WindowSpec[] specs, int fd, ref ProtocolPhase phase, long deadlineUs)
    {
        foreach (WindowSpec spec in specs)
        {
            PairResult pair = ReadPair(ops, clock, result, capture, spec, fd, ref phase, deadlineUs, true);
            if (pair != PairResult.Complete) return pair;
        }
        return PairResult.Complete;
    }

    static CaptureDto ToDto(Capture capture)
    {
        CaptureDto dto = new() { Role = capture.Role, CycleIndex = capture.CycleIndex };
        for (int i = 0; i < capture.WindowCount; i++)
        {
            WindowCapture source = capture.Windows[i]; WindowSpec spec = source.Spec!;
            int rawCount = Math.Max(0, Math.Min(source.Count, spec.Length));
            byte[]? raw = rawCount > 0 ? source.Buffer.AsSpan(0, rawCount).ToArray() : null;
            WindowDto window = new() { Name = spec.Name, Address = $"0x{spec.Address:x8}", Expected = spec.Length,
                Count = source.Count >= 0 ? source.Count : null, Complete = source.Count == spec.Length,
                RawBase64 = raw == null ? null : Convert.ToBase64String(raw),
                Sha256 = raw == null ? null : Convert.ToHexString(SHA256.HashData(raw)).ToLowerInvariant() };
            if (spec == R && source.Count == R.Length)
                window.ObservedRtState = new() { Stop = Half(source.Buffer, 0), Fault = Half(source.Buffer, 0x0a),
                    OrdinaryGate = Half(source.Buffer, 0x0e), Classification = ClassifyRt(source.Buffer).ToString() };
            dto.Windows.Add(window);
        }
        for (int i = 0; i < capture.TransferCount; i++)
        {
            TransferRecord source = capture.Transfers[i];
            dto.Transfers.Add(new() { Name = source.Name, Direction = source.Direction, Expected = source.Expected,
                Count = source.Count, Errno = source.Errno, BeforeUs = source.BeforeUs, AfterUs = source.AfterUs, Error = source.Error });
        }
        return dto;
    }

    // sysfs binary attributes can advertise a length larger than their content.
    static byte[] ReadCachedDescriptors(Stream stream)
    {
        byte[] data = new byte[117]; int used = 0;
        while (used < data.Length)
        {
            int count = stream.Read(data, used, data.Length - used);
            if (count == 0) return data.AsSpan(0, used).ToArray();
            Need(count > 0 && count <= data.Length - used, "descriptor stream count"); used += count;
        }
        throw new InvalidOperationException("cached descriptors exceed 116 bytes");
    }
    static byte[] ReadCachedDescriptors(string path) { using FileStream stream = File.OpenRead(path); return ReadCachedDescriptors(stream); }

    sealed class FakeClock : IClock
    {
        public long Value;
        public int Calls;
        public int ThrowAtCall = -1;public int JumpAtCall=-1;public long JumpUs;
        public long NowUs() { int call = Calls++; if (call == ThrowAtCall) throw new IOException("clock injected");if(call==JumpAtCall)Value+=JumpUs; return Value; }
        public void SleepUs(long microseconds) { if (microseconds < 0) throw new InvalidOperationException(); Value += microseconds; }
    }

}
