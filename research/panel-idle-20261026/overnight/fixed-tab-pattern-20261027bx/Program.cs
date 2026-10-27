using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Threading;

internal static class Program
{
    internal const string ArmText = "BX-ARM-FOR-YOU-V1\n";
    internal const int HardSeconds = 30;
    internal const int Width = 1920, Height = 1080, Columns = 16, Rows = 9;
    private static NativeUi? ui;
    private static Journal? journal;
    private static Session? session;
    private static bool armed;
    private static volatile bool loopRunning;
    private static int quitRequested, exitCode;
    private static string reason = "unstarted", failure = "";
    private static readonly Native.TaskCallback TickDelegate = Tick;
    private static readonly Native.ThreadCallback QuitDelegate = QuitFromSignal;
    private static Engine? engine;
    private static double readyTime;
    private static string stage = "";

    internal sealed class Engine
    {
        internal readonly bool Change;
        internal int Phase;
        internal double Start;
        internal Engine(bool change, double now) { Change = change; Start = now; }
        // No catch-up: a callback over 250ms late rejects the trial before its next color change.
        internal string? Due(double now)
        {
            double due = Phase == 0 ? 2 : Phase == 1 ? 8 : 10;
            if (now < Start + due) return null;
            if (now > Start + due + .250) throw new InvalidDataException("epoch callback late");
            return Phase++ == 0 ? (Change ? "sparse" : "gray") : Phase == 2 ? "gray" : "quit";
        }
    }

    internal static (int r, int g, int b, int a) Color(bool sparse, int index)
    {
        if (index < 0 || index >= Columns * Rows) throw new ArgumentOutOfRangeException(nameof(index));
        int col = index % Columns, row = index / Columns;
        int v = !sparse || (col >= 6 && col < 10 && row >= 3 && row < 6) ? 48 : 8;
        return (v, v, v, 255);
    }

    private static int Main(string[] args)
    {
        if (args.Length == 0) { Console.WriteLine(JsonSerializer.Serialize(new {
            schema="fixed-tab-pattern-dry-v1", dry_run=true, target_operations=0,
            execute_modes=new[]{"--execute-sham","--execute-change"}, hard_seconds=HardSeconds,
            arm_text=ArmText, arm_wait_seconds=8, epochs_seconds=new[]{2,8,10},
            geometry=new[]{Width,Height}, objects=Columns*Rows,
            physical_picture_observed=false, presentation_observed=false })); return 0; }
        if (args.Length == 1 && args[0] == "--self-test") return SelfTest();
        bool check = args.Length == 1 && args[0] == "--check-native";
        if (!check && !(args.Length == 1 && (args[0] == "--execute-sham" || args[0] == "--execute-change"))) return 63;
        if (!BitConverter.IsLittleEndian || IntPtr.Size != 4 || RuntimeInformation.ProcessArchitecture != Architecture.Arm) {
            Console.WriteLine("{\"schema\":\"fixed-tab-pattern-refusal-v1\",\"abi_accepted\":false,\"native_calls\":0}"); return 64;
        }
        bool changed = args[0] == "--execute-change";
        try {
            // Mandatory SIGKILL timer is independent of EFL and managed scheduling once armed.
            Native.ArmKernelDeadline(HardSeconds);
            stage = AppContext.BaseDirectory.TrimEnd('/');
            Native.RequireOwned(stage, 0x4000, Native.geteuid());
            session = Session.Discover();
            Native.RequireExports();
            if (check) { Console.WriteLine(JsonSerializer.Serialize(new {
                schema="fixed-tab-pattern-native-check-v1", native_exports_resolved=true,
                session=session.Public(), ui_initialized=false, hard_deadline_armed=true,
                physical_picture_observed=false, presentation_observed=false })); return 0; }
            foreach (string name in new[]{"events.jsonl","ready.json","done.json","arm"})
                if (File.Exists(Path.Combine(stage,name)) || Directory.Exists(Path.Combine(stage,name)))
                    throw new InvalidDataException("stage already has run artifact: " + name);
            journal = new Journal(Path.Combine(stage,"events.jsonl"));
            journal.Add("start", new { mode=changed?"change":"sham", session=session.Public(), hard_seconds=HardSeconds,
                hard_timeout_scope="from successful kernel timer arm; managed runtime startup precedes it",
                conservative_hard_deadline_monotonic=Native.HardDeadline,
                selected_tab_verified_by_helper=false, physical_picture_observed=false, presentation_observed=false });
            ConfigureUiEnvironment(session);
            ui = new NativeUi(); ui.Create();
            double before = Native.Now(); ui.Apply(false); double after = Native.Now();
            ui.Show(); readyTime = Native.Now();
            journal.Add("initial_pixels_requested",new { before,after, gray_rgb=48, opaque=true,
                scope="Evas setters returned; no commit/scanout/light timestamp" });
            WriteNew("ready.json",new { schema="fixed-tab-pattern-ready-v1", ready_monotonic=readyTime,
                awaiting_arm=true, arm_wait_seconds=8, arm_file="arm", expected_arm=ArmText,
                selected_tab_verified_by_helper=false, presentation_observed=false });
            if (Native.ecore_timer_add(.025, TickDelegate, new IntPtr(changed ? 1 : 0)) == IntPtr.Zero)
                throw new IOException("ecore timer creation failed");
            using var term = PosixSignalRegistration.Create(PosixSignal.SIGTERM, ctx => Signal(ctx));
            using var intr = PosixSignalRegistration.Create(PosixSignal.SIGINT, ctx => Signal(ctx));
            reason = "running"; loopRunning=true;
            if (Volatile.Read(ref quitRequested) == 0) Native.ecore_main_loop_begin();
            else {reason="signal";exitCode=72;}
            loopRunning=false;
            if (reason=="running") { reason="unexpected_main_loop_return"; exitCode=70; }
        } catch (Exception e) {
            exitCode=70; reason="rejected"; failure=e.GetType().Name+": "+Safe(e.Message);
            TryLog("error",new { type=e.GetType().Name, message=Safe(e.Message) });
        } finally {
            loopRunning=false;
            if (ui != null) {
                try { double before=Native.Now(); ui.Hide(); TryLog("window_hidden",new {before,after=Native.Now(),
                    teardown="hide then process exit; no vendor EO delete/shutdown"}); }
                catch (Exception e) { exitCode=71; TryLog("cleanup_error",new {message=Safe(e.Message)}); }
            }
            TryLog("done",new {reason,exit_code=exitCode,hard_deadline_remains_armed=true,
                normal_process_exit_required_for_wayland_teardown=true, presentation_observed=false});
            if (journal != null) {
                try { WriteNew("done.json",new {schema="fixed-tab-pattern-done-v1",reason,exit_code=exitCode,
                    window_hide_attempted=ui!=null, process_exit_not_yet_observed=true,
                    selected_tab_verified_by_helper=false,physical_picture_observed=false,presentation_observed=false}); }
                catch { exitCode=71; }
                journal.Dispose();
            }
            GC.KeepAlive(TickDelegate); GC.KeepAlive(QuitDelegate);
        }
        Console.WriteLine(JsonSerializer.Serialize(new {schema="fixed-tab-pattern-terminal-v1",reason,
            exit_code=exitCode,failure,physical_picture_observed=false,presentation_observed=false}));
        return exitCode;
    }
    private static string Safe(string s) => s.Length > 240 ? s.Substring(0,240) : s;
    private static void WriteNew(string name, object value) {
        using var f=new FileStream(Path.Combine(stage,name),FileMode.CreateNew,FileAccess.Write,FileShare.Read);
        byte[] bytes=Encoding.UTF8.GetBytes(JsonSerializer.Serialize(value)+"\n"); f.Write(bytes); f.Flush(true);
    }
    private static void TryLog(string kind, object value) { try { journal?.Add(kind,value); } catch { exitCode=71; } }
    private static void Signal(PosixSignalContext ctx) { ctx.Cancel=true; Interlocked.Exchange(ref quitRequested,1);
        if (loopRunning) Native.ecore_main_loop_thread_safe_call_async(QuitDelegate,IntPtr.Zero); }
    private static void QuitFromSignal(IntPtr _) { reason="signal"; exitCode=72; Native.ecore_main_loop_quit(); }
    private static int Tick(IntPtr mode)
    {
        try {
            if (Volatile.Read(ref quitRequested)!=0) { QuitFromSignal(IntPtr.Zero); return 0; }
            double now=Native.Now();
            if (!armed) {
                if (now > readyTime+8) { reason="arm_timeout"; exitCode=73; Native.ecore_main_loop_quit(); return 0; }
                string arm=Path.Combine(stage,"arm");
                if (!File.Exists(arm)) return 1;
                Native.RequireOwned(arm,0x8000,Native.geteuid());
                if (ReadBounded(arm,64) != ArmText) throw new InvalidDataException("invalid arm assertion");
                session!.Recheck();
                if(Native.Now()+12>=Native.HardDeadline)throw new InvalidDataException("insufficient hard-deadline reserve to arm epochs");
                armed=true; engine=new Engine(mode!=IntPtr.Zero,Native.Now());
                journal!.Add("armed",new {baseline_monotonic=engine.Start,
                    assertion="central controller asserts ForYou selected and fresh clean/physical baseline",
                    selected_tab_verified_by_helper=false, schedule=new[]{2,8,10}});
                return 1;
            }
            string? epoch=engine!.Due(now);
            if (epoch==null) return 1;
            if (epoch=="quit") { reason="schedule_complete"; Native.ecore_main_loop_quit(); return 0; }
            double requested=engine.Start+(engine.Phase==1?2:8);
            session!.Recheck();
            double before=Native.Now();
            if(before>requested+.250)throw new InvalidDataException("epoch qualification completed late");
            ui!.Apply(epoch=="sparse"); double after=Native.Now();
            journal!.Add("pixels_requested",new {phase=engine.Phase,epoch,scheduled_monotonic=requested,
                before,after,object_setters=Columns*Rows,window_identity_unchanged=true,
                presentation_observed=false,presentation_time=(double?)null,
                scope="Evas setters only; actual commit, scanout and emitted light remain unobserved",
                callback_deadline_met=after<=requested+.250});
            if(after>requested+.250)throw new InvalidDataException("pixel application completed late");
            return 1;
        } catch (Exception e) { exitCode=74; reason="callback_rejected";
            TryLog("callback_error",new {type=e.GetType().Name,message=Safe(e.Message)});
            Native.ecore_main_loop_quit(); return 0; }
    }
    private static void ConfigureUiEnvironment(Session s) {
        Environment.SetEnvironmentVariable("XDG_RUNTIME_DIR",s.Runtime);
        Environment.SetEnvironmentVariable("WAYLAND_DISPLAY",s.Display);
        Environment.SetEnvironmentVariable("DBUS_SESSION_BUS_ADDRESS",s.Bus);
        Environment.SetEnvironmentVariable("ELM_PROFILE","tv");
        Environment.SetEnvironmentVariable("ELM_DISPLAY","wl");
        Environment.SetEnvironmentVariable("ELM_ENGINE","wayland_shm");
        Environment.SetEnvironmentVariable("ECORE_EVAS_ENGINE","wayland_shm");
        Environment.SetEnvironmentVariable("EVAS_WAYLAND_SHM_DISABLE_DMABUF","1");
    }
    internal static string ReadBounded(string path,int limit) {
        using var f=File.OpenRead(path); byte[] bytes=new byte[limit+1]; int n=0;
        while(n<bytes.Length) {int got=f.Read(bytes,n,bytes.Length-n);if(got==0)break;n+=got;}
        if(n>limit)throw new InvalidDataException("file bound exceeded");
        return new UTF8Encoding(false,true).GetString(bytes,0,n);
    }
    internal static Dictionary<string,string> ParseEnvironment(string value) {
        var d=new Dictionary<string,string>(StringComparer.Ordinal);
        foreach(string x in value.Split('\0',StringSplitOptions.RemoveEmptyEntries)) {
            int pos=x.IndexOf('='); if(pos<1)continue; string key=x.Substring(0,pos);
            if(key!="XDG_RUNTIME_DIR" && key!="WAYLAND_DISPLAY" && key!="DBUS_SESSION_BUS_ADDRESS")continue;
            if(!d.TryAdd(key,x.Substring(pos+1)))throw new InvalidDataException("duplicate session key");
        } return d;
    }
    internal static ulong StartIdentity(string value) {
        int end=value.LastIndexOf(')'); if(end<0)throw new InvalidDataException("proc stat");
        string[] fields=value.Substring(end+1).Split(' ',StringSplitOptions.RemoveEmptyEntries);
        if(fields.Length<20 || !ulong.TryParse(fields[19],out ulong id))throw new InvalidDataException("proc start identity");
        return id;
    }
    internal static bool SessionAnchor(string text) => text.Split('\0',StringSplitOptions.RemoveEmptyEntries).Any(x =>
        x=="com.samsung.tv.csfs" || (x.StartsWith("/",StringComparison.Ordinal) &&
        !x.Any(char.IsWhiteSpace) && Path.GetFileName(x).Equals("CSFS.dll",StringComparison.OrdinalIgnoreCase)));
    internal sealed class Session
    {
        internal int Pid; internal uint Uid; internal ulong Start;
        internal string Runtime="",Display="",Command="",Socket="",Bus="";
        internal object Public() => new {pid=Pid,uid=Uid,start_ticks=Start,runtime_directory=Runtime,wayland_display=Display,canonical_socket=Socket,session_bus_discovered=Bus.Length>0};
        internal void Recheck() {
            if(StartIdentity(ReadBounded($"/proc/{Pid}/stat",8192))!=Start ||
                ReadBounded($"/proc/{Pid}/cmdline",16384)!=Command)
                throw new InvalidDataException("CSFS identity changed");
            var env=ParseEnvironment(ReadBounded($"/proc/{Pid}/environ",32768));
            if(env.GetValueOrDefault("XDG_RUNTIME_DIR")!=Runtime || env.GetValueOrDefault("WAYLAND_DISPLAY")!=Display ||
                env.GetValueOrDefault("DBUS_SESSION_BUS_ADDRESS")!=Bus || ResolveSocket(Runtime,Display,Uid)!=Socket)
                throw new InvalidDataException("CSFS session changed");
        }
        internal static string ResolveSocket(string runtime,string display,uint uid) {
            Native.RequireOwned(runtime,0x4000,uid);
            string requested=runtime+"/"+display;
            FileSystemInfo? resolved=new FileInfo(requested).ResolveLinkTarget(true);
            string canonical=resolved?.FullName ?? requested;
            if(!canonical.StartsWith("/run/",StringComparison.Ordinal))throw new InvalidDataException("Wayland socket escaped /run");
            Native.RequireSocket(canonical,uid);return canonical;
        }
        internal static Session Discover() {
            var found=new List<Session>(); int scanned=0;
            foreach(string path in Directory.EnumerateDirectories("/proc")) {
                if(!int.TryParse(Path.GetFileName(path),out int pid))continue;
                if(++scanned>4096)throw new InvalidDataException("process discovery bound");
                string cmd;
                try { cmd=ReadBounded(path+"/cmdline",16384); } catch(IOException){continue;} catch(UnauthorizedAccessException){continue;}
                if(!SessionAnchor(cmd))continue;
                ulong start=StartIdentity(ReadBounded(path+"/stat",8192));
                string status=ReadBounded(path+"/status",16384);
                string line=status.Split('\n').Single(x=>x.StartsWith("Uid:",StringComparison.Ordinal));
                uint[] ids=line.Substring(4).Split((char[]?)null,StringSplitOptions.RemoveEmptyEntries).Select(uint.Parse).ToArray();
                if(ids.Length!=4 || ids[0]==0 || ids.Any(x=>x!=ids[0]))throw new InvalidDataException("CSFS UID mismatch");
                var env=ParseEnvironment(ReadBounded(path+"/environ",32768));
                if(!env.TryGetValue("XDG_RUNTIME_DIR",out string? runtime) || runtime!="/run/user/"+ids[0] ||
                   !env.TryGetValue("WAYLAND_DISPLAY",out string? display) || display.Length<1 || display.Length>64 ||
                   display=="." || display==".." || display.Any(c=>!char.IsAscii(c) || !(char.IsLetterOrDigit(c)||c=='_'||c=='-'||c=='.')))
                    throw new InvalidDataException("missing or noncanonical session environment");
                string busUnix="unix:path="+runtime+"/dbus/user_bus_socket";
                string busKernel="kernel:path=/sys/fs/kdbus/"+ids[0]+"-user/bus;"+busUnix;
                if(!env.TryGetValue("DBUS_SESSION_BUS_ADDRESS",out string? bus) || (bus!=busUnix && bus!=busKernel))
                    throw new InvalidDataException("unqualified session bus address");
                string socket=ResolveSocket(runtime,display,ids[0]);
                var s=new Session{Pid=pid,Uid=ids[0],Start=start,Runtime=runtime,Display=display,Command=cmd,Socket=socket,Bus=bus};
                s.Recheck(); found.Add(s);
            }
            if(found.Count!=1)throw new InvalidDataException("need exactly one qualified CSFS session");
            return found[0];
        }
    }
    internal sealed class Journal : IDisposable
    {
        private readonly FileStream stream; private int count;
        internal Journal(string path) {stream=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.Read);}
        internal void Add(string kind,object data) {
            if(++count>32)throw new InvalidDataException("event count bound");
            byte[] line=Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new {schema="fixed-tab-pattern-event-v1",kind,
                monotonic=Native.Now(),data})+"\n");
            if(line.Length>2048 || stream.Length+line.Length>32768)throw new InvalidDataException("journal byte bound");
            stream.Write(line); stream.Flush(true);
        }
        public void Dispose()=>stream.Dispose();
    }
    internal sealed class NativeUi
    {
        private IntPtr window; private readonly IntPtr[] objects=new IntPtr[Columns*Rows];
        internal void Create() {
            if(Native.elm_init(0,IntPtr.Zero)<=0)throw new IOException("elm_init failed");
            window=Native.elm_win_add(IntPtr.Zero,"bx-fixed-tab-pattern",12);
            if(window==IntPtr.Zero)throw new IOException("elm_win_add failed");
            Native.elm_win_alpha_set(window,1);Native.elm_win_borderless_set(window,1);
            Native.elm_win_prop_focus_skip_set(window,1);
            if(Native.efl_util_set_notification_window_level(window,40)!=0)throw new IOException("notification level failed");
            Native.elm_win_layer_set(window,900);Native.elm_win_input_rect_set(window,0,0,0,0);
            if(Native.elm_win_aux_hint_add(window,"wm.comp.win.effect.enable","0")<0)throw new IOException("effect hint failed");
            Native.evas_object_move(window,0,0);Native.evas_object_resize(window,Width,Height);
            IntPtr canvas=Native.evas_object_evas_get(window);if(canvas==IntPtr.Zero)throw new IOException("canvas failed");
            for(int i=0;i<objects.Length;i++) {
                IntPtr o=Native.evas_object_rectangle_add(canvas);if(o==IntPtr.Zero)throw new IOException("rectangle failed");
                objects[i]=o;Native.evas_object_move(o,(i%Columns)*120,(i/Columns)*120);Native.evas_object_resize(o,120,120);
                Native.evas_object_pass_events_set(o,1);Native.evas_object_show(o);
            }
            Native.evas_object_pass_events_set(window,1);
        }
        internal void Apply(bool sparse) { for(int i=0;i<objects.Length;i++) {
            var c=Color(sparse,i);Native.evas_object_color_set(objects[i],c.r,c.g,c.b,c.a); } }
        internal void Show()=>Native.evas_object_show(window);
        internal void Hide(){if(window!=IntPtr.Zero)Native.evas_object_hide(window);}
    }
    private static int SelfTest()
    {
        int n=0; void Need(bool v){if(!v)throw new Exception("self test "+n);n++;}
        void Reject(Action a){bool failed=false;try{a();}catch(InvalidDataException){failed=true;}Need(failed);}
        foreach(bool change in new[]{false,true}) {
            var e=new Engine(change,100); Need(e.Due(101.999)==null); Need(e.Due(102)==(change?"sparse":"gray"));
            Need(e.Due(107.999)==null);Need(e.Due(108.025)=="gray");Need(e.Due(110)=="quit");Need(e.Phase==3);
        }
        var late=new Engine(true,0);Reject(()=>late.Due(2.251));Need(late.Phase==0);
        int bright=0,dark=0;
        for(int i=0;i<144;i++){var a=Color(false,i);var b=Color(true,i);Need(a==(48,48,48,255));Need(b.a==255);
            if(b.r==48)bright++;else if(b.r==8)dark++;else throw new Exception("color");}
        Need(bright==12 && dark==132);
        Need(ParseEnvironment("SECRET=discard\0WAYLAND_DISPLAY=wayland-7\0XDG_RUNTIME_DIR=/run/user/42\0").Count==2);
        Reject(()=>ParseEnvironment("WAYLAND_DISPLAY=a\0WAYLAND_DISPLAY=b\0"));
        string[] fields=Enumerable.Repeat("0",20).ToArray();fields[0]="S";fields[19]="98765";
        Need(StartIdentity("1 (name with ) bracket) "+string.Join(" ",fields))==98765);
        Reject(()=>StartIdentity("broken"));Need(SessionAnchor("/fixture/host\0/foo/CSFS.dll\0"));
        Need(!SessionAnchor("/tmp/fake-CSFS.dll\0"));Need(!SessionAnchor("/tmp/OTHER.dll\0"));
        Need(Marshal.SizeOf<Native.Timespec32>()==8);Need(Marshal.SizeOf<Native.Itimer32>()==16);
        byte[] ev=Native.SignalEvent32();Need(ev.Length==64);Need(BitConverter.ToInt32(ev,4)==9);Need(BitConverter.ToInt32(ev,8)==0);
        Need(ev.Where((_,i)=>i<4||i>4).All(x=>x==0));
        Console.WriteLine(JsonSerializer.Serialize(new {schema="fixed-tab-pattern-self-test-v1",checks=n,native_calls=0,
            target_operations=0,physical_picture_observed=false,presentation_observed=false}));return 0;
    }
}

internal static class Native
{
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] internal delegate int TaskCallback(IntPtr data);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] internal delegate void ThreadCallback(IntPtr data);
    [StructLayout(LayoutKind.Sequential)] internal struct Timespec32 {internal int Seconds,Nanoseconds;}
    [StructLayout(LayoutKind.Sequential)] internal struct Itimer32 {internal Timespec32 Interval,Value;}
    [DllImport("libc.so.6",SetLastError=true)] internal static extern int clock_gettime(int clock,out Timespec32 value);
    [DllImport("librt.so.1",SetLastError=true)] private static extern int timer_create(int clock,byte[] ev,out IntPtr id);
    [DllImport("librt.so.1",SetLastError=true)] private static extern int timer_settime(IntPtr id,int flags,ref Itimer32 value,IntPtr old);
    [DllImport("libc.so.6")] internal static extern uint geteuid();
    [DllImport("libc.so.6",SetLastError=true)] private static extern int statx(int dirfd,string path,int flags,uint mask,[Out] byte[] buffer);
    internal static double Now() {if(clock_gettime(1,out var t)!=0 || t.Seconds<0 || t.Nanoseconds<0 || t.Nanoseconds>=1000000000)
        throw new IOException("monotonic clock failed");return t.Seconds+t.Nanoseconds/1e9;}
    internal static byte[] SignalEvent32(){byte[] x=new byte[64];BitConverter.GetBytes(9).CopyTo(x,4);return x;}
    internal static double HardDeadline;
    internal static void ArmKernelDeadline(int seconds) {
        double before=Now();
        if(timer_create(1,SignalEvent32(),out IntPtr id)!=0)throw new IOException("kernel deadline create failed errno="+Marshal.GetLastWin32Error());
        var value=new Itimer32{Value=new Timespec32{Seconds=seconds}};
        if(timer_settime(id,0,ref value,IntPtr.Zero)!=0)throw new IOException("kernel deadline arm failed errno="+Marshal.GetLastWin32Error());
        HardDeadline=before+seconds;
    }
    internal static void RequireOwned(string path,int type,uint uid) {
        byte[] buf=new byte[256];
        if(statx(-100,path,0x100,0x7ff,buf)!=0)throw new IOException("statx qualification failed");
        uint mask=BitConverter.ToUInt32(buf,0);ushort mode=BitConverter.ToUInt16(buf,28);
        if((mask&0xb)!=0xb || (mode&0xf000)!=type || BitConverter.ToUInt32(buf,20)!=uid || (mode&0x12)!=0)
            throw new InvalidDataException("path ownership/type/mode rejected");
    }
    internal static void RequireSocket(string path,uint sessionUid) {
        byte[] buf=new byte[256];
        if(statx(-100,path,0x100,0x7ff,buf)!=0)throw new IOException("socket statx qualification failed");
        uint mask=BitConverter.ToUInt32(buf,0), uid=BitConverter.ToUInt32(buf,20);ushort mode=BitConverter.ToUInt16(buf,28);
        if((mask&0xb)!=0xb || (mode&0xf000)!=0xc000 || (uid!=0 && uid!=sessionUid) || (mode&0x12)!=0)
            throw new InvalidDataException("socket ownership/type/mode rejected");
    }
    internal static readonly Dictionary<string,string[]> Exports = new() {
        ["libelementary.so.1"]=new[]{"elm_init","elm_win_add","elm_win_alpha_set","elm_win_borderless_set","elm_win_prop_focus_skip_set","elm_win_layer_set","elm_win_input_rect_set","elm_win_aux_hint_add"},
        ["libcapi-ui-efl-util.so.0"]=new[]{"efl_util_set_notification_window_level"},
        ["libevas.so.1"]=new[]{"evas_object_evas_get","evas_object_rectangle_add","evas_object_color_set","evas_object_move","evas_object_resize","evas_object_pass_events_set","evas_object_show","evas_object_hide"},
        ["libecore.so.1"]=new[]{"ecore_timer_add","ecore_main_loop_begin","ecore_main_loop_quit","ecore_main_loop_thread_safe_call_async"} };
    private static readonly List<IntPtr> Handles=new();
    internal static void RequireExports(){foreach(var mod in Exports){IntPtr h=NativeLibrary.Load(mod.Key);Handles.Add(h);
        foreach(string name in mod.Value)if(!NativeLibrary.TryGetExport(h,name,out _))throw new EntryPointNotFoundException(mod.Key+":"+name);}}
    [DllImport("libelementary.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern int elm_init(int argc,IntPtr argv);
    [DllImport("libelementary.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern IntPtr elm_win_add(IntPtr parent,string name,int type);
    [DllImport("libelementary.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern void elm_win_alpha_set(IntPtr window,int value);
    [DllImport("libelementary.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern void elm_win_borderless_set(IntPtr window,int value);
    [DllImport("libelementary.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern void elm_win_prop_focus_skip_set(IntPtr window,int value);
    [DllImport("libelementary.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern void elm_win_layer_set(IntPtr window,int value);
    [DllImport("libelementary.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern void elm_win_input_rect_set(IntPtr window,int x,int y,int w,int h);
    [DllImport("libelementary.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern int elm_win_aux_hint_add(IntPtr window,string hint,string value);
    [DllImport("libcapi-ui-efl-util.so.0",CallingConvention=CallingConvention.Cdecl)] internal static extern int efl_util_set_notification_window_level(IntPtr window,int value);
    [DllImport("libevas.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern IntPtr evas_object_evas_get(IntPtr obj);
    [DllImport("libevas.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern IntPtr evas_object_rectangle_add(IntPtr canvas);
    [DllImport("libevas.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern void evas_object_color_set(IntPtr obj,int r,int g,int b,int a);
    [DllImport("libevas.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern void evas_object_move(IntPtr obj,int x,int y);
    [DllImport("libevas.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern void evas_object_resize(IntPtr obj,int w,int h);
    [DllImport("libevas.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern void evas_object_pass_events_set(IntPtr obj,int pass);
    [DllImport("libevas.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern void evas_object_show(IntPtr obj);
    [DllImport("libevas.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern void evas_object_hide(IntPtr obj);
    [DllImport("libecore.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern IntPtr ecore_timer_add(double seconds,TaskCallback callback,IntPtr data);
    [DllImport("libecore.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern void ecore_main_loop_begin();
    [DllImport("libecore.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern void ecore_main_loop_quit();
    [DllImport("libecore.so.1",CallingConvention=CallingConvention.Cdecl)] internal static extern void ecore_main_loop_thread_safe_call_async(ThreadCallback callback,IntPtr data);
}
