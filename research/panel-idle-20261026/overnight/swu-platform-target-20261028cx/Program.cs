using System;
using System.Buffers.Binary;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using SwuSectionStream;
using SwuStreamTransport;
internal static class Program {
 internal const string EnvelopePath="/tmp/swu-stream-20261028cx/section-plan.bin";
 internal const string PublicKeyPath="/tmp/swu-stream-20261028cx/tls-config.json";
 internal const string BlobPath="/usr/share/org.tizen.tv.swu/itemsAESPassphraseEncrypted.txt";
 internal const string Boot="00000000-0000-4000-8000-000000000000";
 internal const string PlanHash="d66af8ff9eb3615b47071de9f4917d7112ebb4afb9e04c015ed0374eed48a74a";
 internal const string CipherHash="5b364a622d44cac798f825888bce7a6d709053d76b49d88a054ac258c78f296e";
 internal const long CipherBytes=1455423504,OriginalBytes=1455423488;
 internal static readonly Pin Vconf=new Pin("/usr/lib/libvconf.so.0",57272,"007a02e106ee38d0319084c458f048c556dcf618112cc1114e3e47cb8d226619","8d53d2ed2ee1fb4c8809be0b02fb7ee71fdf7673");
 internal static readonly Pin Common=new Pin("/usr/lib/libteec_trustware_common.so",244580,"353104729c40d6f1eff4f07b96f8a14466dd98efddb21a9cb7d14752351dd139","272f10b47670723b6c7863ca8e331ea2140d1544");
 internal static readonly Pin Backend=new Pin("/usr/lib/libteec_trustware.so",30352,"0574261e6291fb3f28bf8a254c0610c9177e132a6afd0bc7418826173555db81","60872566e5bfe19d56c7175b4071a63d845245c9");
 internal static readonly Pin Wrapper=new Pin("/usr/lib/libteec.so",10892,"926840c9e7b26c59d8cb9d4ab5ae274e62b11efdbf14831b0a4d81d3de720f70","80169c30fb9cc031d073eb88350ada39a0dfba67");
 [UnmanagedFunctionPointer(CallingConvention.Cdecl)]private delegate int GetBool([MarshalAs(UnmanagedType.LPUTF8Str)]string key,out int value);
 internal static byte[] CheckPlan(byte[] p){
  Core.Require(p.Length==72 && Core.Hash(p)==PlanHash,"plan pin");
  Core.Require(p.AsSpan(0,8).SequenceEqual(System.Text.Encoding.ASCII.GetBytes("SWUSEC01")),"plan magic");
  Core.Require(BinaryPrimitives.ReadUInt32LittleEndian(p.AsSpan(8))==1001 && BinaryPrimitives.ReadUInt64LittleEndian(p.AsSpan(12))==CipherBytes && BinaryPrimitives.ReadUInt64LittleEndian(p.AsSpan(20))==OriginalBytes,"plan identity/counts");
  Core.Require(Convert.ToHexString(p.AsSpan(40,32)).ToLowerInvariant()==CipherHash,"cipher pin");return p.AsSpan(32,8).ToArray();
 }
 internal static int Main(string[] args){
  if(args.Length==1 && args[0]=="--host-tests" && RuntimeInformation.ProcessArchitecture==Architecture.X64)return IntegrationTests.Run();
  if(args.Length!=0 || RuntimeInformation.ProcessArchitecture!=Architecture.Arm || IntPtr.Size!=4 || !BitConverter.IsLittleEndian){Console.WriteLine("REFUSED_ARCH_OR_ARGUMENTS target_calls=0");return 64;}
  string stage="sealed-config";byte[]? salt=null;Stopwatch watch=Stopwatch.StartNew();
  try{
   Core.Require(RuntimeConfig.SealReady,"config seal absent");stage="deadline";Native.Deadline();stage="identity";
   Core.Require(Native.getuid()==0 && Native.geteuid()==0 && File.ReadAllText("/proc/sys/kernel/random/boot_id").Trim()==Boot,"identity");stage="file-preflight";
   using PinnedFile plan=new PinnedFile(new Pin(EnvelopePath,72,PlanHash));
   using PinnedFile configFile=new PinnedFile(new Pin(PublicKeyPath,ConfigPin.Bytes,ConfigPin.Sha256));
   using RuntimeConfig options=RuntimeConfig.Parse(configFile.Data);
   using PinnedFile master=new PinnedFile(new Pin(BlobPath,416,Core.BlobHash));
   using PinnedFile vconf=new PinnedFile(Vconf),common=new PinnedFile(Common),backend=new PinnedFile(Backend),wrapper=new PinnedFile(Wrapper);
   salt=CheckPlan(plan.Data);stage="selector-binding";Binding config=new Binding(vconf);GetBool get=config.Get<GetBool>("vconf_get_bool","VCONF_BUXTON_1.0");int guards=0;
   void Guard(){
    Core.Require(get("db/menu/support/softwareupdate/isSubmodelKeyType",out int value)==0 && value==0,"selector");
    plan.Recheck();configFile.Recheck();master.Recheck();vconf.Recheck();common.Recheck();backend.Recheck();wrapper.Recheck();
    Core.Require(File.ReadAllText("/proc/sys/kernel/random/boot_id").Trim()==Boot,"boot drift");guards++;
   }
   Guard();stage="teec-binding";Binding cb=new Binding(common),bb=new Binding(backend),wb=new Binding(wrapper);LiveTeec api=new LiveTeec(wb);Guard();
   stage="tls-channel";
   using TlsSectionChannel channel=new TlsSectionChannel(new ChannelOptions(RuntimeConfig.Server,options.Port,options.CertificateSha256,options.Nonce,CipherBytes,CipherHash,CipherBytes,RuntimeConfig.IoTimeoutSeconds,RuntimeConfig.TotalTimeoutSeconds));
   stage="sequence";
   StreamResult result=StreamingEngine.Run(api,new SectionPlan(CipherBytes,CipherHash,Core.BlobHash,PlanHash),master.Data,salt,channel,channel,Guard);
   Console.WriteLine($"SWU_STREAM_RAW accepted={(result.Accepted?1:0)} first_failure={result.FirstFailure} code=0x{result.Code:x8} origin=0x{result.Origin:x8} calls0={result.Command0Attempts} updates={result.UpdateAttempts} finals={result.FinalAttempts} cipher={result.CipherBytesRead} raw={result.RawBytesProduced} confirmed={result.SinkBytesConfirmed} eof={(result.InputEofObserved?1:0)} digest={(result.CipherDigestMatchedAtEof?1:0)} closed={(result.SessionClosed?1:0)} released={result.Released} finalized={(result.ContextFinalized?1:0)} wiped={(result.OwnedBuffersWipeConfirmed?1:0)} raw_complete={(result.SinkCompletedRaw?1:0)} guards={guards} cleanup_failures={result.CleanupFailures} first_cleanup={result.FirstCleanupFailure} backend_exception={(result.BackendExceptionObserved?1:0)} ownership_uncertain={(result.ResourceOwnershipUncertain?1:0)} elapsed_ms={watch.ElapsedMilliseconds} payload_validated=0 firmware_written=0");
   GC.KeepAlive(config);GC.KeepAlive(get);GC.KeepAlive(cb);GC.KeepAlive(bb);return result.Accepted?0:70;
  }catch(PreflightException e){Console.WriteLine($"REFUSED_OR_FAILED stage={stage} file={e.FileLabel} preflight={e.Stage} reason={e.Reason}");return 65;}
  catch(BindingException e){Console.WriteLine($"REFUSED_OR_FAILED stage={stage} file={e.FileLabel} binding={e.Stage} reason={e.Reason}");return 65;}
  catch(Exception){Console.WriteLine("REFUSED_OR_FAILED stage="+stage);return 65;}
  finally{if(salt!=null)CryptographicOperations.ZeroMemory(salt);}
 }
}
