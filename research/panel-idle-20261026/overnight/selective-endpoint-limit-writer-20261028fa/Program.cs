using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;
using System.Threading;
internal static class Program
{
    const int TimeoutMs=2000;
    static int ExpectedDevice;
    const string ExpectedBoot="00000000-0000-4000-8000-000000000000";
    const string UsbRoot="/sys/bus/usb/devices/7-1";
    const string DeviceHex="12010002ef020140e8040120500201020301";
    const string AllDescriptorsHex=DeviceHex+"090262000301048032080b00020202010a09040000010202010a052400100105240100010424020205240600010705830308001009040100020a00000a07050102400010070581024000000904020002ff0000000705820200020007050202000200";
    readonly record struct Identity(int Bus,int Device) { public string Node=>$"/dev/bus/usb/{Bus:D3}/{Device:D3}"; }
    readonly record struct NativeResult(int Value,int Errno);
    sealed record Spec(string Name,uint Address,int Length);
    static readonly Spec Callback=new("Callback",0x45000580,64), R=new("R",0x47012400,256), M=new("M",0x470004a0,68), C=new("C",0x47000bc0,16);
    static readonly byte[] WriteHeader=Convert.FromHexString("02010000c424014702000000");
    static byte[] Header(Spec s) {byte[] b=new byte[12];BitConverter.GetBytes(0x101u).CopyTo(b,0);BitConverter.GetBytes(s.Address).CopyTo(b,4);BitConverter.GetBytes(s.Length).CopyTo(b,8);return b;}
    static bool AllowedHeader(byte[] b) {if(b.AsSpan().SequenceEqual(WriteHeader))return true;foreach(var s in new[]{Callback,R,M,C})if(b.AsSpan().SequenceEqual(Header(s)))return true;return false;}
    static void Need(bool b,string s){if(!b)throw new InvalidOperationException(s);}
    static int Half(byte[] b,int i)=>b[i]|b[i+1]<<8;
    static string Sha(byte[] b)=>Convert.ToHexString(SHA256.HashData(b)).ToLowerInvariant();
    static string ShortError(Exception e)=>e.GetType().Name+": "+e.Message;
    interface IOps {IReadOnlyList<BindingCheck> BindingChecks{get;} Identity Preflight();NativeResult Open(Identity id);void ValidateFd(int fd,Identity id);void Revalidate(Identity id);NativeResult Claim(int fd);NativeResult Bulk(int fd,bool input,byte[] data,int length);NativeResult Release(int fd);NativeResult Close(int fd);}
    interface IClock {long NowUs();void SleepUs(long us);}
    sealed record Step(string Name,string Direction,int Expected,int? Count,int Errno,long BeforeUs,long AfterUs,string Before,string After);
    sealed record Window(string Name,int Bytes,string Sha256,string Base64);
    sealed class Outcome {
      public int Device{get;set;} public string Schema{get;set;}="fa-fixed-limit-v1";public string Action{get;set;}="";public string ProtocolPhase{get;set;}="ReadyForHeader";public string Stage{get;set;}="preflight";
      public bool Opened{get;set;} public bool Claimed{get;set;} public bool Released{get;set;}=true;public bool Closed{get;set;}=true;
      public bool WriteAttempted{get;set;} public bool WriteTransportComplete{get;set;} public bool ReadbackVerified{get;set;} public bool LimitMayHaveChanged{get;set;} public bool Accepted{get;set;}
      public bool PhysicalPictureObserved{get;set;} public bool RootCauseFixEstablished{get;set;} public int HeadersSent{get;set;} public int BulkTransfers{get;set;}
      public List<BindingCheck> BindingChecks{get;}=new();public List<Step> Steps{get;}=new();public List<Window> Windows{get;}=new();public List<string> Errors{get;}=new();
    }
    static readonly byte[] Profile=Convert.FromHexString("[encoded-payload-omitted]");

    // Historical exclusions are unchanged. Additional model bytes require exact
    // source arithmetic or bounded echo; neither endpoint is an arbitrary wildcard.
    static bool DynamicR(int i)=>(i>=0x86&&i<0x8a)||(i>=0x8c&&i<0x8e)||(i>=0x90&&i<0x94)||(i>=0xa2&&i<0xa4);
    static bool ModelByte(int i)=>i==0x20||i==0x21||i==0x98||i==0x99||i==0xbc||i==0xbd||i==0xac||i==0xad;
    static int Endpoint(int basis,int reference,int temperature,int coefficient,int scale,int floor,int cap) {
      uint product=unchecked(((uint)basis+(uint)coefficient*unchecked((uint)(temperature-reference)))*(uint)scale);
      int candidate=(int)((product>>7)&65535u);return candidate>cap?cap:Math.Max(floor,candidate);
    }
    // Fixed exact image of Endpoint(T0..4095), base2075/reference24/coefficient15/scale195/floor3000/cap3800.
    // The >4000->25 source fallback applies to reference r8, not current temperature sl.
    static readonly int[] AlternateEndpointImage={3000,3001,3003,3024,3026,3046,3049,3069,3072,3092,3094,3115,3117,3138,3140,3161,3163,3183,3186,3206,3209,3229,3231,3252,3254,3275,3277,3298,3300,3321,3323,3343,3346,3366,3369,3389,3391,3412,3414,3435,3437,3458,3460,3481,3483,3503,3506,3526,3529,3549,3551,3572,3574,3595,3597,3618,3620,3641,3643,3663,3666,3686,3689,3709,3711,3732,3734,3755,3757,3778,3780,3800};
    static bool AlternateAllowed(int value)=>Array.BinarySearch(AlternateEndpointImage,value)>=0;
    static void GuardModel(byte[] r) {
      Need(Half(r,0x98)<=4095,"temperature mirror source range");Need(Half(r,0xac)<=254,"own echo range / zero high byte");
      int ordinary=Endpoint(Half(r,0x94),Half(r,0x96),Half(r,0x98),Half(r,0xae),Half(r,0xb0),Half(r,0x2e),Half(r,0xb2));
      Need(ordinary>=3000&&ordinary<=3800&&ordinary>500&&Half(r,0x20)==ordinary,"restrictive ordinary-current endpoint admission");
      Need(AlternateAllowed(Half(r,0xbc)),"alternate endpoint exact finite source image");
    }
    static void GuardPair(byte[] before,byte[] after) {
      Need(Half(before,0x20)==Half(after,0x20)&&Half(before,0x98)==Half(after,0x98)&&Half(before,0xbc)==Half(after,0xbc),"thermal tuple changed within transaction");
      for(int i=0;i<256;i++)if(!DynamicR(i)&&i!=0xc4&&i!=0xac&&i!=0xad)Need(before[i]==after[i],"unexpected R mutation "+i);
    }
    static void GuardR(byte[] r,int expected) {
      Need(r.Length==256,"R extent");
      for(int i=0;i<256;i++)if(!DynamicR(i)&&!ModelByte(i)&&i!=0xc4&&i!=0xc5&&i!=0xca)Need(r[i]==Profile[i],"R profile byte "+i);
      Need(r[0xca]<=1,"R observed selector domain");
      Need(Half(r,0)==0&&Half(r,0xa)==0&&Half(r,0xe)==1&&Half(r,6)==0,"R clean/gate/logger");
      Need(Half(r,0xc4)==expected&&Half(r,0x30)==200&&Half(r,0xc0)==200,"R limit");
      Need(Half(r,0x9e)==1&&Half(r,0x4a)==0&&Half(r,0x4e)==0&&Half(r,0x9a)==0&&Half(r,0x9c)==0,"R alternative gates/latches");
      GuardModel(r);
    }
    static void GuardContext(byte[] m,byte[] c,byte[] r) {
      Need(m.Length==68&&c.Length==16,"context extent");
      Need(BitConverter.ToUInt32(m,64)==0x20010000,"root");Need(Half(m,10)==0&&Half(m,12)==2,"mode1 flags");Need(m[56]==1,"scan enable");
      Need(Half(m,22)==500&&Half(m,24)==0&&Half(m,26)==500&&Half(m,28)==0&&Half(m,38)==Half(r,0x20)&&Half(m,40)==500,"numeric profile / validated ordinary endpoint mirror");
      Need(Half(c,0)==2160&&Half(c,2)==1920&&Half(c,4)==2880&&c[6]==92&&c[7]<=1&&c[8]==3,"C geometry/profile/selector");
    }
    static void GuardCallbacks(byte[] b){uint[] cb={0x2945d,0x293d1,0x294fb,0,0,0x28b85,0x28cf1,0x294f5};Need(b.Length==64,"callback extent");for(int i=0;i<cb.Length;i++)Need(BitConverter.ToUInt32(b,12+i*4)==cb[i],"callback tuple");}
    sealed class Controller {
      readonly IOps ops;readonly IClock clock;readonly Outcome o;readonly int fd;readonly long deadline;long last=-1;
      public Controller(IOps ops,IClock clock,Outcome o,int fd,long deadline){this.ops=ops;this.clock=clock;this.o=o;this.fd=fd;this.deadline=deadline;}
      long Time(){long v=clock.NowUs();Need(v>=last,"clock backwards");last=v;return v;}
      void Budget(){Need(o.ProtocolPhase=="ReadyForHeader","new header forbidden");Need(Time()+4_000_000<=deadline,"transaction budget");}
      void Transfer(string name,bool input,byte[] b,string after){string before=o.ProtocolPhase;long at=last<0?0:last;try{at=Time();}catch(Exception e){o.Errors.Add(ShortError(e));if(before=="ReadyForHeader")throw;}o.ProtocolPhase="Unknown";NativeResult n;try{n=ops.Bulk(fd,input,b,b.Length);}catch{ o.Steps.Add(new(name,input?"IN":"OUT",b.Length,null,0,at,at,before,"Unknown"));o.BulkTransfers++;if(b.Length==12)o.HeadersSent++;throw;}
        o.BulkTransfers++;if(!input&&b.Length==12)o.HeadersSent++;if(n.Value==b.Length)o.ProtocolPhase=after;
        // Accepted header creates a matching transfer obligation even if the clock fails.
        long end=at;try{end=Time();}catch(Exception e){o.Errors.Add(ShortError(e));}
        o.Steps.Add(new(name,input?"IN":"OUT",b.Length,n.Value,n.Errno,at,end,before,o.ProtocolPhase));Need(n.Value==b.Length,"short/failed transfer "+name);
      }
      public byte[] Read(string name,Spec s){Budget();Transfer(name+"-header",false,Header(s),"ExpectingReadIn");byte[] b=new byte[s.Length];Transfer(name+"-data",true,b,"ReadyForHeader");o.Windows.Add(new(name,b.Length,Sha(b),Convert.ToBase64String(b)));Need(o.Errors.Count==0,"clock error after completed read");return b;}
      public void Write(int value){Budget();o.WriteAttempted=true;o.LimitMayHaveChanged=true;Transfer("write-header",false,(byte[])WriteHeader.Clone(),"ExpectingWritePayload");Transfer("write-payload",false,new[]{(byte)value,(byte)0},"ReadyForHeader");o.WriteTransportComplete=true;Need(o.Errors.Count==0,"clock error after completed write");}
    }
    static Outcome Run(IOps ops,IClock clock,bool restore){Outcome o=new(){Action=restore?"restore200to40":"set40to200"};int fd=-1;try{
      long deadline=checked(clock.NowUs()+40_000_000);var id=ops.Preflight();o.Device=id.Device;fd=ops.Open(id).Value;Need(fd>=0,"open");o.Opened=true;o.Closed=false;ops.ValidateFd(fd,id);ops.Revalidate(id);Need(ops.Claim(fd).Value==0,"claim");o.Claimed=true;o.Released=false;ops.Revalidate(id);
      var x=new Controller(ops,clock,o,fd,deadline);int old=restore?200:40,value=restore?40:200;
      GuardCallbacks(x.Read("callbacks",Callback));var baseline=x.Read("baseline-R",R);GuardR(baseline,old);var m=x.Read("pre-M",M);var c=x.Read("pre-C",C);GuardContext(m,c,baseline);var fresh=x.Read("fresh-R",R);GuardR(fresh,old);GuardPair(baseline,fresh);
      o.Stage="write";x.Write(value);o.Stage="readback";var after=x.Read("readback-R",R);GuardR(after,value);
      GuardPair(fresh,after);
      o.ReadbackVerified=true;o.LimitMayHaveChanged=false;
    }catch(Exception e){o.Errors.Add(ShortError(e));}
    finally{if(o.Claimed)try{var n=ops.Release(fd);o.Released=n.Value==0;if(!o.Released)o.Errors.Add("release failed");}catch(Exception e){o.Errors.Add("release "+ShortError(e));}
      if(fd>=0)try{var n=ops.Close(fd);o.Closed=n.Value==0;if(!o.Closed)o.Errors.Add("close failed");}catch(Exception e){o.Errors.Add("close "+ShortError(e));}o.BindingChecks.AddRange(ops.BindingChecks);}
    o.Accepted=o.Errors.Count==0&&o.ReadbackVerified&&o.WriteTransportComplete&&o.ProtocolPhase=="ReadyForHeader"&&o.Released&&o.Closed;o.Stage=o.Accepted?"complete":"rejected";return o;}
    static byte[] ReadCachedDescriptors(Stream stream)
    {
        byte[] data = new byte[117]; int used = 0;
        while (used < data.Length)
        {
            int count = stream.Read(data, used, data.Length - used);
            if (count == 0) return data.AsSpan(0, used).ToArray();
            Need(count > 0 && count <= data.Length - used, "descriptor stream count"); used += count;
        }
        throw new InvalidOperationException("cached descriptors exceed 116 bytes");
    }
    static byte[] ReadCachedDescriptors(string path) { using FileStream stream = File.OpenRead(path); return ReadCachedDescriptors(stream); }

    sealed class RealClock : IClock
    {
        public long NowUs() => (long)(Stopwatch.GetTimestamp() * (1_000_000.0 / Stopwatch.Frequency));
        public void SleepUs(long microseconds)
        {
            if (microseconds <= 0) return;
            int milliseconds = (int)Math.Min(int.MaxValue, (microseconds + 999) / 1000);
            Thread.Sleep(milliseconds);
        }
    }

    const string UsbfsDriver="/sys/bus/usb/drivers/usbfs";
    readonly record struct NativeNode(int Return,int Errno,uint Mask,ushort Mode,ulong Inode,uint DevMajor,uint DevMinor);
    sealed record KernelDriver(int Return,int Errno,string? Name,uint Interface,string RawBase64,string Sha256);
    sealed record BindingCheck(string Stage,bool OwnClaim,bool LocalFdMatches,NativeNode Link,NativeNode Follow,NativeNode Canonical,KernelDriver? Kernel);
    static bool HasTypeInode(NativeNode n,int kind)=>n.Return==0&&n.Errno==0&&(n.Mask&0x103)==0x103&&(n.Mode&0xf000)==kind&&n.Inode!=0;
    static void GuardNativeBinding(BindingCheck c) {
      Need(HasTypeInode(c.Canonical,0x4000),"canonical usbfs directory identity unavailable");
      if(!c.OwnClaim){Need(c.Link.Return==-1&&c.Link.Errno==2&&c.Follow.Return==-1&&c.Follow.Errno==2,"preclaim driver not positively absent");
        if(c.Stage=="before-open")Need(!c.LocalFdMatches&&c.Kernel==null,"initial ownership state");
        else Need(c.Stage=="unclaimed-fd"&&c.LocalFdMatches&&c.Kernel is {Return:-1,Errno:61,Name:null,Interface:2},"preclaim kernel driver not ENODATA");
      }else{
        Need(c.Stage=="claimed-fd"&&c.LocalFdMatches,"local successful claim ownership");
        Need(c.Kernel is {Return:0,Errno:0,Name:"usbfs",Interface:2},"owned kernel driver not usbfs");
        Need(HasTypeInode(c.Link,0xa000)&&HasTypeInode(c.Follow,0x4000),"owned driver native link/directory unavailable");
        Need(c.Follow.Inode==c.Canonical.Inode&&c.Follow.DevMajor==c.Canonical.DevMajor&&c.Follow.DevMinor==c.Canonical.DevMinor,"owned driver differs from canonical usbfs device/inode");
      }
    }
    static KernelDriver DriverRecord(int result,int errno,string? name){byte[] raw=new byte[260];BitConverter.GetBytes(2u).CopyTo(raw,0);if(result==0&&name!=null){byte[] b=System.Text.Encoding.UTF8.GetBytes(name);Need(b.Length<256,"driver name bound");b.CopyTo(raw,4);}return new(result,errno,result==0?name:null,2,Convert.ToBase64String(raw),Sha(raw));}
    static BindingCheck ModelBinding(bool own,bool opened,string? driver,bool dangling=false){NativeNode canonical=new(0,0,0x103,0x41ed,23111,0,19),missing=new(-1,2,0,0,0,0,0),link=new(0,0,0x103,0xa1ff,888,0,19);
      NativeNode followed=driver==null||dangling?missing:canonical with {Inode=driver==UsbfsDriver?23111ul:23112ul};
      return new(opened?(own?"claimed-fd":"unclaimed-fd"):"before-open",own,opened,driver==null?missing:link,followed,canonical,opened?DriverRecord(driver==null?-1:0,driver==null?61:0,driver==null?null:Path.GetFileName(driver)):null);
    }

    sealed class RealOps : IOps
    {
        int openedFd=-1, claimFd=-1; bool ownClaim;readonly List<BindingCheck> bindingChecks=new();public IReadOnlyList<BindingCheck> BindingChecks=>bindingChecks;
        [DllImport("libc.so.6")] static extern uint getuid();
        [DllImport("libc.so.6")] static extern uint geteuid();
        const uint ClaimRequest = 0x8004550f, ReleaseRequest = 0x80045510, BulkRequest = 0xc0105502;
        [StructLayout(LayoutKind.Sequential, Pack = 4)] internal struct Transfer { public uint Ep, Length, Timeout; public IntPtr Data; }
        [DllImport("libc.so.6", SetLastError = true)] static extern int open(string path, int flags);
        [DllImport("libc.so.6", SetLastError = true)] static extern int close(int fd);
        [DllImport("libc.so.6", EntryPoint = "ioctl", SetLastError = true)] static extern int ioctlNumber(int fd, uint request, ref uint data);
        [DllImport("libc.so.6", EntryPoint = "ioctl", SetLastError = true)] static extern int ioctlTransfer(int fd, uint request, ref Transfer data);
        [DllImport("libc.so.6", SetLastError = true)] static extern IntPtr read(int fd, [Out] byte[] data, UIntPtr count);
        [DllImport("libc.so.6", SetLastError = true)] static extern int statx(int dirfd, string path, int flags, uint mask, [Out] byte[] data);
        [DllImport("libc.so.6",EntryPoint="ioctl",SetLastError=true)] static extern int ioctlGetDriver(int fd,uint request,[In,Out]byte[] data);
        static NativeResult Result(int value) => new(value, value < 0 ? Marshal.GetLastWin32Error() : 0);
        static string Text(string name) => File.ReadAllText(UsbRoot + "/" + name).Trim();
        public static bool AbiReady => RuntimeInformation.ProcessArchitecture == Architecture.Arm && IntPtr.Size == 4 && Marshal.SizeOf<Transfer>() == 16 && BitConverter.IsLittleEndian;
        public Identity Preflight() {Need(openedFd<0&&!ownClaim,"initial preflight requires no resources");return CachedIdentity();}
        Identity CachedIdentity()
        {
            Need(getuid() == 0 && geteuid() == 0, "root UID/EUID required");
            Need(File.ReadAllText("/proc/sys/kernel/random/boot_id").Trim() == ExpectedBoot, "boot changed");
            Need(Text("power/runtime_status") == "active", "USB not already active");
            Need(Text("idVendor") == "04e8" && Text("idProduct") == "2001", "USB IDs");
            Need(Text("bConfigurationValue") == "1" && Text("authorized") == "1", "configuration/authorization");
            Need(Convert.ToHexString(ReadCachedDescriptors(UsbRoot + "/descriptors")).Equals(AllDescriptorsHex, StringComparison.OrdinalIgnoreCase), "cached full descriptors");
            string intf = UsbRoot + ":1.2/";
            var binding=ReadBinding(intf+"driver");bindingChecks.Add(binding);GuardNativeBinding(binding);
            Need(File.ReadAllText(intf + "bInterfaceNumber").Trim() == "02" && File.ReadAllText(intf + "bAlternateSetting").Trim() == "0" &&
                File.ReadAllText(intf + "bInterfaceClass").Trim() == "ff" && File.ReadAllText(intf + "bInterfaceSubClass").Trim() == "00" &&
                File.ReadAllText(intf + "bInterfaceProtocol").Trim() == "00", "vendor interface");
            Need(int.TryParse(Text("busnum"), out int bus) && bus == 7, "bus");
            Need(int.TryParse(Text("devnum"), out int device) && device >= 1 && device <= 127 && device == ExpectedDevice, "device address");
            return new(bus, device);
        }
        NativeNode Node(string path,int flags){byte[] b=new byte[256];int r=statx(-100,path,flags,0x103,b),e=r<0?Marshal.GetLastWin32Error():0;return new(r,e,BitConverter.ToUInt32(b,0),BitConverter.ToUInt16(b,28),BitConverter.ToUInt64(b,32),BitConverter.ToUInt32(b,136),BitConverter.ToUInt32(b,140));}
        KernelDriver GetKernelDriver(){byte[] b=new byte[260];BitConverter.GetBytes(2u).CopyTo(b,0);int r=ioctlGetDriver(openedFd,0x41045508,b),e=r<0?Marshal.GetLastWin32Error():0;int nul=Array.IndexOf(b,(byte)0,4);string? name=r==0&&nul>=4?System.Text.Encoding.UTF8.GetString(b,4,nul-4):null;return new(r,e,name,BitConverter.ToUInt32(b,0),Convert.ToBase64String(b),Sha(b));}
        BindingCheck ReadBinding(string driver){return new(openedFd<0?"before-open":ownClaim?"claimed-fd":"unclaimed-fd",ownClaim,openedFd>=0&&(!ownClaim||claimFd==openedFd),Node(driver,0x100),Node(driver,0),Node(UsbfsDriver,0x100),openedFd>=0?GetKernelDriver():null);}
        public void Revalidate(Identity id) {Need(openedFd>=0&&(!ownClaim||claimFd==openedFd),"resource ownership");Need(CachedIdentity()==id,"USB instance changed");ValidateFdIdentity(openedFd,id);}
        public NativeResult Open(Identity id) {Need(openedFd<0&&!ownClaim,"open ownership");var n=Result(open(id.Node,2|0x80000|0x8000));if(n.Value>=0)openedFd=n.Value;return n;}
        public void ValidateFd(int fd,Identity id) {
            Need(fd==openedFd&&!ownClaim,"initial FD ownership");ValidateFdIdentity(fd,id);
            byte[] descriptor=new byte[18];long count=read(fd,descriptor,(UIntPtr)18).ToInt64();int errno=count<0?Marshal.GetLastWin32Error():0;
            Need(count==18,"FD cached descriptor count="+count+" errno="+errno);
            Need(Convert.ToHexString(descriptor).Equals(DeviceHex,StringComparison.OrdinalIgnoreCase),"FD cached descriptor identity");
        }
        void ValidateFdIdentity(int fd, Identity id)
        {
            byte[] status = new byte[256]; int ret = statx(fd, "", 0x1000, 1, status); int errno = ret < 0 ? Marshal.GetLastWin32Error() : 0;
            Need(ret == 0, "statx failed errno=" + errno); Need((BitConverter.ToUInt32(status, 0) & 1) == 1, "statx type unavailable");
            Need((BitConverter.ToUInt16(status, 28) & 0xf000) == 0x2000, "FD not a character device");
            Need(BitConverter.ToUInt32(status, 128) == 189 && BitConverter.ToUInt32(status, 132) == (uint)((id.Bus - 1) * 128 + id.Device - 1), "FD USB device number");
        }
        public NativeResult Claim(int fd) {
            Need(fd==openedFd&&!ownClaim,"claim ownership");uint iface=2;var n=Result(ioctlNumber(fd,ClaimRequest,ref iface));
            if(n.Value==0){ownClaim=true;claimFd=fd;}return n;
        }
        public NativeResult Release(int fd) {
            Need(ownClaim&&fd==claimFd&&fd==openedFd,"release only own claim");uint iface=2;var n=Result(ioctlNumber(fd,ReleaseRequest,ref iface));
            if(n.Value==0){ownClaim=false;claimFd=-1;}return n;
        }
        public NativeResult Close(int fd) {
            Need(fd==openedFd,"close only own FD");var n=Result(close(fd));if(n.Value==0){openedFd=-1;ownClaim=false;claimFd=-1;}return n;
        }
        public NativeResult Bulk(int fd, bool input, byte[] data, int length)
        {
            Need(AbiReady, "bulk ABI");Need(ownClaim&&fd==claimFd&&fd==openedFd,"bulk requires own successful claim");
            if (input) Need(data.Length == length && (length == 64 || length == 256 || length == 68 || length == 16), "fixed input length");
            else Need((length == 12 && AllowedHeader(data)) || (length == 2 && data.Length == 2 && (Half(data,0) == 40 || Half(data,0) == 200)), "fixed OUT only");
            GCHandle pinned = GCHandle.Alloc(data, GCHandleType.Pinned);
            try
            {
                Transfer transfer = new() { Ep = input ? 0x82u : 0x02u, Length = (uint)length, Timeout = TimeoutMs, Data = pinned.AddrOfPinnedObject() };
                return Result(ioctlTransfer(fd, BulkRequest, ref transfer));
            }
            finally { pinned.Free(); }
        }
    }


    sealed class FakeClock:IClock {public long At;public int Calls,Fail=-1;public long NowUs(){if(++Calls==Fail)throw new IOException("clock injected");return At+=100;}public void SleepUs(long us){throw new Exception("sleep forbidden");}}
    sealed class FakeOps:IOps {
      readonly List<BindingCheck> bindingChecks=new();public IReadOnlyList<BindingCheck> BindingChecks=>bindingChecks;public int Opens,Claims,Revalidates,FailRevalidate=-1;public int InitialFdValidations;public bool OwnClaim,BindBeforeClaim,PostClaimDangling;public string? Driver,DriverAfterClaim=UsbfsDriver;public int Calls,Fail=-1,ThrowAt=-1,Releases,Closes,Writes;public bool WrongReadback,ReleaseFail,CloseFail,OpenFail,ClaimFail,CallbackBad,ContextBad,RootBad,Dirty,ProfileBad,ValidateFail;public int Current=40,Temperature=25,RReads,UpperOverride=-1;public int[]? Temperatures,Echoes;public bool StaleNormal;public int AlternateTemperature=-1,AlternateUpperOverride=-1;public int[]? AlternateTemperatures;Spec? pending;
      void DriverGuard(){var b=ModelBinding(OwnClaim,Opens>0,Driver,PostClaimDangling);bindingChecks.Add(b);GuardNativeBinding(b);}
      public Identity Preflight(){Need(!OwnClaim,"fake initial ownership");DriverGuard();return new(7,57);}
      public NativeResult Open(Identity id){Opens++;return new(OpenFail?-1:10,0);}
      public void ValidateFd(int fd,Identity id){InitialFdValidations++;if(ValidateFail)throw new Exception("fd");if(BindBeforeClaim)Driver=UsbfsDriver;}
      public void Revalidate(Identity id){if(++Revalidates==FailRevalidate)throw new IOException("instance changed");DriverGuard();}
      public NativeResult Claim(int fd){Claims++;Need(!OwnClaim&&Driver==null&&fd==10,"fake exclusive claim precondition");if(ClaimFail)return new(-1,0);OwnClaim=true;Driver=DriverAfterClaim;return new(0,0);}
      public NativeResult Release(int fd){Releases++;Need(OwnClaim&&fd==10,"fake release ownership");if(ReleaseFail)return new(-1,0);OwnClaim=false;Driver=null;return new(0,0);}
      public NativeResult Close(int fd){Closes++;Need(fd==10,"fake close identity");if(CloseFail)return new(-1,0);OwnClaim=false;Driver=null;return new(0,0);}
      public NativeResult Bulk(int fd,bool input,byte[] b,int length){Need(OwnClaim&&fd==10,"fake bulk ownership");Calls++;if(Calls==ThrowAt)throw new IOException("bulk injected");if(Calls==Fail)return new(length-1,5);
        if(!input&&length==12){Need(pending==null,"fake header when pending");if(b.AsSpan().SequenceEqual(WriteHeader))pending=new("write",0,2);else foreach(var s in new[]{Callback,R,M,C})if(b.AsSpan().SequenceEqual(Header(s)))pending=s;Need(pending!=null,"fake fixed header");}
        else if(!input){Need(pending?.Name=="write"&&length==2,"fake payload phase");Current=Half(b,0);Writes++;pending=null;}
        else{Need(pending!=null&&pending.Length==length,"fake read phase");var s=pending!;pending=null;
          if(s.Name=="R"){int at=RReads++;int t=Temperatures==null?Temperature:Temperatures[Math.Min(at,Temperatures.Length-1)],echo=Echoes==null?251:Echoes[Math.Min(at,Echoes.Length-1)];ThermalR(t,echo,WrongReadback&&Writes>0?40:Current).CopyTo(b,0);if(AlternateTemperature>=0||AlternateTemperatures!=null)Put(b,0xbc,Endpoint(2075,24,AlternateTemperatures==null?AlternateTemperature:AlternateTemperatures[Math.Min(at,AlternateTemperatures.Length-1)],15,195,3000,3800));if(AlternateUpperOverride>=0)Put(b,0xbc,AlternateUpperOverride);if(StaleNormal)Put(b,0x20,3200);if(Dirty)Put(b,0,1);if(ProfileBad)b[0x20]^=1;}
          if(s.Name=="Callback"){uint[] cb={0x2945d,0x293d1,0x294fb,0,0,0x28b85,0x28cf1,0x294f5};for(int i=0;i<cb.Length;i++)BitConverter.GetBytes(cb[i]).CopyTo(b,12+4*i);if(CallbackBad)b[12]^=1;}
          if(s.Name=="M"){BitConverter.GetBytes(RootBad?0x20020000u:0x20010000u).CopyTo(b,64);Put(b,12,ContextBad?1:2);b[56]=1;Put(b,22,500);Put(b,26,500);Put(b,38,UpperOverride>=0?UpperOverride:Endpoint(2075,24,Temperature,15,195,3000,3800));Put(b,40,500);}
          if(s.Name=="C"){Put(b,0,2160);Put(b,2,1920);Put(b,4,2880);b[6]=92;b[8]=3;}
        }return new(length,0);
      }
    }
    static byte[] ThermalR(int temperature,int echo,int limit) {var r=(byte[])Profile.Clone();Put(r,0x98,temperature);Put(r,0xac,echo);int upper=Endpoint(2075,24,temperature,15,195,3000,3800);Put(r,0x20,upper);Put(r,0xbc,upper);Put(r,0xc4,limit);return r;}
    static void Put(byte[] b,int i,int v){b[i]=(byte)v;b[i+1]=(byte)(v>>8);}
    static string Serialize(Outcome o)=>JsonSerializer.Serialize(o,new JsonSerializerOptions{PropertyNamingPolicy=JsonNamingPolicy.CamelCase});
    static int SelfTest(){int checks=0;void Check(bool b,string s){Need(b,s);checks++;}
      Outcome Test(FakeOps f,bool restore=false,FakeClock? c=null){var o=Run(f,c??new(),restore);Check(f.Closes==(f.Opens==1&&!f.OpenFail?1:0),"exact close");Check(f.Releases==(f.Claims==1&&!f.ClaimFail?1:0),"exact release");return o;}
      var f=new FakeOps();var good=Test(f);Check(good.Accepted&&good.BulkTransfers==14&&good.HeadersSent==7&&f.Writes==1,"set success");
      f=new(){Current=200};var restored=Test(f,true);Check(restored.Accepted&&f.Current==40&&f.Writes==1,"restore success");
      for(int i=1;i<=14;i++){f=new(){Fail=i};var o=Test(f);Check(!o.Accepted&&f.Calls==i&&o.ProtocolPhase=="Unknown","short transfer stops absolutely");}
      for(int i=1;i<=14;i++){f=new(){ThrowAt=i};var o=Test(f);Check(!o.Accepted&&f.Calls==i&&o.ProtocolPhase=="Unknown","throw stops absolutely");}
      foreach(var bad in new[]{new FakeOps{Dirty=true},new FakeOps{CallbackBad=true},new FakeOps{ContextBad=true},new FakeOps{RootBad=true},new FakeOps{ProfileBad=true},new FakeOps{Current=200},new FakeOps{OpenFail=true},new FakeOps{ClaimFail=true},new FakeOps{ValidateFail=true}}){var o=Test(bad);Check(!o.Accepted&&bad.Writes==0,"precondition forbids write");}
      foreach(var bad in new[]{new FakeOps{ReleaseFail=true},new FakeOps{CloseFail=true},new FakeOps{WrongReadback=true}}){var o=Test(bad);Check(!o.Accepted&&bad.Writes==1,"post failure not hidden");}
      for(int i=1;i<=70;i++){f=new();var o=Test(f,false,new FakeClock{Fail=i});if(!o.Accepted)Check(o.Errors.Count>0,"clock rejection recorded");Check(f.Writes<=1,"clock no repeat");}
      for(int i=0;i<256;i++){var a=(byte[])Profile.Clone();a[i]^=0x80;bool pass=true;try{GuardR(a,40);}catch{pass=false;}Check(pass==(DynamicR(i)||i==0xac),"profile rejection matrix "+i);}
      foreach(int fail in new[]{3,28}){f=new();var o=Test(f,false,new FakeClock{Fail=fail});Check(!o.Accepted&&f.Writes==0&&o.ProtocolPhase=="ReadyForHeader"&&f.Calls==(fail==3?0:10),"preheader clock failure sends no OUT");}
      f=new();var obligatory=Test(f,false,new FakeClock{Fail=29});Check(!obligatory.Accepted&&f.Calls==12&&f.Writes==1&&obligatory.ProtocolPhase=="ReadyForHeader","postheader clock failure completes payload then stops");
      foreach(int which in new[]{1,2}){f=new(){FailRevalidate=which};var o=Test(f);Check(!o.Accepted&&f.Calls==0&&f.Writes==0,"instance race rejects before first header");}
      f=new();var owned=Test(f);Check(owned.Accepted&&f.InitialFdValidations==1&&f.Revalidates==2&&f.Claims==1&&f.Releases==1&&!f.OwnClaim&&f.Driver==null,"successful claim bindsusbfs andpostclaim succeeds");
      foreach(var unexpected in new[]{new FakeOps{Driver=UsbfsDriver},new FakeOps{Driver="/sys/bus/usb/drivers/other"},new FakeOps{BindBeforeClaim=true},new FakeOps{DriverAfterClaim="/sys/bus/usb/drivers/other"},new FakeOps{DriverAfterClaim=null},new FakeOps{PostClaimDangling=true}}){var o=Test(unexpected);Check(!o.Accepted&&unexpected.Calls==0&&unexpected.Writes==0&&o.ProtocolPhase=="ReadyForHeader","unexpected orborrowed driver sendsnoheaders");}
      bool Policy(BindingCheck b){try{GuardNativeBinding(b);return true;}catch{return false;}}
      var nativeGood=ModelBinding(true,true,UsbfsDriver);Check(Policy(nativeGood),"actualDO native inode/kernel binding accepted despite managed lexical alias");
      Check(Policy(ModelBinding(false,false,null))&&Policy(ModelBinding(false,true,null)),"native missingness andcached ENODATA");
      foreach(var b in new[]{nativeGood with {OwnClaim=false},nativeGood with {LocalFdMatches=false},nativeGood with {Kernel=DriverRecord(0,0,"other")},nativeGood with {Kernel=DriverRecord(-1,61,null)},nativeGood with {Link=nativeGood.Link with {Mode=0x41ed}},nativeGood with {Follow=nativeGood.Follow with {Inode=23112}},nativeGood with {Follow=nativeGood.Follow with {DevMajor=1}},nativeGood with {Follow=nativeGood.Follow with {DevMinor=20}},nativeGood with {Canonical=nativeGood.Canonical with {Mask=3}},nativeGood with {Follow=nativeGood.Follow with {Return=-1,Errno=2}},ModelBinding(false,true,null) with {Kernel=DriverRecord(0,0,"usbfs")},ModelBinding(false,true,null) with {Link=new NativeNode(-1,13,0,0,0,0,0)}})Check(!Policy(b),"reject wrong kernel/type/inode/device/mask/absence/ownership");
      // Exact DU arithmetic and restrictive admission: same source rules in both actions.
      for(int raw=0;raw<=65535;raw++){int scaled=(int)(uint)((float)raw*0.0625f);Check(scaled==raw/16,"u16 float conversion exact");Check((scaled>4000?25:scaled)==(raw/16>4000?25:raw/16),"reference fallback exact");}
      for(int t=0;t<=4095;t++){int upper=Endpoint(2075,24,t,15,195,3000,3800);Check(upper>=3000&&upper<=3800,"every source temperature bounded");}
      byte[] vectors=new byte[8192];for(int t=0;t<4096;t++)Put(vectors,t*2,Endpoint(2075,24,t,15,195,3000,3800));Check(Sha(vectors)=="923784f6db98e7d188d283dd9adcd3282c92fb57597595fe1e09d268b71c834c","exact frozen DU4096-vector SHA");
      Check(Endpoint(2075,24,24,15,195,3000,3800)==3161&&Endpoint(2075,24,25,15,195,3000,3800)==3183,"retained source arithmetic");
      Check(Endpoint(1,2,0,65535,65535,0,65535)==2559&&Endpoint(65535,0,65535,65535,65535,100,3800)==512,"modular width negative and overflow");
      foreach(bool reverse in new[]{false,true})foreach(int t in new[]{0,24,25,4095}){f=new(){Current=reverse?200:40,Temperature=t,Echoes=new[]{254,0,1}};var o=Test(f,reverse);Check(o.Accepted&&f.Writes==1&&o.ReadbackVerified&&!o.LimitMayHaveChanged,"independent modeled profile set/restore with echo wrap");}
      foreach(var invalid in new[]{new FakeOps{Temperature=4096},new FakeOps{Echoes=new[]{255}},new FakeOps{Echoes=new[]{256}},new FakeOps{StaleNormal=true,Temperature=24},new FakeOps{Temperature=24,UpperOverride=3183},new FakeOps{Temperature=24,ContextBad=true}}){var o=Test(invalid);Check(!o.Accepted&&invalid.Writes==0&&!o.WriteAttempted&&!o.LimitMayHaveChanged&&o.ProtocolPhase=="ReadyForHeader","invalid modeled state refuses before write");}
      f=new(){Temperature=25,Temperatures=new[]{25,24,24}};var beforeDrift=Test(f);Check(!beforeDrift.Accepted&&f.Calls==10&&f.Writes==0&&!beforeDrift.WriteAttempted&&!beforeDrift.LimitMayHaveChanged&&beforeDrift.ProtocolPhase=="ReadyForHeader","fresh thermal drift rejects before write");
      f=new(){Temperature=25,Temperatures=new[]{25,25,24}};var afterDrift=Test(f);Check(!afterDrift.Accepted&&f.Calls==14&&f.Writes==1&&afterDrift.WriteAttempted&&afterDrift.WriteTransportComplete&&!afterDrift.ReadbackVerified&&afterDrift.LimitMayHaveChanged&&afterDrift.ProtocolPhase=="ReadyForHeader","post-write thermal drift retains change ambiguity");
      f=new(){Temperature=24,Temperatures=new[]{24,24,24},Echoes=new[]{0,1,255}};var afterEcho=Test(f);Check(!afterEcho.Accepted&&f.Writes==1&&afterEcho.LimitMayHaveChanged&&!afterEcho.ReadbackVerified,"out-of-domain post-write echo refuses without retry");
      Check(WriteHeader.AsSpan().SequenceEqual(Convert.FromHexString("02010000c424014702000000")),"exact write header");
      // FA finite-preimage policy, source-equivalent native/Python table and EX selective refresh.
      Check(AlternateEndpointImage.Length==72,"exact finite-image cardinality");
      byte[] imageBytes=new byte[144];for(int i=0;i<72;i++){Put(imageBytes,2*i,AlternateEndpointImage[i]);if(i>0)Check(AlternateEndpointImage[i]>AlternateEndpointImage[i-1],"sorted unique finite image");}
      Check(Sha(imageBytes)=="a61417913462d9b4c45d39431dbf6b662c84238e4f3b6585ac24c75654eabc53","exact finite-image SHA");
      var preimages=new HashSet<int>();for(int t=0;t<4096;t++){int v=Endpoint(2075,24,t,15,195,3000,3800);preimages.Add(v);Check(AlternateAllowed(v),"all4096 source preimages admitted");}
      for(int v=0;v<=65535;v++)Check(AlternateAllowed(v)==preimages.Contains(v),"all u16 endpoints iff exact image");
      Check(AlternateAllowed(3138)&&!AlternateAllowed(3200)&&Endpoint(2075,24,23,15,195,3000,3800)==3138,"EX prior-temperature preimage / range gap");
      foreach(bool reverse in new[]{false,true}){f=new(){Current=reverse?200:40,Temperature=24,AlternateTemperature=23,Echoes=new[]{3,4,5}};var o=Test(f,reverse);Check(o.Accepted&&f.Writes==1&&o.ReadbackVerified&&!o.LimitMayHaveChanged,"EX selective endpoint set/restore accepted");}
      foreach(var invalid in new[]{new FakeOps{Temperature=24,AlternateUpperOverride=3200},new FakeOps{Temperature=24,AlternateUpperOverride=3139},new FakeOps{Temperature=24,AlternateTemperature=23,ContextBad=true},new FakeOps{Temperature=24,AlternateTemperature=23,Dirty=true}}){var o=Test(invalid);Check(!o.Accepted&&invalid.Writes==0&&!o.WriteAttempted,"FA gap/mode6/fault rejects before write");}
      f=new(){Temperature=24,AlternateTemperatures=new[]{23,24,24}};var altBefore=Test(f);Check(!altBefore.Accepted&&f.Writes==0&&!altBefore.LimitMayHaveChanged,"alternate drift before write refuses");
      f=new(){Temperature=24,AlternateTemperatures=new[]{23,23,24}};var altAfter=Test(f);Check(!altAfter.Accepted&&f.Writes==1&&altAfter.WriteTransportComplete&&!altAfter.ReadbackVerified&&altAfter.LimitMayHaveChanged,"alternate drift after write retains ambiguity");
      Console.WriteLine(JsonSerializer.Serialize(new{selfTestsPassed=checks,targetOperations=0}));return 0;
    }
    [DllImport("libc.so.6",EntryPoint="open",SetLastError=true)] static extern int ReceiptOpen(string path,int flags,uint mode);
    [DllImport("libc.so.6",EntryPoint="statx",SetLastError=true)] static extern int ReceiptStat(int dirfd,string path,int flags,uint mask,[Out]byte[] data);
    [DllImport("libc.so.6",EntryPoint="getuid")] static extern uint ReceiptUid();
    [DllImport("libc.so.6",EntryPoint="geteuid")] static extern uint ReceiptEuid();
    static FileStream Receipt(string name) {
      Need(name=="selftest.receipt.json"||name=="native.receipt.json","fixed receipt name");
      string dir=Directory.GetCurrentDirectory(),prefix="/tmp/researcher-limit-fa-";Need(dir.StartsWith(prefix,StringComparison.Ordinal)&&dir.Length==prefix.Length+32,"private fixed stage path");
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
      if(args.Length==1&&args[0]=="--self-test")return SelfTest();
      if(args.Length==1&&args[0]=="--receipt-self-test"){
        using var receipt=Receipt("selftest.receipt.json");var saved=Console.Out;using var text=new StringWriter(System.Globalization.CultureInfo.InvariantCulture);int code;
        try{Console.SetOut(text);code=SelfTest();}finally{Console.SetOut(saved);}
        PublishReceipt(receipt,text.ToString());return code;
      }
      if(args.Length==1&&(args[0]=="--host-fixture-set"||args[0]=="--host-fixture-restore")){bool restore=args[0].EndsWith("restore");Console.WriteLine(Serialize(Run(new FakeOps{Current=restore?200:40},new FakeClock(),restore)));return 0;}
      bool set=args.Length==3&&args[0]=="--execute-set", restoreAction=args.Length==3&&args[0]=="--execute-restore";
      if(set||restoreAction){if(args[1]!="--device"||!int.TryParse(args[2],out ExpectedDevice)||ExpectedDevice<1||ExpectedDevice>127||args[2]!=ExpectedDevice.ToString())return 64;}
      if(!set&&!restoreAction){Console.WriteLine("{\"schema\":\"fa-fixed-limit-dry-v1\",\"targetOperations\":0,\"fixedAddress\":\"0x470124c4\",\"bytes\":2,\"automaticRestore\":false}");return args.Length==0?0:64;}
      if(!RealOps.AbiReady){Console.WriteLine("{\"error\":\"ARM32 ABI required before any native operation\"}");return 64;}
      using var nativeReceipt=Receipt("native.receipt.json");var outcome=Run(new RealOps(),new RealClock(),restoreAction);PublishReceipt(nativeReceipt,Serialize(outcome)+"\n");return outcome.Accepted?0:1;
    }

}
