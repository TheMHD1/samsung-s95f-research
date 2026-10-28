using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json;
using SwuSectionStream;

internal sealed class Source:IChunkSource
{
    readonly long length;public long Offset;public int MaxRead=int.MaxValue,ThrowAtCall=-1,BadCount;
    public int Calls,MaximumRequest;
    public Source(long length){this.length=length;}
    public int Read(Span<byte> target) {
        Calls++;MaximumRequest=Math.Max(MaximumRequest,target.Length);
        if(Calls==ThrowAtCall)throw new InvalidOperationException();
        if(BadCount!=0)return BadCount==1?-1:target.Length+1;
        int n=(int)Math.Min(Math.Min(target.Length,MaxRead),length-Offset);
        for(int i=0;i<n;i++)target[i]=(byte)((Offset+i)*17+3);
        Offset+=n;return n;
    }
}
internal sealed class Sink:IChunkSink,IDisposable
{
    public int Begins,Writes,Completes,Aborts,MaximumWrite;
    public bool FailBegin,FailWrite,ShortWrite,FailComplete,FailAbort;
    public long Confirmed;
    readonly IncrementalHash hash=IncrementalHash.CreateHash(HashAlgorithmName.SHA512);
    public void Begin(SectionPlan plan){Begins++;if(FailBegin)throw new InvalidOperationException();}
    public int Write(ReadOnlySpan<byte> bytes) {
        Writes++;MaximumWrite=Math.Max(MaximumWrite,bytes.Length);
        Tests.Need(bytes.Length<=65536 && bytes.ToArray().All(x=>x==0xa5),"sink receives only returned raw bytes");
        if(FailWrite)throw new InvalidOperationException();
        int n=ShortWrite?bytes.Length-1:bytes.Length;
        Confirmed+=n;hash.AppendData(bytes.Slice(0,n));return n;
    }
    public void CompleteRaw(){Completes++;if(FailComplete)throw new InvalidOperationException();}
    public void Abort(){Aborts++;if(FailAbort)throw new InvalidOperationException();}
    public string Hash()=>Convert.ToHexString(hash.GetHashAndReset()).ToLowerInvariant();
    public void Dispose()=>hash.Dispose();
}
internal sealed class Mock:ITeec,IDisposable
{
    public string Failure="",CleanupFailure="";
    public int Initializes,Allocations,Opens,Derives,Updates,Finals,Closes,Releases,Finalizes;
    public int MaximumInput,MaximumOutput;
    public uint UpdateOverride=uint.MaxValue,FinalOutput;
    public bool OverrideUpdate,Withhold16;
    public readonly List<string> Trace=new List<string>();
    readonly List<Block> descriptors=new List<Block>(),buffers=new List<Block>();
    public const uint NativeError=0xf1234567;
    static bool Zero(ReadOnlySpan<byte> data){foreach(byte b in data)if(b!=0)return false;return true;}
    uint Error(string label) {if(Failure=="throw-"+label)throw new InvalidOperationException();return Failure==label?NativeError:0;}
    public uint Initialize(Block c){Initializes++;Trace.Add("init");Tests.Need(c.Size==4&&Zero(c.Bytes),"zero context4");c.Put(0,1);return Error("init");}
    public uint Allocate(Block c,Block s) {
        int i=Allocations++;Trace.Add("alloc"+i);
        Tests.Need(s.Size==36&&s.Get(4)==65536&&s.Get(8)==3&&s.Get(0)==0&&Zero(s.Bytes.Slice(12)),"shared36 input flags/capacity/reserved");
        if(Failure=="throw-alloc"+i)throw new InvalidOperationException();
        if(Failure=="alloc"+i)return NativeError;
        descriptors.Add(s);buffers.Add(new Block(65536));s.Put(0,(uint)(0x1000+i*65536));
        if(Failure=="size"+i)s.Put(4,65535);
        if(Failure=="flags"+i)s.Put(8,1);
        return 0;
    }
    public BlockView Map(Block s) {
        int i=descriptors.IndexOf(s);Trace.Add("map"+i);
        if(Failure=="map"+i)return new BlockView(IntPtr.Zero,65536);
        if(Failure=="alias"+i&&i>0)return new BlockView(buffers[0].Pointer,65536);
        return new BlockView(buffers[i].Pointer,65536);
    }
    public uint Address(Block b) {
        int i=descriptors.IndexOf(b);
        if(Failure=="address"+i)return 0;
        if(Failure=="unaligned"+i)return 0x2001;
        if(Failure=="duplicate"+i&&i>0)return 0x2000;
        return (uint)(0x2000+i*36);
    }
    public uint Open(Block c,Block s,Block u,out uint origin) {
        Opens++;Trace.Add("open");origin=0x41;
        Tests.Need(s.Size==4&&Zero(s.Bytes)&&u.Size==16&&u.Get(0)==0x22222221&&u.Bytes[15]==1&&Zero(u.Bytes.Slice(4,11)),"session4/uuid16");
        s.Put(0,2);return Error("open");
    }
    public uint Invoke(Block s,uint cmd,Block op,out uint origin) {
        origin=0x42;Tests.Need(op.Size==60&&s.Get(0)==2,"operation60/session");
        int count=cmd==1?(int)op.Get(12):0;
        uint[] words=cmd==0?new uint[]{0,0x01010d0d,0x2000,416,0,0x2048,8,0,0,1,0,1,0x201,0,0}:
            cmd==1?new uint[]{0,0x00020e0d,0x2000,(uint)count,0,0x2024,65536,0,0,0,0,0,0,0,0}:
            new uint[]{0,0x0000020e,0x2024,65536,0,0,0,0,0,0,0,0,0,0,0};
        using Block expected=new Block(60);for(int i=0;i<words.Length;i++)expected.Put(i*4,words[i]);
        Tests.Need(op.Bytes.SequenceEqual(expected.Bytes),"independent golden full60 including cancellation tail");
        op.Put(56,0x12345678); // Backend tail write must not survive next frame.
        if(cmd==0){Derives++;Trace.Add("derive");Tests.Need(buffers[0].Bytes.Slice(0,416).ToArray().All(x=>x==0x42)&&buffers[2].Bytes.Slice(0,8).SequenceEqual(new byte[]{0,1,2,3,4,5,6,7}),"synthetic master/salt input");return Error("derive");}
        if(cmd==1) {
            Updates++;Trace.Add("update"+Updates);MaximumInput=Math.Max(MaximumInput,count);MaximumOutput=Math.Max(MaximumOutput,(int)op.Get(24));
            Tests.Need(Zero(buffers[2].Bytes),"salt wiped before updates");
            if(Failure=="throw-update")throw new InvalidOperationException();
            if(Failure=="update"||Failure=="update"+Updates)return NativeError;
            uint output=OverrideUpdate?UpdateOverride:(uint)(count-(Withhold16&&Updates==1?16:0));
            buffers[1].Bytes.Fill(0xa5);op.Put(32,output);return 0;
        }
        Tests.Need(cmd==2,"command allowlist");Finals++;Trace.Add("final");
        if(Failure=="throw-final")throw new InvalidOperationException();
        if(Failure=="final")return NativeError;
        buffers[1].Bytes.Fill(0xa5);op.Put(20,FinalOutput);return 0;
    }
    public void Close(Block s){Closes++;Trace.Add("close");if(CleanupFailure.Contains("close",StringComparison.Ordinal))throw new InvalidOperationException();s.Put(0,0);}
    public void Release(Block s) {
        int i=descriptors.IndexOf(s);Trace.Add("release"+i);Releases++;
        Tests.Need(i==descriptors.Count-Releases,"reverse release order");
        // Unmapped/bad-allocation paths contained no private inputs. All valid
        // mapped regions must be fully zero before release, including tails.
        Tests.Need(Zero(buffers[i].Bytes),"wipe complete shared buffer before release");
        if(CleanupFailure.Contains("release"+i,StringComparison.Ordinal))throw new InvalidOperationException();
    }
    public void FinalizeContext(Block c){Finalizes++;Trace.Add("finalize");if(CleanupFailure.Contains("finalize",StringComparison.Ordinal))throw new InvalidOperationException();c.Put(0,0);}
    public bool BuffersZero()=>buffers.All(b=>Zero(b.Bytes));
    public void Dispose(){foreach(Block b in buffers)b.Dispose();}
}
internal static class Tests
{
    static int checks,cases;
    static JsonElement anchors;
    public static void Need(bool ok,string code){if(!ok)throw new InvalidOperationException(code);checks++;}
    static SectionPlan Plan(long count) {
        string hash=anchors.GetProperty("rows").GetProperty(count.ToString()).GetProperty("cipherSha256").GetString()!;
        return new SectionPlan(count,hash,anchors.GetProperty("masterSha256").GetString()!,anchors.GetProperty("metadataPlanSha256").GetString()!);
    }
    static StreamResult Run(long count,Mock api,Source source,Sink sink,SectionPlan? plan=null,int guardFail=-1) {
        byte[] master=Enumerable.Repeat((byte)0x42,416).ToArray(),salt={0,1,2,3,4,5,6,7};int guards=0;
        StreamResult r=StreamingEngine.Run(api,plan??Plan(count),master,salt,source,sink,()=>{if(++guards==guardFail)throw new InvalidOperationException();});
        Need(master.All(x=>x==0x42)&&salt.SequenceEqual(new byte[]{0,1,2,3,4,5,6,7}),"caller owns original secret wiping");
        Need(api.Derives<=1&&api.Finals<=1&&r.TeecRetries==0,"never retry derive/final");
        Need(r.UpdateAttempts<=(plan??Plan(count)).MaximumUpdateCalls,"bounded update attempts");
        Need(api.BuffersZero(),"shared buffers zero after run");
        Need(!r.PaddingRemoved&&!r.PayloadAuthenticityValidated&&!r.WireSchemaComplete&&!r.FullSchemaValidated&&!r.FirmwareApplicabilityValidated,"raw-only scoped result");
        Need(source.MaximumRequest<=65536&&sink.MaximumWrite<=65536&&r.MaximumInputChunk<=65536&&r.MaximumOutputChunk<=65536,"memory/chunk bounds");
        cases++;return r;
    }
    static void Failure(long count,string failure,Stage expected,int release,int cmd1=0) {
        using Mock api=new Mock{Failure=failure};using Sink sink=new Sink();Source source=new Source(count);
        StreamResult r=Run(count,api,source,sink);
        Need(!r.Accepted&&r.FirstFailure==expected,"first failure stage");
        Need(r.Released==release&&api.Releases==release,"release owned resources");
        Need(api.Updates==cmd1&&sink.Completes==0&&sink.Aborts==1,"stop first failure and abort sink");
        if(new[]{"init","alloc0","alloc1","alloc2","open","derive","update","final"}.Contains(failure))Need(r.Code==Mock.NativeError,"preserve native error code");
    }
    public static int Main(string[] args) {
        try {
            using JsonDocument doc=JsonDocument.Parse(File.ReadAllBytes(args[0]));anchors=doc.RootElement;
            foreach(long n in new long[]{16,1040,65536,65552,131072,166416,196624}) {
                using Mock api=new Mock();using Sink sink=new Sink();Source source=new Source(n);
                StreamResult r=Run(n,api,source,sink);
                JsonElement a=anchors.GetProperty("rows").GetProperty(n.ToString());
                Need(r.Accepted&&r.CipherBytesRead==n&&r.RawBytesProduced==n&&r.SinkBytesConfirmed==n,"complete exact stream");
                Need(r.Command0Attempts==1&&r.UpdateAttempts==(n+65535)/65536&&r.FinalAttempts==1,"0 once/1 bounded/2 once");
                Need(r.InputEofObserved&&r.CipherDigestMatchedAtEof&&r.OwnedBuffersWipeConfirmed,"eof/digest/wipes");
                Need(r.RawEmittedSha512==a.GetProperty("outputSha512").GetString()&&sink.Hash()==r.RawEmittedSha512&&r.RawEmittedCrc32==a.GetProperty("outputCrc32").GetUInt32(),"independent Python raw-output hash/crc");
                Need(api.MaximumOutput==65536&&api.MaximumInput<=65536,"advertised shared capacity not4032");
                Need(api.Trace.IndexOf("final")<api.Trace.IndexOf("close")&&api.Trace.IndexOf("close")<api.Trace.IndexOf("release2")&&api.Trace.IndexOf("release0")<api.Trace.IndexOf("finalize"),"native reverse cleanup sequence");
            }
            using(Mock api=new Mock())using(Sink sink=new Sink()) {
                Source source=new Source(1040){MaxRead=7};StreamResult r=Run(1040,api,source,sink);
                Need(r.Accepted&&r.ReadCalls==150,"ReadExactly partial progress plus EOF");
            }
            using(Mock api=new Mock{Withhold16=true,FinalOutput=16})using(Sink sink=new Sink()) {
                StreamResult r=Run(166416,api,new Source(166416),sink);Need(r.Accepted&&r.RawBytesProduced==166416,"withheld block emitted once at final");
            }
            using(Mock api=new Mock{Withhold16=true})using(Sink sink=new Sink()) {
                StreamResult r=Run(1040,api,new Source(1040),sink);Need(r.Accepted&&r.RawBytesProduced==1024&&!r.PaddingRemoved,"returned1024 from1040 not engine unpadding");
            }
            Failure(1040,"init",Stage.Initialize,0);
            for(int i=0;i<3;i++) {
                Failure(1040,"alloc"+i,(Stage)((int)Stage.Allocate0+i),i);
                Failure(1040,"size"+i,(Stage)((int)Stage.Allocate0+i),i+1);
                Failure(1040,"flags"+i,(Stage)((int)Stage.Allocate0+i),i+1);
                Failure(1040,"map"+i,(Stage)((int)Stage.Map0+i),i+1);
                Failure(1040,"address"+i,(Stage)((int)Stage.Map0+i),i+1);
                Failure(1040,"unaligned"+i,(Stage)((int)Stage.Map0+i),i+1);
            }
            for(int i=1;i<3;i++){Failure(1040,"alias"+i,(Stage)((int)Stage.Map0+i),i+1);Failure(1040,"duplicate"+i,(Stage)((int)Stage.Map0+i),i+1);}
            Failure(1040,"open",Stage.Session,3);Failure(1040,"derive",Stage.Command0,3);
            Failure(1040,"update",Stage.Command1,3,1);Failure(1040,"final",Stage.Command2,3,1);
            Failure(166416,"update2",Stage.Command1,3,2);
            foreach(string failure in new[]{"throw-init","throw-alloc0","throw-alloc1","throw-alloc2","throw-open","throw-derive","throw-update","throw-final"})using(Mock api=new Mock{Failure=failure})using(Sink sink=new Sink()) {
                StreamResult r=Run(1040,api,new Source(1040),sink);
                Need(!r.Accepted&&r.BackendExceptionObserved&&r.Code==0xffff0006&&sink.Aborts==1,"backend exception stops without retry");
                Need(r.ResourceOwnershipUncertain==(failure is "throw-init" or "throw-alloc0" or "throw-alloc1" or "throw-alloc2" or "throw-open"),"unknown ownership explicit on exception");
            }
            foreach(string cleanup in new[]{"close","release2","release1","release0","finalize","close release2 release1 release0 finalize"}) {
                using Mock api=new Mock{CleanupFailure=cleanup};using Sink sink=new Sink();StreamResult r=Run(1040,api,new Source(1040),sink);
                Need(!r.Accepted&&r.CleanupFailures>=1&&r.FirstCleanupFailure!=Stage.None&&api.Releases==3&&api.Finalizes==1&&sink.Completes==0&&sink.Aborts==1,"cleanup errors continue and prevent sink completion");
            }
            using(Mock api=new Mock{Failure="update",CleanupFailure="close release2 release1 release0 finalize"})using(Sink sink=new Sink{FailAbort=true}) {
                StreamResult r=Run(1040,api,new Source(1040),sink);Need(r.FirstFailure==Stage.Command1&&r.Code==Mock.NativeError&&r.Origin==0x42&&r.CleanupFailures==6,"original native error/origin preserved through all cleanup errors");
            }
            for(int g=1;g<=5;g++)using(Mock api=new Mock())using(Sink sink=new Sink()) {
                StreamResult r=Run(1040,api,new Source(1040),sink,guardFail:g);Need(r.FirstFailure==Stage.Guard&&!r.Accepted&&sink.Completes==0,"guard failure no output completion");
            }
            foreach(long actual in new long[]{0,1039,1041})using(Mock api=new Mock())using(Sink sink=new Sink()) {
                StreamResult r=Run(1040,api,new Source(actual),sink);Need(!r.Accepted&&r.FirstFailure==(actual>1040?Stage.InputEof:Stage.InputCount)&&api.Finals==0,"truncated/extra exact input count stops final");
            }
            for(int bad=1;bad<=2;bad++)using(Mock api=new Mock())using(Sink sink=new Sink()) {
                StreamResult r=Run(1040,api,new Source(1040){BadCount=bad},sink);Need(r.FirstFailure==Stage.InputCount&&api.Updates==0,"invalid source read count");
            }
            using(Mock api=new Mock())using(Sink sink=new Sink()) {
                StreamResult r=Run(1040,api,new Source(1040){ThrowAtCall=1},sink);Need(r.FirstFailure==Stage.InputRead&&api.Finals==0,"source failure no final retry");
            }
            using(Mock api=new Mock())using(Sink sink=new Sink()) {
                StreamResult r=Run(1040,api,new Source(1040),sink,Plan(1040) with {CipherSha256=new string('0',64)});
                Need(r.FirstFailure==Stage.InputDigest&&api.Updates==1&&api.Finals==0&&sink.Aborts==1&&!r.CipherDigestMatchedAtEof,"rolling digest is checked only at EOF after update");
            }
            foreach(uint output in new uint[]{1041,65536,65537,uint.MaxValue})using(Mock api=new Mock{OverrideUpdate=true,UpdateOverride=output})using(Sink sink=new Sink()) {
                StreamResult r=Run(1040,api,new Source(1040),sink);Need(r.FirstFailure==Stage.UpdateCount&&sink.Writes==0&&api.Finals==0,"update advertised/aggregate output guard before sink");
            }
            foreach(uint output in new uint[]{1,65536,65537,uint.MaxValue})using(Mock api=new Mock{FinalOutput=output})using(Sink sink=new Sink()) {
                StreamResult r=Run(1040,api,new Source(1040),sink);Need(r.FirstFailure==Stage.FinalCount&&sink.Writes==1&&api.Finals==1,"final advertised/remaining aggregate output guard");
            }
            for(int mode=0;mode<5;mode++)using(Mock api=new Mock())using(Sink sink=new Sink{FailBegin=mode==0,FailWrite=mode==1,ShortWrite=mode==2,FailComplete=mode==3,FailAbort=mode==4}) {
                Source source=new Source(mode==4?1039:1040);StreamResult r=Run(1040,api,source,sink);
                Need(!r.Accepted&&sink.Aborts==1&&!r.SinkCompletedRaw,"sink failure never accepted");
                if(mode==0)Need(api.Initializes==0&&r.FirstFailure==Stage.SinkBegin,"begin failure before initialize");
                if(mode==1||mode==2)Need(api.Updates==1&&api.Finals==0&&r.SinkWriteMayHaveOccurred,"failed/partial sink no retry/final");
                if(mode==2)Need(r.SinkBytesConfirmed==1039&&r.FirstFailure==Stage.SinkCount,"partial sink accounting");
                if(mode==3)Need(r.SinkCompletionAttempted&&api.Finalizes==1&&r.FirstFailure==Stage.SinkComplete,"complete after native cleanup only");
                if(mode==4)Need(r.FirstFailure==Stage.InputCount&&r.FirstCleanupFailure==Stage.SinkAbort,"abort failure preserves input error");
            }
            foreach(SectionPlan plan in new[]{Plan(1040) with {CipherBytes=0},Plan(1040) with {CipherBytes=17},Plan(1040) with {CipherBytes=StreamingEngine.MaximumCipherBytes+16},Plan(1040) with {MetadataPlanSha256="bad"},Plan(1040) with {CipherSha256="bad"}})using(Mock api=new Mock())using(Sink sink=new Sink()) {
                StreamResult r=Run(1040,api,new Source(1040),sink,plan);Need(r.FirstFailure==Stage.Plan&&api.Initializes==0&&sink.Begins==0,"plan refused before effects");
            }
            using(Mock api=new Mock())using(Sink sink=new Sink()) {
                StreamResult r=Run(1040,api,new Source(1040),sink,Plan(1040) with {MasterBlobSha256=new string('0',64)});Need(r.FirstFailure==Stage.SecretPin&&api.Initializes==0,"master encrypted blob pin before TA");
            }
            using(Block op=new Block(60)) {
                foreach(int bad in new[]{0,1,15,65537}) {bool refused=false;try{StreamingEngine.Frame(op,1,1,2,3,bad);}catch(ArgumentException){refused=true;}Need(refused,"frame input count bounded/aligned");}
                bool rejected=false;try{StreamingEngine.Frame(op,3,1,2,3);}catch(ArgumentException){rejected=true;}Need(rejected,"frame command allowlist");
            }
            SectionPlan largest=Plan(1040) with {CipherBytes=StreamingEngine.MaximumCipherBytes};Need(largest.MaximumUpdateCalls==32768&&largest.MaximumRawOutputBytes==2147483648,"long section counters no4k framecount assumption");
            Console.WriteLine(JsonSerializer.Serialize(new {host_only=true,target_operations=0,real_tee_calls=0,cases,checks,max_chunk_bytes=65536,
                full_schema_validated=false,payload_authenticity_validated=false,actual_salts_or_keys_used=false}));return 0;
        } catch(Exception e) {Console.WriteLine("HOST_STREAM_TEST_FAILED code="+e.Message);return 1;}
    }
}
