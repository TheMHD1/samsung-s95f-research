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
    internal static string Label(string p)=>p switch {
        Program.EnvelopePath=>"envelope",Program.BlobPath=>"master",Program.PublicKeyPath=>"public-key","/usr/lib/libvconf.so.0"=>"vconf-file",
        "/usr/lib/libteec_trustware_common.so"=>"common-file","/usr/lib/libteec_trustware.so"=>"backend-file","/usr/lib/libteec.so"=>"wrapper-file",_=>"host-fixture"};
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
    internal readonly Pin Pin;
    internal readonly int Fd;
    internal readonly string Resolved,Identity;
    internal readonly byte[] Data;
    private bool disposed;
    private readonly string label;
    internal PinnedFile(Pin pin,bool hostTest=false)
    {
        Pin=pin;label=Preflight.Label(pin.Path); Fd=-1; Data=Array.Empty<byte>(); Resolved="";Identity="";
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
    private static bool Allowed(string p) => p==Program.EnvelopePath || p==Program.BlobPath || p==Program.PublicKeyPath ||
        p=="/usr/lib/libteec.so" || p=="/usr/lib/libteec_trustware.so" || p=="/usr/lib/libteec_trustware_common.so" || p=="/usr/lib/libvconf.so.0";
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
internal enum BindingStage { Load,LinkMap,LinkMapOwner,Symbol,SymbolAddress,SymbolOwner }
internal enum BindingReason { LoaderReturn,NameBound,NameAllowlist,Realpath,CanonicalMismatch,IdentityMismatch,FileGuard,DllNotFound,EntryPointNotFound,BadImageFormat,Unexpected }
internal sealed class BindingException : Exception
{
    internal readonly BindingStage Stage;
    internal readonly BindingReason Reason;
    internal readonly string FileLabel;
    internal BindingException(PinnedFile file,BindingStage stage,BindingReason reason) {FileLabel=Preflight.Label(file.Pin.Path);Stage=stage;Reason=reason;}
}
internal static class OwnerBinding
{
    private static void Need(bool ok,BindingReason reason) {if(!ok)throw new OwnerFailure(reason);}
    private sealed class OwnerFailure:Exception {internal readonly BindingReason Reason;internal OwnerFailure(BindingReason reason){Reason=reason;}}
    internal static string Name(IntPtr pointer)
    {
        Need(pointer!=IntPtr.Zero,BindingReason.NameBound);
        byte[] bytes=new byte[4096];int n=0;
        for(;n<bytes.Length;n++){bytes[n]=Marshal.ReadByte(pointer,n);if(bytes[n]==0)break;}
        Need(n<bytes.Length && n>0,BindingReason.NameBound);
        // Canonical paths below use exact ordinal comparisons; no decoding replacement.
        for(int i=0;i<n;i++)Need(bytes[i]>=0x20 && bytes[i]<=0x7e,BindingReason.NameAllowlist);
        return Encoding.ASCII.GetString(bytes,0,n);
    }
    internal static bool Allowed(PinnedFile file,string name)=>Allowed(file.Pin,file.Resolved,file.Fd,name);
    internal static bool Allowed(Pin pin,string canonical,int fd,string name)
    {
        if(name=="/proc/self/fd/"+fd || name==pin.Path || name==canonical)return true;
        // Only the exact requested/resolved basenames in the two system library
        // directories are possible extra aliases. Canonical and identity proof follows.
        if(!pin.Path.StartsWith("/usr/lib/",StringComparison.Ordinal))return false;
        string requested=Path.GetFileName(pin.Path),resolved=Path.GetFileName(canonical);
        return name=="/lib/"+requested || name=="/usr/lib/"+requested || name=="/lib/"+resolved || name=="/usr/lib/"+resolved;
    }
    internal static void Verify(PinnedFile file,string name,BindingStage stage)
    {
        try {
            Need(Allowed(file,name),BindingReason.NameAllowlist);file.Recheck();
            using Block path=new Block(4096);Need(Native.realpath(name,path.Pointer)!=IntPtr.Zero,BindingReason.Realpath);
            string canonical=Name(path.Pointer);Need(canonical==file.Resolved,BindingReason.CanonicalMismatch);
            // Scope the path bypass to the independently proved canonical path.
            // The complete original size/SHA256/ELF/Build-ID pin is reused.
            using PinnedFile owner=new PinnedFile(file.Pin with {Path=canonical},true);
            Need(owner.Resolved==file.Resolved,BindingReason.CanonicalMismatch);
            Need(owner.Identity==file.Identity,BindingReason.IdentityMismatch);
            file.Recheck();owner.Recheck();
        } catch(Exception e) {throw Failure(file,stage,e);}
    }
    internal static BindingException Failure(PinnedFile file,BindingStage stage,Exception e)=>new BindingException(file,stage,
        e is BindingException b?b.Reason:e is OwnerFailure o?o.Reason:e is PreflightException?BindingReason.FileGuard:
        e is DllNotFoundException?BindingReason.DllNotFound:e is EntryPointNotFoundException?BindingReason.EntryPointNotFound:
        e is BadImageFormatException?BindingReason.BadImageFormat:BindingReason.Unexpected);
}
internal sealed class Binding
{
    internal readonly PinnedFile File;
    internal readonly IntPtr Handle;
    internal Binding(PinnedFile file) {
        File=file;BindingStage stage=BindingStage.Load;
        try {
            file.Recheck();Handle=Native.dlopen("/proc/self/fd/"+file.Fd,2|0x100);
            if(Handle==IntPtr.Zero)throw new BindingException(file,stage,BindingReason.LoaderReturn);file.Recheck();
            stage=BindingStage.LinkMap;
            if(Native.dlinfo(Handle,2,out IntPtr map)!=0 || map==IntPtr.Zero)throw new BindingException(file,stage,BindingReason.LoaderReturn);
            stage=BindingStage.LinkMapOwner;OwnerBinding.Verify(file,OwnerBinding.Name(Marshal.ReadIntPtr(map,IntPtr.Size)),stage);
        } catch(Exception e) {throw OwnerBinding.Failure(file,stage,e);}
    }
    internal T Get<T>(string symbol,string version) where T:Delegate {
        BindingStage stage=BindingStage.Symbol;
        try {
            IntPtr p=Native.dlvsym(Handle,symbol,version);
            if(p==IntPtr.Zero)throw new BindingException(File,stage,BindingReason.LoaderReturn);
            using Block info=new Block(IntPtr.Size*4);stage=BindingStage.SymbolAddress;
            if(Native.dladdr(p,info.Pointer)==0)throw new BindingException(File,stage,BindingReason.LoaderReturn);
            stage=BindingStage.SymbolOwner;OwnerBinding.Verify(File,OwnerBinding.Name(Marshal.ReadIntPtr(info.Pointer)),stage);
            return Marshal.GetDelegateForFunctionPointer<T>(p);
        } catch(Exception e) {throw OwnerBinding.Failure(File,stage,e);}
    }
    // No dlclose: process exit owns loaded-library lifetime; no rollback claim.
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
