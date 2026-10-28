using System;
using System.IO;
using System.Runtime.InteropServices;
internal static partial class Program
{
    [DllImport("libc.so.6",EntryPoint="open",SetLastError=true)] static extern int ReceiptOpen(string path,int flags,uint mode);
    [DllImport("libc.so.6",EntryPoint="statx",SetLastError=true)] static extern int ReceiptStat(int dirfd,string path,int flags,uint mask,[Out]byte[] data);
    [DllImport("libc.so.6",EntryPoint="getuid")] static extern uint ReceiptUid();
    [DllImport("libc.so.6",EntryPoint="geteuid")] static extern uint ReceiptEuid();
    static FileStream Receipt(string name) {
      Need(name=="selftest.receipt.json"||name=="native.receipt.json","fixed receipt name");
      string dir=Directory.GetCurrentDirectory(),prefix="/tmp/researcher-dx-";Need(dir.StartsWith(prefix,StringComparison.Ordinal)&&dir.Length==prefix.Length+32,"private fixed stage path");
      foreach(char c in dir.Substring(prefix.Length))Need((c>='0'&&c<='9')||(c>='a'&&c<='f'),"stage nonce");
      byte[] st=new byte[256];Need(ReceiptStat(-100,dir,0x100,0xb,st)==0,"receipt directory stat");
      Need((BitConverter.ToUInt32(st,0)&0xb)==0xb,"receipt directory required fields");
      Need(BitConverter.ToUInt16(st,28)==0x41c0&&BitConverter.ToUInt32(st,20)==ReceiptUid()&&ReceiptUid()==ReceiptEuid(),"receipt directory mode/owner");
      int nofollow=RuntimeInformation.ProcessArchitecture==Architecture.Arm?0x8000:0x20000;
      int fd=ReceiptOpen(dir+"/"+name,1|0x40|0x80|0x80000|nofollow,0x180);Need(fd>=0,"exclusive receipt open errno="+Marshal.GetLastWin32Error());
      return new FileStream(new Microsoft.Win32.SafeHandles.SafeFileHandle((IntPtr)fd,true),FileAccess.Write,4096,false);
    }
    static void PublishReceipt(FileStream file,string json){byte[] raw=System.Text.Encoding.UTF8.GetBytes(json);Need(raw.Length<=24576,"receipt byte bound");file.Write(raw,0,raw.Length);file.Flush(true);}
    static int Main(string[] args){
      if(args.Length==1&&args[0]=="--self-test"){Console.WriteLine(SelfTests());return 0;}
      if(args.Length==1&&args[0]=="--receipt-self-test"){using var receipt=Receipt("selftest.receipt.json");PublishReceipt(receipt,SelfTests()+"\n");return 0;}
      if(args.Length==1&&args[0]=="--host-fixture"){Console.WriteLine(Serialize(Run(new FakeOps(),new FakeClock())));return 0;}
      bool execute=args.Length==3&&args[0]=="--execute";
      if(execute){if(args[1]!="--device"||!int.TryParse(args[2],out ExpectedDevice)||ExpectedDevice<1||ExpectedDevice>127||args[2]!=ExpectedDevice.ToString())return 64;}
      if(!execute){Console.WriteLine("{\"schema\":\"dx-code-fingerprint-dry-v1\",\"targetOperations\":0,\"writes\":0,\"uiOperations\":0,\"fixedReadPairs\":4}");return args.Length==0?0:64;}
      if(!RealOps.AbiReady){Console.WriteLine("REFUSED_ARM32_ABI");return 64;}
      using var nativeReceipt=Receipt("native.receipt.json");var o=Run(new RealOps(),new RealClock());PublishReceipt(nativeReceipt,Serialize(o)+"\n");return o.Accepted?0:1;
    }
}
