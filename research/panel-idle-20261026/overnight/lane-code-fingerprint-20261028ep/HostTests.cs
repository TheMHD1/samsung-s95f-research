using System;
using System.IO;
using System.Collections.Generic;
using System.Text.Json;
internal static partial class Program
{
 // Reviewed324-byte instruction excerpts below are FakeOps data only, never executed.
 static readonly string[] SampleHex={"0148006870470000e0040020","f7f7c6fd05460024","42f21040405b06287eda8a480088012803d084480088012804d18748007808b1012000e0002081464ff0000b","15f8140000f0010090b96248005d10b1b9f1000f0cd0a2b201ab009633f814103b68c3f30b005346fff76efe00b963e0601c15f8100000f00100b8b95549601c085c10b1b9f1000f10d0631c9ab20df1040c00963cf813103b68c3f30b3000e087e05346fff750fe00b945e0a01c15f8100000f00100d0b94649a01c085c10b1b9f1000f13d000963b681b0eb7f804c00cf00f0c03eb0c20a31c9ab20df1040c3cf813105346fff72ffe00b924e0e01c15f8100000f00100a0b93649e01c085c10b1b9f1000f0dd0e31c9ab20df1040c00963cf81310bb8818095346fff714fe00b909e0","aa040020c6040020c8040020ca040020ac040020cc0400205cc90020a6040020"};
 sealed class FakeClock:IClock {public int Calls,Fail=-1,Backwards=-1;public long At;public long NowUs(){if(++Calls==Fail)throw new IOException("injected clock");At+=100;return Calls==Backwards?At-1000:At;}}
 sealed class LateFailClock:IClock {int calls;public long NowUs(){if(++calls>3)throw new IOException(new string('<',1000));return calls*100;}}
 sealed class FakeOps:IOps {
  public int Opens,Calls,Fail=-1,ThrowAt=-1,Releases,Closes,Revalidations,RevalidateFail=-1;public bool OpenFail,ClaimFail,ReleaseFail,CloseFail,PreflightFail,ValidateFail,ReleaseThrow,CloseThrow;public int Mismatch=-1,MismatchByte,ReadIndex;Spec? pending;
  readonly List<BindingCheck> bindingChecks=new();public IReadOnlyList<BindingCheck> BindingChecks=>bindingChecks;
  public bool OwnClaim,BindBeforeClaim,PostClaimDangling;public string? Driver,DriverAfterClaim=UsbfsDriver;
  void DriverGuard(){var b=ModelBinding(OwnClaim,Opens>0,Driver,PostClaimDangling);bindingChecks.Add(b);GuardNativeBinding(b);}
  public Identity Preflight(){Need(!OwnClaim,"fake initial ownership");DriverGuard();if(PreflightFail)throw new IOException("preflight injected");return new(7,57);}public NativeResult Open(Identity i){Opens++;return new(OpenFail?-1:10,0);}public void ValidateFd(int f,Identity i){Need(!OwnClaim,"fake initial FD validation");if(ValidateFail)throw new IOException("fd injected");if(BindBeforeClaim)Driver=UsbfsDriver;}
  public void Revalidate(Identity i){if(++Revalidations==RevalidateFail)throw new IOException("instance race");DriverGuard();}public NativeResult Claim(int f){Need(!OwnClaim&&Driver==null&&f==10,"fake claim ownership");if(ClaimFail)return new(-1,0);OwnClaim=true;Driver=DriverAfterClaim;return new(0,0);}
  public NativeResult Release(int f){Releases++;if(ReleaseThrow)throw new IOException("release injected");Need(OwnClaim&&f==10,"fake release ownership");if(ReleaseFail)return new(-1,0);OwnClaim=false;Driver=null;return new(0,0);}public NativeResult Close(int f){Closes++;if(CloseThrow)throw new IOException("close injected");Need(f==10,"fake close identity");if(CloseFail)return new(-1,0);OwnClaim=false;Driver=null;return new(0,0);}
  public NativeResult Bulk(int f,bool input,byte[] b,int n){Need(OwnClaim&&f==10,"fake bulk requires own claim");++Calls;if(Calls==ThrowAt)throw new IOException("injected bulk");if(Calls==Fail)return new(n-1,5);
   if(!input){Need(n==12&&pending==null&&AllowedHeader(b),"only fixed readheader");foreach(var s in Specs)if(b.AsSpan().SequenceEqual(Header(s))){pending=s;break;}Need(pending!=null,"fake pending");}
   else{Need(pending!=null&&pending.Length==n,"matching IN");var s=pending!;pending=null;
    int at=Array.IndexOf(Specs,s);Need(at>=0,"fixed fixture index");Convert.FromHexString(SampleHex[at]).CopyTo(b,0);if(ReadIndex++==Mismatch)b[MismatchByte]^=1;
   }return new(n,0);
  }
 }
 static string SelfTests(){int checks=0;void Check(bool x,string y){Need(x,y);checks++;}
  Outcome Test(FakeOps f,FakeClock? c=null){var o=Run(f,c??new());Check(f.Releases==(o.Claimed?1:0),"release once");Check(f.Closes==(f.Opens==1&&!f.OpenFail?1:0),"close once");return o;}
  var f=new FakeOps();var good=Test(f);Check(good.Accepted&&good.HeadersSent==5&&good.BulkTransfers==10&&good.Windows.Count==5&&good.SampledCodeMatch&&!good.WholeRunningImageAttested&&!good.ExecutableWriteQualified,"one pass");Check(good.Writes==0&&good.UiOperations==0&&!good.AtomicSnapshot&&!good.PhysicalPictureObserved,"narrow claims");
  foreach(bool thrown in new[]{false,true})for(int i=1;i<=10;i++){f=new(){Fail=thrown?-1:i,ThrowAt=thrown?i:-1};var o=Test(f);Check(!o.Accepted&&f.Calls==i&&o.ProtocolPhase=="Unknown","stop after ambiguous transfer");}
  foreach(var fail in new[]{new FakeOps{OpenFail=true},new FakeOps{ClaimFail=true},new FakeOps{RevalidateFail=1},new FakeOps{RevalidateFail=2}}){var o=Test(fail);Check(!o.Accepted&&fail.Calls==0,"no header on precondition failure");}
  foreach(var fail in new[]{new FakeOps{Driver=UsbfsDriver},new FakeOps{Driver="/sys/bus/usb/drivers/other"},new FakeOps{BindBeforeClaim=true},new FakeOps{DriverAfterClaim=null},new FakeOps{DriverAfterClaim="/sys/bus/usb/drivers/other"},new FakeOps{PostClaimDangling=true}}){var o=Test(fail);Check(!o.Accepted&&fail.Calls==0,"unexpected ownership sends no header");}
  Check(!f.OwnClaim&&f.Driver==null,"own claim released");
  foreach(var fail in new[]{new FakeOps{ReleaseFail=true},new FakeOps{CloseFail=true}})Check(!Test(fail).Accepted,"cleanup failure rejected");
  for(int i=1;i<=32;i++){f=new();var o=Test(f,new FakeClock{Fail=i});Check(f.Calls<=10&&o.HeadersSent<=5,"clock no retry");if(!o.Accepted)Check(o.Errors.Count>0,"clock rejected");}
  f=new();var before=Test(f,new FakeClock{Fail=3});Check(!before.Accepted&&f.Calls==0&&before.ProtocolPhase=="ReadyForHeader","preheader failure noOUT");f=new();var after=Test(f,new FakeClock{Fail=4});Check(!after.Accepted&&f.Calls==2&&after.ProtocolPhase=="ReadyForHeader","acceptedheader completion");
  foreach(var s in Specs){Check(AllowedHeader(Header(s))&&InputLength(s.Length),"fixed spec");var h=Header(s);h[0]=2;Check(!AllowedHeader(h),"all writeheaders rejected");Check(s.Address>=0x46000001&&((ulong)s.Address+(ulong)s.Length)<=0x46020000&&s.Address%4==0,"source-qualified code-bank interval");}
  for(int i=0;i<Specs.Length;i++)for(int at=0;at<Specs[i].Length;at++){f=new(){Mismatch=i,MismatchByte=at};var o=Test(f);Check(!o.Accepted&&!o.SampledCodeMatch&&f.Calls==(i+1)*2&&o.Windows.Count==i+1&&o.ProtocolPhase=="ReadyForHeader"&&o.Released&&o.Closed,"mismatch retains completed payload and stops without another header");}
  for(int i=0;i<Specs.Length;i++)Check(Sha(Convert.FromHexString(SampleHex[i]))==Fingerprints[i],"fixed reviewed sample identity");
  foreach(var spec in Specs)for(int at=0;at<12;at++){var header=Header(spec);header[at]^=1;Check(!AllowedHeader(header),"every changed fixed header rejected");}
  for(int length=0;length<=256;length++)Check(InputLength(length)==(length==8||length==12||length==32||length==44||length==228),"five fixed input length");
  foreach(var fail in new[]{new FakeOps{PreflightFail=true},new FakeOps{ValidateFail=true}}){var o=Test(fail);Check(!o.Accepted&&fail.Calls==0,"metadata exception sends no header");}
  foreach(var fail in new[]{new FakeOps{ReleaseThrow=true},new FakeOps{CloseThrow=true}}){var o=Test(fail);Check(!o.Accepted&&fail.Calls==10&&fail.Closes==1,"cleanup exception retained without repeated close");}
  f=new();var backwardBefore=Test(f,new FakeClock{Backwards=3});Check(!backwardBefore.Accepted&&f.Calls==0&&backwardBefore.ProtocolPhase=="ReadyForHeader","backward preheader clock sends nothing");
  f=new();var backwardAfter=Test(f,new FakeClock{Backwards=4});Check(!backwardAfter.Accepted&&f.Calls==2&&backwardAfter.ProtocolPhase=="ReadyForHeader","backward postheader clock still completes matching IN");
  Check(!InputLength(2)&&!InputLength(95)&&!AllowedHeader(new byte[12]),"arbitrary extent/header rejected");Check(System.Text.Encoding.UTF8.GetByteCount(Serialize(good))<24576,"structured extent");
  Check(WorstReceiptBytes()+1<=24576,"adversarial full-width escaped failure receipt including newline");
  foreach(string error in new[]{new string('<',1000),new string('"',1000),new string('\\',1000),new string('\u263a',1000),new string('x',100000)})Check(System.Text.Encoding.UTF8.GetByteCount(JsonSerializer.Serialize(ShortError(error)))<=128,"error JSON byte cap");
  var lateOps=new FakeOps{ReleaseThrow=true,CloseThrow=true};var late=Run(lateOps,new LateFailClock());
  Check(!late.Accepted&&late.Errors.Count==6&&lateOps.Calls==2&&late.ProtocolPhase=="ReadyForHeader"&&lateOps.Releases==1&&lateOps.Closes==1,"three late clock errors and both cleanup errors retain failure after one completed pair");
  foreach(string error in late.Errors)Check(System.Text.Encoding.UTF8.GetByteCount(JsonSerializer.Serialize(error))<=128,"actual late failure bounded JSON error");
  return JsonSerializer.Serialize(new{selfTestsPassed=checks,targetOperations=0});
 }
 static int WorstReceiptBytes(){
  // Deliberately over-approximates actual fixed outcomes, including malformed
  // driver metadata recorded before its rejection. No target operation occurs.
  var o=Run(new FakeOps(),new FakeClock());o.Accepted=false;o.Device=127;o.Opened=false;o.Claimed=false;o.Released=false;o.Closed=false;o.SampledCodeMatch=false;
  for(int i=0;i<o.Steps.Count;i++){var x=o.Steps[i];o.Steps[i]=x with {Count=int.MinValue,Errno=int.MinValue,BeforeUs=long.MaxValue,AfterUs=long.MaxValue};}
  for(int i=0;i<o.Windows.Count;i++){var x=o.Windows[i];o.Windows[i]=x with {Base64=new string('+',4*((x.Bytes+2)/3))};}
  var node=new NativeNode(int.MinValue,int.MinValue,uint.MaxValue,ushort.MaxValue,ulong.MaxValue,uint.MaxValue,uint.MaxValue);
  var kernel=new KernelDriver(int.MinValue,int.MinValue,new string('<',255),uint.MaxValue,new string('+',348),new string('f',64));
  o.BindingChecks.Clear();foreach(string stage in new[]{"before-open","unclaimed-fd","claimed-fd"})o.BindingChecks.Add(new(stage,false,false,node,node,node,kernel));
  for(int i=0;i<8;i++)o.Errors.Add(new string('<',1000));
  return System.Text.Encoding.UTF8.GetByteCount(Serialize(o));
 }
}
