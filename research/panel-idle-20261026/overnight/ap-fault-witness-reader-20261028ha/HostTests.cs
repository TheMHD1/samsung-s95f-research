using System;
using System.IO;
using System.Collections.Generic;
using System.Text.Json;
internal static partial class Program
{
 sealed class FakeClock:IClock {public int Calls,Fail=-1;public long At;public int AdvanceAt=-1;public long Delta;public long NowUs(){if(++Calls==Fail)throw new IOException("injected clock");if(Calls==AdvanceAt)At+=Delta;return At+=100;}}
 sealed class FakeOps:IOps {
  public int Opens,Calls,Fail=-1,ThrowAt=-1,Releases,Closes,Revalidations,RevalidateFail=-1;public bool OpenFail,ClaimFail,ReleaseFail,CloseFail;Spec? pending;
  readonly List<BindingCheck> bindingChecks=new();public IReadOnlyList<BindingCheck> BindingChecks=>bindingChecks;
  public bool OwnClaim,BindBeforeClaim,PostClaimDangling;public string? Driver,DriverAfterClaim=UsbfsDriver;
  void DriverGuard(){var b=ModelBinding(OwnClaim,Opens>0,Driver,PostClaimDangling);bindingChecks.Add(b);GuardNativeBinding(b);}
  public Identity Preflight(){Need(!OwnClaim,"fake initial ownership");DriverGuard();return new(7,70);}public NativeResult Open(Identity i){Opens++;return new(OpenFail?-1:10,0);}public void ValidateFd(int f,Identity i){Need(!OwnClaim,"fake initial FD validation");if(BindBeforeClaim)Driver=UsbfsDriver;}
  public void Revalidate(Identity i){if(++Revalidations==RevalidateFail)throw new IOException("instance race");DriverGuard();}public NativeResult Claim(int f){Need(!OwnClaim&&Driver==null&&f==10,"fake claim ownership");if(ClaimFail)return new(-1,0);OwnClaim=true;Driver=DriverAfterClaim;return new(0,0);}
  public NativeResult Release(int f){Releases++;Need(OwnClaim&&f==10,"fake release ownership");if(ReleaseFail)return new(-1,0);OwnClaim=false;Driver=null;return new(0,0);}public NativeResult Close(int f){Closes++;Need(f==10,"fake close identity");if(CloseFail)return new(-1,0);OwnClaim=false;Driver=null;return new(0,0);}
  static void H(byte[] b,int at,int v){b[at]=(byte)v;b[at+1]=(byte)(v>>8);}
  public NativeResult Bulk(int f,bool input,byte[] b,int n){Need(OwnClaim&&f==10,"fake bulk requires own claim");++Calls;if(Calls==ThrowAt)throw new IOException("injected bulk");if(Calls==Fail)return new(n-1,5);
   if(!input){Need(n==12&&pending==null&&AllowedHeader(b),"only fixed readheader");foreach(var s in Specs)if(b.AsSpan().SequenceEqual(Header(s))){pending=s;break;}Need(pending!=null,"fake pending");}
   else{Need(pending!=null&&pending.Length==n,"matching IN");var s=pending!;pending=null;
    if(s.Address==0x47012400){H(b,0,1);H(b,0xa,0x1001);H(b,0xe,0);H(b,16,4);H(b,0xc4,40);}
    else if(s.Name=="AP"){H(b,0,0x1234);H(b,0x10,0x10);}
    else if(s.Name=="AP-EXCO-data"){H(b,0,0xabcd);H(b,8,0);}
    else if(s.Name=="AP-EXCO-context"){BitConverter.GetBytes(0x1000u).CopyTo(b,0);}
   }return new(n,0);
  }
 }
 static string SelfTests(){int checks=0;void Check(bool x,string y){Need(x,y);checks++;}
  Outcome Test(FakeOps f,FakeClock? c=null){var o=Run(f,c??new());Check(f.Releases==(o.Claimed?1:0),"release once");Check(f.Closes==(f.Opens==1&&!f.OpenFail?1:0),"close once");return o;}
  var f=new FakeOps();var good=Test(f);Check(good.Accepted&&good.HeadersSent==5&&good.BulkTransfers==10&&good.Windows.Count==5,"one pass");Check(good.Writes==0&&good.UiOperations==0&&!good.AtomicSnapshot&&!good.PhysicalPictureObserved,"narrow claims");
  foreach(bool thrown in new[]{false,true})for(int i=1;i<=10;i++){f=new(){Fail=thrown?-1:i,ThrowAt=thrown?i:-1};var o=Test(f);Check(!o.Accepted&&f.Calls==i&&o.ProtocolPhase=="Unknown","stop after ambiguous transfer");}
  foreach(var fail in new[]{new FakeOps{OpenFail=true},new FakeOps{ClaimFail=true},new FakeOps{RevalidateFail=1},new FakeOps{RevalidateFail=2}}){var o=Test(fail);Check(!o.Accepted&&fail.Calls==0,"no header on precondition failure");}
  foreach(var fail in new[]{new FakeOps{Driver=UsbfsDriver},new FakeOps{Driver="/sys/bus/usb/drivers/other"},new FakeOps{BindBeforeClaim=true},new FakeOps{DriverAfterClaim=null},new FakeOps{DriverAfterClaim="/sys/bus/usb/drivers/other"},new FakeOps{PostClaimDangling=true}}){var o=Test(fail);Check(!o.Accepted&&fail.Calls==0,"unexpected ownership sends no header");}
  Check(!f.OwnClaim&&f.Driver==null,"own claim released");
  foreach(var fail in new[]{new FakeOps{ReleaseFail=true},new FakeOps{CloseFail=true}})Check(!Test(fail).Accepted,"cleanup failure rejected");
  for(int i=1;i<=100;i++){f=new();var o=Test(f,new FakeClock{Fail=i});Check(f.Calls<=10&&o.HeadersSent<=5,"clock no retry");if(!o.Accepted)Check(o.Errors.Count>0,"clock rejected");}
  f=new();var before=Test(f,new FakeClock{Fail=3});Check(!before.Accepted&&f.Calls==0&&before.ProtocolPhase=="ReadyForHeader","preheader failure noOUT");f=new();var after=Test(f,new FakeClock{Fail=4});Check(!after.Accepted&&f.Calls==2&&after.ProtocolPhase=="ReadyForHeader","acceptedheader completion");
  f=new();var expired=Test(f,new FakeClock{AdvanceAt=2,Delta=40_000_000});Check(!expired.Accepted&&f.Calls==0,"deadline before first header");
  f=new();var pendingDeadline=Test(f,new FakeClock{AdvanceAt=4,Delta=40_000_000});Check(!pendingDeadline.Accepted&&f.Calls==2&&pendingDeadline.ProtocolPhase=="ReadyForHeader","deadline still completes promisedIN before refusal");
  foreach(var s in Specs){Check(AllowedHeader(Header(s))&&InputLength(s.Length),"fixed spec");var h=Header(s);h[0]=2;Check(!AllowedHeader(h),"all writeheaders rejected");for(int bi=0;bi<12;bi++){var bad=Header(s);bad[bi]^=0x80;Check(!AllowedHeader(bad),"fixed header mutation rejected");}Check((s.Address>=0x45000000&&((ulong)s.Address+(ulong)s.Length)<=0x45020000)||(s.Address>=0x47000000&&((ulong)s.Address+(ulong)s.Length)<=0x47020000),"full SRAM alias interval");}
  Check(!InputLength(2)&&!InputLength(95)&&!AllowedHeader(new byte[12]),"arbitrary extent/header rejected");Check(System.Text.Encoding.UTF8.GetByteCount(Serialize(good))<24576,"structured extent");
  return JsonSerializer.Serialize(new{selfTestsPassed=checks,targetOperations=0});
 }
}
