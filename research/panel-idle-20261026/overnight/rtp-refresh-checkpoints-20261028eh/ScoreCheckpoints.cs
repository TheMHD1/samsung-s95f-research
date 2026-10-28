using System;
using System.Security.Cryptography;
using System.Text.Json;
internal static partial class Program
{
 sealed class ScoreCheckpointBuffer
 {
  const int Size=54, Capacity=60;
  readonly byte[] raw=new byte[Size*Capacity];
  public string Schema=>"eh-refresh-checkpoints-v1";
  public int RecordBytes=>Size;
  public int Count{get;private set;}
  public string RawBase64=>Convert.ToBase64String(raw,0,Count*Size);
  public string Sha256=>Convert.ToHexString(SHA256.HashData(raw.AsSpan(0,Count*Size))).ToLowerInvariant();
  void U32(int at,uint value)=>BitConverter.TryWriteBytes(raw.AsSpan(at,4),value);
  uint Delta(long? value,long start){Need(value.HasValue&&value.Value>=start&&value.Value-start<=uint.MaxValue,"checkpoint timestamp extent");return (uint)(value!.Value-start);}
  public void Add(Capture c,long start){
   Need(Count<Capacity&&c.CycleIndex==Count+1&&c.WindowCount==8&&c.TransferCount==16,"checkpoint complete sequential cycle capacity");
   for(int i=0;i<8;i++)Need(c.Windows[i].Spec==CycleSpecs[i]&&c.Windows[i].Count==CycleSpecs[i].Length,"checkpoint fixed complete windows");
   int at=Count*Size;byte[] r=c.Windows[0].Buffer, e=c.Windows[7].Buffer, h=c.Windows[5].Buffer,n=c.Windows[4].Buffer;
   raw[at]=(byte)(((byte)ClassifyRt(r)<<4)|(byte)ClassifyRt(e));raw[at+1]=c.Windows[2].Buffer[7];
   Array.Copy(r,0xc4,raw,at+2,2);Array.Copy(e,0xc4,raw,at+4,2);
   Array.Copy(h,4,raw,at+6,4);Array.Copy(h,28,raw,at+10,2);Array.Copy(h,40,raw,at+12,8);
   Array.Copy(n,0,raw,at+20,4);
   U32(at+24,Delta(c.Transfers[10].BeforeUs,start));U32(at+28,Delta(c.Transfers[11].AfterUs,start));
   Array.Copy(c.Windows[1].Buffer,42,raw,at+32,2);
   // Appended source bytes only: earlier M/P reads and the completed end-R.
   byte[] m=c.Windows[1].Buffer,p=c.Windows[3].Buffer;
   Array.Copy(m,2,raw,at+34,2);Array.Copy(m,4,raw,at+36,2);
   Array.Copy(m,0x22,raw,at+38,2);Array.Copy(m,0x24,raw,at+40,2);
   Array.Copy(e,0x60,raw,at+42,2);Array.Copy(e,0x6e,raw,at+44,2);
   Array.Copy(p,4,raw,at+46,4);Array.Copy(p,8,raw,at+50,4);
   Count++;
  }
 }
 sealed class ScoreFakeOps:IOps {
  public readonly FakeOps Inner;int hCount,mCount,rCount;WindowSpec? pending;
  static void SetHalf(byte[] data,int at,int value)=>BitConverter.TryWriteBytes(data.AsSpan(at,2),(ushort)value);
  public ScoreFakeOps(FakeOps inner){Inner=inner;}
  public System.Collections.Generic.IReadOnlyList<BindingCheck> BindingChecks=>Inner.BindingChecks;public void Revalidate(Identity id)=>Inner.Revalidate(id);
  public Identity Preflight()=>Inner.Preflight();public NativeResult Open(Identity id)=>Inner.Open(id);public void ValidateFd(int fd,Identity id)=>Inner.ValidateFd(fd,id);public NativeResult Claim(int fd)=>Inner.Claim(fd);public NativeResult Release(int fd)=>Inner.Release(fd);public NativeResult Close(int fd)=>Inner.Close(fd);
  public NativeResult Bulk(int fd,bool input,byte[] data,int length){if(!input)pending=FindHeader(data);var r=Inner.Bulk(fd,input,data,length);if(input&&r.Value==length){if(length==96){Array.Clear(data,4,4);BitConverter.GetBytes(++hCount==20?44u:0u).CopyTo(data,4);Array.Clear(data,28,2);Array.Clear(data,40,8);}if(length==16)data[7]=1;if(length==68){mCount++;SetHalf(data,2,mCount);SetHalf(data,4,0x1100+mCount);SetHalf(data,0x22,0x2200+mCount);SetHalf(data,0x24,0x3300+mCount);}if(pending==P){BitConverter.GetBytes(0xa0000000u+(uint)mCount).CopyTo(data,4);BitConverter.GetBytes(0xb0000000u+(uint)mCount).CopyTo(data,8);}if(length==256){data[0xc4]=200;data[0xc5]=0;rCount++;SetHalf(data,0x60,0x4000+rCount);SetHalf(data,0x6e,0x5000+rCount);}}return r;}
 }
 static int ScoreFixture(string kind){
  var clock=new FakeClock();var inner=new FakeOps{Clock=clock};
  if(kind!="clean"){for(int i=0;i<(kind=="full"?119:118);i++)inner.RtStates.Add(RtState.Clean);inner.RtStates.Add(RtState.Faulted);inner.RtStates.Add(RtState.Faulted);}
  var trigger=new FakeIntervention{Ops=inner};var result=Run(new ScoreFakeOps(inner),clock,new Config{MaxCycles=60},trigger);long at=trigger.State.ArmedUs!.Value;
  foreach(var call in trigger.State.Calls){call.BeforeUs=at;call.AfterUs=at;call.ExitCode=0;call.Started=call.Reaped=true;}trigger.State.EndUs=at;result.ObservationAccepted=result.Accepted;
  Console.WriteLine(Serialize(result));return 0;
 }
 static int CheckpointSelfTest(){int tests=0;void Check(bool b,string s){Need(b,s);tests++;}
  var clock=new FakeClock();var ops=new FakeOps{Clock=clock};var clean=Run(ops,clock,new Config{MaxCycles=60,PeriodUs=10});
  Check(clean.Accepted&&clean.CleanCyclesCompleted==60&&clean.ScoreCheckpoints.Count==60,"all60clean cycles retain checkpoints");
  Check(clean.HeadersSent==480&&clean.BulkTransfers==960&&ops.Calls.FindAll(x=>x.StartsWith("out",StringComparison.Ordinal)).Count==480,"no added transactions");
  Check(Convert.FromBase64String(clean.ScoreCheckpoints.RawBase64).Length==60*54,"fixed54-byte bounded packed layout");
  var packed=Convert.FromBase64String(clean.ScoreCheckpoints.RawBase64);Check(packed[0]==0,"clean exact classifications");
  var retained=clean.Retained.Find(x=>x.Role=="last-clean")!;var last=packed.AsSpan(59*54,54);var hh=Convert.FromBase64String(retained.Windows[5].RawBase64!);var nn=Convert.FromBase64String(retained.Windows[4].RawBase64!);
  Check(last.Slice(6,4).SequenceEqual(hh.AsSpan(4,4))&&last.Slice(10,2).SequenceEqual(hh.AsSpan(28,2))&&last.Slice(12,8).SequenceEqual(hh.AsSpan(40,8))&&last.Slice(32,2).SequenceEqual(Convert.FromBase64String(retained.Windows[1].RawBase64!).AsSpan(42,2)),"exactH/M selected raw offsets");
  Check(last.Slice(20,4).SequenceEqual(nn.AsSpan(0,4)),"exactN selected raw offsets");
  var mm=Convert.FromBase64String(retained.Windows[1].RawBase64!);var pp=Convert.FromBase64String(retained.Windows[3].RawBase64!);var ee=Convert.FromBase64String(retained.Windows[7].RawBase64!);
  Check(last.Slice(34,2).SequenceEqual(mm.AsSpan(2,2))&&last.Slice(36,2).SequenceEqual(mm.AsSpan(4,2))&&last.Slice(38,2).SequenceEqual(mm.AsSpan(0x22,2))&&last.Slice(40,2).SequenceEqual(mm.AsSpan(0x24,2)),"exactM append sources");
  Check(last.Slice(42,2).SequenceEqual(ee.AsSpan(0x60,2))&&last.Slice(44,2).SequenceEqual(ee.AsSpan(0x6e,2))&&last.Slice(46,4).SequenceEqual(pp.AsSpan(4,4))&&last.Slice(50,4).SequenceEqual(pp.AsSpan(8,4)),"endR and earlierP append sources");
  clock=new(){Value=long.MaxValue-1_000_000_000};ops=new(){Clock=clock};for(int i=0;i<119;i++)ops.RtStates.Add(RtState.Clean);ops.RtStates.Add(RtState.Faulted);ops.RtStates.Add(RtState.Faulted);var trigger=new FakeIntervention{Ops=ops};var fault=Run(ops,clock,new Config{MaxCycles=60,PeriodUs=10},trigger);
  Check(fault.Accepted&&fault.ScoreCheckpoints.Count==60&&fault.CleanCyclesCompleted==59&&fault.OnsetObserved,"60th complete cycle fault retained");
  Check(fault.ScoreCheckpoints.Count==60&&Convert.FromBase64String(fault.ScoreCheckpoints.RawBase64)[59*54]==1,"fault-end classification");
  Check(trigger.Starts==1&&trigger.Finishes==1&&fault.Retained.Exists(c=>c.Role=="trigger-baseline"),"unchanged one key trigger semantics");
  foreach(var call in trigger.State.Calls){call.BeforeUs=clock.Value;call.AfterUs=clock.Value;call.ExitCode=0;call.Started=call.Reaped=true;call.StdoutBytes=call.StderrBytes=4096;}trigger.State.EndUs=clock.Value;
  int maximum=System.Text.Encoding.UTF8.GetByteCount(Serialize(fault));Check(maximum<=OutputLimit,"60checkpoint plus worst retained output bound="+maximum);
  Check(fault.BindingQualified&&fault.BindingChecks==null&&!Serialize(fault).Contains("bindingChecks",StringComparison.Ordinal),"successful trace keepscompactbindingflag only");
  clock=new();ops=new(){Clock=clock,FailPostBinding=true};var bindingRefusal=Run(ops,clock,new Config());Check(!bindingRefusal.Accepted&&!bindingRefusal.BindingQualified&&bindingRefusal.HeadersSent==0&&bindingRefusal.Released&&bindingRefusal.Closed&&bindingRefusal.BindingChecks?.Count==3&&System.Text.Encoding.UTF8.GetByteCount(Serialize(bindingRefusal))+1<=OutputLimit,"preheader bindingrefusal retainsfullaudit andcleanup");
  int lateMaximum=0;string escaped=new string('\u0001',240)+new string('"',240)+new string('é',240);
  string bounded=ShortError(new System.IO.IOException(escaped));Check(System.Text.Encoding.UTF8.GetByteCount(JsonSerializer.Serialize(bounded))<=128,"escaped error JSON byte bound");
  for(int fail=960;fail<974;fail++){
   clock=new(){Value=long.MaxValue-1_000_000_000};ops=new(){Clock=clock,FailBulkAt=fail,ThrowBulk=true,BulkError=escaped};for(int i=0;i<119;i++)ops.RtStates.Add(RtState.Clean);ops.RtStates.Add(RtState.Faulted);ops.RtStates.Add(RtState.Faulted);trigger=new(){Ops=ops};var rejected=Run(ops,clock,new Config{MaxCycles=60,PeriodUs=10},trigger);
   foreach(var call in trigger.State.Calls){call.BeforeUs=clock.Value;call.AfterUs=clock.Value;call.ExitCode=0;call.Started=call.Reaped=true;call.StdoutBytes=call.StderrBytes=4096;call.Error=bounded;}trigger.State.EndUs=clock.Value;trigger.State.Error=bounded;rejected.ObservationAccepted=false;
   int bytes=System.Text.Encoding.UTF8.GetByteCount(Serialize(rejected));lateMaximum=Math.Max(lateMaximum,bytes);Check(!rejected.Accepted&&rejected.ScoreCheckpoints.Count==60&&rejected.BindingChecks==null&&bytes+1<=OutputLimit,"late escaped postfault failure bounded, no extra binding audit");
  }
  Check(lateMaximum+1<=OutputLimit,"alllate failures hard receipt cap includesnewline");maximum=Math.Max(maximum,lateMaximum);
  for(int fail=0;fail<16;fail++){clock=new();ops=new(){Clock=clock,FailBulkAt=fail};var o=Run(ops,clock,new Config{MaxCycles=60,PeriodUs=10});Check(!o.Accepted&&o.ScoreCheckpoints.Count==0&&ops.BulkTransfers()==fail+1,"partial cycle never checkpointed or retried");}
  Console.WriteLine(JsonSerializer.Serialize(new{checkpointTestsPassed=tests,targetOperations=0,maxTestOutputBytes=maximum,recordBytes=54,maxCheckpoints=60}));return 0;
 }
}
