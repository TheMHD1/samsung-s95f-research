using System;
using System.IO;
using System.Collections.Generic;
using System.Text.Json;
internal static partial class Program
{
 sealed class FakeClock:IClock {public int Calls,Fail=-1;public long At;public long NowUs(){if(++Calls==Fail)throw new IOException("injected clock");return At+=100;}}
 sealed class FakeOps:IOps {
  public int Opens,Calls,Fail=-1,ThrowAt=-1,Releases,Closes,Revalidations,RevalidateFail=-1;public bool OpenFail,ClaimFail,ReleaseFail,CloseFail;public int GeometryFault;Spec? pending;
  readonly List<BindingCheck> bindingChecks=new();public IReadOnlyList<BindingCheck> BindingChecks=>bindingChecks;
  public bool OwnClaim,BindBeforeClaim,PostClaimDangling;public string? Driver,DriverAfterClaim=UsbfsDriver;
  void DriverGuard(){var b=ModelBinding(OwnClaim,Opens>0,Driver,PostClaimDangling);bindingChecks.Add(b);GuardNativeBinding(b);}
  public Identity Preflight(){Need(!OwnClaim,"fake initial ownership");DriverGuard();return new(7,57);}public NativeResult Open(Identity i){Opens++;return new(OpenFail?-1:10,0);}public void ValidateFd(int f,Identity i){Need(!OwnClaim,"fake initial FD validation");if(BindBeforeClaim)Driver=UsbfsDriver;}
  public void Revalidate(Identity i){if(++Revalidations==RevalidateFail)throw new IOException("instance race");DriverGuard();}public NativeResult Claim(int f){Need(!OwnClaim&&Driver==null&&f==10,"fake claim ownership");if(ClaimFail)return new(-1,0);OwnClaim=true;Driver=DriverAfterClaim;return new(0,0);}
  public NativeResult Release(int f){Releases++;Need(OwnClaim&&f==10,"fake release ownership");if(ReleaseFail)return new(-1,0);OwnClaim=false;Driver=null;return new(0,0);}public NativeResult Close(int f){Closes++;Need(f==10,"fake close identity");if(CloseFail)return new(-1,0);OwnClaim=false;Driver=null;return new(0,0);}
  static void H(byte[] b,int at,int v){b[at]=(byte)v;b[at+1]=(byte)(v>>8);}
  public NativeResult Bulk(int f,bool input,byte[] b,int n){Need(OwnClaim&&f==10,"fake bulk requires own claim");++Calls;if(Calls==ThrowAt)throw new IOException("injected bulk");if(Calls==Fail)return new(n-1,5);
   if(!input){Need(n==12&&pending==null&&AllowedHeader(b),"only fixed readheader");foreach(var s in Specs)if(b.AsSpan().SequenceEqual(Header(s))){pending=s;break;}Need(pending!=null,"fake pending");}
   else{Need(pending!=null&&pending.Length==n,"matching IN");var s=pending!;pending=null;
    if(s.Address==0x47012400){H(b,0,1);H(b,0xa,0x1001);H(b,16,GeometryFault==6?6:GeometryFault==9?65535:4);H(b,0x30,200);H(b,0xc0,200);H(b,0xc4,40);H(b,0x86,7);H(b,0x90,41);}
    else if(s.Name=="M"){BitConverter.GetBytes(0x20010000u).CopyTo(b,64);H(b,6,2880);H(b,8,1920);H(b,12,2);H(b,38,3183);H(b,40,500);H(b,42,40);if(GeometryFault==1)H(b,6,2879);if(GeometryFault==2)H(b,8,1919);if(GeometryFault==3)H(b,32,1);if(GeometryFault==4)b[64]^=1;}
    else if(s.Name=="C"){H(b,0,2160);H(b,2,1920);H(b,4,2880);b[7]=1;if(GeometryFault==5)b[0]^=1;if(GeometryFault==7)b[2]^=1;if(GeometryFault==8)b[4]^=1;}
    else if(s.Address==0x4700ba28)BitConverter.GetBytes(41u).CopyTo(b,0);
    else if(s.Name=="primary-lane-gate"){for(int i=0;i<68;i++)H(b,2*i,0x100|(i&1));}
    else if(s.Name=="secondary-lane-gate"){for(int i=0;i<68;i++)b[i]=(byte)(i%3);}
    else if(s.Length==104){for(int i=0;i<17;i++){byte[] packed=PackTestGroup(i*4+568,i*4+569,i*4+570,i*4+571);packed.CopyTo(b,i*6);}b[102]=0xff;b[103]=0xff;}
    else if(s.Length==96){for(int i=0;i<48;i++)H(b,2*i,s.Name=="X"?100+i:s.Name=="Y"?2159:s.Name=="RGB"?0:s.Name=="B"?20:700);}
   }return new(n,0);
  }
 }
 static string SelfTests(){int checks=0;void Check(bool x,string y){Need(x,y);checks++;}
  Outcome Test(FakeOps f,FakeClock? c=null){var o=Run(f,c??new());Check(f.Releases==(o.Claimed?1:0),"release once");Check(f.Closes==(f.Opens==1&&!f.OpenFail?1:0),"close once");return o;}
  var f=new FakeOps();var good=Test(f);Check(good.Accepted&&good.HeadersSent==16&&good.BulkTransfers==32&&good.Windows.Count==16&&good.PackingQualified,"one pass");Check(good.Writes==0&&good.UiOperations==0&&!good.AtomicSnapshot&&!good.PhysicalPictureObserved,"narrow claims");
  foreach(bool thrown in new[]{false,true})for(int i=1;i<=32;i++){f=new(){Fail=thrown?-1:i,ThrowAt=thrown?i:-1};var o=Test(f);Check(!o.Accepted&&f.Calls==i&&o.ProtocolPhase=="Unknown","stop after ambiguous transfer");}
  foreach(var fail in new[]{new FakeOps{OpenFail=true},new FakeOps{ClaimFail=true},new FakeOps{RevalidateFail=1},new FakeOps{RevalidateFail=2}}){var o=Test(fail);Check(!o.Accepted&&fail.Calls==0,"no header on precondition failure");}
  foreach(var fail in new[]{new FakeOps{Driver=UsbfsDriver},new FakeOps{Driver="/sys/bus/usb/drivers/other"},new FakeOps{BindBeforeClaim=true},new FakeOps{DriverAfterClaim=null},new FakeOps{DriverAfterClaim="/sys/bus/usb/drivers/other"},new FakeOps{PostClaimDangling=true}}){var o=Test(fail);Check(!o.Accepted&&fail.Calls==0,"unexpected ownership sends no header");}
  Check(!f.OwnClaim&&f.Driver==null,"own claim released");
  foreach(var fail in new[]{new FakeOps{ReleaseFail=true},new FakeOps{CloseFail=true}})Check(!Test(fail).Accepted,"cleanup failure rejected");
  for(int i=1;i<=100;i++){f=new();var o=Test(f,new FakeClock{Fail=i});Check(f.Calls<=32&&o.HeadersSent<=16,"clock no retry");if(!o.Accepted)Check(o.Errors.Count>0,"clock rejected");}
  f=new();var before=Test(f,new FakeClock{Fail=3});Check(!before.Accepted&&f.Calls==0&&before.ProtocolPhase=="ReadyForHeader","preheader failure noOUT");f=new();var after=Test(f,new FakeClock{Fail=4});Check(!after.Accepted&&f.Calls==2&&after.ProtocolPhase=="ReadyForHeader","acceptedheader completion");
  foreach(var s in Specs){Check(AllowedHeader(Header(s))&&InputLength(s.Length),"fixed spec");var h=Header(s);h[0]=2;Check(!AllowedHeader(h),"all writeheaders rejected");for(int bi=0;bi<12;bi++){var bad=Header(s);bad[bi]^=0x80;Check(!AllowedHeader(bad),"fixed header mutation rejected");}Check(s.Address>=0x47000000&&((ulong)s.Address+(ulong)s.Length)<=0x47020000,"SRAM alias bound");}
  Check(!InputLength(2)&&!InputLength(95)&&!AllowedHeader(new byte[12]),"arbitrary extent/header rejected");Check(System.Text.Encoding.UTF8.GetByteCount(Serialize(good))<24576,"structured extent");
  LaneGateSelfTests(Check);ReferenceSelfTests(Check);for(int g=1;g<=9;g++){f=new(){GeometryFault=g};var bad=Test(f);Check(!bad.Accepted&&!bad.PackingQualified&&f.Calls==20&&bad.Windows.Count==10&&bad.ProtocolPhase=="ReadyForHeader","packing drift refuses before new header");}
  return JsonSerializer.Serialize(new{selfTestsPassed=checks,targetOperations=0});
 }
}
