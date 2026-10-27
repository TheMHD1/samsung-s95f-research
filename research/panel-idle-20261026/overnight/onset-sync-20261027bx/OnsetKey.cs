using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Threading;
using System.Threading.Tasks;

internal static partial class Program
{
    sealed class KeyCall
    {
        public string Phase { get; set; } = "";
        public long? BeforeUs { get; set; }
        public long? AfterUs { get; set; }
        public int? ExitCode { get; set; }
        public bool Started { get; set; }
        public bool Reaped { get; set; }
        public bool TimedOut { get; set; }
        public long StdoutBytes { get; set; }
        public long StderrBytes { get; set; }
        public string? Error { get; set; }
    }
    sealed class InterventionState
    {
        public string Key { get; set; } = "Left";
        public string Trigger { get; set; } = "first-full-clean-cycle";
        public bool Attempted { get; set; }
        public bool Completed { get; set; }
        public long? ArmedUs { get; set; }
        public long? EndUs { get; set; }
        public string? Error { get; set; }
        public bool UiReceiptObserved { get; set; }
        public bool PhysicalPictureObserved { get; set; }
        public List<KeyCall> Calls { get; set; } = new(2) {
            new KeyCall { Phase = "down" }, new KeyCall { Phase = "up" }
        };
    }
    interface IIntervention
    {
        InterventionState State { get; }
        void Start(IClock clock);
        void Finish();
    }
    interface IKeyOps
    {
        void Send(KeyCall call);
        void Hold();
    }
    sealed class OneLeft : IIntervention
    {
        public InterventionState State { get; } = new();
        readonly IKeyOps ops;
        Thread? worker;
        public OneLeft(IKeyOps ops) { this.ops = ops; }
        public void Start(IClock clock)
        {
            Need(!State.Attempted, "key intervention cannot repeat");
            // Set before scheduling: a failed Thread.Start cannot lead to a retry.
            State.Attempted = true;
            State.ArmedUs = clock.NowUs();
            worker = new Thread(() => Work(clock)) { IsBackground = true };
            worker.Start();
        }
        void Send(string phase, IClock clock)
        {
            KeyCall call = State.Calls[phase == "down" ? 0 : 1];
            try { call.BeforeUs = clock.NowUs(); }
            catch (Exception e) { call.Error = ShortError(e); }
            // A missing timestamp must never suppress the release attempt.
            try { ops.Send(call); }
            catch (Exception e) { call.Error ??= ShortError(e); }
            try { call.AfterUs = clock.NowUs(); }
            catch (Exception e) { call.Error ??= ShortError(e); }
            if (!call.Started || !call.Reaped || call.TimedOut || call.ExitCode != 0 ||
                call.StdoutBytes > 4096 || call.StderrBytes > 4096)
                call.Error ??= "key child contract failed";
            State.Error ??= call.Error;
        }
        void Work(IClock clock)
        {
            try
            {
                try { Send("down", clock); ops.Hold(); }
                finally { Send("up", clock); }
            }
            catch (Exception e) { State.Error ??= ShortError(e); }
            finally
            {
                try { State.EndUs = clock.NowUs(); }
                catch (Exception e) { State.Error ??= ShortError(e); }
                State.Completed = true;
            }
        }
        public void Finish()
        {
            if (!State.Attempted) return;
            Need(worker != null && worker.Join(7000), "key worker not reconciled within 7 seconds");
        }
    }
    sealed class RealKeyOps : IKeyOps
    {
        const string Utility = "/usr/bin/input_keyevent";
        const string UtilitySha = "7284ad5b0117a96a166a4fe327c6361bea998e5d2086a0e1a36d2a3477a87db9";
        public RealKeyOps()
        {
            Need(Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(Utility))).Equals(UtilitySha, StringComparison.OrdinalIgnoreCase), "normal key utility changed");
        }
        public void Hold() => Thread.Sleep(150);
        // Drain with fixed storage; never accumulate child output in memory.
        static long Drain(Stream stream)
        {
            byte[] bytes = new byte[1024]; long count = 0; int n;
            while ((n = stream.Read(bytes, 0, bytes.Length)) > 0) count = Math.Min(1_000_000_000L, count + n);
            return count;
        }
        public void Send(KeyCall call)
        {
            Need(call.Phase == "down" || call.Phase == "up", "fixed phase");
            using Process child = new();
            child.StartInfo = new ProcessStartInfo(Utility) {
                UseShellExecute = false, RedirectStandardOutput = true, RedirectStandardError = true
            };
            child.StartInfo.ArgumentList.Add("Left");
            child.StartInfo.ArgumentList.Add(call.Phase);
            call.Started = child.Start();
            Need(call.Started, "key child failed to start");
            Task<long> stdout = Task.Run(() => Drain(child.StandardOutput.BaseStream));
            Task<long> stderr = Task.Run(() => Drain(child.StandardError.BaseStream));
            if (!child.WaitForExit(1500))
            {
                call.TimedOut = true;
                try { child.Kill(entireProcessTree: true); }
                catch (Exception e) { call.Error = ShortError(e); }
            }
            call.Reaped = child.WaitForExit(750);
            if (call.Reaped) call.ExitCode = child.ExitCode;
            if (Task.WaitAll(new Task[] { stdout, stderr }, 500))
            {
                call.StdoutBytes = stdout.Result; call.StderrBytes = stderr.Result;
            }
            else call.Error ??= "key output pipes not reconciled";
        }
    }
    sealed class FakeKeyOps : IKeyOps
    {
        public readonly List<string> Calls = new();
        public string? Fail;
        public bool BadExit, Unreaped, Oversized;
        public void Hold() { Calls.Add("hold"); if (Fail == "hold") throw new IOException("hold failed"); }
        public void Send(KeyCall call)
        {
            Calls.Add(call.Phase);
            if (Fail == call.Phase) throw new IOException("key injected");
            call.Started = true; call.Reaped = !Unreaped; call.ExitCode = BadExit ? 1 : 0;
            call.StdoutBytes = Oversized ? 4097 : 0;
        }
    }
    sealed class FakeIntervention : IIntervention
    {
        public InterventionState State { get; } = new();
        public FakeOps? Ops;
        public int Starts, Finishes;
        public bool FailStart, FailFinish;
        public void Start(IClock clock)
        {
            Starts++; State.Attempted = true; State.ArmedUs = clock.NowUs();
            Need(Ops!.BulkTransfers() == 12, "trigger must follow complete first cycle");
            if (FailStart) throw new IOException("schedule failed");
        }
        public void Finish() { Finishes++; if (FailFinish) throw new IOException("join failed"); State.Completed = State.Attempted; }
    }
    sealed class BlockingKeyOps : IKeyOps
    {
        public readonly ManualResetEventSlim DownPending = new(false), ReleaseDown = new(false);
        public int Downs, Ups;
        public void Hold() { }
        public void Send(KeyCall call)
        {
            if (call.Phase == "down")
            {
                Downs++; DownPending.Set();
                Need(ReleaseDown.Wait(2000), "test down not released");
            }
            else Ups++;
            call.Started = call.Reaped = true; call.ExitCode = 0;
        }
    }
    sealed class KeyFaultClock : IClock
    {
        public int Calls, ThrowAt;
        public long NowUs() { int current = Calls++; if (current == ThrowAt) throw new IOException("action clock failed"); return current * 100; }
        public void SleepUs(long us) { }
    }
    static int KeySelfTest()
    {
        int tests = 0;
        foreach (string? fail in new string?[] { null, "down", "hold", "up" })
        {
            FakeKeyOps ops = new() { Fail = fail }; OneLeft key = new(ops);
            key.Start(new RealClock()); key.Finish();
            Need(key.State.Attempted && key.State.Completed && key.State.Calls.Count == 2, "bounded single down/up");
            Need(string.Join(",", ops.Calls) == "down,hold,up", "up follows down/hold failure");
            Need((key.State.Error == null) == (fail == null), "worker failure retained");
            Need(key.State.Calls[0].BeforeUs <= key.State.Calls[0].AfterUs && key.State.Calls[0].AfterUs <= key.State.Calls[1].BeforeUs, "key timestamps");
            bool repeat = false; try { key.Start(new RealClock()); } catch (InvalidOperationException) { repeat = true; }
            Need(repeat, "no key retry"); tests++;
        }
        foreach (string failure in new[] { "exit", "reap", "output" })
        {
            FakeKeyOps ops = new() { BadExit = failure == "exit", Unreaped = failure == "reap", Oversized = failure == "output" };
            OneLeft key = new(ops); key.Start(new RealClock()); key.Finish();
            Need(key.State.Completed && key.State.Error != null && key.State.Calls.Count == 2, "bad child rejected"); tests++;
        }
        foreach (string failure in new[] { "none", "initial-fault", "preflight", "first-out", "first-in", "start", "finish" })
        {
            FakeOps ops = new(); FakeClock clock = new(); ops.Clock = clock;
            if (failure == "initial-fault") ops.RtStates.Add(RtState.Faulted);
            if (failure == "preflight") ops.ThrowAt = "preflight";
            if (failure == "first-out") ops.FailBulkAt = 0;
            if (failure == "first-in") ops.FailBulkAt = 1;
            FakeIntervention action = new() { Ops = ops, FailStart = failure == "start", FailFinish = failure == "finish" };
            Outcome result = Run(ops, clock, new Config { MaxCycles = 3, PeriodUs = 10 }, action);
            bool armed = failure == "none" || failure == "start" || failure == "finish";
            Need(action.Starts == (armed ? 1 : 0) && action.Finishes == 1, "exact trigger/cleanup count");
            Need(result.Retained.Exists(c => c.Role == "trigger-baseline") == armed, "trigger baseline retention");
            if (armed) Need(result.Retained.Find(c => c.Role == "trigger-baseline")!.CycleIndex == 1, "baseline frozen cycle1");
            if (failure == "start") Need(ops.BulkTransfers() == 12 && result.ProtocolPhase == "ReadyForHeader" && !result.Accepted, "schedule failure no extra header");
            if (failure == "finish") Need(!result.Accepted && result.ProtocolPhase == "ReadyForHeader", "join failure rejected");
            Need(!result.Opened || result.Closed, "close after action failure");
            Need(!result.Claimed || result.Released, "release after action failure"); tests++;
        }
        // Worst retained transition plus the immutable trigger baseline.
        FakeOps maximum = new(); FakeClock maxClock = new(); maximum.Clock = maxClock;
        maximum.RtStates.AddRange(new[] { RtState.Clean, RtState.Clean, RtState.Clean, RtState.Faulted, RtState.Faulted });
        FakeIntervention trigger = new() { Ops = maximum };
        Outcome max = Run(maximum, maxClock, new Config { MaxCycles = 5, PeriodUs = 10 }, trigger);
        int bytes = System.Text.Encoding.UTF8.GetByteCount(Serialize(max));
        Need(max.Accepted && max.Retained.Count == 4 && bytes <= OutputLimit, "bounded key transition output"); tests++;
        for (int failure = 1; failure <= 5; failure++)
        {
            FakeKeyOps ops = new(); OneLeft key = new(ops);
            key.Start(new KeyFaultClock { ThrowAt = failure }); key.Finish();
            Need(key.State.Error != null && key.State.Completed && key.State.Calls.Count == 2 &&
                string.Join(",", ops.Calls) == "down,hold,up", "clock failure preserves up"); tests++;
        }
        foreach (bool fault in new[] { false, true })
        {
            FakeOps usb = new(); FakeClock clock = new(); usb.Clock = clock;
            BlockingKeyOps keyOps = new(); OneLeft key = new(keyOps); int whilePending = 0;
            if (fault) usb.RtStates.AddRange(new[] { RtState.Clean, RtState.Clean, RtState.Faulted, RtState.Faulted });
            usb.OnBulk = (index, input) => {
                if (index == 12) Need(keyOps.DownPending.Wait(1000), "worker scheduled before subsequent cycle");
                if (index >= 12 && !keyOps.ReleaseDown.IsSet) whilePending++;
                if ((!fault && index == 36) || (fault && index == 22)) keyOps.ReleaseDown.Set();
            };
            Outcome observed = Run(usb, clock, new Config { MaxCycles = 5, PeriodUs = 10 }, key);
            Need(observed.Accepted && whilePending >= 10 && keyOps.Downs == 1 && keyOps.Ups == 1 &&
                key.State.Completed && key.State.Error == null, "USB continues during blocked key");
            Need(observed.OnsetObserved == fault, "fault while down pending retained"); tests++;
        }
        Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(new { keyTestsPassed = tests, targetOperations = 0, maxTestOutputBytes = bytes }));
        return 0;
    }
}
