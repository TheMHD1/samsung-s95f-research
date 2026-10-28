using System;
using System.Collections.Generic;
internal static partial class Program
{
 static readonly int[] CandidateX={570,571,622,623,624,625,632,633};
 static void ValidatePacking(byte[] m,byte[] c){
  Need(m.Length==68&&c.Length==16,"packing metadata extent");
  Need(BitConverter.ToUInt32(m,64)==0x20010000u,"packing root");
  Need(BitConverter.ToUInt16(m,6)==2880&&BitConverter.ToUInt16(m,8)==1920&&BitConverter.ToUInt16(m,32)==0,"packing span/lanes/xbase");
  Need(BitConverter.ToUInt16(c,0)==2160&&BitConverter.ToUInt16(c,2)==1920&&BitConverter.ToUInt16(c,4)==2880,"packing context geometry");
 }
 static Dictionary<int,int> DecodeFixedCandidate(byte[] raw){
  Need(raw.Length==104,"fixed candidate exact extent");var lanes=new int[68];
  for(int group=0;group<17;group++){int at=group*6;uint word=BitConverter.ToUInt32(raw,at);int tail=BitConverter.ToUInt16(raw,at+4);
   lanes[group*4]=(int)(word&4095);lanes[group*4+1]=(int)((word>>12)&4095);lanes[group*4+2]=(int)(word>>24)|((tail&15)<<8);lanes[group*4+3]=tail>>4;}
  var values=new Dictionary<int,int>();foreach(int x in CandidateX)values.Add(x,lanes[x-568]);return values;
 }
 static byte[] PackTestGroup(int a,int b,int c,int d){
  // Independent 48-bit construction for host tests; never a controller output path.
  ulong bits=(ulong)(uint)a|((ulong)(uint)b<<12)|((ulong)(uint)c<<24)|((ulong)(uint)d<<36);var raw=new byte[6];
  for(int i=0;i<6;i++)raw[i]=(byte)(bits>>(8*i));return raw;
 }
 static void ReferenceSelfTests(Action<bool,string> check){
  byte[] raw=new byte[104];Convert.FromHexString("23614589c7ab").CopyTo(raw,78); // group155 => lane620..623
  var decoded=DecodeFixedCandidate(raw);check(decoded[622]==0x789&&decoded[623]==0xabc,"golden mixed nibbles");
  for(int group=0;group<17;group++)PackTestGroup(568+group*4,569+group*4,570+group*4,571+group*4).CopyTo(raw,group*6);
  raw[102]=raw[103]=0xff;decoded=DecodeFixedCandidate(raw);foreach(int x in CandidateX)check(decoded[x]==x,"exact fixed lane index");
  foreach(int size in new[]{0,96,102,103,105,120}){bool refused=false;try{DecodeFixedCandidate(new byte[size]);}catch(InvalidOperationException){refused=true;}check(refused,"fixed extent refusal");}
  foreach(var s in Specs)if(s.Name.StartsWith("fixed-",StringComparison.Ordinal)){check(s.Length==104,"fixed candidate length");check(Convert.ToHexString(Header(s)).ToLowerInvariant()==(s.Name=="fixed-top-candidate"?"010100005453014768000000":"010100006462014768000000"),"source qualified fixed header");}
  // Worst plus-heavy Base64 and 19-digit timestamps test the actual default JSON serializer.
  var worst=Run(new FakeOps(),new FakeClock());for(int wi=0;wi<worst.Windows.Count;wi++){var w=worst.Windows[wi];var bytes=new byte[w.Bytes];for(int i=0;i<bytes.Length;i++)bytes[i]=new byte[]{0xfb,0xef,0xbe}[i%3];worst.Windows[wi]=w with{Sha256=Sha(bytes),Base64=Convert.ToBase64String(bytes)};}
  for(int i=0;i<worst.Steps.Count;i++)worst.Steps[i]=worst.Steps[i] with{BeforeUs=long.MaxValue-1,AfterUs=long.MaxValue};
  worst.Errors.Add("late failure "+new string('"',128));
  check(System.Text.Encoding.UTF8.GetByteCount(Serialize(worst))+1<=24576,"worst plus escaping/late error/timestamps receipt extent");
 }
}
