using System.Collections;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Runtime.Loader;
using System.Text.Json;

// Read-only diagnostic. App-context state is lifecycle state, not a frontmost
// window guarantee. Its output must never be used as a persistent keep-awake gate.
internal static class Program
{
    [DllImport("libc")] private static extern uint getuid();
    private const string Build = "BUILD_ID=T-RSMFAKUC-0090-REL-202607141953";

    private static int Main(string[] args)
    {
        try
        {
            if (args.Length != 1 || args[0] != "query")
                throw new ArgumentException("Use query");
            if (getuid() != 901 || IntPtr.Size != 4 || !File.ReadLines("/etc/tizen-release").Contains(Build))
                throw new InvalidOperationException("SDK/exact-build guard failed");

            InstallResolver();
            var assembly = Assembly.LoadFrom("/usr/share/dotnet.tizen/framework/Tizen.Applications.Common.dll");
            var manager = assembly.GetType("Tizen.Applications.ApplicationManager", throwOnError: true)!;
            var request = manager.GetMethod("GetAllRunningApplicationsAsync", BindingFlags.Public | BindingFlags.Static)!
                .Invoke(null, null)!;
            ((Task)request).GetAwaiter().GetResult();
            var rows = ((IEnumerable)request.GetType().GetProperty("Result")!.GetValue(request)!)
                .Cast<object>()
                .Select(context => new
                {
                    applicationId = Get(context, "ApplicationId"),
                    processId = Get(context, "ProcessId"),
                    state = Get(context, "State"),
                    isTerminated = Get(context, "IsTerminated"),
                    isSubApp = Get(context, "IsSubApp")
                })
                .ToArray();

            Console.WriteLine(JsonSerializer.Serialize(new
            {
                query = "ApplicationManager.GetAllRunningApplicationsAsync",
                rows,
                safeForForegroundGate = false,
                limitation = "ApplicationRunningContext.State is app lifecycle state; this API does not establish frontmost/focused window ownership.",
                noMutation = true
            }));
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine(exception);
            return 1;
        }
    }

    private static object? Get(object source, string property) =>
        source.GetType().GetProperty(property, BindingFlags.Public | BindingFlags.Instance)?.GetValue(source);

    private static void InstallResolver() =>
        AssemblyLoadContext.Default.Resolving += (_, name) =>
        {
            foreach (var directory in new[] { "/usr/share/dotnet.tizen/framework/", "/usr/share/dotnet.tizen/tvappapi/" })
            {
                var candidate = Path.Combine(directory, name.Name + ".dll");
                if (File.Exists(candidate))
                    return AssemblyLoadContext.Default.LoadFromAssemblyPath(candidate);
            }
            return null;
        };
}
