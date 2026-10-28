using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Runtime.InteropServices;

internal sealed class Mock : ITeec,IDisposable
{
    internal int Fail=-1,Mode,Step,Commands,Released,Closed,Finalized,Allocated,AllocationFault=-1,FaultKind;
    private readonly List<Block> descriptors=new List<Block>(),buffers=new List<Block>();
    private uint Next()=>Step++==Fail?0xffff0001u:0;
    private static void Zero(Block b)=>Core.Require(b.Bytes.ToArray().All(x=>x==0),"nonzero storage");
    public uint Initialize(Block c) { Zero(c); c.Put(0,1); return Next(); }
    public uint Allocate(Block c,Block s) {
        Core.Require(c.Get(0)==1 && s.Size==36 && s.Get(4)==Core.Shared && s.Get(8)==3,"allocation frame");
        Core.Require(s.Bytes.Slice(12).ToArray().All(x=>x==0),"reserved shared storage");
        uint rc=Next(); if(rc!=0)return rc;
        descriptors.Add(s); buffers.Add(new Block(Core.Shared)); Allocated++; s.Put(0,(uint)Allocated);
        if(Allocated-1==AllocationFault && FaultKind==0)s.Put(4,Core.Shared-1);
        if(Allocated-1==AllocationFault && FaultKind==1)s.Put(0,0);
        return 0;
    }
    public uint Open(Block c,Block s,Block u,out uint origin) {
        Core.Require(u.Get(0)==0x22222221 && u.Bytes[15]==1 && u.Bytes.Slice(4,11).ToArray().All(x=>x==0),"UUID");
        Zero(s); s.Put(0,2); origin=3; return Next();
    }
    public uint Invoke(Block s,uint cmd,Block o,out uint origin) {
        Core.Require(cmd==(uint)Commands && cmd<3 && s.Get(0)==2,"command order");
        using Block expected=new Block(60); Core.Frame(expected,(int)cmd,0x2000,0x2024,0x2048);
        Core.Require(o.Bytes.SequenceEqual(expected.Bytes),"fresh exact operation");
        o.Put(56,0x12345678); o.Put(0,3); Commands++; origin=4; uint rc=Next();
        buffers[1].Bytes.Fill(0xa5);
        if(cmd==1) { o.Put(24,Mode==1?uint.MaxValue:0); o.Put(32,rc!=0?uint.MaxValue:Mode==2?4033u:4016u); }
        if(cmd==2) { o.Put(12,Mode==1?uint.MaxValue:0); o.Put(20,rc!=0?uint.MaxValue:Mode==3?17u:Mode==4?65537u:16u); }
        return rc;
    }
    public void Close(Block s) { Core.Require(s.Get(0)==2,"session close"); Closed++; }
    public void Release(Block s) { Core.Require(s==descriptors[Allocated-Released-1],"release reverse order"); Zero(buffers[Allocated-Released-1]); Released++; }
    public void FinalizeContext(Block c) { Core.Require(c.Get(0)==1,"context finalize"); Finalized++; }
    public uint Address(Block s)=>descriptors.IndexOf(s)==AllocationFault && FaultKind==3?0u:(uint)(0x2000+descriptors.IndexOf(s)*36);
    public BlockView Map(Block s) { int i=descriptors.IndexOf(s); return new BlockView(i==AllocationFault && FaultKind==2?IntPtr.Zero:buffers[i].Pointer,Core.Shared); }
    public void Dispose() { foreach(Block b in buffers)b.Dispose(); }
}
internal static class HostTests
{
    internal static int Run()
    {
        try {
            Core.Require(RuntimeInformation.ProcessArchitecture==Architecture.X64 && IntPtr.Size==8,"host tests require x64");
            Core.Require(Core.Hash(Array.Empty<byte>())=="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","SHA256 empty");
            Core.Require(Core.Hash(System.Text.Encoding.ASCII.GetBytes("abc"))=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad","SHA256 abc");
            uint[][] golden={new uint[]{0,0x01010d0d,0x2000,416,0,0x2048,8,0,0,1,0,1,0x201,0,0},new uint[]{0,0x00020e0d,0x2000,4032,0,0x2024,4032,0,0,0,0,0,0,0,0},new uint[]{0,0x0000020e,0x2024,65536,0,0,0,0,0,0,0,0,0,0,0}};
            for(int cmd=0;cmd<3;cmd++) {
                using Block op=new Block(60); op.Bytes.Fill(0xa5); Core.Frame(op,cmd,0x2000,0x2024,0x2048);
                for(int i=0;i<15;i++)Core.Require(op.Get(i*4)==golden[cmd][i],"golden frame");
                Console.WriteLine("GOLDEN"+cmd+"="+Convert.ToHexString(op.Bytes).ToLowerInvariant());
            }
            for(int failure=-1;failure<8;failure++) Sequence(failure,0);
            for(int mode=1;mode<5;mode++)Sequence(-1,mode);
            for(int allocation=0;allocation<3;allocation++)for(int kind=0;kind<4;kind++) {
                using Mock fault=new Mock{AllocationFault=allocation,FaultKind=kind}; byte[] e=new byte[Core.Envelope],b=new byte[Core.Blob]; Array.Fill(b,(byte)0x42);
                Result faultResult=Core.Run(fault,e,b,()=>{});
                Core.Require(faultResult.LocalFailure && fault.Commands==0 && fault.Released==allocation+1 && fault.Finalized==1 && fault.Closed==0 && b.All(x=>x==0),"allocation fault containment");
            }
            for(int failSelector=0;failSelector<3;failSelector++) {
                using Mock drift=new Mock(); byte[] e=new byte[Core.Envelope],b=new byte[Core.Blob]; int checks=0;
                Result driftResult=Core.Run(drift,e,b,()=>{Core.Require(checks++!=failSelector,"selector drift");});
                Core.Require(driftResult.LocalFailure && drift.Commands==(failSelector==2?3:0),"selector drift containment");
                Core.Require(drift.Released==drift.Allocated,"selector drift release");
            }
            byte[] envelope=new byte[Core.Envelope],blob=new byte[Core.Blob]; bool rejected=false;
            try { Core.Validate(envelope,blob); } catch { rejected=true; } Core.Require(rejected,"invalid input accepted");
            // Host file preflight verifies real statx/open/EOF/hash logic using
            // temporary public fixture data; never target paths or libraries.
            string path=Path.Combine(Path.GetTempPath(),"swu-host-"+Guid.NewGuid().ToString("N"));
            byte[] bytes=System.Text.Encoding.ASCII.GetBytes("public-host-fixture"); File.WriteAllBytes(path,bytes);
            try {
                using PinnedFile f=new PinnedFile(new Pin(path,bytes.Length,Core.Hash(bytes)),true); f.Recheck();
                rejected=false; try { using PinnedFile bad=new PinnedFile(new Pin(path,bytes.Length-1,Core.Hash(bytes)),true); } catch { rejected=true; } Core.Require(rejected,"wrong file size accepted");
                rejected=false; try { using PinnedFile bad=new PinnedFile(new Pin(path,bytes.Length,new string('0',64)),true); } catch { rejected=true; } Core.Require(rejected,"wrong file hash accepted");
                File.WriteAllText(path,"changed"); rejected=false; try { f.Recheck(); } catch { rejected=true; } Core.Require(rejected,"file drift accepted");
            } finally { File.Delete(path); }
            VerifyStatMaskAndOpenFlags();
            VerifyElfPins();
            VerifyDynamicBindings();
            Console.WriteLine("PASS host_only=1 target_library_loads=0 golden_frames=3 teec_failure_stages=8 count_overflows=3 allocation_faults=12 selector_drift=3 sha256_kats=2 file_guard=pass stat_mask_acceptances=3 missing_required_bits=9 correct_open_flags=2 nofollow_symlink_refusal=1 safe_preflight_failures=2 elf_pins=4 host_mock_versioned_bindings=7"); return 0;
        } catch(Exception e) { Console.WriteLine("HOST_TEST_FAILED "+e.Message); return 1; }
    }
    private static void VerifyStatMaskAndOpenFlags()
    {
        foreach(uint mask in new uint[]{0x7ff,0x7df,0x3df}) {
            byte[] stat=new byte[256];System.Buffers.Binary.BinaryPrimitives.WriteUInt32LittleEndian(stat,mask);Native.ValidateStatMask(stat);
        }
        int missing=0;
        for(int bit=0;bit<11;bit++)if((Native.RequiredStatMask&(1u<<bit))!=0) {
            byte[] stat=new byte[256];System.Buffers.Binary.BinaryPrimitives.WriteUInt32LittleEndian(stat,0x7ffu&~(1u<<bit));
            bool rejected=false;try{Native.ValidateStatMask(stat);}catch(PreflightException e){rejected=e.Reason==PreflightReason.StatxMask;}
            Core.Require(rejected,"required stat bit accepted");missing++;
        }
        Core.Require(missing==9 && Native.RequiredStatMask==0x3df,"required stat bit inventory");
        Core.Require(Native.OpenFlags(Architecture.Arm)==0xa8000 && Native.OpenFlags(Architecture.X64)==0xa0000,"architecture open flags");
        string path=Path.Combine(Path.GetTempPath(),"swu-nofollow-"+Guid.NewGuid().ToString("N")),link=path+"-link";
        byte[] bytes=System.Text.Encoding.ASCII.GetBytes("public nofollow fixture");File.WriteAllBytes(path,bytes);File.CreateSymbolicLink(link,path);
        try {
            int fd=Native.OpenReadOnlyNoFollow(link);int error=Marshal.GetLastWin32Error();
            if(fd>=0)Native.close(fd);Core.Require(fd==-1 && error==40,"nofollow final symlink accepted");
            bool rejected=false;try{using PinnedFile wrong=new PinnedFile(new Pin(path,bytes.Length-1,Core.Hash(bytes)),true);}
            catch(PreflightException e){rejected=e.Reason==PreflightReason.FileSize && e.Stage==PreflightStage.Size && e.FileLabel=="host-fixture";}
            Core.Require(rejected,"safe file-size diagnostic");
            rejected=false;try{using PinnedFile wrong=new PinnedFile(new Pin(path,bytes.Length,new string('0',64)),true);}
            catch(PreflightException e){rejected=e.Reason==PreflightReason.Hash && e.Stage==PreflightStage.Hash && e.FileLabel=="host-fixture";}
            Core.Require(rejected,"safe hash diagnostic");
        } finally {File.Delete(link);File.Delete(path);}
    }
    private static void VerifyDynamicBindings()
    {
        string path=Path.Combine(AppContext.BaseDirectory,"host_mock.so"); byte[] bytes=File.ReadAllBytes(path);
        using PinnedFile file=new PinnedFile(new Pin(path,bytes.Length,Core.Hash(bytes)),true);
        Binding binding=new Binding(file); LiveTeec api=new LiveTeec(binding);
        using Block c=new Block(4),s=new Block(4),shared=new Block(36),u=new Block(16),op=new Block(60);
        Core.Require(api.Initialize(c)==0 && c.Get(0)==0x11223344,"native mock initialize");
        shared.Put(4,Core.Shared); shared.Put(8,3); Core.Require(api.Allocate(c,shared)==0 && shared.Get(0)==0x1000,"native mock allocate");
        u.Put(0,0x22222221); u.Bytes[15]=1;
        Core.Require(api.Open(c,s,u,out uint origin)==0 && origin==3,"native mock open ABI");
        for(int command=0;command<3;command++) {
            Core.Frame(op,command,0x2000,0x2024,0x2048);
            Core.Require(api.Invoke(s,(uint)command,op,out origin)==0 && origin==4 && op.Get(56)==0x12345678,"native mock invoke ABI");
        }
        api.Close(s); api.Release(shared); api.FinalizeContext(c);
        Core.Require(s.Get(0)==0 && shared.Get(0)==0 && c.Get(0)==0,"native mock void ABI");
        Core.Require(Native.Pointer32(new IntPtr(0x80000000L))==0x80000000u,"unsigned address");
        bool rejected=false; try { Native.Pointer32(new IntPtr(0x1001)); } catch { rejected=true; } Core.Require(rejected,"unaligned pointer accepted");
    }
    private static void VerifyElfPins()
    {
        const string root="${S95F_EVIDENCE_ROOT}/";
        string[] paths={root+"research-20261027-external/target-file-acquisition-02/libteec.so",root+"research-20261027-external/target-file-acquisition-02/libteec_trustware.so",root+"research-20261027-external/target-file-acquisition-04/libteec_trustware_common.so",root+"panel-idle-20261026/overnight/supporting-files-20261027bx/vconf-copy/libvconf.so.0.3.1"};
        Pin[] pins={Program.Wrapper,Program.Backend,Program.Common,Program.Vconf};
        for(int i=0;i<paths.Length;i++) {
            byte[] b=File.ReadAllBytes(paths[i]); Core.Require(b.Length==pins[i].Size && Core.Hash(b)==pins[i].Hash && Elf.BuildId(b)==pins[i].BuildId,"retained ELF pin");
            byte[] bad=(byte[])b.Clone(); bad[4]=2; bool rejected=false; try{Elf.BuildId(bad);}catch{rejected=true;}Core.Require(rejected,"ELF64 accepted");
        }
    }
    private static void Sequence(int failure,int mode)
    {
        using Mock m=new Mock{Fail=failure,Mode=mode}; byte[] env=new byte[Core.Envelope],blob=new byte[Core.Blob]; Array.Fill(blob,(byte)0x42);
        Result r=Core.Run(m,env,blob,()=>{}); bool success=failure<0 && mode<2;
        Core.Require((r.Stage=="quarantined" && r.Code==0)==success,"sequence outcome");
        Core.Require(m.Released==m.Allocated && r.Released==m.Allocated,"release count");
        Core.Require(m.Closed==(failure>=0 && failure<=4?0:1),"close count");
        Core.Require(m.Finalized==(failure==0?0:1),"finalize count");
        Core.Require(blob.All(x=>x==0),"blob wipe");
        if(failure>=0)Core.Require(m.Commands==(failure<5?0:failure-4),"stop after failure");
        if(failure==6)Core.Require(r.Observed[0]==0,"failed update output observed");
        if(failure==7)Core.Require(r.Observed[1]==0,"failed final output observed");
        if(mode==2)Core.Require(m.Commands==2 && r.Observed[0]==4033 && r.Counts[0]==0,"update overflow");
        if(mode>=3)Core.Require(m.Commands==3 && r.Counts[1]==0,"final overflow");
        for(int i=0;i<3;i++)Core.Require(r.Calls[i]==(m.Commands>i?1u:0u),"command budget");
    }
}
