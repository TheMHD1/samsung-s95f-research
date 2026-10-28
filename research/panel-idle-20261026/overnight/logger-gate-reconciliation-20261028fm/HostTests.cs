using System;
using System.Collections.Generic;
using System.Text.Json;
internal static partial class Program {
 sealed class FakeOps:IOps {
  public IReadOnlyList<BindingCheck> BindingChecks=>Array.Empty<BindingCheck>();
  public int Calls,ShortAt=-1,ThrowAt=-1,HeaderCount,InputCount,Payloads,Gate=1,Subtype=0,Scan=1;public bool Released,Closed;public string? Drift;public RtState State=RtState.Quiescent;
  WindowSpec? pending;bool payload;
  public Identity Preflight()=>new(7,65);public NativeResult Open(Identity id)=>new(7,0);public void ValidateFd(int f,Identity id){}public void Revalidate(Identity id){}
  public NativeResult Claim(int f)=>new(0,0);public NativeResult Release(int f){Released=true;return new(0,0);}public NativeResult Close(int f){Closed=true;return new(0,0);}
  public NativeResult Bulk(int fd,bool input,byte[] b,int length){int at=Calls++;if(at==ThrowAt)throw new InvalidOperationException("injected");if(at==ShortAt)return new(length-1,0);
   if(payload){Need(!input&&length==2&&b.Length==2&&b[0]==0&&b[1]==0,"restore-only payload");payload=false;Payloads++;Gate=0;return new(2,0);}
   if(!input){Need(pending==null&&length==12,"one header");HeaderCount++;if(b.AsSpan().SequenceEqual(LoggerHeader)){payload=true;return new(12,0);}pending=FindHeader(b);Need(pending!=null,"fixed read header");return new(12,0);}
   Need(pending!=null&&length==pending.Length,"matching IN");InputCount++;Array.Clear(b,0,b.Length);
   void H(int o,int v){b[o]=(byte)v;b[o+1]=(byte)(v>>8);}
   if(pending==M){H(10,0);H(12,2);b[56]=(byte)Scan;BitConverter.GetBytes(0x20010000u).CopyTo(b,64);if(Drift=="root")b[64]=1;}
   if(pending==C){H(0,2160);H(2,1920);H(4,2880);b[6]=92;b[7]=1;b[8]=(byte)Subtype;if(Drift=="geometry")b[0]=0;}
   if(pending==R){H(6,Gate);H(0xc4,40);H(0x30,200);H(0xc0,200);H(0x9e,1);if(State==RtState.Clean)H(14,1);if(State==RtState.Faulted){H(0,1);H(10,4097);}if(State==RtState.Unexpected)H(14,2);if(Drift=="upper")H(6,257);if(Drift=="limit")H(0xc4,200);if(Drift=="alternative")H(0x9a,1);if(InputCount==4&&Drift=="readback-one")H(6,1);if(InputCount==4&&Drift=="readback-upper")H(6,256);}
   pending=null;return new(length,0);
  }
 }
 static string SelfTest(){int checks=0,cases=0;void Check(bool b){checks++;Need(b,"test "+checks);}
  Reconciliation Test(FakeOps a,FakeClock? c=null){cases++;var x=Run(a,c??new FakeClock());Check(a.Released&&a.Closed);Check(a.Payloads<=1);Check(x.O.Writes<=1);Check(System.Text.Encoding.UTF8.GetByteCount(Serialize(x))+1<=24576);return x;}
  foreach(int subtype in new[]{0,3})foreach(int scan in new[]{0,1})foreach(int gate in new[]{0,1}){var a=new FakeOps{Subtype=subtype,Scan=scan,Gate=gate};var x=Test(a);Check(x.O.Accepted);Check(x.O.HeadersSent==(gate==1?5:4));Check(x.O.BulkTransfers==(gate==1?10:8));Check(a.Payloads==gate);}
  foreach(int subtype in new[]{1,2,4,255}){var a=new FakeOps{Subtype=subtype};Check(!Test(a).O.Accepted);Check(a.Payloads==0);}
  foreach(string drift in new[]{"root","geometry","upper","limit","alternative"}){var a=new FakeOps{Drift=drift};Check(!Test(a).O.Accepted);Check(a.Payloads==0);}
  Check(!Test(new FakeOps{Scan=2}).O.Accepted);
  foreach(var state in new[]{RtState.Clean,RtState.Quiescent,RtState.Faulted})Check(Test(new FakeOps{State=state}).O.Accepted);
  Check(!Test(new FakeOps{State=RtState.Unexpected}).O.Accepted);
  for(int at=0;at<10;at++){foreach(bool throwing in new[]{false,true}){var a=new FakeOps();if(throwing)a.ThrowAt=at;else a.ShortAt=at;var x=Test(a);Check(!x.O.Accepted);Check(a.Calls==at+1);if(at<6)Check(a.Payloads==0);}}
  for(int clock=0;clock<26;clock++){var a=new FakeOps();var c=new FakeClock{ThrowAtCall=clock};cases++;var x=Run(a,c);Check(!x.O.Accepted||clock>=c.Calls);Check(a.Payloads<=1);if(x.O.Opened)Check(a.Released&&a.Closed);}
  // Four read pairs and one write payload pair; a late clock after accepted OUT
  // must preserve its exact IN/payload and stop before any later header.
  for(int clock=1;clock<24;clock++){var a=new FakeOps();var c=new FakeClock{ThrowAtCall=clock};var x=Run(a,c);Check(x.O.BulkTransfers%2==0);}
  foreach(int lateClock in new[]{14,15,16}){var a=new FakeOps();var x=Run(a,new FakeClock{ThrowAtCall=lateClock});Check(!x.O.Accepted&&a.Payloads==1&&x.O.HeadersSent==4&&x.O.BulkTransfers==8&&x.O.ProtocolPhase=="ReadyForHeader");}
  {var a=new FakeOps();var x=Run(a,new FakeClock{ThrowAtCall=13});Check(!x.O.Accepted&&a.Payloads==0&&x.O.HeadersSent==3);}
  {var a=new FakeOps();var x=Run(a,new FakeClock{JumpAtCall=13,JumpUs=23_000_001});Check(!x.O.Accepted&&a.Payloads==0&&x.O.HeadersSent==3);}
  foreach(string drift in new[]{"readback-one","readback-upper"}){var a=new FakeOps{Gate=0,Drift=drift};var x=Test(a);Check(!x.O.Accepted&&x.Restore=="observed-zero-unverified");using var j=JsonDocument.Parse(Serialize(x));Check(j.RootElement.GetProperty("loggerMayRemain").GetBoolean());}
  foreach(int fault in new[]{6,7}){var a=new FakeOps{Gate=0,ShortAt=fault};var x=Test(a);Check(!x.O.Accepted&&x.Restore=="observed-zero-unverified");using var j=JsonDocument.Parse(Serialize(x));Check(j.RootElement.GetProperty("loggerMayRemain").GetBoolean());}
  {var a=new FakeOps{Gate=0};var x=Run(a,new FakeClock{ThrowAtCall=16});Check(!x.O.Accepted&&x.Restore=="observed-zero-unverified");using var j=JsonDocument.Parse(Serialize(x));Check(j.RootElement.GetProperty("loggerMayRemain").GetBoolean());}
  return JsonSerializer.Serialize(new{schema="fm-host-tests-v1",checks,cases,targetOperations=0,restoreOnly=true});
 }
}
