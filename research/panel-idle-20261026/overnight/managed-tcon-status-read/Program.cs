using System;
using System.Runtime.InteropServices;

// One ARM32 read-status ioctl. This helper has no setter, retry, loop, power,
// PM, tracing, logging, or recovery interface.
internal static class Program
{
    private const string Device = "/dev/tztv_tcon";
    private const int OpenReadWrite = 2;
    private const int OpenCloseOnExec = 0x80000;
    private const uint Request = 0xc010749f;
    private const uint Operation = 0x1f;
    private const uint Sentinel = 0xa55a5aa5;

    [StructLayout(LayoutKind.Sequential, Pack = 4, Size = 16)]
    private struct TconRequest
    {
        public uint Operation;
        public uint Output;
        public uint Opaque2;
        public uint Opaque3;
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
        $"{value.Operation:x8},{value.Output:x8},{value.Opaque2:x8},{value.Opaque3:x8}";

    private static int Main()
    {
        Console.WriteLine("QD_TCON_STATUS_READ_V1");
        Console.WriteLine("ARCH=" + RuntimeInformation.ProcessArchitecture);
        Console.WriteLine("PTR_BYTES=" + IntPtr.Size);
        Console.WriteLine("STRUCT_BYTES=" + Marshal.SizeOf<TconRequest>());
        Console.WriteLine("ENDIAN_LITTLE=" + (BitConverter.IsLittleEndian ? 1 : 0));
        Console.WriteLine("OUTPUT_OFFSET=" + Marshal.OffsetOf<TconRequest>(nameof(TconRequest.Output)));
        if (RuntimeInformation.ProcessArchitecture != Architecture.Arm || IntPtr.Size != 4 ||
            Marshal.SizeOf<TconRequest>() != 16 || !BitConverter.IsLittleEndian ||
            Marshal.OffsetOf<TconRequest>(nameof(TconRequest.Output)).ToInt32() != 4)
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
            Operation = Operation, Output = Sentinel, Opaque2 = 0, Opaque3 = 0
        };
        Console.WriteLine("DEVICE=" + Device);
        Console.WriteLine($"OPEN_FLAGS=0x{(OpenReadWrite | OpenCloseOnExec):x}");
        Console.WriteLine($"IOCTL_REQUEST=0x{Request:x8}");
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

        if (ioctlReturn != 0)
        {
            Console.WriteLine("IOCTL_FAILED_OR_NONZERO");
            return 69;
        }
        if (value.Operation != Operation || value.Opaque2 != 0 || value.Opaque3 != 0)
        {
            Console.WriteLine("REFUSED_ENVELOPE_MUTATION");
            return 70;
        }
        if (value.Output == Sentinel)
        {
            Console.WriteLine("NO_FRESH_KERNEL_OUTPUT_DEMONSTRATED");
            return 71;
        }

        Console.WriteLine("CLASSIFICATION=kernel_output_written");
        Console.WriteLine($"TCON_STATUS_HEX=0x{value.Output:x8}");
        if (closeReturn != 0)
        {
            Console.WriteLine("CLOSE_FAILED");
            return 68;
        }
        Console.WriteLine("READ_COMPLETE");
        return 0;
    }
}
