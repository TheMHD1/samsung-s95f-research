using System;
using System.Buffers.Binary;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;

internal enum PreflightReason { PathAllowlist,Realpath,CanonicalPath,Open,StatxReturn,StatxMask,RegularMode,FileSize,Read,EndOfFile,IdentityDrift,Hash,ElfValidation,Unexpected }
internal enum PreflightStage { Start,Realpath,CanonicalPath,Open,StatBefore,Mode,Size,Read,EndOfFile,StatAfter,Hash,Elf,RecheckHeld,RecheckOpen,RecheckPath }
internal sealed class PreflightException : Exception
{
    internal readonly PreflightReason Reason;
    internal readonly PreflightStage Stage;
    internal readonly string FileLabel;
    internal PreflightException(PreflightReason reason,PreflightStage stage=PreflightStage.Start,string label="none") {Reason=reason;Stage=stage;FileLabel=label;}
}
internal static class Preflight
{
    internal static void Need(bool ok,PreflightReason reason) {if(!ok)throw new PreflightException(reason);}
    internal static string Label(string p)=>p==Program.Vconf.Path?"vconf-file":"host-fixture";
}
internal static class Native
{
    internal const uint RequiredStatMask=0x3df; // TYPE MODE NLINK UID GID MTIME CTIME INO SIZE; no ATIME/BLOCKS.
    internal static int OpenFlags(Architecture architecture)=>architecture switch {
        Architecture.Arm=>0x80000|0x8000|0x20000, // CLOEXEC|ARM NOFOLLOW|ARM LARGEFILE; RDONLY=0.
        Architecture.X64=>0x80000|0x20000, // CLOEXEC|x64 NOFOLLOW; RDONLY=0.
        _=>throw new InvalidOperationException("unsupported open architecture")};
    internal static int OpenReadOnlyNoFollow(string path)=>open(path,OpenFlags(RuntimeInformation.ProcessArchitecture));
    internal static void ValidateStatMask(byte[] b)=>Preflight.Need((BinaryPrimitives.ReadUInt32LittleEndian(b)&RequiredStatMask)==RequiredStatMask,PreflightReason.StatxMask);

    [DllImport("libc.so.6",SetLastError=true)] internal static extern int open(string path,int flags);
    [DllImport("libc.so.6",SetLastError=true)] internal static extern int close(int fd);
    [DllImport("libc.so.6",SetLastError=true)] internal static extern IntPtr read(int fd,IntPtr data,UIntPtr count);
    [DllImport("libc.so.6",SetLastError=true)] internal static extern IntPtr realpath(string path,IntPtr resolved);
    [DllImport("libc.so.6",SetLastError=true)] internal static extern IntPtr syscall(IntPtr number,IntPtr fd,byte[] empty,IntPtr flags,IntPtr mask,byte[] result);
    [DllImport("libc.so.6")] internal static extern uint alarm(uint seconds);
    [DllImport("libc.so.6")] internal static extern IntPtr signal(int number,IntPtr handler);
    [DllImport("libc.so.6")] internal static extern int sigemptyset(IntPtr set);
    [DllImport("libc.so.6")] internal static extern int sigaddset(IntPtr set,int number);
    [DllImport("libc.so.6")] internal static extern int sigprocmask(int how,IntPtr set,IntPtr old);
    [DllImport("libc.so.6")] internal static extern uint getuid();
    [DllImport("libc.so.6")] internal static extern uint geteuid();
    [DllImport("libdl.so.2")] internal static extern IntPtr dlerror();
    [DllImport("libdl.so.2")] internal static extern IntPtr dlopen(string path,int flags);
    [DllImport("libdl.so.2")] internal static extern IntPtr dlvsym(IntPtr handle,string name,string version);
    [DllImport("libdl.so.2")] internal static extern int dladdr(IntPtr address,IntPtr info);
    [DllImport("libdl.so.2")] internal static extern int dlinfo(IntPtr handle,int request,out IntPtr info);
    internal static uint Pointer32(IntPtr p) {
        ulong n=IntPtr.Size==4?unchecked((uint)p.ToInt32()):unchecked((ulong)p.ToInt64());
        Core.Require(n>0 && n<=uint.MaxValue && (n&3)==0,"ARM32 aligned address"); return (uint)n;
    }
    internal static void Deadline() {
        using Block set=new Block(128); // glibc sigset_t storage on target ARM32
        Core.Require(signal(14,IntPtr.Zero)!=new IntPtr(-1),"SIGALRM default");
        Core.Require(sigemptyset(set.Pointer)==0 && sigaddset(set.Pointer,14)==0 && sigprocmask(1,set.Pointer,IntPtr.Zero)==0,"SIGALRM unblock");
        alarm(25); // SIG_DFL terminates this process; does not undo TA state.
    }
    internal static byte[] Stat(int fd)
    {
        byte[] b=new byte[256];
        int nr=RuntimeInformation.ProcessArchitecture==Architecture.Arm?397:RuntimeInformation.ProcessArchitecture==Architecture.X64?332:-1;
        Core.Require(nr>=0,"statx architecture");
        Preflight.Need(syscall((IntPtr)nr,(IntPtr)fd,new byte[1],(IntPtr)0x1000,(IntPtr)0x7ff,b).ToInt64()==0,PreflightReason.StatxReturn);
        ValidateStatMask(b); return b;
    }
    internal static string Identity(byte[] s)
    {
        // Linux UAPI statx: omit access time, which ordinary reads may change.
        return Convert.ToHexString(s.AsSpan(16,32))+Convert.ToHexString(s.AsSpan(96,48));
    }
}
internal readonly record struct Pin(string Path,int Size,string Hash,string BuildId="");
internal sealed class PinnedFile : IDisposable
{
    internal readonly int Fd;
    internal readonly string Resolved,Identity;
    internal readonly byte[] Data;
    private bool disposed;
    private readonly string label;
    internal PinnedFile(Pin pin,bool hostTest=false)
    {
        label=Preflight.Label(pin.Path); Fd=-1; Data=Array.Empty<byte>(); Resolved="";Identity="";
        PreflightStage stage=PreflightStage.Realpath;
        try {
            using Block name=new Block(4096);
            Preflight.Need(Native.realpath(pin.Path,name.Pointer)!=IntPtr.Zero,PreflightReason.Realpath);
            Resolved=Marshal.PtrToStringUTF8(name.Pointer)??throw new PreflightException(PreflightReason.Realpath);
            stage=PreflightStage.CanonicalPath;
            if(!hostTest) {
                Preflight.Need(Allowed(pin.Path),PreflightReason.PathAllowlist);
                Preflight.Need(Resolved==pin.Path || (pin.Path.StartsWith("/usr/lib/",StringComparison.Ordinal) && Resolved.StartsWith("/usr/lib/",StringComparison.Ordinal)),PreflightReason.CanonicalPath);
            }
            stage=PreflightStage.Open;Fd=Native.OpenReadOnlyNoFollow(Resolved);Preflight.Need(Fd>=0,PreflightReason.Open);
            Data=new byte[pin.Size];stage=PreflightStage.StatBefore;
            byte[] before=Native.Stat(Fd); Identity=Native.Identity(before);
            stage=PreflightStage.Mode;ushort mode=BinaryPrimitives.ReadUInt16LittleEndian(before.AsSpan(28));
            Preflight.Need((mode&0xf000)==0x8000 && (mode&0x12)==0,PreflightReason.RegularMode);
            stage=PreflightStage.Size;Preflight.Need(BinaryPrimitives.ReadUInt64LittleEndian(before.AsSpan(40))==(ulong)pin.Size,PreflightReason.FileSize);
            stage=PreflightStage.Read;GCHandle held=GCHandle.Alloc(Data,GCHandleType.Pinned);
            try {
                int offset=0;
                while(offset<Data.Length) {
                    long n=Native.read(Fd,IntPtr.Add(held.AddrOfPinnedObject(),offset),(UIntPtr)(Data.Length-offset)).ToInt64();
                    Preflight.Need(n>0 && n<=Data.Length-offset,PreflightReason.Read); offset+=(int)n;
                }
                stage=PreflightStage.EndOfFile;using Block extra=new Block(1);
                Preflight.Need(Native.read(Fd,extra.Pointer,(UIntPtr)1).ToInt64()==0,PreflightReason.EndOfFile);
            } finally { held.Free(); }
            stage=PreflightStage.StatAfter;Preflight.Need(Identity==Native.Identity(Native.Stat(Fd)),PreflightReason.IdentityDrift);
            stage=PreflightStage.Hash;Preflight.Need(Core.Hash(Data)==pin.Hash,PreflightReason.Hash);
            stage=PreflightStage.Elf;if(pin.BuildId.Length>0)Preflight.Need(Elf.BuildId(Data)==pin.BuildId,PreflightReason.ElfValidation);
        } catch(Exception e) {
            CryptographicOperations.ZeroMemory(Data);if(Fd>=0)Native.close(Fd);
            throw new PreflightException(e is PreflightException p?p.Reason:stage==PreflightStage.Elf?PreflightReason.ElfValidation:PreflightReason.Unexpected,stage,label);
        }
    }
    private static bool Allowed(string p)=>p==Program.Vconf.Path;
    internal void Recheck() {
        PreflightStage stage=PreflightStage.RecheckHeld;int fd=-1;
        try {
            Preflight.Need(!disposed && Identity==Native.Identity(Native.Stat(Fd)),PreflightReason.IdentityDrift);
            stage=PreflightStage.RecheckOpen;fd=Native.OpenReadOnlyNoFollow(Resolved);Preflight.Need(fd>=0,PreflightReason.Open);
            stage=PreflightStage.RecheckPath;Preflight.Need(Identity==Native.Identity(Native.Stat(fd)),PreflightReason.IdentityDrift);
        } catch(Exception e) {
            throw new PreflightException(e is PreflightException p?p.Reason:PreflightReason.Unexpected,stage,label);
        } finally {if(fd>=0)Native.close(fd);}
    }
    public void Dispose() { if(!disposed) { CryptographicOperations.ZeroMemory(Data); Native.close(Fd); disposed=true; } }
}
internal static class Elf
{
    private static uint U32(byte[] b,int p) { Core.Require(p>=0 && p<=b.Length-4,"ELF bound"); return BinaryPrimitives.ReadUInt32LittleEndian(b.AsSpan(p)); }
    private static ushort U16(byte[] b,int p) { Core.Require(p>=0 && p<=b.Length-2,"ELF bound"); return BinaryPrimitives.ReadUInt16LittleEndian(b.AsSpan(p)); }
    internal static string BuildId(byte[] b)
    {
        Core.Require(b.Length>=52 && b[0]==127 && b[1]==69 && b[2]==76 && b[3]==70 && b[4]==1 && b[5]==1 && U16(b,18)==40 && U32(b,36)==0x05000200,"ELF32 ARM EABI5 softfloat");
        uint ph=U32(b,28); ushort size=U16(b,42),count=U16(b,44); Core.Require(size==32 && count<=128,"ELF phdr");
        for(int i=0;i<count;i++) {
            int p=checked((int)ph+i*size); if(U32(b,p)!=4) continue;
            int at=checked((int)U32(b,p+4)),end=checked(at+(int)U32(b,p+16)); Core.Require(at>=0 && end<=b.Length,"ELF note range");
            while(at<=end-12) {
                int ns=checked((int)U32(b,at)),ds=checked((int)U32(b,at+4)); uint kind=U32(b,at+8); at+=12;
                Core.Require(ns>=0 && ds>=0 && ns<=end-at,"ELF note name"); int desc=checked(at+((ns+3)&~3)); Core.Require(desc<=end && ds<=end-desc,"ELF note desc");
                if(kind==3 && ns==4 && b.AsSpan(at,4).SequenceEqual(new byte[]{71,78,85,0})) return Convert.ToHexString(b.AsSpan(desc,ds)).ToLowerInvariant();
                at=checked(desc+((ds+3)&~3));
            }
        }
        throw new InvalidOperationException("ELF GNU Build ID absent");
    }
}
