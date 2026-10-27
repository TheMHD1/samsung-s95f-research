using System;
using System.Buffers.Binary;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;

internal static class Native
{
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
        Core.Require(syscall((IntPtr)nr,(IntPtr)fd,new byte[1],(IntPtr)0x1000,(IntPtr)0x7ff,b).ToInt64()==0,"statx failed");
        Core.Require((BinaryPrimitives.ReadUInt32LittleEndian(b)&0x7ff)==0x7ff,"statx mask"); return b;
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
    internal PinnedFile(Pin pin,bool hostTest=false)
    {
        using Block name=new Block(4096);
        Core.Require(Native.realpath(pin.Path,name.Pointer)!=IntPtr.Zero,"realpath failed");
        Resolved=Marshal.PtrToStringUTF8(name.Pointer)??throw new InvalidOperationException("realpath string");
        if(!hostTest) {
            Core.Require(Allowed(pin.Path),"path allowlist");
            Core.Require(Resolved==pin.Path || (pin.Path.StartsWith("/usr/lib/",StringComparison.Ordinal) && Resolved.StartsWith("/usr/lib/",StringComparison.Ordinal)),"canonical allowlist");
        }
        Fd=Native.open(Resolved,0x80000|0x20000); // O_RDONLY|O_CLOEXEC|O_NOFOLLOW
        Core.Require(Fd>=0,"open failed"); Data=new byte[pin.Size];
        try {
            byte[] before=Native.Stat(Fd); Identity=Native.Identity(before);
            ushort mode=BinaryPrimitives.ReadUInt16LittleEndian(before.AsSpan(28));
            Core.Require((mode&0xf000)==0x8000 && (mode&0x12)==0,"regular non-group/other-writable file");
            Core.Require(BinaryPrimitives.ReadUInt64LittleEndian(before.AsSpan(40))==(ulong)pin.Size,"file size");
            GCHandle held=GCHandle.Alloc(Data,GCHandleType.Pinned);
            try {
                int offset=0;
                while(offset<Data.Length) {
                    long n=Native.read(Fd,IntPtr.Add(held.AddrOfPinnedObject(),offset),(UIntPtr)(Data.Length-offset)).ToInt64();
                    Core.Require(n>0 && n<=Data.Length-offset,"complete read"); offset+=(int)n;
                }
                using Block extra=new Block(1);
                Core.Require(Native.read(Fd,extra.Pointer,(UIntPtr)1).ToInt64()==0,"EOF");
            } finally { held.Free(); }
            Core.Require(Identity==Native.Identity(Native.Stat(Fd)),"file identity drift");
            Core.Require(Core.Hash(Data)==pin.Hash,"file hash");
            if(pin.BuildId.Length>0) Core.Require(Elf.BuildId(Data)==pin.BuildId,"ELF Build ID");
        } catch { CryptographicOperations.ZeroMemory(Data); Native.close(Fd); throw; }
    }
    private static bool Allowed(string p) => p==Program.EnvelopePath || p==Program.BlobPath ||
        p=="/usr/lib/libteec.so" || p=="/usr/lib/libteec_trustware.so" || p=="/usr/lib/libteec_trustware_common.so" || p=="/usr/lib/libvconf.so.0";
    internal void Recheck() {
        Core.Require(!disposed && Identity==Native.Identity(Native.Stat(Fd)),"held file drift");
        int fd=Native.open(Resolved,0x80000|0x20000); Core.Require(fd>=0,"path disappeared");
        try { Core.Require(Identity==Native.Identity(Native.Stat(fd)),"path replacement"); } finally { Native.close(fd); }
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
internal sealed class Binding
{
    internal readonly PinnedFile File;
    internal readonly IntPtr Handle;
    internal Binding(PinnedFile file) {
        File=file; file.Recheck(); Handle=Native.dlopen("/proc/self/fd/"+file.Fd,2|0x100); // NOW|GLOBAL, dependencies pin-preloaded in order
        Core.Require(Handle!=IntPtr.Zero,"dlopen failed"); file.Recheck();
        Core.Require(Native.dlinfo(Handle,2,out IntPtr map)==0 && map!=IntPtr.Zero,"loader link map");
        Core.Require(Marshal.PtrToStringUTF8(Marshal.ReadIntPtr(map,IntPtr.Size))=="/proc/self/fd/"+file.Fd,"loaded object ownership");
    }
    internal T Get<T>(string symbol,string version) where T:Delegate {
        IntPtr p=Native.dlvsym(Handle,symbol,version); Core.Require(p!=IntPtr.Zero,"versioned symbol absent");
        using Block info=new Block(IntPtr.Size*4);
        Core.Require(Native.dladdr(p,info.Pointer)!=0,"symbol ownership");
        string? owner=Marshal.PtrToStringUTF8(Marshal.ReadIntPtr(info.Pointer));
        Core.Require(owner=="/proc/self/fd/"+File.Fd,"symbol owner changed"); File.Recheck();
        return Marshal.GetDelegateForFunctionPointer<T>(p);
    }
    // Deliberately no dlclose: NODELETE/constructors have effects; process exit
    // owns loaded-library lifetime. Close is never advertised as rollback.
}
internal sealed class LiveTeec : ITeec
{
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate uint InitFn(IntPtr name,IntPtr ctx);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate uint AllocFn(IntPtr ctx,IntPtr shared);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate uint OpenFn(IntPtr ctx,IntPtr session,IntPtr uuid,uint login,IntPtr data,IntPtr operation,out uint origin);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate uint InvokeFn(IntPtr session,uint command,IntPtr operation,out uint origin);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate void VoidFn(IntPtr value);
    private readonly InitFn init; private readonly AllocFn alloc; private readonly OpenFn open;
    private readonly InvokeFn invoke; private readonly VoidFn close,release,finalize;
    internal LiveTeec(Binding wrapper) {
        const string v="TRUSTWARE3.0";
        init=wrapper.Get<InitFn>("TEEC_InitializeContext",v); alloc=wrapper.Get<AllocFn>("TEEC_AllocateSharedMemory",v);
        open=wrapper.Get<OpenFn>("TEEC_OpenSession",v); invoke=wrapper.Get<InvokeFn>("TEEC_InvokeCommand",v);
        close=wrapper.Get<VoidFn>("TEEC_CloseSession",v); release=wrapper.Get<VoidFn>("TEEC_ReleaseSharedMemory",v); finalize=wrapper.Get<VoidFn>("TEEC_FinalizeContext",v);
    }
    public uint Initialize(Block c)=>init(IntPtr.Zero,c.Pointer);
    public uint Allocate(Block c,Block s)=>alloc(c.Pointer,s.Pointer);
    public uint Open(Block c,Block s,Block u,out uint origin)=>open(c.Pointer,s.Pointer,u.Pointer,0,IntPtr.Zero,IntPtr.Zero,out origin);
    public uint Invoke(Block s,uint command,Block o,out uint origin) {
        Core.Require(command<=2 && o.Size==60,"command allowlist"); return invoke(s.Pointer,command,o.Pointer,out origin);
    }
    public void Close(Block s)=>close(s.Pointer);
    public void Release(Block s)=>release(s.Pointer);
    public void FinalizeContext(Block c)=>finalize(c.Pointer);
    public uint Address(Block b)=>Native.Pointer32(b.Pointer);
    public BlockView Map(Block s) {
        Core.Require(s.Size==36 && s.Get(4)==Core.Shared && s.Get(0)!=0,"shared map");
        return new BlockView(new IntPtr(unchecked((int)s.Get(0))),Core.Shared);
    }
}
