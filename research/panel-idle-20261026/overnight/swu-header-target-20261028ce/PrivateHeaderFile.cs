using System;
using System.Buffers.Binary;
using System.Runtime.InteropServices;

// This is private quarantine output, never a firmware write or public export.
internal static class PrivateHeaderFile
{
    [DllImport("libc.so.6",EntryPoint="open",SetLastError=true)]
    private static extern int Create(string path,int flags,uint mode);
    [DllImport("libc.so.6",SetLastError=true)]
    private static extern IntPtr write(int fd,IntPtr bytes,UIntPtr count);
    [DllImport("libc.so.6",SetLastError=true)]
    private static extern int fsync(int fd);

    internal static int CreateFlags(Architecture architecture) =>
        Native.OpenFlags(architecture)|1|0x40|0x80; // WRONLY|CREAT|EXCL, retain NOFOLLOW/CLOEXEC.

    internal static void SaveRaw(ReadOnlySpan<byte> raw) => SaveAt(Program.OutputPath,raw);

    // Only the host self-test calls the variable-path implementation directly.
    internal static void SaveHostFixture(string path,ReadOnlySpan<byte> raw)
    {
        Core.Require(RuntimeInformation.ProcessArchitecture==Architecture.X64,"host fixture only");
        SaveAt(path,raw);
    }

    private static void CheckStat(byte[] stat,ulong size)
    {
        ushort mode=BinaryPrimitives.ReadUInt16LittleEndian(stat.AsSpan(28));
        Core.Require((mode&0xf000)==0x8000 && (mode&0xfff)==0x180,"private output regular0600");
        Core.Require(BinaryPrimitives.ReadUInt32LittleEndian(stat.AsSpan(16))==1,"private output link count");
        Core.Require(BinaryPrimitives.ReadUInt32LittleEndian(stat.AsSpan(20))==Native.geteuid(),"private output uid");
        Core.Require(BinaryPrimitives.ReadUInt64LittleEndian(stat.AsSpan(40))==size,"private output extent");
    }

    private static void SaveAt(string path,ReadOnlySpan<byte> raw)
    {
        Core.Require(raw.Length==Core.Cipher,"fixed private output count");
        int fd=Create(path,CreateFlags(RuntimeInformation.ProcessArchitecture),0x180);
        Core.Require(fd>=0,"exclusive private output create");
        try {
            CheckStat(Native.Stat(fd),0);
            using Block snapshot=new Block(Core.Cipher);
            raw.CopyTo(snapshot.Bytes);
            // One bounded write. A short/error result retains an unaccepted
            // private partial file; it does not cause a write or TEEC retry.
            Core.Require(write(fd,snapshot.Pointer,(UIntPtr)Core.Cipher).ToInt64()==Core.Cipher,"private output write count");
            Core.Require(fsync(fd)==0,"private output sync");
            CheckStat(Native.Stat(fd),Core.Cipher);
            int closing=fd;fd=-1;
            Core.Require(Native.close(closing)==0,"private output close");
        } finally { if(fd>=0)Native.close(fd); }
    }
}
