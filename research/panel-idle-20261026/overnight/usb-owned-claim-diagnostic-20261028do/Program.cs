using System;
using System.IO;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
internal static class Program {
 const string Boot="00000000-0000-4000-8000-000000000000",Usb="/sys/bus/usb/devices/7-1",Node="/dev/bus/usb/007/058",Driver=Usb+":1.2/driver";
 const string DeviceHex="12010002ef020140e8040120500201020301",Descriptors=DeviceHex+"090262000301048032080b00020202010a09040000010202010a052400100105240100010424020205240600010705830308001009040100020a00000a07050102400010070581024000000904020002ff0000000705820200020007050202000200";
 const uint ClaimRequest=0x8004550f,ReleaseRequest=0x80045510,GetDriverRequest=0x41045508;
 [DllImport("libc.so.6",SetLastError=true)]static extern int open(string path,int flags,uint mode);
 [DllImport("libc.so.6",SetLastError=true)]static extern int close(int fd);
 [DllImport("libc.so.6",SetLastError=true)]static extern int statx(int fd,string path,int flags,uint mask,[Out]byte[] data);
 [DllImport("libc.so.6",SetLastError=true)]static extern IntPtr read(int fd,[Out]byte[] data,UIntPtr length);
 [DllImport("libc.so.6",SetLastError=true)]static extern IntPtr readlink(string path,[Out]byte[] data,UIntPtr length);
 [DllImport("libc.so.6",EntryPoint="ioctl",SetLastError=true)]static extern int ioctlInterface(int fd,uint request,ref uint number);
 [DllImport("libc.so.6",EntryPoint="ioctl",SetLastError=true)]static extern int ioctlGetDriver(int fd,uint request,[In,Out]byte[] data);
 [DllImport("libc.so.6")]static extern uint getuid();[DllImport("libc.so.6")]static extern uint geteuid();
 sealed record Observation(bool Ok,string? Value,string? Error);
 sealed record Status(int Return,int Errno,uint Mask,ushort Mode,uint RdevMajor,uint RdevMinor,ulong Inode);
 sealed record DriverName(int Return,int Errno,string? Name,string RawBase64,string Sha256);
 sealed record LinkValue(long Count,int Errno,string? Target,string RawBase64);
 sealed class Snapshot {public long BeforeUs{get;set;}public long AfterUs{get;set;}public Dictionary<string,Observation> Managed{get;set;}=new();public LinkValue? NativeLink{get;set;}public Status? NoFollowStat{get;set;}public Status? FollowStat{get;set;}}
 sealed class Outcome {public string Schema{get;set;}="do-usb-owned-claim-diagnostic-v1";public int Device{get;set;}=58;public int Interface{get;set;}=2;public int VendorHeaders{get;set;}public int VendorBulkTransfers{get;set;}public int VendorControlTransfers{get;set;}
  public bool Opened{get;set;}public bool Claimed{get;set;}public bool Released{get;set;}=true;public bool Closed{get;set;}=true;public bool Accepted{get;set;}public bool DriverPolicyEstablished{get;set;}public bool PhysicalPictureObserved{get;set;}
  public int? ClaimReturn{get;set;}public int? ClaimErrno{get;set;}public int? ReleaseReturn{get;set;}public int? ReleaseErrno{get;set;}public int? CloseReturn{get;set;}public int? CloseErrno{get;set;}
  public Snapshot? PreDriver{get;set;}public Snapshot? PostDriver{get;set;}public DriverName? PreKernelDriver{get;set;}public DriverName? PostKernelDriver{get;set;}public Status? PreFd{get;set;}public Status? PostFd{get;set;}public List<string> Errors{get;}=new();}
 static void Need(bool b,string s){if(!b)throw new InvalidOperationException(s);}static long Now()=>checked((long)(Stopwatch.GetTimestamp()*(1_000_000.0/Stopwatch.Frequency)));
 static string Sha(byte[] b)=>Convert.ToHexString(SHA256.HashData(b)).ToLowerInvariant();
 static Observation Observe(Func<string?> f){try{return new(true,f(),null);}catch(Exception e){return new(false,null,e.GetType().Name+": "+e.Message);}}
 static Status Stat(int fd,string path,int flags){byte[] b=new byte[256];int r=statx(fd,path,flags,0x103,b),e=r<0?Marshal.GetLastWin32Error():0;return new(r,e,BitConverter.ToUInt32(b,0),BitConverter.ToUInt16(b,28),BitConverter.ToUInt32(b,128),BitConverter.ToUInt32(b,132),BitConverter.ToUInt64(b,32));}
 static Snapshot DriverSnapshot(){var s=new Snapshot{BeforeUs=Now()};s.Managed["linkTarget"]=Observe(()=>new DirectoryInfo(Driver).LinkTarget);s.Managed["resolvedFinal"]=Observe(()=>new DirectoryInfo(Driver).ResolveLinkTarget(true)?.FullName);s.Managed["directoryExists"]=Observe(()=>Directory.Exists(Driver).ToString());s.Managed["fileExists"]=Observe(()=>File.Exists(Driver).ToString());
  byte[] b=new byte[4096];long n=readlink(Driver,b,(UIntPtr)b.Length).ToInt64();int e=n<0?Marshal.GetLastWin32Error():0;int used=(int)Math.Clamp(n,0,b.Length);byte[] raw=b.AsSpan(0,used).ToArray();s.NativeLink=new(n,e,n>=0&&n<b.Length?Encoding.UTF8.GetString(raw):null,Convert.ToBase64String(raw));s.NoFollowStat=Stat(-100,Driver,0x100);s.FollowStat=Stat(-100,Driver,0);s.AfterUs=Now();return s;}
 static bool Absent(Snapshot s)=>s.Managed["linkTarget"] is {Ok:true,Value:null}&&s.Managed["directoryExists"] is {Ok:true,Value:"False"}&&s.Managed["fileExists"] is {Ok:true,Value:"False"};
 static DriverName GetDriver(int fd){byte[] b=new byte[260];BitConverter.GetBytes(2u).CopyTo(b,0);int r=ioctlGetDriver(fd,GetDriverRequest,b),e=r<0?Marshal.GetLastWin32Error():0;int nul=Array.IndexOf(b,(byte)0,4);string? name=r==0&&nul>=4?Encoding.UTF8.GetString(b,4,nul-4):null;return new(r,e,name,Convert.ToBase64String(b),Sha(b));}
 static byte[] CachedDescriptors(){using var f=File.OpenRead(Usb+"/descriptors");byte[] b=new byte[117];int n=0;while(n<b.Length){int c=f.Read(b,n,b.Length-n);if(c==0)return b.AsSpan(0,n).ToArray();n+=c;}throw new IOException("descriptor extent exceeds116");}
 static string Text(string name)=>File.ReadAllText(Usb+"/"+name).Trim();
 static void Identity(){Need(getuid()==0&&geteuid()==0,"root UID/EUID");Need(File.ReadAllText("/proc/sys/kernel/random/boot_id").Trim()==Boot,"boot");Need(Text("busnum")=="7"&&Text("devnum")=="58","fixed bus/device");Need(Text("idVendor")=="04e8"&&Text("idProduct")=="2001"&&Text("bConfigurationValue")=="1"&&Text("authorized")=="1"&&Text("power/runtime_status")=="active","cached identity/configuration");Need(Convert.ToHexString(CachedDescriptors()).Equals(Descriptors,StringComparison.OrdinalIgnoreCase),"full cached descriptors");
  string i=Usb+":1.2/";Need(File.ReadAllText(i+"bInterfaceNumber").Trim()=="02"&&File.ReadAllText(i+"bAlternateSetting").Trim()=="0"&&File.ReadAllText(i+"bInterfaceClass").Trim()=="ff"&&File.ReadAllText(i+"bInterfaceSubClass").Trim()=="00"&&File.ReadAllText(i+"bInterfaceProtocol").Trim()=="00","interface2");}
 static void FdIdentity(Status s){Need(s.Return==0&&(s.Mask&1)==1&&(s.Mode&0xf000)==0x2000&&s.RdevMajor==189&&s.RdevMinor==825,"fixed USB FD identity");}
 static Outcome Run(){var o=new Outcome();int fd=-1;try{long deadline=Now()+15_000_000;Identity();fd=open(Node,2|0x80000|0x8000,0);Need(fd>=0,"open errno="+Marshal.GetLastWin32Error());o.Opened=true;o.Closed=false;o.PreFd=Stat(fd,"",0x1000);FdIdentity(o.PreFd);
   byte[] d=new byte[18];long n=read(fd,d,(UIntPtr)18).ToInt64();Need(n==18&&Convert.ToHexString(d).Equals(DeviceHex,StringComparison.OrdinalIgnoreCase),"initial FD cached descriptor");
   o.PreDriver=DriverSnapshot();o.PreKernelDriver=GetDriver(fd);Need(Absent(o.PreDriver),"preclaim interface must be unbound");Identity();Need(Now()<deadline,"preclaim deadline");uint number=2;int r=ioctlInterface(fd,ClaimRequest,ref number);o.ClaimReturn=r;o.ClaimErrno=r<0?Marshal.GetLastWin32Error():0;Need(r==0,"claim failed");o.Claimed=true;o.Released=false;
   // Diagnostic observation, deliberately no post-claim driver acceptance gate.
   o.PostDriver=DriverSnapshot();o.PostKernelDriver=GetDriver(fd);o.PostFd=Stat(fd,"",0x1000);FdIdentity(o.PostFd);Identity();Need(Now()<deadline,"diagnostic deadline");
  }catch(Exception e){o.Errors.Add(e.GetType().Name+": "+e.Message);}finally{
   if(o.Claimed)try{uint number=2;int r=ioctlInterface(fd,ReleaseRequest,ref number);o.ReleaseReturn=r;o.ReleaseErrno=r<0?Marshal.GetLastWin32Error():0;o.Released=r==0;if(!o.Released)o.Errors.Add("release failed");}catch(Exception e){o.Errors.Add("release: "+e.Message);}
   if(fd>=0)try{int r=close(fd);o.CloseReturn=r;o.CloseErrno=r<0?Marshal.GetLastWin32Error():0;o.Closed=r==0;if(!o.Closed)o.Errors.Add("close failed");}catch(Exception e){o.Errors.Add("close: "+e.Message);}}
  o.Accepted=o.Errors.Count==0&&o.Opened&&o.Claimed&&o.Released&&o.Closed&&o.PostDriver!=null&&o.PostKernelDriver!=null;return o;}
 static string Serialize(object o)=>JsonSerializer.Serialize(o,new JsonSerializerOptions{PropertyNamingPolicy=JsonNamingPolicy.CamelCase});
 static string SelfTest(){int tests=0;void Check(bool b){Need(b,"self-test");tests++;}Check(GetDriverRequest==(0x40000000u|(260u<<16)|0x5508u));Check(((GetDriverRequest>>16)&0x3fff)==260);Check((GetDriverRequest&255)==8);Check(ClaimRequest==0x8004550f&&ReleaseRequest==0x80045510);Check(Descriptors.Length==232);var s=new Snapshot();s.Managed["linkTarget"]=new(true,null,null);s.Managed["directoryExists"]=new(true,"False",null);s.Managed["fileExists"]=new(true,"False",null);Check(Absent(s));s.Managed["linkTarget"]=new(true,"usbfs",null);Check(!Absent(s));s.Managed["linkTarget"]=new(false,null,"unknown");Check(!Absent(s));s.Managed["linkTarget"]=new(true,null,null);s.Managed["fileExists"]=new(true,"True",null);Check(!Absent(s));Check(Encoding.UTF8.GetBytes(Serialize(new Outcome())).Length<24576);return Serialize(new{selfTestsPassed=tests,targetOperations=0});}
 static FileStream Receipt(string name){Need(name=="selftest.receipt.json"||name=="native.receipt.json","fixed receipt");string dir=Directory.GetCurrentDirectory(),prefix="/tmp/researcher-do-";Need(dir.StartsWith(prefix,StringComparison.Ordinal)&&dir.Length==prefix.Length+32,"fixed private stage");foreach(char c in dir.Substring(prefix.Length))Need((c>='0'&&c<='9')||(c>='a'&&c<='f'),"nonce");byte[] s=new byte[256];Need(statx(-100,dir,0x100,0xb,s)==0&&(BitConverter.ToUInt32(s,0)&0xb)==0xb&&BitConverter.ToUInt16(s,28)==0x41c0&&BitConverter.ToUInt32(s,20)==getuid()&&getuid()==geteuid(),"private directory owner/mode");int nf=RuntimeInformation.ProcessArchitecture==Architecture.Arm?0x8000:0x20000;int fd=open(dir+"/"+name,1|0x40|0x80|0x80000|nf,0x180);Need(fd>=0,"exclusive receipt");return new FileStream(new Microsoft.Win32.SafeHandles.SafeFileHandle((IntPtr)fd,true),FileAccess.Write,4096,false);}
 static void Publish(FileStream f,string text){byte[] b=Encoding.UTF8.GetBytes(text+"\n");Need(b.Length<=24576,"receipt bound");f.Write(b,0,b.Length);f.Flush(true);}
 static int Main(string[] args){if(args.Length==1&&args[0]=="--self-test"){Console.WriteLine(SelfTest());return 0;}if(args.Length==1&&args[0]=="--receipt-self-test"){using var f=Receipt("selftest.receipt.json");Publish(f,SelfTest());return 0;}if(args.Length!=1||args[0]!="--execute"){Console.WriteLine("{\"schema\":\"do-usb-claim-dry-v1\",\"targetOperations\":0}");return args.Length==0?0:64;}if(RuntimeInformation.ProcessArchitecture!=Architecture.Arm||IntPtr.Size!=4||!BitConverter.IsLittleEndian){Console.WriteLine("REFUSED_ARM32_ABI");return 64;}using var receipt=Receipt("native.receipt.json");var o=Run();Publish(receipt,Serialize(o));return o.Accepted?0:1;}
}
