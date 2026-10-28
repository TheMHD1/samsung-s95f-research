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
}
