using System;
internal static partial class Program
{
 static void ValidateLaneContext(byte[] r,byte[] m,byte[] c){
  ValidatePacking(m,c);Need(r.Length==256,"lane context R extent");
  Need(BitConverter.ToUInt16(r,16)<6,"ordinary lane gate operating mode");
 }
 static bool LaneEligible(ushort primary,byte secondary,ushort aa,ushort ac,byte enabled){
  bool sb=(aa==1||ac==1)&&enabled!=0;
  return (primary&1)==0&&(secondary==0||sb);
 }
 static void LaneGateSelfTests(Action<bool,string> check){
  foreach(ushort primary in new ushort[]{0,1,2,3,0x100,0x101,0xfffe,0xffff})
   foreach(byte secondary in new byte[]{0,1,255})
    foreach(ushort aa in new ushort[]{0,1,2,65535})
     foreach(ushort ac in new ushort[]{0,1,2,65535})
      foreach(byte enabled in new byte[]{0,1,255}){
       bool expected=primary%2==0&&(secondary==0||((aa==1||ac==1)&&enabled>0));
       check(LaneEligible(primary,secondary,aa,ac,enabled)==expected,"gate predicate truth table");
      }
  foreach(var s in Specs)if(s.Name.EndsWith("lane-gate",StringComparison.Ordinal))
   check(Convert.ToHexString(Header(s)).ToLowerInvariant()==(s.Name=="primary-lane-gate"?"010100007004014788000000":"0101000094cb004744000000"),"EA fixed lane gate header");
  for(int mode=0;mode<8;mode++){
   var r=new byte[256];var m=new byte[68];var c=new byte[16];
   BitConverter.GetBytes((ushort)mode).CopyTo(r,16);BitConverter.GetBytes(0x20010000u).CopyTo(m,64);
   BitConverter.GetBytes((ushort)2880).CopyTo(m,6);BitConverter.GetBytes((ushort)1920).CopyTo(m,8);
   BitConverter.GetBytes((ushort)2160).CopyTo(c,0);BitConverter.GetBytes((ushort)1920).CopyTo(c,2);BitConverter.GetBytes((ushort)2880).CopyTo(c,4);
   bool accepted=true;try{ValidateLaneContext(r,m,c);}catch(InvalidOperationException){accepted=false;}
   check(accepted==(mode<6),"ordinary mode guard is not category1");
  }
 }
}
