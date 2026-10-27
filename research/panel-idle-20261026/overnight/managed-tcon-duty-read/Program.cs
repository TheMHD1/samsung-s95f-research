using System;
using System.Runtime.InteropServices;

// One fixed ARM32 generic-read ioctl for hexadecimal selector 0x128.
// There is no arbitrary command argument, setter, retry, loop, power, PM,
// GPIO, protection, reset, recovery, settings, or network interface.
internal static class Program
{
    private const string Device = "/dev/tztv_tcon";
    private const int OpenReadWrite = 2;
    private const int OpenCloseOnExec = 0x80000;
    private const uint Request = 0xc010749f;
    private const uint Operation = 19;
    private const uint Sentinel = 0xa55a5aa5;
    private const uint CommandHigh = 0x0000f300;
    private const uint CommandLow = 0x00000128;
    private const uint PackagedMaximum = 1023;

    [StructLayout(LayoutKind.Sequential, Pack = 4, Size = 16)]
    private struct TconRequest
    {
        public uint Operation;
        public uint Output;
        public uint CommandHigh;
        public uint CommandLow;
    }

    [DllImport("libc.so.6", EntryPoint = "syscall", SetLastError = true,
        CallingConvention = CallingConvention.Cdecl)]
    private static extern IntPtr Syscall(IntPtr number, IntPtr a1, IntPtr a2,
        IntPtr a3, IntPtr a4, IntPtr a5);
    [DllImport("libc.so.6", SetLastError = true, CallingConvention = CallingConvention.Cdecl)]
    private static extern int open(string path, int flags);
    [DllImport("libc.so.6", SetLastError = true, CallingConvention = CallingConvention.Cdecl)]
    private static extern int ioctl(int fd, uint request, ref TconRequest value);
    [DllImport("libc.so.6", SetLastError = true, CallingConvention = CallingConvention.Cdecl)]
    private static extern int close(int fd);
    [DllImport("libc.so.6", CallingConvention = CallingConvention.Cdecl)]
    private static extern int getpid();
    [DllImport("libc.so.6", CallingConvention = CallingConvention.Cdecl)]
    private static extern uint getuid();
    [DllImport("libc.so.6", CallingConvention = CallingConvention.Cdecl)]
    private static extern uint geteuid();

    private static string Words(TconRequest value) =>
        $"{value.Operation:x8},{value.Output:x8},{value.CommandHigh:x8},{value.CommandLow:x8}";

    private static int Main(string[] args)
    {
        Console.WriteLine("QD_TCON_DUTY_READ_V1");
        Console.WriteLine("ARCH=" + RuntimeInformation.ProcessArchitecture);
        Console.WriteLine("PTR_BYTES=" + IntPtr.Size);
        Console.WriteLine("STRUCT_BYTES=" + Marshal.SizeOf<TconRequest>());
        Console.WriteLine("ENDIAN_LITTLE=" + (BitConverter.IsLittleEndian ? 1 : 0));
        Console.WriteLine("OPERATION_OFFSET=" + Marshal.OffsetOf<TconRequest>(nameof(TconRequest.Operation)));
        Console.WriteLine("OUTPUT_OFFSET=" + Marshal.OffsetOf<TconRequest>(nameof(TconRequest.Output)));
        Console.WriteLine("COMMAND_HIGH_OFFSET=" + Marshal.OffsetOf<TconRequest>(nameof(TconRequest.CommandHigh)));
        Console.WriteLine("COMMAND_LOW_OFFSET=" + Marshal.OffsetOf<TconRequest>(nameof(TconRequest.CommandLow)));
        Console.WriteLine("ARGUMENT_COUNT=" + args.Length);

        if (args.Length != 0)
        {
            Console.WriteLine("REFUSED_ARGUMENTS");
            return 63;
        }
        if (RuntimeInformation.ProcessArchitecture != Architecture.Arm || IntPtr.Size != 4 ||
            Marshal.SizeOf<TconRequest>() != 16 || !BitConverter.IsLittleEndian ||
            Marshal.OffsetOf<TconRequest>(nameof(TconRequest.Operation)).ToInt32() != 0 ||
            Marshal.OffsetOf<TconRequest>(nameof(TconRequest.Output)).ToInt32() != 4 ||
            Marshal.OffsetOf<TconRequest>(nameof(TconRequest.CommandHigh)).ToInt32() != 8 ||
            Marshal.OffsetOf<TconRequest>(nameof(TconRequest.CommandLow)).ToInt32() != 12)
        {
            Console.WriteLine("REFUSED_ARCH_ABI");
            return 64;
        }

        uint uid = getuid();
        uint euid = geteuid();
        int libcPid = getpid();
        long rawPid = Syscall(new IntPtr(20), IntPtr.Zero, IntPtr.Zero,
            IntPtr.Zero, IntPtr.Zero, IntPtr.Zero).ToInt64();
        Console.WriteLine("UID=" + uid);
        Console.WriteLine("EUID=" + euid);
        Console.WriteLine("PID_LIBC=" + libcPid);
        Console.WriteLine("PID_SYSCALL=" + rawPid);
        if (uid != 0 || euid != 0)
        {
            Console.WriteLine("REFUSED_UID");
            return 65;
        }
        if (libcPid <= 0 || rawPid != libcPid)
        {
            Console.WriteLine("REFUSED_ARM_EABI");
            return 66;
        }

        TconRequest value = new TconRequest {
            Operation = Operation,
            Output = Sentinel,
            CommandHigh = CommandHigh,
            CommandLow = CommandLow
        };
        Console.WriteLine("DEVICE=" + Device);
        Console.WriteLine($"OPEN_FLAGS=0x{(OpenReadWrite | OpenCloseOnExec):x}");
        Console.WriteLine($"IOCTL_REQUEST=0x{Request:x8}");
        Console.WriteLine("COMMAND_U64=0x0000f30000000128");
        Console.WriteLine("WIRE_REQUEST_HEX=f30000000128");
        Console.WriteLine("EXPECTED_RESPONSE_BYTES=4");
        Console.WriteLine("PAYLOAD_BEFORE=" + Words(value));

        Marshal.SetLastPInvokeError(0);
        int fd = open(Device, OpenReadWrite | OpenCloseOnExec);
        int openErrno = Marshal.GetLastWin32Error();
        Console.WriteLine("OPEN_RETURN=" + fd);
        Console.WriteLine("OPEN_ERRNO=" + openErrno);
        if (fd < 0)
        {
            Console.WriteLine("OPEN_FAILED");
            return 67;
        }

        int ioctlReturn;
        int ioctlErrno;
        int closeReturn;
        int closeErrno;
        try
        {
            Marshal.SetLastPInvokeError(0);
            ioctlReturn = ioctl(fd, Request, ref value);
            ioctlErrno = Marshal.GetLastWin32Error();
        }
        finally
        {
            Marshal.SetLastPInvokeError(0);
            closeReturn = close(fd);
            closeErrno = Marshal.GetLastWin32Error();
        }

        Console.WriteLine("IOCTL_RETURN=" + ioctlReturn);
        Console.WriteLine("IOCTL_ERRNO=" + ioctlErrno);
        Console.WriteLine("PAYLOAD_AFTER=" + Words(value));
        Console.WriteLine("CLOSE_RETURN=" + closeReturn);
        Console.WriteLine("CLOSE_ERRNO=" + closeErrno);

        if (value.Operation != Operation || value.CommandHigh != CommandHigh ||
            value.CommandLow != CommandLow)
        {
            Console.WriteLine("REFUSED_ENVELOPE_MUTATION");
            return 70;
        }
        if (ioctlReturn != 0)
        {
            Console.WriteLine("IOCTL_FAILED_OR_NONZERO");
            return 69;
        }
        if (value.Output == Sentinel)
        {
            Console.WriteLine("NO_FRESH_KERNEL_OUTPUT_DEMONSTRATED");
            return 71;
        }
        if (closeReturn != 0)
        {
            Console.WriteLine("FRESH_KERNEL_OUTPUT_UNCLASSIFIED_CLOSE_FAILED");
            return 68;
        }

        Console.WriteLine("CLASSIFICATION=kernel_output_written");
        Console.WriteLine($"RESULT_HEX=0x{value.Output:x8}");
        Console.WriteLine("RESULT_U32=" + value.Output);
        Console.WriteLine("PHYSICAL_BRIGHTNESS_INFERRED=0");
        if (value.Output > PackagedMaximum)
        {
            Console.WriteLine("PACKAGED_RANGE_0_1023=0");
            Console.WriteLine("PROFILE_RANGE_CLASSIFICATION=incompatible_profile_range");
            return 72;
        }

        Console.WriteLine("PACKAGED_RANGE_0_1023=1");
        Console.WriteLine("PROFILE_RANGE_CLASSIFICATION=within_packaged_low10_range");
        Console.WriteLine("READ_COMPLETE");
        return 0;
    }
}
