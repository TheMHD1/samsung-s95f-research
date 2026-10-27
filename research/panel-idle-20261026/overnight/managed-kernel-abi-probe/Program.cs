using System;
using System.IO;
using System.Runtime.InteropServices;

// Linux ARM EABI userspace only. Invalid requests cannot load BPF, allocate a
// map, attach a hook, or open a perf event. No output, display, or driver APIs.
internal static class Program
{
    [DllImport("libc.so.6", EntryPoint = "syscall", SetLastError = true,
        CallingConvention = CallingConvention.Cdecl)]
    private static extern IntPtr Syscall(IntPtr number, IntPtr a1, IntPtr a2,
        IntPtr a3, IntPtr a4, IntPtr a5);
    [DllImport("libc.so.6", CallingConvention = CallingConvention.Cdecl)]
    private static extern int getpid();
    [DllImport("libc.so.6", CallingConvention = CallingConvention.Cdecl)]
    private static extern uint getuid();
    [DllImport("libc.so.6", CallingConvention = CallingConvention.Cdecl)]
    private static extern uint geteuid();

    private static int Main()
    {
        Console.WriteLine("QDKABI_MANAGED_ARM_V1");
        Console.WriteLine("ARCH=" + RuntimeInformation.ProcessArchitecture);
        Console.WriteLine("PTR_BYTES=" + IntPtr.Size);
        if (IntPtr.Size != 4 || RuntimeInformation.ProcessArchitecture != Architecture.Arm)
        {
            Console.WriteLine("REFUSED_ARCH");
            return 64;
        }
        if (getuid() != 0 || geteuid() != 0)
        {
            Console.WriteLine("REFUSED_UID");
            return 65;
        }
        bool unfiltered = false;
        foreach (string line in File.ReadAllLines("/proc/self/status"))
        {
            if (line.StartsWith("Uid:") || line.StartsWith("Gid:") ||
                line.StartsWith("CapEff:") || line.StartsWith("NoNewPrivs:") ||
                line.StartsWith("Seccomp:"))
                Console.WriteLine(line);
            if (line.StartsWith("Seccomp:") && line.Substring(8).Trim() == "0")
                unfiltered = true;
        }
        if (!unfiltered)
        {
            Console.WriteLine("REFUSED_SECCOMP");
            return 66;
        }
        IntPtr zero = IntPtr.Zero;
        int libcPid = getpid();
        long syscallPid = Syscall(new IntPtr(20), zero, zero, zero, zero, zero).ToInt64();
        Console.WriteLine("PID_LIBC=" + libcPid);
        Console.WriteLine("PID_SYSCALL=" + syscallPid);
        if (libcPid <= 0 || syscallPid != libcPid)
        {
            Console.WriteLine("REFUSED_ABI");
            return 67;
        }
        // ARM EABI __NR_bpf=386; command=-1, attr=NULL, size=0.
        long bpf = Syscall(new IntPtr(386), new IntPtr(-1), zero, zero, zero, zero).ToInt64();
        int bpfErrno = Marshal.GetLastWin32Error();
        Console.WriteLine("BPF_RETURN=" + bpf);
        Console.WriteLine("BPF_ERRNO=" + bpfErrno);
        if (bpf != -1)
        {
            Console.WriteLine("UNEXPECTED_BPF_RETURN");
            return 68;
        }
        // ARM EABI __NR_perf_event_open=364; attr=NULL, pid=0, cpu=-1,
        // group_fd=-1, flags=0. No valid attribute buffer or event requested.
        long perf = Syscall(new IntPtr(364), zero, zero, new IntPtr(-1), new IntPtr(-1), zero).ToInt64();
        int perfErrno = Marshal.GetLastWin32Error();
        Console.WriteLine("PERF_RETURN=" + perf);
        Console.WriteLine("PERF_ERRNO=" + perfErrno);
        if (perf != -1)
        {
            Console.WriteLine("UNEXPECTED_PERF_RETURN");
            return 69;
        }
        Console.WriteLine("PROBE_COMPLETE");
        return 0;
    }
}
