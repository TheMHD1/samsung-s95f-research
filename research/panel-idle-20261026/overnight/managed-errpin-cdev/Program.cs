using System;
using System.Runtime.InteropServices;

// Default mode does only GPIO-chip and line metadata ioctls.  --input-once is
// intentionally separate: one input line-handle request and one value GET;
// there is no SET, retry, loop, output flag, or active-low flag anywhere.
internal static unsafe class Program
{
    const string Device = "/dev/gpiochip15";
    const int O_RDONLY = 0, O_CLOEXEC = 0x80000;
    const uint CHIPINFO = 0x8044b401, LINEINFO = 0xc048b402;
    const uint GET_HANDLE = 0xc16cb403, GET_VALUES = 0xc040b408;
    const uint INPUT = 1; const uint Offset = 5; const uint Sentinel = 0xa5;

    [StructLayout(LayoutKind.Sequential, Pack = 4, Size = 68)]
    struct ChipInfo { public fixed byte name[32]; public fixed byte label[32]; public uint lines; }
    [StructLayout(LayoutKind.Sequential, Pack = 4, Size = 72)]
    struct LineInfo { public uint line_offset; public uint flags; public fixed byte name[32]; public fixed byte consumer[32]; }
    [StructLayout(LayoutKind.Sequential, Pack = 4, Size = 364)]
    struct HandleRequest { public fixed uint offsets[64]; public uint flags; public fixed byte defaults[64]; public fixed byte consumer_label[32]; public uint lines; public int fd; }
    [StructLayout(LayoutKind.Sequential, Pack = 4, Size = 64)]
    struct HandleData { public fixed byte values[64]; }

    [DllImport("libc.so.6", SetLastError = true)] static extern int open(string p, int f);
    [DllImport("libc.so.6", SetLastError = true)] static extern int ioctl(int fd, uint request, ref ChipInfo v);
    [DllImport("libc.so.6", SetLastError = true)] static extern int ioctl(int fd, uint request, ref LineInfo v);
    [DllImport("libc.so.6", SetLastError = true)] static extern int ioctl(int fd, uint request, ref HandleRequest v);
    [DllImport("libc.so.6", SetLastError = true)] static extern int ioctl(int fd, uint request, ref HandleData v);
    [DllImport("libc.so.6", SetLastError = true)] static extern int close(int fd);
    [DllImport("libc.so.6")] static extern uint getuid();
    [DllImport("libc.so.6")] static extern uint geteuid();

    static void Out(string k, object v) => Console.WriteLine(k + "=" + v);
    static string C(byte* p, int n) { int z = 0; while (z < n && p[z] != 0) z++; for (int i = z; i < n; i++) if (p[i] != 0) throw new InvalidOperationException("nonzero C tail"); return System.Text.Encoding.ASCII.GetString(p, z); }
    static bool Is(HandleData d, int index, byte value) => d.values[index] == value;

    static int Main(string[] args)
    {
        bool once = args.Length == 1 && args[0] == "--input-once";
        if (!(args.Length == 0 || once)) { Console.WriteLine("REFUSED_ARGUMENTS"); return 64; }
        Out("GPIO_CDEV_MODE", once ? "input_once" : "metadata_only");
        Out("ARCH", RuntimeInformation.ProcessArchitecture); Out("PTR_BYTES", IntPtr.Size);
        Out("ENDIAN_LITTLE", BitConverter.IsLittleEndian ? 1 : 0);
        Out("CHIPINFO_BYTES", Marshal.SizeOf<ChipInfo>()); Out("LINEINFO_BYTES", Marshal.SizeOf<LineInfo>());
        Out("HANDLE_REQUEST_BYTES", Marshal.SizeOf<HandleRequest>()); Out("HANDLE_DATA_BYTES", Marshal.SizeOf<HandleData>());
        if (RuntimeInformation.ProcessArchitecture != Architecture.Arm || IntPtr.Size != 4 || !BitConverter.IsLittleEndian ||
            Marshal.SizeOf<ChipInfo>() != 68 || Marshal.SizeOf<LineInfo>() != 72 || Marshal.SizeOf<HandleRequest>() != 364 || Marshal.SizeOf<HandleData>() != 64 ||
            Marshal.OffsetOf<LineInfo>(nameof(LineInfo.flags)).ToInt32() != 4 || Marshal.OffsetOf<HandleRequest>(nameof(HandleRequest.flags)).ToInt32() != 256 ||
            Marshal.OffsetOf<HandleRequest>(nameof(HandleRequest.lines)).ToInt32() != 356 || Marshal.OffsetOf<HandleRequest>(nameof(HandleRequest.fd)).ToInt32() != 360)
        { Console.WriteLine("REFUSED_ABI"); return 65; }
        Out("UID", getuid()); Out("EUID", geteuid()); if (getuid() != 0 || geteuid() != 0) { Console.WriteLine("REFUSED_UID"); return 66; }
        int chip = open(Device, O_RDONLY | O_CLOEXEC); int oe = Marshal.GetLastWin32Error(); Out("CHIP_OPEN_RETURN", chip); Out("CHIP_OPEN_ERRNO", oe);
        if (chip < 0) return 67;
        int rc = 0, re = 0, hr = -1, he = 0, handle = -1;
        try {
            ChipInfo ci = default; rc = ioctl(chip, CHIPINFO, ref ci); re = Marshal.GetLastWin32Error(); Out("CHIPINFO_RETURN", rc); Out("CHIPINFO_ERRNO", re); if (rc != 0) return 68;
            string chipName; string chipLabel; { byte* n = ci.name; byte* l = ci.label; chipName=C(n,32); chipLabel=C(l,32); Out("CHIP_NAME", chipName); Out("CHIP_LABEL", chipLabel); } Out("CHIP_LINES", ci.lines);
            if (chipName != "gpiochip15" || chipLabel != "gpio15" || ci.lines != 8) { Console.WriteLine("REFUSED_CHIP_IDENTITY"); return 69; }
            LineInfo li = default; li.line_offset = Offset; rc = ioctl(chip, LINEINFO, ref li); re = Marshal.GetLastWin32Error(); Out("LINEINFO_RETURN", rc); Out("LINEINFO_ERRNO", re); if (rc != 0) return 70;
            string consumer; { byte* n = li.name; byte* c = li.consumer; Out("LINE_NAME", C(n,32)); consumer=C(c,32); Out("LINE_CONSUMER", consumer); }
            Out("LINE_OFFSET", li.line_offset); Out("LINE_FLAGS", "0x" + li.flags.ToString("x8"));
            if (li.line_offset != Offset || li.flags != 0 || consumer != "") { Console.WriteLine("REFUSED_LINE_STATE"); return 71; }
            if (!once) { Console.WriteLine("METADATA_COMPLETE"); return 0; }
            HandleRequest h = default; h.offsets[0] = Offset; h.flags = INPUT; h.lines = 1; h.fd = -1;
            byte[] label = System.Text.Encoding.ASCII.GetBytes("researcher-errdet"); for (int i=0;i<label.Length;i++) h.consumer_label[i]=label[i];
            hr = ioctl(chip, GET_HANDLE, ref h); he = Marshal.GetLastWin32Error(); Out("HANDLE_RETURN", hr); Out("HANDLE_ERRNO", he); Out("HANDLE_FLAGS", "0x" + h.flags.ToString("x8")); Out("HANDLE_LINES", h.lines); Out("HANDLE_FD", h.fd);
            handle = h.fd;
            if (hr != 0 || handle < 0 || h.flags != INPUT || h.lines != 1) return 72;
            HandleData d = default; for (int i=0;i<64;i++) d.values[i]=(byte)Sentinel;
            int vr = ioctl(handle, GET_VALUES, ref d); int ve = Marshal.GetLastWin32Error(); Out("GET_RETURN", vr); Out("GET_ERRNO", ve);
            bool tail = true; for (int i=1;i<64;i++) tail &= Is(d,i,0); Out("VALUE0", Is(d,0,0) ? 0 : Is(d,0,1) ? 1 : 255); Out("VALUE_TAIL_ZERO", tail ? 1 : 0);
            if (vr != 0 || (!Is(d,0,0) && !Is(d,0,1)) || !tail) return 73;
            Console.WriteLine("INPUT_ONCE_COMPLETE"); return 0;
        } finally {
            if (handle >= 0) { int hc = close(handle); Out("HANDLE_CLOSE_RETURN", hc); Out("HANDLE_CLOSE_ERRNO", Marshal.GetLastWin32Error()); }
            int chipClose = close(chip); Out("CHIP_CLOSE_RETURN", chipClose); Out("CHIP_CLOSE_ERRNO", Marshal.GetLastWin32Error());
        }
    }
}
