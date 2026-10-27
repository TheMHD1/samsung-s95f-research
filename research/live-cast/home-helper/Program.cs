using System.Runtime.InteropServices;
using System.Text.Json;

static class Home
{
    const string Build = "BUILD_ID=T-RSMFAKUC-0090-REL-202607141953";
    const string Operation = "http://tizen.org/appcontrol/operation/main";
    const string Target = "HEPsqFNie0.tvplusstandalone";
    const string HomeKey = "db/appfw/home_appid";
    static readonly string[] Keys = { HomeKey, "db/appfw/startup_appid", "db/appfw/booting_appid_backup", "db/first_screen/type" };
    const string AutoKey = "db/menu/smart_hub/ontvsetting/auto_start";
    [DllImport("libc")] static extern uint getuid();
    [DllImport("libc")] static extern void free(IntPtr p);
    [DllImport("libbundle.so.0")] static extern IntPtr bundle_create();
    [DllImport("libbundle.so.0")] static extern void bundle_free(IntPtr b);
    [DllImport("libaul.so.0")] static extern int aul_svc_set_operation(IntPtr b, string op);
    [DllImport("libaul.so.0")] static extern int aul_get_default_app(IntPtr b, out IntPtr app);
    [DllImport("libcapi-appfw-app-operation-tv.so.0")] static extern int app_operation_set_current_app(string op, string app);
    [DllImport("libvconf.so.0")] static extern IntPtr vconf_get_str(string key);
    [DllImport("libvconf.so.0")] static extern int vconf_set_str(string key, string value);
    [DllImport("libvconf.so.0")] static extern int vconf_get_int(string key, out int value);
    [DllImport("libvconf.so.0")] static extern int vconf_set_int(string key, int value);
    [DllImport("libapp-context-manager-common.so")] static extern byte util_is_appbooting_supported_webapp_byappid(string app);

    public record Snapshot(string HomeOperation, Dictionary<string,string> Strings, int Autostart);
    static string ReadString(string key)
    {
        var p = vconf_get_str(key);
        if (p == IntPtr.Zero) throw new Exception("Cannot read " + key);
        try { return Marshal.PtrToStringAnsi(p) ?? throw new Exception("Null value"); }
        finally { free(p); }
    }
    static string ReadHome()
    {
        var b = bundle_create();
        if (b == IntPtr.Zero) throw new Exception("bundle_create failed");
        try {
            if (aul_svc_set_operation(b, Operation) != 0 || aul_get_default_app(b, out var p) != 0 || p == IntPtr.Zero)
                throw new Exception("Cannot read Home operation");
            try { return Marshal.PtrToStringAnsi(p) ?? throw new Exception("Null Home"); }
            finally { free(p); }
        } finally { bundle_free(b); }
    }
    static Snapshot Query()
    {
        var values = Keys.ToDictionary(k => k, ReadString);
        if (vconf_get_int(AutoKey, out var auto) != 0) throw new Exception("Cannot read autostart");
        return new Snapshot(ReadHome(), values, auto);
    }
    static void SetHome(string app)
    {
        var result = app_operation_set_current_app(Operation, app);
        if (result != 0 || ReadHome() != app) throw new Exception("Home operation write/readback failed: " + result);
    }
    static void SetString(string key, string value)
    {
        if (vconf_set_str(key, value) != 0 || ReadString(key) != value) throw new Exception("Preference write/readback failed: " + key);
    }
    static void Restore(Snapshot original)
    {
        SetHome(original.HomeOperation);
        SetString(HomeKey, original.Strings[HomeKey]);
        SetAuto(original.Autostart);
    }
    static void SetAuto(int value)
    {
        if (vconf_set_int(AutoKey, value) != 0 || vconf_get_int(AutoKey, out var after) != 0 || after != value)
            throw new Exception("Autostart write/readback failed");
    }
    static bool Same(Snapshot a, Snapshot b) => a.HomeOperation == b.HomeOperation && a.Autostart == b.Autostart && Keys.All(k => a.Strings[k] == b.Strings[k]);
    public static int Main(string[] args)
    {
        try {
            if (getuid() != 901 || IntPtr.Size != 4 || !File.ReadAllLines("/etc/tizen-release").Contains(Build))
                throw new Exception("Exact S95F build/SDK identity guard failed");
            if (args.Length == 1 && args[0] == "query") {
                Console.WriteLine(JsonSerializer.Serialize(new { snapshot = Query(), target = Target, boot_supported = util_is_appbooting_supported_webapp_byappid(Target) }));
                return 0;
            }
            if (args.Length != 2 || (args[0] != "apply" && args[0] != "restore")) throw new Exception("Use query or apply|restore BASELINE.json");
            var original = JsonSerializer.Deserialize<Snapshot>(File.ReadAllText(args[1])) ?? throw new Exception("Missing baseline");
            if (original.HomeOperation != "com.samsung.tv.csfs" || original.Strings.Count != Keys.Length || original.Autostart != 1 || Keys.Any(k => !original.Strings.TryGetValue(k, out var v) || v != "com.samsung.tv.csfs"))
                throw new Exception("Unexpected original values; review before writes");
            var current = Query();
            if (args[0] == "restore") {
                if (current.HomeOperation != Target && current.HomeOperation != original.HomeOperation) throw new Exception("Unexpected current Home");
                if (current.Strings[HomeKey] != Target && current.Strings[HomeKey] != original.Strings[HomeKey]) throw new Exception("Unexpected current preference");
                if (current.Autostart != original.Autostart && current.Autostart != 0) throw new Exception("Autostart changed unexpectedly");
                Restore(original);
                var restored = Query();
                if (restored.HomeOperation != original.HomeOperation || restored.Strings[HomeKey] != original.Strings[HomeKey] || restored.Autostart != original.Autostart || Keys.Where(k => k != HomeKey).Any(k => restored.Strings[k] != current.Strings[k])) throw new Exception("Restoration verification failed");
            } else {
                if (!Same(current, original)) throw new Exception("Current settings differ from baseline");
                // TV Plus is used only for the Home button. It is not assigned
                // to startup_appid: the exact-TV query says it cannot boot.
                // The guarded caller verifies this exact application's enabled
                // database entry; store widgets need not have a top-level config.xml.
                try {
                    SetHome(Target);
                    SetString(HomeKey, Target);
                    SetAuto(0);
                    var after = Query();
                    if (after.HomeOperation != Target || after.Strings[HomeKey] != Target || after.Autostart != 0 || Keys.Where(k => k != HomeKey).Any(k => after.Strings[k] != original.Strings[k])) throw new Exception("Verification mismatch");
                } catch { Restore(original); throw; }
            }
            Console.WriteLine(JsonSerializer.Serialize(Query()));
            return 0;
        } catch (Exception e) { Console.Error.WriteLine(e.GetType().Name + ": " + e.Message); return 1; }
    }
}
