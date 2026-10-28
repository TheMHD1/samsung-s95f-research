using System;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
internal static partial class Program {
 const long WholeBudgetUs=30_000_000,PairBudgetUs=4_000_000;
 static readonly byte[] LoggerOffPayload={0,0};
 static readonly int[] AlternativeOffsets={0x4a,0x4e,0x9a,0x9c};
 sealed class Reconciliation {
  public readonly Outcome O=new();public readonly Capture[] Caps={new(),new(),new(),new(),new()};public int Used;
  public long Deadline;public string Restore="not-attempted";public bool RestoreAttempted;
 }
 static bool Admit(long now,long deadline,long cost)=>now>=0&&now<=deadline&&cost<=deadline-now;
 static void LoggerR(byte[] r,int logger){
  Need(r.Length==256&&ClassifyRt(r)!=RtState.Unexpected,"known RT at40");Need(Half(r,6)==logger,"exact full logger halfword");
  Need(Half(r,0x30)==200&&Half(r,0xc0)==200&&Half(r,0x9e)==1,"R configured limit/gate profile");
  foreach(int at in AlternativeOffsets)Need(Half(r,at)==0,"R alternative gate/latch");
 }
 static void Context(byte[] m,byte[] c){
  Need(BitConverter.ToUInt32(m,64)==0x20010000&&Half(m,10)==0&&Half(m,12)==2&&m[56]<=1,"root/mode1/finite scan");
  Need(Half(c,0)==2160&&Half(c,2)==1920&&Half(c,4)==2880&&c[6]==92&&c[7]<=1&&(c[8]==0||c[8]==3),"C geometry/category/finite observed subtype");
 }
 static Capture Cap(Reconciliation x,string role){Need(x.Used<x.Caps.Length,"fixed capture capacity");var c=x.Caps[x.Used++];c.Begin(role,0);return c;}
 static byte[] Read(IOps ops,IClock clock,Reconciliation x,WindowSpec s,int fd,ref ProtocolPhase phase,long remainingCost){
  var c=Cap(x,"fresh-"+s.Name);Need(ReadPair(ops,clock,x.O,c,s,fd,ref phase,x.Deadline-remainingCost-PairBudgetUs+1,true)==PairResult.Complete,"complete "+s.Name);return c.Windows[0].Buffer;
 }
 static PairResult Restore(IOps ops,IClock clock,Reconciliation x,int fd,ref ProtocolPhase phase){
  var o=x.O;var cap=Cap(x,"restore");string? ce=null;long? before=Stamp(clock,ref ce);
  if(ce!=null){o.Error=ce;return PairResult.ClockFailure;}
  if(!Admit(before!.Value,x.Deadline,2*PairBudgetUs)){o.Error="restore/readback budget";return PairResult.Deadline;}
  phase=ProtocolPhase.Unknown;x.RestoreAttempted=true;x.Restore="header-attempted";NativeResult n;string? error=null;
  try{n=ops.Bulk(fd,false,LoggerHeader,12);}catch(Exception e){n=new(-1,0);error=ShortError(e);}
  o.HeadersSent++;o.BulkTransfers++;cap.AddTransfer(new(){Name="logger-header",Direction="OUT",Expected=12,Count=error==null?n.Value:null,Errno=n.Errno,BeforeUs=before,AfterUs=Stamp(clock,ref ce),Error=error});
  if(error!=null||n.Value!=12){o.Error=error??"logger header count";return PairResult.TransportFailure;}
  phase=ProtocolPhase.ExpectingPayload;before=Stamp(clock,ref ce);phase=ProtocolPhase.Unknown;error=null;
  // Accepted header always gets its one fixed matching payload, including clock failure.
  try{n=ops.Bulk(fd,false,LoggerOffPayload,2);}catch(Exception e){n=new(-1,0);error=ShortError(e);}
  o.BulkTransfers++;o.Writes++;o.BusContentsAltered=true;
  cap.AddTransfer(new(){Name="restore-payload",Direction="OUT",Expected=2,Count=error==null?n.Value:null,Errno=n.Errno,BeforeUs=before,AfterUs=Stamp(clock,ref ce),Error=error});
  if(error!=null||n.Value!=2){o.Error=error??"logger payload count";return PairResult.TransportFailure;}
  phase=ProtocolPhase.ReadyForHeader;x.Restore="payload-completed-unverified";
  if(ce!=null){o.Error=ce;return PairResult.ClockFailure;}return PairResult.Complete;
 }
 static Reconciliation Run(IOps ops,IClock clock){
  var x=new Reconciliation();var o=x.O;int fd=-1;var phase=ProtocolPhase.ReadyForHeader;
  try{
   o.StartUs=clock.NowUs();x.Deadline=checked(o.StartUs.Value+WholeBudgetUs);
   var id=ops.Preflight();o.Device=id.Device;var n=ops.Open(id);Need(n.Value>=0,"open");fd=n.Value;o.Opened=true;o.Closed=false;
   ops.ValidateFd(fd,id);ops.Revalidate(id);n=ops.Claim(fd);Need(n.Value==0,"claim");o.Claimed=true;o.Released=false;ops.Revalidate(id);o.BindingQualified=true;
   var m=Read(ops,clock,x,M,fd,ref phase,4*PairBudgetUs);var c=Read(ops,clock,x,C,fd,ref phase,3*PairBudgetUs);Context(m,c);
   var r=Read(ops,clock,x,R,fd,ref phase,2*PairBudgetUs);int gate=Half(r,6);Need(gate==0||gate==1,"logger upper-bit drift");LoggerR(r,gate);
   if(gate==1)Need(Restore(ops,clock,x,fd,ref phase)==PairResult.Complete,"restore pair");else x.Restore="observed-zero-unverified";
   var after=Read(ops,clock,x,R,fd,ref phase,0);LoggerR(after,0);x.Restore=gate==1?"readback-zero":"already-zero-no-write";
   o.TerminalReason="Reconciled";
  }catch(Exception e){o.Error??=ShortError(e);o.TerminalReason="Refused";}
  finally{
   if(o.Claimed)try{var n=ops.Release(fd);o.Released=n.Value==0;if(!o.Released)o.Error??="release failed";}catch(Exception e){o.Error??=ShortError(e);}
   if(o.Opened)try{var n=ops.Close(fd);o.Closed=n.Value==0;if(!o.Closed)o.Error??="close failed";}catch(Exception e){o.Error??=ShortError(e);}
   o.ProtocolPhase=phase.ToString();string? endError=null;o.EndUs=Stamp(clock,ref endError);o.Error??=endError;
   if(o.HeadersSent==0)o.BindingChecks=new(ops.BindingChecks);
   o.Accepted=o.Error==null&&o.EndUs.HasValue&&o.EndUs<=x.Deadline&&phase==ProtocolPhase.ReadyForHeader&&o.Opened&&o.Claimed&&o.Released&&o.Closed&&(x.Restore=="readback-zero"||x.Restore=="already-zero-no-write");
  }return x;
 }
 static string Serialize(Reconciliation x)=>JsonSerializer.Serialize(new{schema="logger-gate-reconciliation-fm-v1",accepted=x.O.Accepted,restore=x.Restore,restoreAttempted=x.RestoreAttempted,loggerMayRemain=x.Restore!="readback-zero"&&x.Restore!="already-zero-no-write",phase=x.O.ProtocolPhase,device=x.O.Device,bindingQualified=x.O.BindingQualified,bindingChecks=x.O.BindingChecks,opened=x.O.Opened,claimed=x.O.Claimed,released=x.O.Released,closed=x.O.Closed,error=x.O.Error,headers=x.O.HeadersSent,bulks=x.O.BulkTransfers,inputs=x.O.InputsCompleted,writes=x.O.Writes,retries=0,thresholdWrites=0,arms=0,uiOperations=0,resets=0,startUs=x.O.StartUs,endUs=x.O.EndUs,wholeDeadlineUs=x.Deadline,retained=x.Caps.Take(x.Used).Select(ToDto),physicalPictureObserved=false,atomicContextProven=false},new JsonSerializerOptions{PropertyNamingPolicy=JsonNamingPolicy.CamelCase,DefaultIgnoreCondition=JsonIgnoreCondition.WhenWritingNull});
}
