using System;
using System.IO;
using System.Runtime.InteropServices;
internal static partial class Program {
 [DllImport("libc.so.6",EntryPoint="open",SetLastError=true)]static extern int ReceiptOpen(string p,int f,uint m);
 [DllImport("libc.so.6",EntryPoint="statx",SetLastError=true)]static extern int ReceiptStat(int fd,string p,int f,uint m,byte[] b);
 [DllImport("libc.so.6",EntryPoint="getuid")]static extern uint ReceiptUid();
 [DllImport("libc.so.6",EntryPoint="geteuid")]static extern uint ReceiptEuid();
 static FileStream Receipt(string name){
  Need(name=="native.receipt.json"||name=="selftest.receipt.json","fixed receipt name");string dir=Directory.GetCurrentDirectory(),prefix="/tmp/researcher-fm-";
  Need(dir.StartsWith(prefix,StringComparison.Ordinal)&&dir.Length==prefix.Length+32,"private nonce stage");foreach(char c in dir.Substring(prefix.Length))Need((c>='0'&&c<='9')||(c>='a'&&c<='f'),"stage nonce");
  byte[] s=new byte[256];Need(ReceiptStat(-100,dir,0x100,0xb,s)==0&&(BitConverter.ToUInt32(s,0)&0xb)==0xb,"receipt fields");
  Need(BitConverter.ToUInt16(s,28)==0x41c0&&BitConverter.ToUInt32(s,20)==ReceiptUid()&&ReceiptUid()==ReceiptEuid(),"receipt private owner/mode");
  int nofollow=RuntimeInformation.ProcessArchitecture==Architecture.Arm?0x8000:0x20000;int fd=ReceiptOpen(dir+"/"+name,1|0x40|0x80|0x80000|nofollow,0x180);Need(fd>=0,"exclusive receipt");return new FileStream(new Microsoft.Win32.SafeHandles.SafeFileHandle((IntPtr)fd,true),FileAccess.Write,4096,false);
 }
 static void Publish(FileStream f,string text){byte[] b=System.Text.Encoding.UTF8.GetBytes(text+"\n");Need(b.Length<=24576,"receipt bound");f.Write(b);f.Flush(true);}
 static int Main(string[] args){
  if(args.Length==1&&args[0]=="--self-test"){Console.WriteLine(SelfTest());return 0;}
  if(args.Length==1&&args[0]=="--fixture"){var x=Run(new FakeOps(),new FakeClock());Console.WriteLine(Serialize(x));return x.O.Accepted?0:1;}
  if(args.Length==1&&args[0]=="--receipt-self-test"){using var f=Receipt("selftest.receipt.json");Publish(f,SelfTest());return 0;}
  if(args.Length==3&&args[0]=="--execute"){
   if(args[1]!="--device"||!int.TryParse(args[2],out ExpectedDevice)||ExpectedDevice<1||ExpectedDevice>127||args[2]!=ExpectedDevice.ToString()||!RealOps.AbiReady)return 64;
   using var f=Receipt("native.receipt.json");var x=Run(new RealOps(),new RealClock());Publish(f,Serialize(x));return x.O.Accepted?0:1;
  }
  Console.WriteLine("{\"schema\":\"fm-dry-v1\",\"targetOperations\":0,\"restoreOnly\":true,\"arms\":0,\"uiOperations\":0}");return args.Length==0?0:64;
 }
}
