using System;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;

// Resolves one fixed vconf symbol for metadata only. It is never converted
// into a delegate or called. No TEEC/common/backend/updater path exists.
internal static class Program
{
    const string Boot="00000000-0000-4000-8000-000000000000";
    internal static readonly Pin Vconf=new Pin("/usr/lib/libvconf.so.0",57272,"007a02e106ee38d0319084c458f048c556dcf618112cc1114e3e47cb8d226619","8d53d2ed2ee1fb4c8809be0b02fb7ee71fdf7673");
    enum Stage { Guard,Deadline,Identity,MapsBefore,FilePreflight,DlerrorBeforeOpen,Dlopen,DlerrorAfterOpen,RecheckAfterOpen,Dlinfo,DlerrorAfterInfo,LinkMapName,LinkMapOwnerFile,DlerrorBeforeSymbol,Dlvsym,DlerrorAfterSymbol,Dladdr,DlerrorAfterAddress,SymbolOwnerName,SymbolOwnerFile,FinalRecheck,MapsAfter,Done }
    enum Reason { None,RefusedArchitectureOrArgs,RefusedIdentity,DllNotFound,EntryPointNotFound,BadImageFormat,InvalidLoaderResult,NameTooLong,OwnerPathSuppressed,OwnerCanonicalMismatch,OwnerIdentityMismatch,FilePreflight,Unexpected }
    sealed class Failure:Exception {internal readonly Reason Code;internal Failure(Reason reason){Code=reason;} }
    static Stage stage=Stage.Guard;
    static void Need(bool ok,Reason reason) {if(!ok)throw new Failure(reason);}
    static string PointerText(IntPtr pointer,int maximum=256)
    {
        if(pointer==IntPtr.Zero)return "";
        byte[] bytes=new byte[maximum];int n=0;
        for(;n<maximum;n++){bytes[n]=Marshal.ReadByte(pointer,n);if(bytes[n]==0)break;}
        Need(n<maximum,Reason.NameTooLong);
        // Only ASCII path/error metadata is eligible for later allowlisting.
        return System.Text.Encoding.ASCII.GetString(bytes,0,n);
    }
    static bool AllowedName(string name,string fdPath,Pin pin,bool host)
    {
        if(name==fdPath || (host&&name==pin.Path))return true;
        return Regex.IsMatch(name,@"^/(usr/)?lib/libvconf\.so(?:\.[0-9]+)*$");
    }
    static string ShowName(string name,string fdPath,Pin pin,bool host)=>AllowedName(name,fdPath,pin,host)||Regex.IsMatch(name,@"^libvconf\.so(?:\.[0-9]+)*$")?name:"suppressed";
    static void ErrorMetadata()
    {
        string error=PointerText(Native.dlerror(),512);
        // Do not print arbitrary loader text or dependency paths. Categorize a
        // bounded copy against fixed tokens; raw exception messages are absent.
        string category=error.Length==0?"None":error.Contains("undefined symbol",StringComparison.Ordinal)?"UndefinedSymbol":error.Contains("version",StringComparison.Ordinal)&&error.Contains("not found",StringComparison.Ordinal)?"VersionNotFound":error.Contains("cannot open shared object file",StringComparison.Ordinal)?"CannotOpenObject":"OtherSuppressed";
        Console.WriteLine($"DLERROR at={stage} present={(error.Length==0?0:1)} category={category}");
    }
    static string Resolve(string name)
    {
        using Block p=new Block(4096);Need(Native.realpath(name,p.Pointer)!=IntPtr.Zero,Reason.OwnerCanonicalMismatch);
        return PointerText(p.Pointer,4096);
    }
    static void OwnerProof(string name,string fdPath,Pin pin,PinnedFile original,bool host,string kind)
    {
        Need(AllowedName(name,fdPath,pin,host),Reason.OwnerPathSuppressed);
        Need(Resolve(name)==original.Resolved,Reason.OwnerCanonicalMismatch);
        // Content hashes remain comparisons only, never printed. Exact owner
        // descriptor identity must equal the original held descriptor identity.
        using PinnedFile owner=new PinnedFile(new Pin(name,pin.Size,pin.Hash,pin.BuildId),true);
        Need(owner.Identity==original.Identity,Reason.OwnerIdentityMismatch);original.Recheck();owner.Recheck();
        Console.WriteLine($"OWNER kind={kind} canonical_match=1 stat_identity_match=1 pinned_size_hash_buildid=1");
    }
    static bool TryOwnerProof(string name,string fdPath,Pin pin,PinnedFile file,bool host,string kind)
    {
        try {OwnerProof(name,fdPath,pin,file,host,kind);return true;}
        catch(Failure e){Console.WriteLine($"OWNER kind={kind} match=0 reason={e.Code}");return false;}
        catch(PreflightException e){Console.WriteLine($"OWNER kind={kind} match=0 reason=FilePreflight file_stage={e.Stage} file_reason={e.Reason}");return false;}
    }
    static void MappedNames(Pin pin,bool host,string when)
    {
        byte[] bytes=new byte[1024*1024];int used=0;
        using FileStream stream=File.OpenRead("/proc/self/maps");
        while(used<bytes.Length){int n=stream.Read(bytes,used,bytes.Length-used);if(n==0)break;used+=n;}
        Need(used<bytes.Length,Reason.InvalidLoaderResult);
        string text=System.Text.Encoding.ASCII.GetString(bytes,0,used);int count=0;
        foreach(string line in text.Split('\n')) {
            string[] fields=line.Split(' ',6,StringSplitOptions.RemoveEmptyEntries);
            if(fields.Length<6||!fields[5].Contains(host?"host_vconf_mock.so":"libvconf.so",StringComparison.Ordinal))continue;
            if(count++>=16)continue;
            Console.WriteLine($"MAP at={when} name={ShowName(fields[5],"",pin,host)}");
        }
        Console.WriteLine($"MAP_COUNT at={when} matched={count} printed={Math.Min(count,16)}");
    }
    static void Diagnostic(Pin pin,bool host,bool preload)
    {
        stage=Stage.MapsBefore;MappedNames(pin,host,"before");
        stage=Stage.FilePreflight;using PinnedFile file=new PinnedFile(pin,host);file.Recheck();
        Console.WriteLine("FILE pinned=1");string fdPath="/proc/self/fd/"+file.Fd;
        if(preload){ // Host mock only: reproduce an already loaded canonical object.
            Need(host,Reason.InvalidLoaderResult);Need(Native.dlopen(pin.Path,2|0x100)!=IntPtr.Zero,Reason.InvalidLoaderResult);
        }
        stage=Stage.DlerrorBeforeOpen;ErrorMetadata();stage=Stage.Dlopen;
        IntPtr handle=Native.dlopen(fdPath,2|0x100);Console.WriteLine($"DLOPEN nonzero={(handle!=IntPtr.Zero?1:0)} flags=0x102");
        stage=Stage.DlerrorAfterOpen;ErrorMetadata();Need(handle!=IntPtr.Zero,Reason.InvalidLoaderResult);
        stage=Stage.RecheckAfterOpen;file.Recheck();stage=Stage.Dlinfo;
        int infoResult=Native.dlinfo(handle,2,out IntPtr map);Console.WriteLine($"DLINFO rc={infoResult} map_nonzero={(map!=IntPtr.Zero?1:0)}");
        stage=Stage.DlerrorAfterInfo;ErrorMetadata();Need(infoResult==0&&map!=IntPtr.Zero,Reason.InvalidLoaderResult);
        stage=Stage.LinkMapName;string mapName=PointerText(Marshal.ReadIntPtr(map,IntPtr.Size));
        Console.WriteLine($"LINK_MAP name={ShowName(mapName,fdPath,pin,host)} fd_spelling_match={(mapName==fdPath?1:0)}");
        if(preload)Need(mapName==pin.Path && mapName!=fdPath,Reason.InvalidLoaderResult);
        stage=Stage.LinkMapOwnerFile;bool mapMatch=TryOwnerProof(mapName,fdPath,pin,file,host,"link-map");
        stage=Stage.DlerrorBeforeSymbol;ErrorMetadata();stage=Stage.Dlvsym;
        IntPtr symbol=Native.dlvsym(handle,"vconf_get_bool","VCONF_BUXTON_1.0");Console.WriteLine($"DLVSYM nonzero={(symbol!=IntPtr.Zero?1:0)} exact_version=VCONF_BUXTON_1.0");
        stage=Stage.DlerrorAfterSymbol;ErrorMetadata();Need(symbol!=IntPtr.Zero,Reason.InvalidLoaderResult);
        using Block info=new Block(IntPtr.Size*4);stage=Stage.Dladdr;
        int addrResult=Native.dladdr(symbol,info.Pointer);Console.WriteLine($"DLADDR rc={addrResult}");
        stage=Stage.DlerrorAfterAddress;ErrorMetadata();Need(addrResult!=0,Reason.InvalidLoaderResult);
        stage=Stage.SymbolOwnerName;string ownerName=PointerText(Marshal.ReadIntPtr(info.Pointer));
        Console.WriteLine($"SYMBOL_OWNER name={ShowName(ownerName,fdPath,pin,host)} fd_spelling_match={(ownerName==fdPath?1:0)}");
        stage=Stage.SymbolOwnerFile;bool symbolMatch=TryOwnerProof(ownerName,fdPath,pin,file,host,"symbol");
        stage=Stage.FinalRecheck;file.Recheck();stage=Stage.MapsAfter;MappedNames(pin,host,"after");stage=Stage.Done;
        // No delegate creation, invocation or dlclose. Exit owns loader lifetime.
        Console.WriteLine($"VCONF_LOADER_ONLY complete=1 owner_files_matched={(mapMatch&&symbolMatch?1:0)} resolved_pointer_called=0 getter_calls=0 teec_calls=0 plaintext_bytes=0");
        if(host)Need(mapMatch&&symbolMatch,Reason.InvalidLoaderResult);
    }
    internal static int Main(string[] args)
    {
        try {
            if(args.Length==1&&args[0]=="--self-test")return HostTest();
            if(args.Length!=0||RuntimeInformation.ProcessArchitecture!=Architecture.Arm||IntPtr.Size!=4||!BitConverter.IsLittleEndian){Console.WriteLine("REFUSED reason=RefusedArchitectureOrArgs target_calls=0");return 64;}
            stage=Stage.Deadline;Native.Deadline();stage=Stage.Identity;
            Need(Native.getuid()==0&&Native.geteuid()==0&&File.ReadAllText("/proc/sys/kernel/random/boot_id").Trim()==Boot,Reason.RefusedIdentity);
            Diagnostic(Vconf,false,false);return 0;
        } catch(PreflightException e){Console.WriteLine($"FAILED stage={stage} reason=FilePreflight file={e.FileLabel} file_stage={e.Stage} file_reason={e.Reason} getter_calls=0 teec_calls=0");return 65;}
        catch(Exception e){Reason reason=e is Failure f?f.Code:e is DllNotFoundException?Reason.DllNotFound:e is EntryPointNotFoundException?Reason.EntryPointNotFound:e is BadImageFormatException?Reason.BadImageFormat:Reason.Unexpected;Console.WriteLine($"FAILED stage={stage} reason={reason} getter_calls=0 teec_calls=0");return 65;}
    }
    static int HostTest()
    {
        Need(RuntimeInformation.ProcessArchitecture==Architecture.X64,Reason.RefusedArchitectureOrArgs);
        string path=Path.Combine(AppContext.BaseDirectory,"host_vconf_mock.so");byte[] bytes=File.ReadAllBytes(path);
        Pin pin=new Pin(path,bytes.Length,Core.Hash(bytes));
        // A spelling mismatch is diagnostic evidence, not silently bypassed.
        Need(!AllowedName("/tmp/arbitrary.so","/proc/self/fd/12",Vconf,false),Reason.InvalidLoaderResult);
        Diagnostic(pin,true,true);Console.WriteLine("PASS host_only=1 canonical_preload=1 getter_calls=0 teec_calls=0 target_vconf_loaded=0");return 0;
    }
}
