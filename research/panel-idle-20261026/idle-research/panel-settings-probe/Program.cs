using System.Reflection;
using System.Runtime.InteropServices;
using System.Runtime.Loader;
using System.Text.Json;

// Query only. There is deliberately no SetItemValue reference in this source.
internal static class Program
{
    [DllImport("libc")] private static extern uint getuid();
    private const string Build = "BUILD_ID=T-RSMFAKUC-0090-REL-202607141953";
    private static readonly string[] Items =
    {
        // Full static-image protection / screensaver candidates in the audited Energy schema.
        "screen-saver", "screen-saver-aot",
        // Picture-protection candidates. Unknown IDs return Read=false without changing state.
        "luminance-detection", "adjust-logo-brightness", "logo-brightness",
        // Energy/ambient controls that can resemble a black-panel event but are separate paths.
        "brightness-optimization", "auto-screen-dim", "energy-saving-solution",
        "motion-lighting", "auto-power-off", "sleeptimer", "offtimer1-setup",
        // Read-only contextual picture controls; they are not modified by this probe.
        "picture-mode", "eye-comfort-mode"
    };

    private static Type Api = null!;

    private sealed record Item(string Id, bool Read, bool Visible, bool Enabled,
        string Value, string Display, string[] Choices);

    private static object Call(string name, params object?[] args) =>
        Api.GetMethods(BindingFlags.Public | BindingFlags.Static)
            .Single(method => method.Name == name && method.GetParameters().Length == args.Length)
            .Invoke(null, args)!;

    private static Item Query(string id)
    {
        object?[] value = { id, null, null };
        bool read = (bool)Call("GetItemValue", value)!;
        object?[] visible = { id, false };
        bool visibleRead = (bool)Call("GetItemVisible", visible)!;
        object?[] enabled = { id, false };
        bool enabledRead = (bool)Call("GetItemEnable", enabled)!;
        object?[] list = { id, null };
        bool listRead = (bool)Call("GetItemDataList", list)!;
        return new Item(id, read, visibleRead && (bool)visible[1]!, enabledRead && (bool)enabled[1]!,
            value[2] as string ?? "", value[1] as string ?? "",
            listRead && list[1] is List<string> choices ? choices.ToArray() : Array.Empty<string>());
    }

    private static int Main(string[] args)
    {
        try
        {
            if (args.Length != 1 || args[0] != "query")
                throw new ArgumentException("Use query");
            if (getuid() != 901 || IntPtr.Size != 4 || !File.ReadLines("/etc/tizen-release").Contains(Build))
                throw new InvalidOperationException("SDK/exact-build guard failed");

            AssemblyLoadContext.Default.Resolving += (_, name) =>
            {
                foreach (string directory in new[] { "/usr/share/dotnet.tizen/framework/", "/usr/share/dotnet.tizen/tvappapi/" })
                {
                    string candidate = Path.Combine(directory, name.Name + ".dll");
                    if (File.Exists(candidate)) return AssemblyLoadContext.Default.LoadFromAssemblyPath(candidate);
                }
                return null;
            };
            Api = Assembly.LoadFrom("/usr/share/dotnet.tizen/framework/Tizen.TV.Service.Settings.dll")
                .GetType("Tizen.TV.Service.Settings.Settings", throwOnError: true)!;

            Console.WriteLine(JsonSerializer.Serialize(new
            {
                command = "query",
                queryOnly = true,
                settersPresent = false,
                items = Items.Select(Query),
                note = "Read=false means the native settings API did not expose that candidate ID; it is not evidence of Off."
            }));
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine(exception);
            return 1;
        }
    }
}
