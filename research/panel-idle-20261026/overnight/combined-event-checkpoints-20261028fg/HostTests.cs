using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
internal static partial class Program {
 sealed class TestKey:IIntervention{public bool FailStart,FailBeforeStamp;public InterventionState State{get;}=new();public void Start(IClock c){Need(!State.Attempted,"one key");State.Attempted=true;if(FailBeforeStamp)throw new IOException("clock failure");State.ArmedUs=c.NowUs();if(FailStart)throw new IOException("thread start failure");foreach(var call in State.Calls){call.Started=call.Reaped=true;call.ExitCode=0;call.BeforeUs=call.AfterUs=State.ArmedUs;}}public void Finish(){State.Completed=State.Attempted;State.EndUs=State.ArmedUs;}}
 sealed class TestOps:IOps{
  public IReadOnlyList<BindingCheck> BindingChecks=>checks;readonly List<BindingCheck> checks=new();bool own;WindowSpec? pending;bool payload;public int Logger,Bulks,Writes,Releases,Closes,AfterClockBulks;public bool FailRelease,FailClose,JumpBeforeOptional;public int? FixedScan;public int FailAt=-1,FailDelta=-1,ThrowAt=-1,ClockAt=-1;public long Step=100;public int GateDriftAt=-1,ContextDriftAt=-1,LimitDriftAt=-1,GateAlreadyZeroAt=-1;public int FaultR=-1,QFrom=-1,ScanZeroFrom=-1;int rCount;public readonly List<string> Log=new();readonly FakeClock clock;
  public TestOps(FakeClock c){clock=c;}
  public Identity Preflight(){var b=ModelBinding(false,false,null);checks.Add(b);GuardNativeBinding(b);return new(7,60);}
  public void Revalidate(Identity id){var b=ModelBinding(own,true,own?UsbfsDriver:null);checks.Add(b);GuardNativeBinding(b);}
  public NativeResult Open(Identity id)=>new(9,0);public void ValidateFd(int fd,Identity id){}public NativeResult Claim(int fd){own=true;return new(0,0);}public NativeResult Release(int fd){Releases++;return new(FailRelease?-1:0,FailRelease?5:0);}public NativeResult Close(int fd){Closes++;return new(FailClose?-1:0,FailClose?5:0);}
  static void U(byte[] b,int at,int n)=>BitConverter.GetBytes((ushort)n).CopyTo(b,at);
  public NativeResult Bulk(int fd,bool input,byte[] b,int length){
   if(clock.ThrowAtCall>=0&&clock.Calls>clock.ThrowAtCall)AfterClockBulks++;int i=Bulks++;Log.Add((input?"IN":"OUT")+":"+length);clock.Value+=Step;if(i==ClockAt)clock.ThrowAtCall=clock.Calls;if(i==ThrowAt)throw new IOException("injected bulk");if(i==FailAt)return new(length+FailDelta,5);
   if(!input){if(payload){Need(length==2&&b[1]==0&&b[0]<=1,"fixed payload");Logger=b[0];Writes++;payload=false;return new(2,0);}if(b.AsSpan().SequenceEqual(LoggerHeader)){payload=true;return new(12,0);}pending=FindHeader(b);Need(pending!=null&&length==12,"fixed header");return new(12,0);}
   var s=pending!;Need(s!=null&&s.Length==length,"matching IN");Array.Clear(b,0,b.Length);
   if(s==R){rCount++;if(rCount==2&&JumpBeforeOptional){clock.Value=2_999_999;clock.JumpAtCall=clock.Calls+5;clock.JumpUs=3;}if(rCount==GateAlreadyZeroAt)Logger=0;U(b,6,rCount==GateDriftAt?3:Logger);U(b,0xc4,rCount==LimitDriftAt?200:40);U(b,0x30,200);U(b,0xc0,200);U(b,0x9e,1);U(b,0xe,1);if(rCount>=FaultR&&FaultR>0){U(b,0,1);U(b,0xa,0x1001);U(b,0xe,0);}else if(rCount>=QFrom&&QFrom>0)U(b,0xe,0);}
   if(s==M){BitConverter.GetBytes(0x20010000u).CopyTo(b,64);U(b,12,i==ContextDriftAt?1:2);b[56]=(byte)(FixedScan??(rCount>=FaultR&&FaultR>0||rCount>=ScanZeroFrom&&ScanZeroFrom>0?0:1));}
   if(s==C){U(b,0,2160);U(b,2,1920);U(b,4,2880);b[6]=92;b[8]=3;}
   if(s==Ring){U(b,0,4);b[12]=7;}pending=null;return new(length,0);
  }
 }
 static int tests;static void Check(bool b,string message){Need(b,message);tests++;}
 static string SmokeTest(){var c=new FakeClock();var a=new TestOps(c);var x=Run(a,c,new Config{MaxCycles=1},new TestKey());Need(x.O.Accepted&&x.O.HeadersSent==20&&x.O.BulkTransfers==40&&x.O.Writes==2&&x.Restore=="readback-zero"&&x.PreRing.Windows[0].Count==15372&&x.PostRing.Windows[0].Count==15372&&x.O.ScoreCheckpoints.Count==1,"compact zero-target smoke");return "{\"smokeTestsPassed\":8,\"targetOperations\":0}";}
 static string SelfTest(){tests=0;int max=0;
  Combined Case(Action<TestOps>? setup=null){var c=new FakeClock();var a=new TestOps(c);setup?.Invoke(a);var x=Run(a,c,new Config(),new TestKey());Check(a.Releases==1&&a.Closes==1,"cleanup lifecycle");max=Math.Max(max,System.Text.Encoding.UTF8.GetByteCount(Serialize(x))+1);return x;}
  foreach(string? fail in new string?[]{null,"down","hold","up"}){var k=new FakeKeyOps{Fail=fail,BadExit=false,Unreaped=false,Oversized=false};var key=new OneLeft(k);key.Start(new RealClock());key.Finish();Check(k.Calls.Contains("up")&&key.State.Completed,"up attempted despite child failure");}
  var good=Case();Check(good.O.Accepted&&good.O.ScoreCheckpoints.Count==56&&good.O.HeadersSent==460&&good.O.BulkTransfers==920&&good.O.Writes==2,"56cycles plus12controlpairs");Check(good.Restore=="readback-zero"&&good.PostRing.Windows[0].Count==15372,"sidecars restore");
  for(int i=0;i<good.O.BulkTransfers;i++){var x=Case(a=>a.FailAt=i);Check(!x.O.Accepted&&x.O.ProtocolPhase=="Unknown","any short means unknown");Check(x.O.BulkTransfers==i+1,"no header after unknown");}
  for(int i=0;i<28;i++){var x=Case(a=>a.ThrowAt=i);Check(!x.O.Accepted&&x.O.BulkTransfers==i+1,"exception stops no retry");}
  for(int i=0;i<28;i++){var x=Case(a=>a.ClockAt=i);Check(!x.O.Accepted&&x.O.ProtocolPhase=="ReadyForHeader","afterbulk clock failure completes pair");Check(x.O.BulkTransfers==(i/2+1)*2,"clock no next header");}
  for(int k=0;k<2;k++){var c=new FakeClock();var a=new TestOps(c);var key=new TestKey{FailStart=k==0,FailBeforeStamp=k==1};var failed=Run(a,c,new Config(),key);Check(!failed.O.Accepted&&failed.O.ScoreCheckpoints.Count==1,"key scheduling failure preserved complete baseline");Check(k==0?failed.Restore=="readback-zero":failed.Restore=="not-attempted","known scheduling failure cleanup / unknownclock noheader");}
  var cutoff=Case(a=>a.JumpBeforeOptional=true);Check(cutoff.O.BulkTransfers==24&&cutoff.O.ProtocolPhase=="ReadyForHeader"&&cutoff.Restore=="readback-zero"&&cutoff.O.Intervention?.Attempted!=true,"fresh preheader admission cutoff");
  var slow=Case(a=>a.Step=1_000_000);Check(!slow.ArmAttempted&&slow.O.Writes==0,"slowprearm refuses beforearm");
  var medium=Case(a=>a.Step=200_000);Check(medium.O.ProtocolPhase=="ReadyForHeader"&&medium.Restore=="readback-zero"&&!medium.O.Accepted&&medium.O.Intervention?.Attempted!=true,"partial cycle no key restored");
  var fault=Case(a=>a.FaultR=6);Check(fault.O.Accepted&&fault.O.OnsetObserved&&fault.Restore=="readback-zero","fault cleanup allowed");
  for(int scan=0;scan<3;scan++){byte[] m=new byte[68],c=new byte[16];BitConverter.GetBytes(0x20010000u).CopyTo(m,64);BitConverter.GetBytes((ushort)2).CopyTo(m,12);m[56]=(byte)scan;BitConverter.GetBytes((ushort)2160).CopyTo(c,0);BitConverter.GetBytes((ushort)1920).CopyTo(c,2);BitConverter.GetBytes((ushort)2880).CopyTo(c,4);c[6]=92;c[8]=3;bool allowed=true;try{Context(m,c);}catch{allowed=false;}Check(allowed==(scan<2),"finite lagged scan cleanup");}
  foreach(bool faultAtArm in new[]{false,true}){var armNotClean=Case(a=>{if(faultAtArm)a.FaultR=2;else a.QFrom=2;});Check(!armNotClean.O.Accepted&&armNotClean.Restore=="readback-zero"&&armNotClean.O.Intervention?.Attempted!=true&&armNotClean.O.BulkTransfers==24,"armed readbackQ/fault cleanup without observation");}
  foreach(int kind in new[]{0,1,2}){var firstNotClean=Case(a=>{if(kind==0)a.QFrom=3;else if(kind==1)a.FaultR=3;else a.ScanZeroFrom=3;});Check(!firstNotClean.O.Accepted&&firstNotClean.Restore=="readback-zero"&&firstNotClean.O.Intervention?.Attempted!=true&&firstNotClean.O.ScoreCheckpoints.Count==0,"initialQ/fault/scan0 stillcleanup noLeft");}
  var zeroInitial=Case(a=>a.FixedScan=0);Check(!zeroInitial.ArmAttempted&&zeroInitial.O.Writes==0,"prearm scan0 refuses noarm");
  var q=Case(a=>a.QFrom=5);Check(q.O.Accepted&&q.O.QuiescentCyclesCompleted>0,"Q retained not projected clean");
  var drift=Case(a=>a.GateDriftAt=115);Check(!drift.O.Accepted&&drift.O.Writes==1&&drift.Restore=="not-attempted","upper drift no restore");
  for(int t=0;t<40;t++){Check(Admit(t,40,30)==(t<=10),"pair reserve predicate");}
  for(int at=0;at<90;at++){var c=new FakeClock{ThrowAtCall=at};var a=new TestOps(c);var x=Run(a,c,new Config(),new TestKey());Check(!x.O.Accepted&&a.Bulks%2==0&&a.AfterClockBulks<=1,"preheaderclock no newheader/pendingcompletion");Check(a.Releases==(x.O.Claimed?1:0)&&a.Closes==(x.O.Opened?1:0),"clock lifecycle exact");}
  for(int i=0;i<28;i++){var over=Case(a=>{a.FailAt=i;a.FailDelta=1;});Check(over.O.ProtocolPhase=="Unknown"&&over.O.BulkTransfers==i+1,"overlong no nextheader");var negative=Case(a=>{a.FailAt=i;a.FailDelta=-20000;});Check(negative.O.ProtocolPhase=="Unknown"&&negative.O.BulkTransfers==i+1,"negative no nextheader");}
  var badRelease=Case(a=>a.FailRelease=true);Check(!badRelease.O.Accepted&&!badRelease.O.Released&&badRelease.O.Closed,"releasefail stillclose");var badClose=Case(a=>a.FailClose=true);Check(!badClose.O.Accepted&&badClose.O.Released&&!badClose.O.Closed,"closefail retained");
  var already=Case(a=>a.GateAlreadyZeroAt=115);Check(already.O.Accepted&&already.Restore=="already-zero-no-write"&&already.O.Writes==1,"fresh alreadyzero distinct");
  var earlyZero=Case(a=>a.GateAlreadyZeroAt=3);Check(!earlyZero.O.Accepted&&earlyZero.Restore=="already-zero-no-write"&&earlyZero.O.Intervention?.Attempted!=true,"earlyzero no key/no blindwrite");
  for(int i=1;i<=116;i++){var bad=Case(a=>a.LimitDriftAt=i);Check(!bad.O.Accepted,"fixed40 drift allreads "+i);}
  // Constructive serializer maximum: all bounded retention slots simultaneously full,
  // extreme integer widths and every error field that can coexist on one failure path.
  var wide=Case();string bounded=ShortError(new IOException(new string('\u0001',300)));
  foreach(var cap in wide.Controls)Widen(cap);foreach(var cap in new[]{wide.Initial,wide.Last,wide.Current,wide.PreRing,wide.PostRing})Widen(cap);
  void Widen(Capture cap){for(int i=0;i<cap.TransferCount;i++){cap.Transfers[i].BeforeUs=long.MaxValue-1;cap.Transfers[i].AfterUs=long.MaxValue;}}
  wide.O.StartUs=long.MaxValue-40000000;wide.O.EndUs=long.MaxValue;wide.O.DeadlineUs=long.MaxValue;wide.WholeDeadline=long.MaxValue;wide.O.Error=bounded;wide.CleanupError=bounded;wide.KeyError=bounded;
  wide.O.Intervention!.Error=bounded;wide.O.Intervention.ArmedUs=wide.O.Intervention.EndUs=long.MaxValue;
  foreach(var call in wide.O.Intervention.Calls){call.BeforeUs=call.AfterUs=long.MaxValue;call.Error=bounded;call.StdoutBytes=call.StderrBytes=1000000000;}
  wide.Current.Transfers[15].Error=bounded;max=Math.Max(max,System.Text.Encoding.UTF8.GetByteCount(Serialize(wide))+1);
  var rejectedBinding=new Combined();rejectedBinding.O.BindingChecks=new();for(int i=0;i<3;i++){var binding=ModelBinding(true,true,UsbfsDriver);rejectedBinding.O.BindingChecks.Add(binding with {Kernel=DriverRecord(0,0,new string('\u0001',255))});}max=Math.Max(max,System.Text.Encoding.UTF8.GetByteCount(Serialize(rejectedBinding))+1);
  Check(max<=OutputLimit,"all receipt lengths including stress and preheader binding bound "+max);
  return JsonSerializer.Serialize(new{selfTestsPassed=tests,targetOperations=0,maxReceiptBytes=max,sidecarBytes=15372,maxControlPairs=12,maxRows=56});
 }
}
