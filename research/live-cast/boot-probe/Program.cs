using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Text.Json;
using Tizen.Applications;

sealed class Probe : ServiceApplication
{
    protected override void OnCreate()
    {
        base.OnCreate();
        var output = Path.Combine(DirectoryInfo.Data, "researcher-root-suitability.json");
        try {
            var self = File.ReadAllText("/proc/self/status");
            var label = File.ReadAllText("/proc/self/attr/current");
            string? child = null, error = null;
            int? code = null;
            try {
                if (!File.ReadAllLines("/etc/tizen-release").Contains("BUILD_ID=T-RSMFAKUC-0090-REL-202607141953")) throw new Exception("Build guard mismatch");
                var start = new ProcessStartInfo("/usr/bin/dotnet") { UseShellExecute=false, RedirectStandardOutput=true, RedirectStandardError=true };
                start.ArgumentList.Add("/home/researcher/share/tmp/sdk_tools/researcher-live-cast/CoreProbe.dll");
                using var process = Process.Start(start) ?? throw new Exception("Child did not start");
                if (!process.WaitForExit(5000)) { process.Kill(); throw new Exception("Child timeout"); }
                code = process.ExitCode;
                child = process.StandardOutput.ReadToEnd();
                error = process.StandardError.ReadToEnd();
            } catch(Exception e) { error=e.GetType().Name+": "+e.Message; }
            string socketTest;
            try {
                using var socket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp) { ReceiveTimeout=2000, SendTimeout=2000 };
                if (!socket.ConnectAsync("127.0.0.1", 26101).Wait(2000)) throw new Exception("Loopback connect timeout");
                byte[] hello = Convert.FromHexString("434e584e00001000000004000700000032020000bcb1a7b1686f73743a3a00");
                socket.Send(hello);
                var frame=new byte[24];
                var count=socket.Receive(frame);
                socketTest="Loopback SDB bytes="+count+" frame="+Convert.ToHexString(frame.AsSpan(0,count));
            } catch(Exception e) { socketTest=e.GetType().Name+": "+e.Message; }
            string listenerTest;
            try {
                var listener=new TcpListener(IPAddress.Parse("198.51.100.20"),26104);
                listener.Start(1); listener.Stop(); listenerTest="LAN listener permitted";
            } catch(Exception e) { listenerTest=e.GetType().Name+": "+e.Message; }
            File.WriteAllText(output, JsonSerializer.Serialize(new { self, label, child, code, error, socketTest, listenerTest }));
        } finally { Exit(); }
    }
    static void Main(string[] args) { using var app = new Probe(); app.Run(args); }
}
