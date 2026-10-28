using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using SwuHeaderAuthentication;

internal static class Program
{
    internal const string EnvelopePath="/tmp/swu-header-20261028ce/header-envelope.bin";
    internal const string PublicKeyPath="/usr/share/org.tizen.tv.swu/itemsPublicRSAKey.txt";
    internal const string OutputPath="/tmp/swu-header-20261028ce/authenticated-header-raw.bin";
    internal const string BlobPath="/usr/share/org.tizen.tv.swu/itemsAESPassphraseEncrypted.txt";
    internal const string Boot="00000000-0000-4000-8000-000000000000";
    internal static readonly Pin Vconf=new Pin("/usr/lib/libvconf.so.0",57272,"007a02e106ee38d0319084c458f048c556dcf618112cc1114e3e47cb8d226619","8d53d2ed2ee1fb4c8809be0b02fb7ee71fdf7673");
    internal static readonly Pin Common=new Pin("/usr/lib/libteec_trustware_common.so",244580,"353104729c40d6f1eff4f07b96f8a14466dd98efddb21a9cb7d14752351dd139","272f10b47670723b6c7863ca8e331ea2140d1544");
    internal static readonly Pin Backend=new Pin("/usr/lib/libteec_trustware.so",30352,"0574261e6291fb3f28bf8a254c0610c9177e132a6afd0bc7418826173555db81","60872566e5bfe19d56c7175b4071a63d845245c9");
    internal static readonly Pin Wrapper=new Pin("/usr/lib/libteec.so",10892,"926840c9e7b26c59d8cb9d4ab5ae274e62b11efdbf14831b0a4d81d3de720f70","80169c30fb9cc031d073eb88350ada39a0dfba67");
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int GetBool([MarshalAs(UnmanagedType.LPUTF8Str)] string key,out int value);
    internal static int Main(string[] args)
    {
        if(args.Length==1 && args[0]=="--self-test") return HostTests.Run();
        if(args.Length==1 && args[0]=="--integration-self-test" && RuntimeInformation.ProcessArchitecture==Architecture.X64) return IntegrationTests.Run();
        if(args.Length==1 && args[0]=="--self-test-deadline" && RuntimeInformation.ProcessArchitecture==Architecture.X64) {
            Native.Deadline(); System.Threading.Thread.Sleep(60000); return 99;
        }
        // This guard precedes every platform/library/configuration call. There
        // is no force flag, arbitrary input, command or environment override.
        if(args.Length!=0 || RuntimeInformation.ProcessArchitecture!=Architecture.Arm || IntPtr.Size!=4 || !BitConverter.IsLittleEndian) {
            Console.WriteLine("REFUSED_ARCH_OR_ARGUMENTS target_calls=0"); return 64;
        }
        string stage="deadline";
        try {
            Native.Deadline();
            stage="identity"; Core.Require(Native.getuid()==0 && Native.geteuid()==0,"root identity");
            Core.Require(File.ReadAllText("/proc/sys/kernel/random/boot_id").Trim()==Boot,"boot drift");
            stage="file-preflight";
            using PinnedFile env=new PinnedFile(new Pin(EnvelopePath,Core.Envelope,Core.EnvelopeHash));
            using PinnedFile blob=new PinnedFile(new Pin(BlobPath,Core.Blob,Core.BlobHash));
            using PinnedFile publicKey=new PinnedFile(new Pin(PublicKeyPath,426,"ebf12ab9d4ef069e1a6030b8c3b117894746637715270f7e3d37d3cd737f71a3"));
            using PinnedFile vconf=new PinnedFile(Vconf),common=new PinnedFile(Common),backend=new PinnedFile(Backend),wrapper=new PinnedFile(Wrapper);
            Core.Validate(env.Data,blob.Data);
            stage="selector-binding";
            Binding config=new Binding(vconf);
            GetBool get=config.Get<GetBool>("vconf_get_bool","VCONF_BUXTON_1.0");
            void SelectorCheck() {
                int rc=get("db/menu/support/softwareupdate/isSubmodelKeyType",out int value);
                Console.WriteLine($"SELECTOR result={rc} value={value}");
                Core.Require(rc==0 && value==0,"master selector drift");
                vconf.Recheck(); env.Recheck(); blob.Recheck(); publicKey.Recheck(); common.Recheck(); backend.Recheck(); wrapper.Recheck();
                Core.Require(File.ReadAllText("/proc/sys/kernel/random/boot_id").Trim()==Boot,"boot drift");
            }
            SelectorCheck();
            stage="teec-binding";
            // Exact held descriptors are loaded in dependency order. This does
            // execute library constructors; it belongs inside the deadline.
            Binding commonBinding=new Binding(common),backendBinding=new Binding(backend),wrapperBinding=new Binding(wrapper);
            GC.KeepAlive(commonBinding); GC.KeepAlive(backendBinding);
            LiveTeec api=new LiveTeec(wrapperBinding);
            SelectorCheck(); stage="sequence";
            ValidationResult? authentication=null; bool rawSaved=false;
            Result result=Core.Run(api,env.Data,blob.Data,SelectorCheck,plaintext=> {
                byte[] raw=plaintext.ToArray();
                try {
                    authentication=Validator.Authenticate4032(raw,publicKey.Data,PublicPemPin.Master);
                    if(authentication.Accepted) { PrivateHeaderFile.SaveRaw(raw); rawSaved=true; }
                } finally { CryptographicOperations.ZeroMemory(raw); }
            });
            result.Print(); GC.KeepAlive(config); GC.KeepAlive(get);
            if(authentication!=null) Console.WriteLine($"SWU_HEADER_AUTH accepted={(authentication.Accepted?1:0)} reason={authentication.Reason} representation={authentication.Representation} raw_bytes=4032 selected_bytes={authentication.SelectedBytes} padding_bytes={authentication.PaddingBytes} root_count={authentication.RootCount} present_roots={authentication.PresentRoots} checked_leaves={authentication.CheckedLeaves} signature_authenticity_validated={(authentication.SignatureAuthenticityValidated?1:0)} framing_subset_checked={(authentication.FramingSubsetChecked?1:0)} full_schema_validated=0 metadata_published=0 private_raw_saved={(rawSaved?1:0)}");
            return result.Stage=="quarantined" && result.Code==0 && result.SessionClosed && result.Released==3 && result.ContextFinalized && authentication?.Accepted==true && rawSaved?0:70;
        } catch(BindingException e) {
            Console.WriteLine($"REFUSED_OR_FAILED stage={stage} file={e.FileLabel} binding_stage={e.Stage} reason={e.Reason} metadata_published=0"); return 65;
        } catch(PreflightException e) {
            Console.WriteLine($"REFUSED_OR_FAILED stage={stage} file={e.FileLabel} file_stage={e.Stage} reason={e.Reason} metadata_published=0"); return 65;
        } catch(Exception) {
            // Deliberately do not print exception strings, buffers or keys.
            Console.WriteLine("REFUSED_OR_FAILED stage="+stage+" metadata_published=0"); return 65;
        }
    }
}
