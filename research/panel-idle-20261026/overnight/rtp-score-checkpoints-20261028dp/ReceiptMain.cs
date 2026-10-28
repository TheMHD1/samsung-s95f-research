using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text.Json;
internal static partial class Program
{
    [DllImport("libc.so.6",EntryPoint="open",SetLastError=true)] static extern int ReceiptOpen(string path,int flags,uint mode);
    [DllImport("libc.so.6",EntryPoint="statx",SetLastError=true)] static extern int ReceiptStat(int dirfd,string path,int flags,uint mask,[Out]byte[] data);
    [DllImport("libc.so.6",EntryPoint="getuid")] static extern uint ReceiptUid();
    [DllImport("libc.so.6",EntryPoint="geteuid")] static extern uint ReceiptEuid();
    static FileStream Receipt(string name) {
      Need(name=="selftest.receipt.json"||name=="native.receipt.json","fixed receipt name");
      string dir=Directory.GetCurrentDirectory(),prefix="/tmp/researcher-dp-";Need(dir.StartsWith(prefix,StringComparison.Ordinal)&&dir.Length==prefix.Length+32,"private fixed stage path");
      foreach(char c in dir.Substring(prefix.Length))Need((c>='0'&&c<='9')||(c>='a'&&c<='f'),"stage nonce");
      byte[] st=new byte[256];Need(ReceiptStat(-100,dir,0x100,0xb,st)==0,"receipt directory stat");
      Need((BitConverter.ToUInt32(st,0)&0xb)==0xb,"receipt directory required fields");
      Need(BitConverter.ToUInt16(st,28)==0x41c0&&BitConverter.ToUInt32(st,20)==ReceiptUid()&&ReceiptUid()==ReceiptEuid(),"receipt directory mode/owner");
      int nofollow=RuntimeInformation.ProcessArchitecture==Architecture.Arm?0x8000:0x20000;
      int fd=ReceiptOpen(dir+"/"+name,1|0x40|0x80|0x80000|nofollow,0x180);Need(fd>=0,"exclusive receipt open errno="+Marshal.GetLastWin32Error());
      return new FileStream(new Microsoft.Win32.SafeHandles.SafeFileHandle((IntPtr)fd,true),FileAccess.Write,4096,false);
    }
    static void PublishReceipt(FileStream file,string json){byte[] raw=System.Text.Encoding.UTF8.GetBytes(json);Need(raw.Length<=24576,"receipt byte bound");file.Write(raw,0,raw.Length);file.Flush(true);}
    static bool QualifiedBindingReady=>true; // switched only with reviewed DQ integration
    static int Main(string[] args){
      if(args.Length==1&&args[0]=="--receipt-self-test"){
        using var receipt=Receipt("selftest.receipt.json");using var writer=new StringWriter();var original=Console.Out;
        try{Console.SetOut(writer);SelfTest();KeySelfTest();CheckpointSelfTest();}finally{Console.SetOut(original);}
        string[] lines=writer.ToString().Split('\n',StringSplitOptions.RemoveEmptyEntries);Need(lines.Length==3,"three managed fake selftests");
        using var a=JsonDocument.Parse(lines[0]);using var b=JsonDocument.Parse(lines[1]);using var c=JsonDocument.Parse(lines[2]);
        Need(a.RootElement.GetProperty("selfTestsPassed").GetInt32()==93&&b.RootElement.GetProperty("keyTestsPassed").GetInt32()==22&&c.RootElement.GetProperty("checkpointTestsPassed").GetInt32()==44,"exact fake suite checks");
        PublishReceipt(receipt,JsonSerializer.Serialize(new{selfTestsPassed=93,keyTestsPassed=22,checkpointTestsPassed=44,targetOperations=0})+"\n");return 0;
      }
      if(args.Length==3&&args[0]=="--execute"){
        if(args[1]!="--device"||!int.TryParse(args[2],out ExpectedDevice)||ExpectedDevice<1||ExpectedDevice>127||args[2]!=ExpectedDevice.ToString())return 64;
        if(!QualifiedBindingReady)return 63;if(!RealOps.AbiReady)return 64;
        using var receipt=Receipt("native.receipt.json");var outcome=Run(new RealOps(),new RealClock(),new Config(),new OneLeft(new RealKeyOps()));
        outcome.ObservationAccepted=outcome.Accepted;outcome.Accepted=outcome.Accepted&&outcome.Intervention!=null&&outcome.Intervention.Completed&&outcome.Intervention.Error==null;
        PublishReceipt(receipt,Serialize(outcome)+"\n");return outcome.Accepted?0:1;
      }
      return HostMain(args);
    }
}
