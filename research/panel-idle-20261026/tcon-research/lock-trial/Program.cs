using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Threading;

internal static class Program
{
    // These values were decoded from the exact libdeviced build collected from this TV.
    private const int LcdOn = 1;
    private const int GoToStateNow = 2;
    private const int TrialMilliseconds = 180000;
    private const int ResetTimer = 0;
    private const string ExactLibraryPath = "/usr/lib/libdeviced.so.1.0.3";
    private const string ExactLibrarySha256 =
        "ea3ddbe08dbad2eb3d969d0df434be23afe69eb00921a7969191646e2d1bcb1a";

    private static int Main(string[] args)
    {
        if (args.Length != 1 || (args[0] != "query" && args[0] != "trial"))
        {
            Console.Error.WriteLine("usage: S95fDisplayLockTrial.dll query|trial");
            return 2;
        }

        try
        {
            RequireSupportedRuntime();
            RequireAuthorizedUid();
            if (args[0] == "query")
            {
                Print("query", ReadSnapshot());
                return 0;
            }

            return RunTrial();
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine("display-lock helper refused: " + exception.Message);
            return 1;
        }
    }

    private static int RunTrial()
    {
        Print("before", ReadSnapshot());

        int lockStatus = Native.display_lock_state(LcdOn, GoToStateNow, TrialMilliseconds);
        Console.WriteLine("{\"event\":\"lock_result\",\"status\":" + lockStatus
            + ",\"timeout_ms\":" + TrialMilliseconds + "}");
        Console.Out.Flush();

        if (lockStatus != 0)
        {
            Print("after", ReadSnapshot());
            return 1;
        }

        int unlockStatus = int.MinValue;
        try
        {
            // This read is inside finally protection: it cannot strand a successful lock.
            Print("after_lock", ReadSnapshot());
            Console.Out.Flush();
            // No renewal is performed. The OS receives the same 180-second bound.
            Thread.Sleep(TrialMilliseconds);
        }
        finally
        {
            unlockStatus = Native.display_unlock_state(LcdOn, ResetTimer);
            Console.WriteLine("{\"event\":\"unlock_result\",\"status\":" + unlockStatus + "}");
            Print("after", ReadSnapshot());
        }

        return unlockStatus == 0 ? 0 : 1;
    }

    private static Snapshot ReadSnapshot()
    {
        // The exact ABI for device_get_screen_state is a zero-argument read-only query.
        return new Snapshot(Native.device_get_screen_state());
    }

    private static void RequireSupportedRuntime()
    {
        if (IntPtr.Size != 4)
            throw new InvalidOperationException("requires the TV's 32-bit ARM .NET runtime");

        if (!File.Exists(ExactLibraryPath))
            throw new InvalidOperationException("exact libdeviced path is absent: " + ExactLibraryPath);

        string actualHash;
        using (SHA256 sha256 = SHA256.Create())
        using (FileStream stream = File.OpenRead(ExactLibraryPath))
            actualHash = ToHex(sha256.ComputeHash(stream));

        if (!string.Equals(actualHash, ExactLibrarySha256, StringComparison.Ordinal))
            throw new InvalidOperationException("libdeviced exact-build hash mismatch");
    }

    private static void RequireAuthorizedUid()
    {
        uint uid = Native.geteuid();
        if (uid != 0 && uid != 901)
            throw new InvalidOperationException("trial requires euid 0 or 901; current euid is " + uid);
    }

    private static string ToHex(byte[] bytes)
    {
        char[] chars = new char[bytes.Length * 2];
        const string hex = "0123456789abcdef";
        for (int i = 0; i < bytes.Length; i++)
        {
            chars[i * 2] = hex[bytes[i] >> 4];
            chars[(i * 2) + 1] = hex[bytes[i] & 0x0f];
        }
        return new string(chars);
    }

    private static void Print(string eventName, Snapshot snapshot)
    {
        Console.WriteLine("{\"event\":\"" + eventName + "\",\"screen_state\":"
            + snapshot.ScreenState + "}");
    }

    private readonly struct Snapshot
    {
        internal Snapshot(int screenState)
        {
            ScreenState = screenState;
        }

        internal int ScreenState { get; }
    }

    private static class Native
    {
        [DllImport("libdeviced.so.1", CallingConvention = CallingConvention.Cdecl,
            PreserveSig = true, EntryPoint = "display_lock_state")]
        internal static extern int display_lock_state(int state, int flags, int timeoutMilliseconds);

        [DllImport("libdeviced.so.1", CallingConvention = CallingConvention.Cdecl,
            PreserveSig = true, EntryPoint = "display_unlock_state")]
        internal static extern int display_unlock_state(int state, int action);

        [DllImport("libdeviced.so.1", CallingConvention = CallingConvention.Cdecl,
            PreserveSig = true, EntryPoint = "device_get_screen_state")]
        internal static extern int device_get_screen_state();

        [DllImport("libc", CallingConvention = CallingConvention.Cdecl,
            PreserveSig = true, EntryPoint = "geteuid")]
        internal static extern uint geteuid();
    }
}
