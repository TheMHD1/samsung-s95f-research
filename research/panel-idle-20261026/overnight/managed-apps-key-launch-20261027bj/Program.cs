using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text.Json;
using Tizen.Applications;

internal static class Program
{
    private const string Schema = "managed-apps-key-launch-v1";
    private const string ExpectedBoot = "00000000-0000-4000-8000-000000000000";
    private const string ApplicationId = "com.samsung.tv.csfs";
    private const string ExtraKey = "switch_page";
    private const string AppsPage = "d/apps.tab";
    private const string EntryPointKey = "entry_point";
    private const string AppsKey = "apps_key";

    private static readonly JsonSerializerOptions JsonOptions = new();

    private sealed record RequestRecord(
        string application_id,
        string switch_page_key,
        string switch_page_value,
        string entry_point_key,
        string entry_point_value,
        bool operation_set,
        bool no_raise_window_set);

    private sealed record ExceptionRecord(string phase, string type, string message);

    private sealed record ResultRecord(
        string schema,
        string mode,
        RequestRecord request,
        string expected_boot_id,
        string? boot_id_before,
        string? boot_id_after,
        bool boot_matched_before,
        bool boot_matched_after,
        string? uptime_before,
        string? uptime_after,
        string architecture,
        int pointer_bytes,
        bool little_endian,
        bool abi_accepted,
        bool request_constructed,
        bool send_attempted,
        bool send_returned,
        bool handle_disposed,
        ExceptionRecord? exception,
        int target_operations,
        bool physical_picture_observed,
        bool execution_confirmed);

    private static string Clip(string value) => value.Length <= 512 ? value : value[..512];

    private static string? ReadTrimmed(string path, ref ExceptionRecord? error, string phase)
    {
        try
        {
            return File.ReadAllText(path).Trim();
        }
        catch (Exception ex)
        {
            error ??= new ExceptionRecord(phase, ex.GetType().FullName ?? ex.GetType().Name,
                                          Clip(ex.Message));
            return null;
        }
    }

    private static void Emit(ResultRecord result) =>
        Console.WriteLine(JsonSerializer.Serialize(result, JsonOptions));

    private static int DryRun()
    {
        Console.WriteLine(JsonSerializer.Serialize(new
        {
            schema = "managed-apps-key-launch-dry-v1",
            dry_run = true,
            target_operations = 0,
            application_id = ApplicationId,
            request = new { application_id = ApplicationId, switch_page = AppsPage,
                            entry_point = AppsKey },
            operation_set = false,
            no_raise_window_set = false,
            retries = 0,
            physical_picture_observed = false,
            execution_confirmed = false
        }));
        return 0;
    }

    private static int Execute()
    {
        RequestRecord requestRecord = new(ApplicationId, ExtraKey, AppsPage,
                                          EntryPointKey, AppsKey, false, false);
        string architecture = RuntimeInformation.ProcessArchitecture.ToString();
        bool abiAccepted = RuntimeInformation.ProcessArchitecture == Architecture.Arm &&
                           IntPtr.Size == 4 && BitConverter.IsLittleEndian;
        ExceptionRecord? error = null;
        string? bootBefore = ReadTrimmed("/proc/sys/kernel/random/boot_id", ref error, "boot-before");
        string? uptimeBefore = ReadTrimmed("/proc/uptime", ref error, "uptime-before");
        bool bootMatchedBefore = bootBefore == ExpectedBoot;
        bool requestConstructed = false;
        bool sendAttempted = false;
        bool sendReturned = false;
        bool handleDisposed = false;
        int operations = 0;

        // All target and current-boot checks occur before AppControl construction.
        if (error is null && abiAccepted && bootMatchedBefore)
        {
            SafeAppControlHandle? safeHandle = null;
            try
            {
                AppControl appControl = new();
                requestConstructed = true;
                safeHandle = appControl.SafeAppControlHandle;
                appControl.ApplicationId = ApplicationId;
                appControl.ExtraData.Add(ExtraKey, AppsPage);
                appControl.ExtraData.Add(EntryPointKey, AppsKey);
                sendAttempted = true;
                operations = 1;
                AppControl.SendLaunchRequest(appControl);
                sendReturned = true;
            }
            catch (Exception ex)
            {
                error = new ExceptionRecord(sendAttempted ? "send" : "construct-request",
                                            ex.GetType().FullName ?? ex.GetType().Name,
                                            Clip(ex.Message));
            }
            finally
            {
                if (safeHandle is not null)
                {
                    try
                    {
                        safeHandle.Dispose();
                        handleDisposed = true;
                    }
                    catch (Exception ex)
                    {
                        error ??= new ExceptionRecord("dispose-handle",
                                                     ex.GetType().FullName ?? ex.GetType().Name,
                                                     Clip(ex.Message));
                    }
                }
            }
        }
        else if (error is null && !abiAccepted)
        {
            error = new ExceptionRecord("preflight", "AbiRefusal", "Expected little-endian ARM32 process");
        }
        else if (error is null)
        {
            error = new ExceptionRecord("preflight", "BootRefusal", "Boot identifier differs from reviewed boot");
        }

        string? bootAfter = ReadTrimmed("/proc/sys/kernel/random/boot_id", ref error, "boot-after");
        string? uptimeAfter = ReadTrimmed("/proc/uptime", ref error, "uptime-after");
        bool bootMatchedAfter = bootAfter == ExpectedBoot;
        Emit(new ResultRecord(
            Schema, "apps-key", requestRecord, ExpectedBoot, bootBefore, bootAfter,
            bootMatchedBefore, bootMatchedAfter, uptimeBefore, uptimeAfter,
            architecture, IntPtr.Size, BitConverter.IsLittleEndian, abiAccepted,
            requestConstructed, sendAttempted, sendReturned, handleDisposed, error,
            operations, false, false));

        if (!abiAccepted) return 64;
        if (!bootMatchedBefore || !bootMatchedAfter) return 65;
        // AppControl exceptions are fully represented in the one JSON outcome. Returning
        // zero preserves that outcome through the strict root transport without retry.
        return 0;
    }

    private static int Main(string[] args)
    {
        if (args.Length == 0) return DryRun();
        if (args.Length != 1) return 63;
        return args[0] switch
        {
            "--apps-key" => Execute(),
            _ => 63
        };
    }
}
