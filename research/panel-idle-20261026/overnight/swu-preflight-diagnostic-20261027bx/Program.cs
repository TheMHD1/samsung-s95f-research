using System;
using System.Buffers.Binary;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Cryptography;

// Fixed-file preflight diagnostic only. No TEEC, selector getter, dlopen,
// dlsym, updater, network, process-launch or arbitrary-file interface exists.
internal static class Program
{
    const string Boot="00000000-0000-4000-8000-000000000000";
    readonly record struct Pin(string Label,string Path,int Size,string Hash,string BuildId="");
    static readonly Pin[] Files={
        new("envelope","/tmp/swu-metadata-20261027bx/header-envelope.bin",4056,"6da1e2386f0f97a180984f249febaf831febfee1adb35a8cefa96f89ad069e0d"),
        new("master","/usr/share/org.tizen.tv.swu/itemsAESPassphraseEncrypted.txt",416,"d8af420d63b9cb2643783c56ce7396a5fd4d809e48df0bd321781cfd025e8220"),
        new("vconf-file","/usr/lib/libvconf.so.0",57272,"007a02e106ee38d0319084c458f048c556dcf618112cc1114e3e47cb8d226619","8d53d2ed2ee1fb4c8809be0b02fb7ee71fdf7673"),
        new("common-file","/usr/lib/libteec_trustware_common.so",244580,"353104729c40d6f1eff4f07b96f8a14466dd98efddb21a9cb7d14752351dd139","272f10b47670723b6c7863ca8e331ea2140d1544"),
        new("backend-file","/usr/lib/libteec_trustware.so",30352,"0574261e6291fb3f28bf8a254c0610c9177e132a6afd0bc7418826173555db81","60872566e5bfe19d56c7175b4071a63d845245c9"),
        new("wrapper-file","/usr/lib/libteec.so",10892,"926840c9e7b26c59d8cb9d4ab5ae274e62b11efdbf14831b0a4d81d3de720f70","80169c30fb9cc031d073eb88350ada39a0dfba67")};
    enum Reason { None,Realpath,CanonicalPath,Open,StatxReturn,StatxMask,RegularMode,FileSize,Read,EndOfFile,IdentityDrift,Hash,ElfBounds,ElfIdentity,ElfBuildId,Unexpected }
    sealed class Rejected : Exception { internal readonly Reason Code; internal Rejected(Reason code){Code=code;} }
    static void Need(bool ok,Reason reason) { if(!ok)throw new Rejected(reason); }
    static string stage="start",label="none";
    static int nativeErrno;
    [DllImport("libc.so.6",SetLastError=true)] static extern int open(string path,int flags);
    [DllImport("libc.so.6",SetLastError=true)] static extern int close(int fd);
    [DllImport("libc.so.6",SetLastError=true)] static extern IntPtr read(int fd,IntPtr data,UIntPtr count);
    [DllImport("libc.so.6",SetLastError=true)] static extern IntPtr realpath(string path,IntPtr resolved);
    // Original BX signature reproduced exactly: output array has no [Out].
    [DllImport("libc.so.6",EntryPoint="syscall",SetLastError=true)] static extern IntPtr Original(IntPtr number,IntPtr fd,byte[] empty,IntPtr flags,IntPtr mask,byte[] result);
    [DllImport("libc.so.6",EntryPoint="syscall",SetLastError=true)] static extern IntPtr ExplicitOut(IntPtr number,IntPtr fd,[In] byte[] empty,IntPtr flags,IntPtr mask,[Out] byte[] result);
    [DllImport("libc.so.6")] static extern uint getuid();
    [DllImport("libc.so.6")] static extern uint geteuid();
    [DllImport("libc.so.6")] static extern uint alarm(uint seconds);
    static uint U32(byte[] b,int p) {Need(p>=0&&p<=b.Length-4,Reason.ElfBounds);return BinaryPrimitives.ReadUInt32LittleEndian(b.AsSpan(p));}
    static ushort U16(byte[] b,int p) {Need(p>=0&&p<=b.Length-2,Reason.ElfBounds);return BinaryPrimitives.ReadUInt16LittleEndian(b.AsSpan(p));}
    static string Hash(byte[] b)=>Convert.ToHexString(SHA256.HashData(b)).ToLowerInvariant();
    static string Identity(byte[] b)=>Convert.ToHexString(b.AsSpan(16,32))+Convert.ToHexString(b.AsSpan(96,48));
    static byte[] Stat(int fd,string when)
    {
        int nr=RuntimeInformation.ProcessArchitecture==Architecture.Arm?397:332;
        byte[] original=new byte[256],explicitOut=new byte[256];
        long rc=Original((IntPtr)nr,(IntPtr)fd,new byte[1],(IntPtr)0x1000,(IntPtr)0x7ff,original).ToInt64();int error=Marshal.GetLastWin32Error();
        long alt=ExplicitOut((IntPtr)nr,(IntPtr)fd,new byte[1],(IntPtr)0x1000,(IntPtr)0x7ff,explicitOut).ToInt64();int altError=Marshal.GetLastWin32Error();
        Console.WriteLine($"STAT file={label} at={when} signature=original nr={nr} rc={rc} errno={error} mask=0x{U32(original,0):x8} mode=0x{U16(original,28):x4} size={BinaryPrimitives.ReadUInt64LittleEndian(original.AsSpan(40))}");
        Console.WriteLine($"STAT file={label} at={when} signature=explicit-out nr={nr} rc={alt} errno={altError} mask=0x{U32(explicitOut,0):x8} mode=0x{U16(explicitOut,28):x4} size={BinaryPrimitives.ReadUInt64LittleEndian(explicitOut.AsSpan(40))} fields_equal={(Identity(original)==Identity(explicitOut)&&U32(original,0)==U32(explicitOut,0)?1:0)}");
        nativeErrno=error; Need(rc==0,Reason.StatxReturn);
        Need((U32(original,0)&0x7ff)==0x7ff,Reason.StatxMask);
        return original; // Alternate marshaling never changes original guard decisions.
    }
    static string BuildId(byte[] b)
    {
        Need(b.Length>=52 && b[0]==127&&b[1]==69&&b[2]==76&&b[3]==70&&b[4]==1&&b[5]==1&&U16(b,18)==40&&U32(b,36)==0x05000200,Reason.ElfIdentity);
        int ph=checked((int)U32(b,28));ushort size=U16(b,42),count=U16(b,44);Need(size==32&&count<=128,Reason.ElfBounds);
        for(int i=0;i<count;i++) {
            int p=checked(ph+i*size);if(U32(b,p)!=4)continue;
            int at=checked((int)U32(b,p+4)),end=checked(at+(int)U32(b,p+16));Need(at>=0&&end<=b.Length,Reason.ElfBounds);
            while(at<=end-12) {
                int ns=checked((int)U32(b,at)),ds=checked((int)U32(b,at+4));uint kind=U32(b,at+8);at+=12;
                Need(ns>=0&&ds>=0&&ns<=end-at,Reason.ElfBounds);int desc=checked(at+((ns+3)&~3));Need(desc<=end&&ds<=end-desc,Reason.ElfBounds);
                if(kind==3&&ns==4&&b.AsSpan(at,4).SequenceEqual(new byte[]{71,78,85,0}))return Convert.ToHexString(b.AsSpan(desc,ds)).ToLowerInvariant();
                at=checked(desc+((ds+3)&~3));
            }
        }
        throw new Rejected(Reason.ElfBuildId);
    }
    static void Check(Pin pin,bool hostTest=false)
    {
        label=pin.Label;nativeErrno=0;int fd=-1;byte[] data=new byte[pin.Size];IntPtr resolved=Marshal.AllocHGlobal(4096);
        try {
            stage="realpath";IntPtr path=realpath(pin.Path,resolved);nativeErrno=Marshal.GetLastWin32Error();Need(path!=IntPtr.Zero,Reason.Realpath);
            string canonical=Marshal.PtrToStringUTF8(resolved)??"";
            stage="canonical";if(!hostTest)Need(canonical==pin.Path||(pin.Path.StartsWith("/usr/lib/",StringComparison.Ordinal)&&canonical.StartsWith("/usr/lib/",StringComparison.Ordinal)),Reason.CanonicalPath);
            stage="open";
            // Reproduce BX original numeric flags exactly. On ARM 0x20000 is
            // LARGEFILE, not NOFOLLOW. This probe diagnoses; it does not claim
            // or silently repair that defect in the frozen live adapter.
            const int flags=0x80000|0x20000;fd=open(canonical,flags);nativeErrno=Marshal.GetLastWin32Error();
            Console.WriteLine($"OPEN file={label} flags=0x{flags:x} rc={fd} errno={nativeErrno} original_arm_nofollow_missing={(RuntimeInformation.ProcessArchitecture==Architecture.Arm?1:0)}");Need(fd>=0,Reason.Open);
            stage="stat-before";byte[] before=Stat(fd,"before");string identity=Identity(before);
            stage="mode";ushort mode=U16(before,28);Need((mode&0xf000)==0x8000&&(mode&0x12)==0,Reason.RegularMode);
            stage="size";Need(BinaryPrimitives.ReadUInt64LittleEndian(before.AsSpan(40))==(ulong)pin.Size,Reason.FileSize);
            stage="read";GCHandle hold=GCHandle.Alloc(data,GCHandleType.Pinned);
            try {
                int used=0;while(used<data.Length){long n=read(fd,IntPtr.Add(hold.AddrOfPinnedObject(),used),(UIntPtr)(data.Length-used)).ToInt64();nativeErrno=Marshal.GetLastWin32Error();Need(n>0&&n<=data.Length-used,Reason.Read);used+=(int)n;}
                stage="eof";IntPtr extra=Marshal.AllocHGlobal(1);try{long n=read(fd,extra,(UIntPtr)1).ToInt64();nativeErrno=Marshal.GetLastWin32Error();Need(n==0,Reason.EndOfFile);}finally{Marshal.FreeHGlobal(extra);}
            } finally { hold.Free(); }
            stage="stat-after";Need(identity==Identity(Stat(fd,"after")),Reason.IdentityDrift);
            stage="hash";Need(Hash(data)==pin.Hash,Reason.Hash);
            stage="elf";if(pin.BuildId.Length>0)Need(BuildId(data)==pin.BuildId,Reason.ElfBuildId);
            Console.WriteLine($"FILE file={label} pass=1 reason=None");
        } finally {CryptographicOperations.ZeroMemory(data);if(fd>=0)close(fd);Marshal.FreeHGlobal(resolved);}
    }
    static int Main(string[] args)
    {
        if(args.Length==1&&args[0]=="--self-test")return SelfTest();
        if(args.Length!=0||RuntimeInformation.ProcessArchitecture!=Architecture.Arm||IntPtr.Size!=4||!BitConverter.IsLittleEndian){Console.WriteLine("REFUSED_ARCH_OR_ARGUMENTS target_calls=0");return 64;}
        if(getuid()!=0||geteuid()!=0||File.ReadAllText("/proc/sys/kernel/random/boot_id").Trim()!=Boot){Console.WriteLine("REFUSED_IDENTITY target_calls=0");return 64;}
        alarm(25);int failures=0;
        foreach(Pin pin in Files) {
            try{Check(pin);}catch(Rejected e){Console.WriteLine($"FILE file={label} pass=0 stage={stage} reason={e.Code} errno={nativeErrno}");failures++;}
            catch(Exception){Console.WriteLine($"FILE file={label} pass=0 stage={stage} reason=Unexpected errno={nativeErrno}");failures++;}
        }
        Console.WriteLine($"PREFLIGHT_ONLY files={Files.Length} failed={failures} target_library_loads=0 selector_calls=0 teec_calls=0 data_bytes_printed=0");return failures==0?0:65;
    }
    static int SelfTest()
    {
        if(RuntimeInformation.ProcessArchitecture!=Architecture.X64)return 64;
        string path=Path.Combine(Path.GetTempPath(),"swu-preflight-public-"+Guid.NewGuid().ToString("N"));byte[] data=System.Text.Encoding.ASCII.GetBytes("public fixture");File.WriteAllBytes(path,data);
        try {
            Check(new Pin("host-fixture",path,data.Length,Hash(data)),true);
            bool rejected=false;try{Check(new Pin("host-badsize",path,data.Length-1,Hash(data)),true);}catch(Rejected e){rejected=e.Code==Reason.FileSize;}Need(rejected,Reason.Unexpected);
            rejected=false;try{Check(new Pin("host-badhash",path,data.Length,new string('0',64)),true);}catch(Rejected e){rejected=e.Code==Reason.Hash;}Need(rejected,Reason.Unexpected);
            Console.WriteLine("PASS host_only=1 original_and_explicit_out_compared=1 target_libraries_loaded=0 selector_calls=0 teec_calls=0");return 0;
        } finally {CryptographicOperations.ZeroMemory(data);File.Delete(path);}
    }
}
