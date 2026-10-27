using System.Reflection;
using System.Runtime.InteropServices;
using System.Text.Json;

// Intentionally does not call ScreenManagerSetAutoPowerControl or ambient-mode APIs.
// `extend` performs one non-persistent request and exits; it has no timer loop.
class Program
{
    [DllImport("libc")] static extern uint getuid();

    static int Main(string[] args)
    {
        try
        {
            if (getuid() != 901 || IntPtr.Size != 4 ||
                !File.ReadAllLines("/etc/tizen-release")
                    .Contains("BUILD_ID=T-RSMFAKUC-0090-REL-202607141953"))
                throw new InvalidOperationException("SDK/exact-build guard failed");
            if (args.Length != 1 || (args[0] != "query" && args[0] != "extend"))
                throw new ArgumentException("Use query or extend");

            AssemblyLoadContext();
            var assembly = Assembly.LoadFrom("/usr/share/dotnet.tizen/framework/Tizen.TV.System.Screen.dll");
            var api = assembly.GetType("Tizen.TV.System.Screen.ScreenAPI", true)!;
            var sensor = assembly.GetType("Tizen.TV.System.Screen.ScreenManagerSensorType", true)!;
            var initialized = (bool)api.GetMethod("ScreenManagerIsInitialized")!.Invoke(null, null)!;

            object?[] beforeArgs = { Enum.ToObject(sensor, 0) };
            var beforeResult = (int)api.GetMethod("ScreenManagerGetSuspendReason")!.Invoke(null, beforeArgs)!;
            object? extendResult = null;
            if (args[0] == "extend")
                extendResult = (int)api.GetMethod("ScreenManagerExtendSensorTimer")!.Invoke(null, null)!;
            object?[] afterArgs = { Enum.ToObject(sensor, 0) };
            var afterResult = (int)api.GetMethod("ScreenManagerGetSuspendReason")!.Invoke(null, afterArgs)!;
            Console.WriteLine(JsonSerializer.Serialize(new {
                initialized,
                before = new { result = beforeResult, reason = beforeArgs[0]!.ToString() },
                extendResult,
                after = new { result = afterResult, reason = afterArgs[0]!.ToString() },
                persistentSettingChanged = false,
                prohibitedCalls = new[] { "ScreenManagerSetAutoPowerControl", "ambient mode", "power off" }
            }));
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine(exception);
            return 1;
        }
    }

    static void AssemblyLoadContext()
    {
        System.Runtime.Loader.AssemblyLoadContext.Default.Resolving += (_, name) =>
        {
            foreach (var directory in new[] { "/usr/share/dotnet.tizen/framework/", "/usr/share/dotnet.tizen/tvappapi/" })
            {
                var candidate = directory + name.Name + ".dll";
                if (File.Exists(candidate))
                    return System.Runtime.Loader.AssemblyLoadContext.Default.LoadFromAssemblyPath(candidate);
            }
            return null;
        };
    }
}
