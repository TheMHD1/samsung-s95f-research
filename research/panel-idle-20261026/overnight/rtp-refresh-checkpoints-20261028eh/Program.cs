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
    static readonly WindowSpec H = Spec("H", 0x4700d0e0, 96);
    static readonly WindowSpec L = Spec("L", 0x47010f00, 64);
    static readonly WindowSpec P = Spec("P", 0x47000490, 16);
    static readonly WindowSpec N = Spec("N", 0x4700ba28, 36);
    static readonly WindowSpec[] CycleSpecs = { R, M, C, P, N, H, L, R };
    static readonly WindowSpec[] RestSpecs = { M, C, P, N, H, L, R };
    static readonly WindowSpec[] PostSpecs = { M, C, P, N, H, L, R };
    static readonly WindowSpec[] AllSpecs = { R, M, C, P, N, H, L };
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
    enum ProtocolPhase { ReadyForHeader, ExpectingIn, Unknown }
    enum PairResult { Complete, Deadline, TransportFailure, ClockFailure }
    enum RtState { Clean, Faulted, Unexpected }

    sealed class Config
    {
        public long DurationUs = 15_000_000;
        public int MaxCycles = 60;
        public long PeriodUs = 250_000;
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
        public readonly byte[] Buffer = new byte[256];
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
        public Capture() { for (int i = 0; i < Windows.Length; i++) Windows[i] = new(); }
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
        public string Schema { get; set; } = "managed-usb-rt-synchronized-key-eh-v1";
        public ScoreCheckpointBuffer ScoreCheckpoints { get; } = new();
        public int Device{get;set;}
        public bool BindingQualified{get;set;}
        public List<BindingCheck>? BindingChecks{get;set;}
        public InterventionState? Intervention { get; set; }
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
        public int CleanCyclesDiscarded { get; set; }
        public int BulkTransfers { get; set; }
        public int HeadersSent { get; set; }
        public int InputsCompleted { get; set; }
        public long? StartUs { get; set; }
        public long? DeadlineUs { get; set; }
        public long? EndUs { get; set; }
        public long? OvershootUs { get; set; }
        public string RetentionPolicy { get; set; } = "last-fully-clean+transition+one-postfault-set+current-partial; older-clean-discarded";
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
        int stop = Half(value, 0), fault = Half(value, 0x0a), gate = Half(value, 0x0e);
        if (stop == 0 && fault == 0 && gate == 1) return RtState.Clean;
        if (stop == 1 && fault == 0x1001 && gate == 0) return RtState.Faulted;
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

    static Outcome Run(IOps ops, IClock clock, Config config, IIntervention? intervention = null)
    {
        Buffers buffers = new(); // must precede any IOps call
        Outcome result = new();
        ProtocolPhase phase = ProtocolPhase.ReadyForHeader;
        int fd = -1;
        bool terminalSuccess = false;
        try
        {
            Identity id = ops.Preflight();result.Device=id.Device;
            result.Stage = "open";
            NativeResult opened = ops.Open(id); Need(opened.Value >= 0, "open failed errno=" + opened.Errno);
            fd = opened.Value; result.Opened = true; result.Closed = false;
            result.Stage = "fd-validation"; ops.ValidateFd(fd, id);
            result.Stage = "identity-recheck"; ops.Revalidate(id);
            result.Stage = "claim";
            NativeResult claim = ops.Claim(fd); Need(claim.Value == 0, "claim failed errno=" + claim.Errno);
            result.Claimed = true; result.Released = false;ops.Revalidate(id);result.BindingQualified=true;

            string? startError = null;
            long? start = Stamp(clock, ref startError); Need(startError == null && start.HasValue, "clock start " + startError);
            result.StartUs = start; result.DeadlineUs = checked(start!.Value + config.DurationUs);

            bool stop = false;
            while (!stop)
            {
                string? nowError = null; long? now = Stamp(clock, ref nowError);
                if (nowError != null) { result.Error = nowError; result.TerminalReason = "ClockFailure"; break; }
                if (now!.Value >= result.DeadlineUs.Value) { result.TerminalReason = "TimeLimit"; terminalSuccess = true; break; }
                if (result.CyclesStarted >= config.MaxCycles) { result.TerminalReason = "CycleLimit"; terminalSuccess = true; break; }

                int cycleIndex = ++result.CyclesStarted;
                long cycleStart = now.Value;
                buffers.Current.Begin("current-partial", cycleIndex);
                PairResult startPair = ReadPair(ops, clock, result, buffers.Current, R, fd, ref phase, result.DeadlineUs.Value, true);
                if (startPair != PairResult.Complete)
                {
                    result.TerminalReason = startPair == PairResult.Deadline ? "TimeLimit" : startPair.ToString();
                    terminalSuccess = startPair == PairResult.Deadline; break;
                }
                RtState startState = ClassifyRt(buffers.Current.Windows[0].Buffer);
                if (startState == RtState.Faulted)
                {
                    if (cycleIndex == 1)
                    {
                        result.OnsetMissed = true; buffers.Initial.CopyFrom(buffers.Current, "initial-faulted");
                    }
                    else { result.OnsetObserved = true; buffers.Transition.CopyFrom(buffers.Current, "transition"); }
                    buffers.Current.Clear(); buffers.PostFault.Begin("post-fault", cycleIndex);
                    PairResult post = ReadSet(ops, clock, result, buffers.PostFault, PostSpecs, fd, ref phase, result.DeadlineUs.Value);
                    if (post != PairResult.Complete)
                    {
                        result.TerminalReason = post == PairResult.Deadline ? "PostFaultDeadline" : post.ToString(); break;
                    }
                    RtState final = ClassifyRt(buffers.PostFault.Windows[6].Buffer);
                    if (final != RtState.Faulted) { result.TerminalReason = "PostFaultRtChanged"; break; }
                    result.TerminalReason = cycleIndex == 1 ? "AlreadyFaulted" : "TransitionCaptured";
                    terminalSuccess = true; stop = true; continue;
                }
                if (startState != RtState.Clean) { result.TerminalReason = cycleIndex == 1 ? "UnexpectedInitialRt" : "UnexpectedRt"; break; }

                PairResult rest = ReadSet(ops, clock, result, buffers.Current, RestSpecs, fd, ref phase, result.DeadlineUs.Value);
                if (rest != PairResult.Complete)
                {
                    result.TerminalReason = rest == PairResult.Deadline ? "TimeLimit" : rest.ToString();
                    terminalSuccess = rest == PairResult.Deadline; break;
                }
                result.ScoreCheckpoints.Add(buffers.Current, result.StartUs!.Value);
                RtState endState = ClassifyRt(buffers.Current.Windows[7].Buffer);
                if (endState == RtState.Faulted)
                {
                    result.OnsetObserved = true; buffers.Transition.CopyFrom(buffers.Current, "transition"); buffers.Current.Clear();
                    buffers.PostFault.Begin("post-fault", cycleIndex);
                    PairResult post = ReadSet(ops, clock, result, buffers.PostFault, PostSpecs, fd, ref phase, result.DeadlineUs.Value);
                    if (post != PairResult.Complete)
                    {
                        result.TerminalReason = post == PairResult.Deadline ? "PostFaultDeadline" : post.ToString(); break;
                    }
                    if (ClassifyRt(buffers.PostFault.Windows[6].Buffer) != RtState.Faulted)
                    { result.TerminalReason = "PostFaultRtChanged"; break; }
                    result.TerminalReason = "TransitionCaptured"; terminalSuccess = true; stop = true; continue;
                }
                if (endState != RtState.Clean) { result.TerminalReason = "UnexpectedRt"; break; }

                result.CleanCyclesCompleted++;
                if (buffers.LastClean.Present) result.CleanCyclesDiscarded++;
                buffers.LastClean.CopyFrom(buffers.Current, "last-clean"); buffers.Current.Clear();
                if (intervention != null && result.CleanCyclesCompleted == 1)
                {
                    Need(phase == ProtocolPhase.ReadyForHeader, "key trigger phase");
                    buffers.TriggerBaseline.CopyFrom(buffers.LastClean, "trigger-baseline");
                    result.Intervention = intervention.State;
                    intervention.Start(clock);
                }

                string? afterError = null; long? after = Stamp(clock, ref afterError);
                if (afterError != null) { result.Error = afterError; result.TerminalReason = "ClockFailure"; break; }
                long sleep = cycleStart + config.PeriodUs - after!.Value;
                if (sleep > 0)
                {
                    long untilDeadline = result.DeadlineUs.Value - after.Value;
                    if (untilDeadline <= 0) continue;
                    try { clock.SleepUs(Math.Min(sleep, untilDeadline)); }
                    catch (Exception e) { result.Error = ShortError(e); result.TerminalReason = "ClockFailure"; break; }
                }
            }
            result.Stage = "terminal";
        }
        catch (Exception e)
        {
            if (phase != ProtocolPhase.ReadyForHeader) phase = ProtocolPhase.Unknown;
            result.Error = ShortError(e); result.TerminalReason = "Exception";
        }
        finally
        {
            if (result.Claimed)
            {
                try { NativeResult release = ops.Release(fd); result.Released = release.Value == 0; if (!result.Released) result.Error ??= "release errno=" + release.Errno; }
                catch (Exception e) { result.Released = false; result.Error ??= ShortError(e); }
            }
            if (fd >= 0)
            {
                try { NativeResult close = ops.Close(fd); result.Closed = close.Value == 0; if (!result.Closed) result.Error ??= "close errno=" + close.Errno; }
                catch (Exception e) { result.Closed = false; result.Error ??= ShortError(e); }
            }
        }
        if (intervention != null)
        {
            result.Intervention = intervention.State;
            try { intervention.Finish(); }
            catch (Exception e) { result.Error ??= "key cleanup: " + ShortError(e); }
        }
        string? endError = null; result.EndUs = Stamp(clock, ref endError); result.Error ??= endError;
        if (result.DeadlineUs.HasValue && result.EndUs.HasValue) result.OvershootUs = Math.Max(0, result.EndUs.Value - result.DeadlineUs.Value);
        if(!result.BindingQualified&&result.HeadersSent==0)result.BindingChecks=new List<BindingCheck>(ops.BindingChecks);
        result.ProtocolPhase = phase.ToString();
        result.Accepted = terminalSuccess && phase == ProtocolPhase.ReadyForHeader && result.Released && result.Closed && result.Error == null;
        foreach (Capture capture in new[] { buffers.TriggerBaseline, buffers.LastClean, buffers.Initial, buffers.Transition, buffers.PostFault, buffers.Current })
            if (capture.Present) result.Retained.Add(ToDto(capture));
        return result;
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
        public int ThrowAtCall = -1;
        public long NowUs() { int call = Calls++; if (call == ThrowAtCall) throw new IOException("clock injected"); return Value; }
        public void SleepUs(long microseconds) { if (microseconds < 0) throw new InvalidOperationException(); Value += microseconds; }
    }

    sealed class FakeOps : IOps
    {
        readonly List<BindingCheck> bindingChecks=new();public IReadOnlyList<BindingCheck> BindingChecks=>bindingChecks;bool ownClaim;
        public readonly List<string> Calls = new();
        public readonly List<RtState> RtStates = new();
        public FakeClock? Clock;
        public long AdvanceUs = 100;
        public int FailBulkAt = -1;
        public bool ThrowBulk;public string BulkError="bulk injected";
        public int FailDelta = -1;
        public int OpenReturn = 9, ClaimReturn, ReleaseReturn, CloseReturn;
        public string? ThrowAt;
        public bool ChangeIdentity, FailPostBinding;
        public Action<int, bool>? OnBulk;
        int preflights, bulkIndex, rtIndex;
        WindowSpec? pending;
        void Hit(string value) { Calls.Add(value); if (ThrowAt == value) throw new IOException("injected " + value); }
        public Identity Preflight() { Hit("preflight");var b=ModelBinding(false,false,null);bindingChecks.Add(b);GuardNativeBinding(b); return new(7, ChangeIdentity && ++preflights == 2 ? 46 : 45); }
        public void Revalidate(Identity id){Hit("identity-recheck");Need(id==new Identity(7,ChangeIdentity&&++preflights==2?46:45),"USB identity changed");var b=ModelBinding(ownClaim,true,ownClaim?(FailPostBinding?"/sys/bus/usb/drivers/other":UsbfsDriver):null);bindingChecks.Add(b);GuardNativeBinding(b);}
        public NativeResult Open(Identity id) { Hit("open"); return new(OpenReturn, OpenReturn < 0 ? 5 : 0); }
        public void ValidateFd(int fd, Identity id) { Hit("fd-validation"); }
        public NativeResult Claim(int fd) { Hit("claim");if(ClaimReturn==0)ownClaim=true; return new(ClaimReturn, ClaimReturn < 0 ? 16 : 0); }
        public NativeResult Release(int fd) { Hit("release"); return new(ReleaseReturn, ReleaseReturn < 0 ? 5 : 0); }
        public NativeResult Close(int fd) { Hit("close"); return new(CloseReturn, CloseReturn < 0 ? 5 : 0); }
        public NativeResult Bulk(int fd, bool input, byte[] data, int length)
        {
            int index = bulkIndex++; OnBulk?.Invoke(index, input); Clock!.Value += AdvanceUs;
            string call = input ? "in" : "out"; Calls.Add(call + index);
            if (index == FailBulkAt && ThrowBulk) throw new IOException(BulkError);
            if (!input)
            {
                Need(length == 12, "fake header length"); pending = FindHeader(data); Need(pending != null, "fake header");
                int count = index == FailBulkAt ? 12 + FailDelta : 12; return new(count, count < 0 ? 5 : 0);
            }
            WindowSpec current = pending ?? throw new InvalidOperationException("fake no pending input");
            Need(data.Length == 256 && length == current.Length, "fake pending input");
            for (int i = 0; i < length; i++) data[i] = (byte)((current.Address + (uint)i) & 0xff);
            if (current == R)
            {
                RtState state = rtIndex < RtStates.Count ? RtStates[rtIndex++] : RtState.Clean;
                SetHalf(data, 0, state == RtState.Faulted ? 1 : state == RtState.Clean ? 0 : 2);
                SetHalf(data, 0x0a, state == RtState.Faulted ? 0x1001 : state == RtState.Clean ? 0 : 0x2222);
                SetHalf(data, 0x0e, state == RtState.Clean ? 1 : 0);
            }
            int expected = length;
            int returned = index == FailBulkAt ? expected + FailDelta : expected;
            pending = null; return new(returned, returned < 0 ? 5 : 0);
        }
        static void SetHalf(byte[] data, int offset, int value) { data[offset] = (byte)value; data[offset + 1] = (byte)(value >> 8); }
    }

    sealed class PartialNonseekableStream : Stream
    {
        readonly byte[] data; int position;
        public PartialNonseekableStream(byte[] data) { this.data = data; }
        public override bool CanRead => true; public override bool CanSeek => false; public override bool CanWrite => false;
        public override long Length => throw new InvalidOperationException("Length must not be used");
        public override long Position { get => throw new NotSupportedException(); set => throw new NotSupportedException(); }
        public override int Read(byte[] buffer, int offset, int count) { int available = Math.Min(Math.Min(count, 7), data.Length - position); Array.Copy(data, position, buffer, offset, available); position += available; return available; }
        public override void Flush() => throw new NotSupportedException(); public override long Seek(long offset, SeekOrigin origin) => throw new NotSupportedException();
        public override void SetLength(long value) => throw new NotSupportedException(); public override void Write(byte[] buffer, int offset, int count) => throw new NotSupportedException();
    }

    static Outcome FakeRun(FakeOps ops, FakeClock clock, Config config)
    { ops.Clock = clock; return Run(ops, clock, config); }
    static string Serialize(Outcome outcome) => JsonSerializer.Serialize(outcome, new JsonSerializerOptions { Encoder=System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping, PropertyNamingPolicy = JsonNamingPolicy.CamelCase, DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull });

    static int SelfTest()
    {
        int tests = 0;
        void CheckCleanup(string name, FakeOps ops, Outcome outcome)
        {
            if (outcome.Opened) Need(ops.Calls.Contains("close"), name + " close");
            if (outcome.Claimed) Need(ops.Calls.Contains("release"), name + " release");
        }
        Outcome RunCase(FakeOps ops, Config config, FakeClock? clock = null)
        { FakeClock use = clock ?? new(); Outcome value = FakeRun(ops, use, config); CheckCleanup("case", ops, value); tests++; return value; }

        Config one = new() { DurationUs = 10_000_000, MaxCycles = 1, PeriodUs = 250_000 };
        Outcome clean = RunCase(new(), one);
        Need(clean.Accepted && clean.TerminalReason == "CycleLimit" && clean.CleanCyclesCompleted == 1 && clean.Retained.Count == 1, "clean cycle cap");

        FakeOps rollingOps = new(); Outcome rolling = RunCase(rollingOps, new() { DurationUs = 10_000_000, MaxCycles = 3, PeriodUs = 10 });
        Need(rolling.Accepted && rolling.CleanCyclesCompleted == 3 && rolling.CleanCyclesDiscarded == 2 && rolling.Retained.Count == 1 && rolling.Retained[0].CycleIndex == 3, "rolling retention");

        FakeOps within = new(); within.RtStates.AddRange(new[] { RtState.Clean, RtState.Faulted, RtState.Faulted });
        Outcome withinResult = RunCase(within, new() { DurationUs = 10_000_000, MaxCycles = 5, PeriodUs = 10 });
        Need(withinResult.Accepted && withinResult.TerminalReason == "TransitionCaptured" && withinResult.OnsetObserved && withinResult.Retained.Count == 2, "within transition");
        Need(withinResult.Retained[0].Role == "transition" && withinResult.Retained[0].Windows.Count == 8 && withinResult.Retained[1].Windows.Count == 7, "within retained sets");

        FakeOps between = new(); between.RtStates.AddRange(new[] { RtState.Clean, RtState.Clean, RtState.Faulted, RtState.Faulted });
        Outcome betweenResult = RunCase(between, new() { DurationUs = 10_000_000, MaxCycles = 5, PeriodUs = 10 });
        Need(betweenResult.Accepted && betweenResult.Retained.Count == 3 && betweenResult.Retained[0].Role == "last-clean" && betweenResult.Retained[1].Windows.Count == 1, "between transition");

        // This is the largest legal retained success: a prior full clean cycle,
        // a later full cycle that transitions at R-end, and one full post set.
        FakeOps maximum = new(); maximum.RtStates.AddRange(new[] { RtState.Clean, RtState.Clean, RtState.Clean, RtState.Faulted, RtState.Faulted });
        Outcome maximumResult = RunCase(maximum, new() { DurationUs = 10_000_000, MaxCycles = 5, PeriodUs = 10 });
        Need(maximumResult.Accepted && maximumResult.Retained.Count == 3 && maximumResult.Retained[0].Windows.Count == 8 &&
            maximumResult.Retained[1].Windows.Count == 8 && maximumResult.Retained[2].Windows.Count == 7, "maximum retained success");

        FakeOps already = new(); already.RtStates.AddRange(new[] { RtState.Faulted, RtState.Faulted });
        Outcome alreadyResult = RunCase(already, one);
        Need(alreadyResult.Accepted && alreadyResult.OnsetMissed && !alreadyResult.OnsetObserved && alreadyResult.TerminalReason == "AlreadyFaulted" && alreadyResult.Retained.Count == 2, "already faulted");

        FakeOps unexpected = new(); unexpected.RtStates.Add(RtState.Unexpected);
        Outcome unexpectedResult = RunCase(unexpected, one);
        Need(!unexpectedResult.Accepted && unexpectedResult.TerminalReason == "UnexpectedInitialRt" && unexpected.BulkTransfers() == 2, "unexpected initial");

        for (int bulk = 0; bulk < 16; bulk++)
        {
            foreach (bool throws in new[] { false, true })
            {
                FakeOps failure = new() { FailBulkAt = bulk, ThrowBulk = throws, FailDelta = -1 };
                Outcome failed = RunCase(failure, one);
                Need(!failed.Accepted && failed.TerminalReason == "TransportFailure", "bulk failure " + bulk + "/" + throws);
                Need(failure.BulkTransfers() == bulk + 1, "no following traffic " + bulk + "/" + throws);
                Need(failed.Retained.Exists(x => x.Role == "current-partial"), "partial retained " + bulk);
            }
        }

        for (int bulk = 16; bulk < 30; bulk++)
        {
            foreach (bool throws in new[] { false, true })
            {
                FakeOps failure = new() { FailBulkAt = bulk, ThrowBulk = throws, FailDelta = -1 };
                failure.RtStates.AddRange(new[] { RtState.Clean, RtState.Faulted });
                Outcome failed = RunCase(failure, new() { DurationUs = 10_000_000, MaxCycles = 5, PeriodUs = 10 });
                Need(!failed.Accepted && failed.TerminalReason == "TransportFailure", "post bulk failure " + bulk + "/" + throws);
                Need(failure.BulkTransfers() == bulk + 1, "post no following traffic " + bulk + "/" + throws);
                Need(failed.Retained.Exists(x => x.Role == "transition") && failed.Retained.Exists(x => x.Role == "post-fault"), "post partial retained " + bulk);
            }
        }

        FakeOps partialRawOps = new() { FailBulkAt = 1, FailDelta = -1 };
        Outcome partialRaw = RunCase(partialRawOps, one);
        CaptureDto partialCapture = partialRaw.Retained.Find(x => x.Role == "current-partial") ?? throw new InvalidOperationException("partial capture absent");
        Need(partialCapture.Windows.Count == 1 && partialCapture.Windows[0].Count == 255 &&
            partialCapture.Windows[0].RawBase64 != null && Convert.FromBase64String(partialCapture.Windows[0].RawBase64!).Length == 255,
            "partial actual count/raw prefix retained");

        FakeClock deadlineClock = new(); FakeOps deadlineOps = new() { AdvanceUs = 70_000 };
        Outcome deadline = RunCase(deadlineOps, new() { DurationUs = 100_000, MaxCycles = 60, PeriodUs = 250_000 }, deadlineClock);
        Need(deadline.Accepted && deadline.TerminalReason == "TimeLimit" && deadline.OvershootUs <= 280_000 && deadlineOps.BulkTransfers() == 2, "deadline pending pair");

        FakeClock postDeadlineClock = new(); FakeOps postDeadlineOps = new() { AdvanceUs = 70_000 };
        postDeadlineOps.RtStates.AddRange(new[] { RtState.Clean, RtState.Faulted });
        Outcome postDeadline = RunCase(postDeadlineOps, new() { DurationUs = 1_200_000, MaxCycles = 5, PeriodUs = 10 }, postDeadlineClock);
        Need(!postDeadline.Accepted && postDeadline.TerminalReason == "PostFaultDeadline" && postDeadline.ProtocolPhase == "ReadyForHeader" &&
            postDeadline.Retained.Exists(x => x.Role == "post-fault"), "post deadline partial");

        FakeClock clockFailureClock = new() { ThrowAtCall = 3 }; FakeOps clockFailureOps = new();
        Outcome clockFailure = RunCase(clockFailureOps, one, clockFailureClock);
        Need(!clockFailure.Accepted && clockFailure.TerminalReason == "ClockFailure" && clockFailure.ProtocolPhase == "ReadyForHeader" && clockFailureOps.BulkTransfers() == 2, "clock failure completes pending IN");

        FakeOps unexpectedEnd = new(); unexpectedEnd.RtStates.AddRange(new[] { RtState.Clean, RtState.Unexpected });
        Outcome unexpectedEndResult = RunCase(unexpectedEnd, one);
        Need(!unexpectedEndResult.Accepted && unexpectedEndResult.TerminalReason == "UnexpectedRt" && unexpectedEndResult.ProtocolPhase == "ReadyForHeader", "unexpected end RT");

        FakeOps postChanged = new(); postChanged.RtStates.AddRange(new[] { RtState.Clean, RtState.Faulted, RtState.Clean });
        Outcome postChangedResult = RunCase(postChanged, new() { DurationUs = 10_000_000, MaxCycles = 5, PeriodUs = 10 });
        Need(!postChangedResult.Accepted && postChangedResult.TerminalReason == "PostFaultRtChanged", "post RT changed");

        FakeOps release = new() { ReleaseReturn = -1 }; Outcome releaseResult = RunCase(release, one);
        Need(!releaseResult.Accepted && !releaseResult.Released, "release failure");
        FakeOps close = new() { CloseReturn = -1 }; Outcome closeResult = RunCase(close, one);
        Need(!closeResult.Accepted && !closeResult.Closed, "close failure");

        foreach ((string name, FakeOps ops, string forbidden) in new[] {
            ("open", new FakeOps { OpenReturn = -1 }, "claim"),
            ("claim", new FakeOps { ClaimReturn = -1 }, "out0"),
            ("identity", new FakeOps { ChangeIdentity = true }, "claim"),
            ("preflight-ex", new FakeOps { ThrowAt = "preflight" }, "open"),
            ("fd-ex", new FakeOps { ThrowAt = "fd-validation" }, "claim") })
        {
            Outcome local = RunCase(ops, one); Need(!local.Accepted && !ops.Calls.Contains(forbidden), name + " fail closed");
        }

        Need(Convert.ToHexString(R.Header) == "010100000024014700010000", "R header");
        Need(Convert.ToHexString(M.Header) == "01010000A004004744000000", "M header");
        Need(Convert.ToHexString(C.Header) == "01010000C00B004710000000", "C header");
        Need(Convert.ToHexString(H.Header) == "01010000E0D0004760000000", "H header");
        Need(Convert.ToHexString(L.Header) == "01010000000F014740000000", "L header"); Need(Convert.ToHexString(P.Header) == "010100009004004710000000", "P header");
        Need(Convert.ToHexString(N.Header) == "0101000028BA004724000000", "N header"); tests += 7;

        foreach (int length in new[] { 0, 115, 116 })
        {
            byte[] input = new byte[length]; using PartialNonseekableStream stream = new(input);
            Need(ReadCachedDescriptors(stream).Length == length, "descriptor " + length); tests++;
        }
        bool oversized = false; try { using PartialNonseekableStream stream = new(new byte[117]); ReadCachedDescriptors(stream); }
        catch (InvalidOperationException) { oversized = true; }
        Need(oversized, "descriptor oversized"); tests++;

        string largest = Serialize(maximumResult); Need(System.Text.Encoding.UTF8.GetByteCount(largest) <= OutputLimit, "bounded maximum success output"); tests++;
        Need(clean.Writes == 0 && clean.Retries == 0 && clean.BusContentsAltered == false, "read only contract"); tests++;
        Console.WriteLine(JsonSerializer.Serialize(new { selfTestsPassed = tests, targetOperations = 0, maxTestOutputBytes = System.Text.Encoding.UTF8.GetByteCount(largest) }));
        return 0;
    }

    static int BulkTransfers(this FakeOps ops)
    {
        int count = 0; foreach (string call in ops.Calls) if (call.StartsWith("in", StringComparison.Ordinal) || call.StartsWith("out", StringComparison.Ordinal)) count++; return count;
    }

    static int HostMain(string[] args)
    {
        if (args.Length == 0)
        {
            Console.WriteLine(JsonSerializer.Serialize(new { schema = "managed-usb-rt-synchronized-key-dry-v1", intervention = "one Left down/up after first complete clean cycle", dryRun = true,
                targetOperations = 0, target = "0x101", cycle = new[] { "R", "M", "C", "P", "N", "H", "L", "R" },
                addresses = new[] { "0x47012400/256", "0x470004a0/68", "0x47000bc0/16", "0x47000490/16", "0x4700ba28/36", "0x4700d0e0/96", "0x47010f00/64" },
                durationMs = 15000, maxCycles = 60, nominalPeriodMs = 250, timeoutMs = TimeoutMs,
                interfaceNumber = 2, writes = 0, retries = 0, outputLimitBytes = OutputLimit }));
            return 0;
        }
        // Host-only fixture from the actual eight-window Run engine. No native bindings.
        if (args.Length == 1 && args[0] == "--host-fixture")
        {
            FakeClock clock = new(); FakeOps ops = new() { Clock = clock };
            ops.RtStates.AddRange(new[] { RtState.Clean, RtState.Clean, RtState.Clean, RtState.Faulted, RtState.Faulted });
            FakeIntervention trigger = new() { Ops = ops };
            Outcome sample = Run(ops, clock, new Config(), trigger);
            long stamp = trigger.State.ArmedUs!.Value;
            foreach (KeyCall call in trigger.State.Calls) { call.BeforeUs = stamp; call.AfterUs = stamp; call.ExitCode = 0; call.Started = call.Reaped = true; }
            trigger.State.EndUs = stamp;
            sample.ObservationAccepted = sample.Accepted;
            Console.WriteLine(Serialize(sample));
            return 0;
        }
        if(args.Length==1&&args[0].StartsWith("--checkpoint-fixture-",StringComparison.Ordinal)){string kind=args[0].Substring("--checkpoint-fixture-".Length);if(kind=="clean"||kind=="partial"||kind=="full")return ScoreFixture(kind);return 63;}
        if (args.Length == 1 && args[0] == "--checkpoint-self-test") return CheckpointSelfTest();
        if (args.Length == 1 && args[0] == "--self-test") return SelfTest();
        if (args.Length == 1 && args[0] == "--key-self-test") return KeySelfTest();
        // Target entrypoint remains disabled pending centrally qualified ownership binding.
        return 63;
    }
}
