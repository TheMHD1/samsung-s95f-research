using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
internal static partial class Program {
 const long PairBudgetUs=4_000_000, MarginUs=2_000_000, CleanupReserveUs=6*PairBudgetUs+MarginUs, KeyJoinReserveUs=7_000_000, WholeBudgetUs=40_000_000;
 sealed class Combined {
  public readonly Outcome O=new(); public readonly List<Capture> Controls=new(10);public readonly Capture[] ControlPool=new Capture[10];public Combined(){for(int i=0;i<10;i++)ControlPool[i]=new();}
  public readonly Capture Initial=new(),Last=new(),Current=new(),PreRing=new(15372),PostRing=new(15372);
  public string Arm="not-attempted",Restore="not-attempted"; public bool ArmAttempted,RestoreAttempted,ObservationComplete;
  public bool KeyDispatched;public long WholeDeadline; public string? CleanupError,KeyError;
 }
 static bool Admit(long now,long deadline,long cost)=>now<=deadline&&cost<=deadline-now;
 static bool Budget(IClock c,Combined x,long cost){string? error=null;long? now=Stamp(c,ref error);x.O.Error??=error;return now.HasValue&&Admit(now.Value,x.WholeDeadline,cost);}
 static Capture Control(Combined x,string role){Need(x.Controls.Count<10,"fixed control capacity");var c=x.ControlPool[x.Controls.Count];c.Begin(role,0);x.Controls.Add(c);return c;}
 static bool ReadControl(IOps a,IClock c,Combined x,string role,WindowSpec spec,int fd,ref ProtocolPhase phase,out byte[] raw){
  var cap=Control(x,role);var p=ReadPair(a,c,x.O,cap,spec,fd,ref phase,x.WholeDeadline,true);raw=cap.WindowCount>0?cap.Windows[0].Buffer:Array.Empty<byte>();return p==PairResult.Complete;
 }
 static readonly int[] AlternativeOffsets={0x4a,0x4e,0x9a,0x9c};
 static readonly byte[] LoggerOnPayload={1,0},LoggerOffPayload={0,0};
 static void LoggerR(byte[] r,int logger){
  Need(r.Length>=256&&ClassifyRt(r)!=RtState.Unexpected,"known RT at200");Need(Half(r,6)==logger,"exact logger gate/upper bits");
  Need(Half(r,0x30)==200&&Half(r,0xc0)==200&&Half(r,0x9e)==1,"R configured limit/gate profile");
  foreach(int at in AlternativeOffsets)Need(Half(r,at)==0,"R alternative gate/latch");
 }
 static void Context(byte[] m,byte[] c,bool initial=false){
  Need(BitConverter.ToUInt32(m,64)==0x20010000&&Half(m,10)==0&&Half(m,12)==2&&m[56]<=1&&(!initial||m[56]==1),"root/mode1/finite scan");
  Need(Half(c,0)==2160&&Half(c,2)==1920&&Half(c,4)==2880&&c[6]==92&&c[7]<=1&&c[8]<=4&&(!initial||c[8]==3),"C geometry/category/selector");
 }
 static PairResult WriteLogger(IOps ops,IClock clock,Combined x,int fd,ref ProtocolPhase phase,bool arm){
  var o=x.O;var cap=Control(x,arm?"arm":"restore");string? ce=null;long? before=Stamp(clock,ref ce);
  if(ce!=null){o.Error=ce;return PairResult.ClockFailure;}long required=arm?2*PairBudgetUs+PairBudgetUs+CleanupReserveUs:3*PairBudgetUs+(x.KeyDispatched?KeyJoinReserveUs:0);
  if(!Admit(before!.Value,x.WholeDeadline,required)){o.Error="write pair budget";return PairResult.Deadline;}
  byte[] payload=arm?LoggerOnPayload:LoggerOffPayload;phase=ProtocolPhase.Unknown;
  if(arm){x.ArmAttempted=true;x.Arm="header-attempted";}else{x.RestoreAttempted=true;x.Restore="header-attempted";}
  NativeResult n;string? error=null;try{n=ops.Bulk(fd,false,LoggerHeader,12);}catch(Exception e){n=new(-1,0);error=ShortError(e);}
  o.HeadersSent++;o.BulkTransfers++;cap.AddTransfer(new(){Name="logger-header",Direction="OUT",Expected=12,Count=error==null?n.Value:null,Errno=n.Errno,BeforeUs=before,AfterUs=Stamp(clock,ref ce),Error=error});
  if(error!=null||n.Value!=12){o.Error=error??"logger header count";return PairResult.TransportFailure;}
  phase=ProtocolPhase.ExpectingPayload;before=Stamp(clock,ref ce);phase=ProtocolPhase.Unknown;
  error=null;try{n=ops.Bulk(fd,false,payload,2);}catch(Exception e){n=new(-1,0);error=ShortError(e);}
  o.BulkTransfers++;o.Writes++;o.BusContentsAltered=true;
  cap.AddTransfer(new(){Name=arm?"arm-payload":"restore-payload",Direction="OUT",Expected=2,Count=error==null?n.Value:null,Errno=n.Errno,BeforeUs=before,AfterUs=Stamp(clock,ref ce),Error=error});
  if(error!=null||n.Value!=2){o.Error=error??"logger payload count";return PairResult.TransportFailure;}
  phase=ProtocolPhase.ReadyForHeader;if(arm)x.Arm="payload-completed-unverified";else x.Restore="payload-completed-unverified";
  if(ce!=null){o.Error=ce;return PairResult.ClockFailure;}return PairResult.Complete;
 }
 static bool RingRead(IOps ops,IClock clock,Combined x,int fd,ref ProtocolPhase phase,bool post){
  Capture c=post?x.PostRing:x.PreRing;c.Begin(post?"post-ring":"baseline-ring",0);
  return ReadPair(ops,clock,x.O,c,Ring,fd,ref phase,x.WholeDeadline,true)==PairResult.Complete;
 }
 static Combined Run(IOps ops,IClock clock,Config config,IIntervention? key=null){
  Combined x=new();var o=x.O;ProtocolPhase phase=ProtocolPhase.ReadyForHeader;int fd=-1;bool clockLost=false;
  try{
   Need(config.MaxCycles>=1&&config.MaxCycles<=56&&config.DurationUs==2_000_000&&config.PeriodUs==25_000,"fixed observation caps");
   o.StartUs=clock.NowUs();x.WholeDeadline=checked(o.StartUs.Value+WholeBudgetUs);
   Identity id=ops.Preflight();o.Device=id.Device;var n=ops.Open(id);Need(n.Value>=0,"open");fd=n.Value;o.Opened=true;o.Closed=false;
   ops.ValidateFd(fd,id);ops.Revalidate(id);n=ops.Claim(fd);Need(n.Value==0,"claim");o.Claimed=true;o.Released=false;ops.Revalidate(id);o.BindingQualified=true;
   // Prearm reads cannot create a logger-write obligation. Each remains a full matching pair.
   Need(Budget(clock,x,PairBudgetUs)&&RingRead(ops,clock,x,fd,ref phase,false),"baseline ring");
   Need(Budget(clock,x,PairBudgetUs),"prearm pair budget");Need(ReadControl(ops,clock,x,"prearm-R",R,fd,ref phase,out var pre),"prearm R");LoggerR(pre,0);Need(ClassifyRt(pre)==RtState.Clean,"initial clean R");
   Need(Budget(clock,x,PairBudgetUs),"prearm pair budget");Need(ReadControl(ops,clock,x,"prearm-M",M,fd,ref phase,out var pm),"prearm M");
   Need(Budget(clock,x,PairBudgetUs),"prearm pair budget");Need(ReadControl(ops,clock,x,"prearm-C",C,fd,ref phase,out var pc),"prearm C");Context(pm,pc,true);
   Need(Budget(clock,x,2*PairBudgetUs+PairBudgetUs+CleanupReserveUs),"insufficient prearm reserve");
   Need(WriteLogger(ops,clock,x,fd,ref phase,true)==PairResult.Complete,"arm pair");
   Need(ReadControl(ops,clock,x,"armed-R",R,fd,ref phase,out var armed),"armed R");LoggerR(armed,1);x.Arm="readback-one";if(ClassifyRt(armed)!=RtState.Clean){o.TerminalReason="ArmedNotClean";return x;}
   o.DeadlineUs=checked(clock.NowUs()+config.DurationUs);o.TerminalReason="NotStarted";
   for(int cycle=1;cycle<=config.MaxCycles;cycle++){
    if(clock.NowUs()>=o.DeadlineUs){o.TerminalReason="TimeLimit";x.ObservationComplete=true;break;}
    x.Current.Begin("current",cycle);o.CyclesStarted++;bool full=true;
    foreach(var s in CycleSpecs){
     // Admission before EVERY optional pair reserves all six cleanup pairs plus explicit margin.
     if(clock.NowUs()>=o.DeadlineUs){o.TerminalReason="TimeLimitedPartial";full=false;break;}
     if(!Budget(clock,x,PairBudgetUs+CleanupReserveUs+KeyJoinReserveUs)){o.TerminalReason="BudgetLimitedPartial";full=false;break;}
     var p=ReadPair(ops,clock,o,x.Current,s,fd,ref phase,x.WholeDeadline-(PairBudgetUs+CleanupReserveUs+KeyJoinReserveUs)+1,true);
     if(p!=PairResult.Complete){clockLost=p==PairResult.ClockFailure;o.TerminalReason=p.ToString();full=false;break;}
     if(s==R){var currentR=x.Current.Windows[x.Current.WindowCount-1].Buffer;int logger=Half(currentR,6);LoggerR(currentR,logger==0?0:1);if(logger==0){o.TerminalReason="LoggerZeroDuringObservation";full=false;break;}}
    }
    if(!full)break;
    var start=ClassifyRt(x.Current.Windows[0].Buffer);var end=ClassifyRt(x.Current.Windows[7].Buffer);Context(x.Current.Windows[1].Buffer,x.Current.Windows[2].Buffer);
    if(cycle==1&&!(start==RtState.Clean&&end==RtState.Clean&&x.Current.Windows[1].Buffer[56]==1&&x.Current.Windows[2].Buffer[8]==3)){o.TerminalReason="InitialNotCleanOrScanOneOrC8Three";break;}
    o.ScoreCheckpoints.Add(x.Current,o.StartUs.Value);x.Last.CopyFrom(x.Current,"last-complete");
    if(start!=RtState.Faulted&&end!=RtState.Faulted){if(start==RtState.Clean&&end==RtState.Clean)o.CleanCyclesCompleted++;else o.QuiescentCyclesCompleted++;}
    if(cycle==1){x.Initial.CopyFrom(x.Current,"trigger-baseline");Need(Budget(clock,x,CleanupReserveUs+KeyJoinReserveUs),"key dispatch reserve");x.KeyDispatched=key!=null;try{key?.Start(clock);}catch(Exception e){x.KeyError=ShortError(e);o.TerminalReason="KeyStartFailure";if(key?.State.ArmedUs==null){clockLost=true;o.Error=x.KeyError;}break;}}
    if(start==RtState.Faulted||end==RtState.Faulted){o.OnsetObserved=cycle>1;o.TerminalReason=cycle>1?"TransitionCaptured":"AlreadyFaulted";x.ObservationComplete=cycle>1;break;}
    if(cycle==config.MaxCycles){o.TerminalReason="CycleLimit";x.ObservationComplete=true;break;}
    long left=o.DeadlineUs.Value-clock.NowUs();if(left>0)clock.SleepUs(Math.Min(left,config.PeriodUs));
   }
  }catch(Exception e){o.Error??=ShortError(e);if(o.TerminalReason=="NotStarted")o.TerminalReason="Refused";}
  finally{
   // Clock failure/Unknown disallows any new header, including a guessed restore.
   if(x.ArmAttempted&&phase==ProtocolPhase.ReadyForHeader&&!clockLost&&o.Error==null){
    try{
     Need(Budget(clock,x,CleanupReserveUs-MarginUs+(key?.State.Attempted==true?KeyJoinReserveUs:0)),"cleanup remaining budget");
     Need(ReadControl(ops,clock,x,"prerestore-M",M,fd,ref phase,out var m),"fresh restore M");
     Need(ReadControl(ops,clock,x,"prerestore-C",C,fd,ref phase,out var c),"fresh restore C");Context(m,c);
     Need(ReadControl(ops,clock,x,"prerestore-R",R,fd,ref phase,out var r),"fresh restore R");
     int gate=Half(r,6);Need(gate==0||gate==1,"logger upper bit drift");LoggerR(r,gate);
     if(gate==1)Need(WriteLogger(ops,clock,x,fd,ref phase,false)==PairResult.Complete,"restore pair");else x.Restore="observed-zero-unverified";
     Need(ReadControl(ops,clock,x,"restored-R",R,fd,ref phase,out var after),"restored R");LoggerR(after,0);x.Restore=gate==1?"readback-zero":"already-zero-no-write";
     Need(RingRead(ops,clock,x,fd,ref phase,true),"post ring");
    }catch(Exception e){x.CleanupError=ShortError(e);}
   }else if(x.ArmAttempted)x.CleanupError="no new header permitted: ambiguity, clock failure, or prior error";
   if(o.Claimed)try{var n=ops.Release(fd);o.Released=n.Value==0;if(!o.Released)o.Error??="release failed";}catch(Exception e){o.Error??=ShortError(e);}
   if(o.Opened)try{var n=ops.Close(fd);o.Closed=n.Value==0;if(!o.Closed)o.Error??="close failed";}catch(Exception e){o.Error??=ShortError(e);}
   try{key?.Finish();}catch(Exception e){x.KeyError=ShortError(e);}o.Intervention=key?.State;
   o.ProtocolPhase=phase.ToString();string? endError=null;o.EndUs=Stamp(clock,ref endError);o.Error??=endError;
   if(o.HeadersSent==0)o.BindingChecks=new(ops.BindingChecks);
   o.ObservationAccepted=x.ObservationComplete;o.Accepted=x.ObservationComplete&&o.EndUs.HasValue&&o.EndUs<=x.WholeDeadline&&o.Error==null&&x.CleanupError==null&&x.KeyError==null&&phase==ProtocolPhase.ReadyForHeader&&o.Released&&o.Closed&&(x.Restore=="readback-zero"||x.Restore=="already-zero-no-write")&&key?.State.Completed==true&&key.State.Error==null;
  }
  return x;
 }
 static object Compact(Capture c,bool raw=true)=>new{role=c.Role,cycle=c.CycleIndex,windows=Enumerable.Range(0,c.WindowCount).Select(i=>{
  var w=c.Windows[i];int count=Math.Max(0,Math.Min(w.Count,w.Spec!.Length));return new{name=w.Spec.Name,count=w.Count,raw=raw?Convert.ToBase64String(w.Buffer,0,count):null};}),
  transfers=Enumerable.Range(0,c.TransferCount).Select(i=>{var t=c.Transfers[i];return new object?[]{t.Direction,t.Expected,t.Count,t.Errno,t.BeforeUs,t.AfterUs,t.Error};})};
 static object RingMeta(Capture c)=>new{complete=c.WindowCount==1&&c.Windows[0].Count==15372,bytes=c.WindowCount==1?Math.Max(0,Math.Min(c.Windows[0].Count,15372)):0,sha256=c.WindowCount==1&&c.Windows[0].Count>0?Sha(c.Windows[0].Buffer.AsSpan(0,Math.Min(c.Windows[0].Count,15372)).ToArray()):Sha(Array.Empty<byte>()),transfer=Compact(c,false)};
 static string Serialize(Combined x)=>JsonSerializer.Serialize(new{schema="live-saver-event200-gg-v1",accepted=x.O.Accepted,observationComplete=x.ObservationComplete,arm=x.Arm,restore=x.Restore,armAttempted=x.ArmAttempted,restoreAttempted=x.RestoreAttempted,loggerMayRemain=x.ArmAttempted&&x.Restore!="readback-zero"&&x.Restore!="already-zero-no-write",phase=x.O.ProtocolPhase,device=x.O.Device,bindingQualified=x.O.BindingQualified,bindingChecks=x.O.BindingChecks,opened=x.O.Opened,claimed=x.O.Claimed,released=x.O.Released,closed=x.O.Closed,terminal=x.O.TerminalReason,error=x.O.Error,cleanupError=x.CleanupError,keyError=x.KeyError,headers=x.O.HeadersSent,bulks=x.O.BulkTransfers,inputs=x.O.InputsCompleted,writes=x.O.Writes,retries=0,threshold=200,physicalPictureObserved=false,keyCausalityEstablished=false,startUs=x.O.StartUs,endUs=x.O.EndUs,wholeDeadlineUs=x.WholeDeadline,observationDeadlineUs=x.O.DeadlineUs,cyclesStarted=x.O.CyclesStarted,cleanCycles=x.O.CleanCyclesCompleted,quiescentCycles=x.O.QuiescentCyclesCompleted,rows=x.O.ScoreCheckpoints,intervention=x.O.Intervention,controls=x.Controls.Select(c=>Compact(c)),retained=new[]{x.Initial,x.Last,x.Current}.Where(c=>c.Present).Select(c=>Compact(c)),baselineRing=RingMeta(x.PreRing),postRing=RingMeta(x.PostRing)},new JsonSerializerOptions{PropertyNamingPolicy=JsonNamingPolicy.CamelCase,DefaultIgnoreCondition=JsonIgnoreCondition.WhenWritingNull});
}
