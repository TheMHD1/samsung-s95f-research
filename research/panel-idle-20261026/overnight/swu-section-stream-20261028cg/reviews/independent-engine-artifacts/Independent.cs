using System;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json;
using SwuSectionStream;
sealed class Wrapped:ITeec,IDisposable {
 public readonly Mock Inner=new Mock(); public int Mode; int maps; BlockView first;
 public uint Initialize(Block c)=>Inner.Initialize(c);
 public uint Allocate(Block c,Block s)=>Inner.Allocate(c,s);
 public BlockView Map(Block s){var v=Inner.Map(s);int n=maps++;if(n==0)first=v;if(Mode==1&&n==1)return new BlockView(IntPtr.Add(first.Pointer,32768),65536);if(Mode==2&&n==0)return new BlockView(v.Pointer,65535);return v;}
 public uint Address(Block b)=>Inner.Address(b);
 public uint Open(Block c,Block s,Block u,out uint o)=>Inner.Open(c,s,u,out o);
 public uint Invoke(Block s,uint c,Block p,out uint o){uint r=Inner.Invoke(s,c,p,out o);if(Mode==3){p.Put(c==1?24:12,uint.MaxValue);p.Put(56,uint.MaxValue);}return r;}
 public void Close(Block s)=>Inner.Close(s);public void Release(Block s)=>Inner.Release(s);public void FinalizeContext(Block c)=>Inner.FinalizeContext(c);public void Dispose()=>Inner.Dispose();
}
sealed class BadSink:IChunkSink {public int Mode,Aborts,Completes;public void Begin(SectionPlan p){}public int Write(ReadOnlySpan<byte> p)=>Mode==0?-1:p.Length+1;public void CompleteRaw(){Completes++;}public void Abort(){Aborts++;}}
static class Independent {
 static int checks,cases; static void Need(bool v){checks++;if(!v)throw new Exception("independent check "+checks);}
 static SectionPlan Plan(){byte[] p=new byte[1040];for(int i=0;i<p.Length;i++)p[i]=(byte)(i*17+3);return new SectionPlan(1040,Convert.ToHexString(SHA256.HashData(p)).ToLowerInvariant(),Convert.ToHexString(SHA256.HashData(Enumerable.Repeat((byte)0x42,416).ToArray())).ToLowerInvariant(),new string('a',64));}
 static StreamResult Run(ITeec api,IChunkSink sink,SectionPlan? plan=null)=>StreamingEngine.Run(api,plan??Plan(),Enumerable.Repeat((byte)0x42,416).ToArray(),new byte[]{0,1,2,3,4,5,6,7},new Source(1040),sink,()=>{});
 public static void Main(){
 for(int mode=1;mode<=3;mode++){using var api=new Wrapped{Mode=mode};using var sink=new Sink();var r=Run(api,sink);cases++;if(mode<=2){Need(!r.Accepted);Need(r.FirstFailure==(mode==1?Stage.Map1:Stage.Map0));Need(api.Inner.Derives==0);Need(sink.Aborts==1);}else{Need(r.Accepted);Need(r.RawBytesProduced==1040);Need(r.Released==3);Need(sink.Completes==1);}Need(api.Inner.BuffersZero());}
 for(int mode=0;mode<2;mode++){using var api=new Mock();var sink=new BadSink{Mode=mode};var r=Run(api,sink);cases++;Need(!r.Accepted);Need(r.FirstFailure==Stage.SinkCount);Need(r.SinkBytesConfirmed==0);Need(api.Finals==0);Need(sink.Aborts==1);Need(r.Released==3);}
 using(var api=new Mock{OverrideUpdate=true,UpdateOverride=0})using(var sink=new Sink()){var r=Run(api,sink);cases++;Need(r.Accepted);Need(r.RawBytesProduced==0);Need(r.SinkBytesConfirmed==0);Need(!r.PayloadAuthenticityValidated);Need(r.RawEmittedSha512==Convert.ToHexString(SHA512.HashData(Array.Empty<byte>())).ToLowerInvariant());Need(r.RawEmittedCrc32==0);}
 using(var api=new Mock())using(var sink=new Sink()){var r=Run(api,sink,Plan() with{MetadataPlanSha256=new string('b',64)});cases++;Need(r.Accepted);Need(!r.FullSchemaValidated);}
 Console.WriteLine(JsonSerializer.Serialize(new{host_only=true,real_tee_calls=0,cases,independent_checks=checks,raw_transport_acceptance_does_not_assert_nonzero_plaintext=true,metadata_plan_identity_is_caller_bound=true,backend_returned_capacity_not_trusted=true}));
 }
}
