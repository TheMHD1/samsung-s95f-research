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
    interface IOps {Identity Preflight();NativeResult Open(Identity id);void ValidateFd(int fd,Identity id);void Revalidate(Identity id);NativeResult Claim(int fd);NativeResult Bulk(int fd,bool input,byte[] data,int length);NativeResult Release(int fd);NativeResult Close(int fd);}
    interface IClock {long NowUs();void SleepUs(long us);}
    sealed record Step(string Name,string Direction,int Expected,int? Count,int Errno,long BeforeUs,long AfterUs,string Before,string After);
    sealed record Window(string Name,int Bytes,string Sha256,string Base64);
    sealed class Outcome {
      public int Device{get;set;} public string Schema{get;set;}="dn-fixed-limit-v1";public string Action{get;set;}="";public string ProtocolPhase{get;set;}="ReadyForHeader";public string Stage{get;set;}="preflight";
      public bool Opened{get;set;} public bool Claimed{get;set;} public bool Released{get;set;}=true;public bool Closed{get;set;}=true;
      public bool WriteAttempted{get;set;} public bool WriteTransportComplete{get;set;} public bool ReadbackVerified{get;set;} public bool LimitMayHaveChanged{get;set;} public bool Accepted{get;set;}
      public bool PhysicalPictureObserved{get;set;} public bool RootCauseFixEstablished{get;set;} public int HeadersSent{get;set;} public int BulkTransfers{get;set;}
      public List<Step> Steps{get;}=new();public List<Window> Windows{get;}=new();public List<string> Errors{get;}=new();
    }
    static readonly byte[] Profile=Convert.FromHexString("[encoded-payload-omitted]");

    // Only historical action buckets, record/event latches and q-publication latch are
    // excluded from profile equality. Stop/fault/gates are independently strict.
    static bool DynamicR(int i)=>(i>=0x86&&i<0x8a)||(i>=0x8c&&i<0x8e)||(i>=0x90&&i<0x94)||(i>=0xa2&&i<0xa4);
    static void GuardR(byte[] r,int expected) {
      Need(r.Length==256,"R extent");
      for(int i=0;i<256;i++)if(!DynamicR(i)&&i!=0xc4&&i!=0xc5&&i!=0xca)Need(r[i]==Profile[i],"R profile byte "+i);
      Need(r[0xca]<=1,"R observed selector domain");
      Need(Half(r,0)==0&&Half(r,0xa)==0&&Half(r,0xe)==1&&Half(r,6)==0,"R clean/gate/logger");
      Need(Half(r,0xc4)==expected&&Half(r,0x30)==200&&Half(r,0xc0)==200,"R limit");
      Need(Half(r,0x9e)==1&&Half(r,0x4a)==0&&Half(r,0x4e)==0&&Half(r,0x9a)==0&&Half(r,0x9c)==0,"R alternative gates/latches");
    }
    static void GuardContext(byte[] m,byte[] c) {
      Need(m.Length==68&&c.Length==16,"context extent");
      Need(BitConverter.ToUInt32(m,64)==0x20010000,"root");Need(Half(m,10)==0&&Half(m,12)==2,"mode1 flags");Need(m[56]==1,"scan enable");
      Need(Half(m,22)==500&&Half(m,24)==0&&Half(m,26)==500&&Half(m,28)==0&&Half(m,38)==3183&&Half(m,40)==500,"numeric profile");
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
      GuardCallbacks(x.Read("callbacks",Callback));var baseline=x.Read("baseline-R",R);GuardR(baseline,old);var m=x.Read("pre-M",M);var c=x.Read("pre-C",C);GuardContext(m,c);var fresh=x.Read("fresh-R",R);GuardR(fresh,old);Need(fresh[0xca]==baseline[0xca],"selector changed during preflight");
      o.Stage="write";x.Write(value);o.Stage="readback";var after=x.Read("readback-R",R);GuardR(after,value);
      // Every non-status byte, including the unknown selector byte, must remain exact.
      for(int i=0;i<256;i++)if(!DynamicR(i)&&i!=0xc4)Need(after[i]==fresh[i],"unexpected R mutation "+i);
      o.ReadbackVerified=true;o.LimitMayHaveChanged=false;
    }catch(Exception e){o.Errors.Add(ShortError(e));}
    finally{if(o.Claimed)try{var n=ops.Release(fd);o.Released=n.Value==0;if(!o.Released)o.Errors.Add("release failed");}catch(Exception e){o.Errors.Add("release "+ShortError(e));}
      if(fd>=0)try{var n=ops.Close(fd);o.Closed=n.Value==0;if(!o.Closed)o.Errors.Add("close failed");}catch(Exception e){o.Errors.Add("close "+ShortError(e));}}
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
    static void GuardDriver(bool ownClaim,string? linkTarget,string? resolvedTarget,bool directoryExists,bool fileExists) {
      if(!ownClaim)Need(linkTarget==null&&!directoryExists&&!fileExists,"interface already bound before own claim");
      else Need(linkTarget!=null&&directoryExists&&!fileExists&&resolvedTarget==UsbfsDriver,"owned claim lacks exact usbfs driver");
    }
    sealed class RealOps : IOps
    {
        int openedFd=-1, claimFd=-1; bool ownClaim;
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
            var driver=new DirectoryInfo(intf+"driver");string? link=driver.LinkTarget;
            string? resolved=link==null?null:driver.ResolveLinkTarget(true)?.FullName;
            GuardDriver(ownClaim,link,resolved,Directory.Exists(intf+"driver"),File.Exists(intf+"driver"));
            Need(File.ReadAllText(intf + "bInterfaceNumber").Trim() == "02" && File.ReadAllText(intf + "bAlternateSetting").Trim() == "0" &&
                File.ReadAllText(intf + "bInterfaceClass").Trim() == "ff" && File.ReadAllText(intf + "bInterfaceSubClass").Trim() == "00" &&
                File.ReadAllText(intf + "bInterfaceProtocol").Trim() == "00", "vendor interface");
            Need(int.TryParse(Text("busnum"), out int bus) && bus == 7, "bus");
            Need(int.TryParse(Text("devnum"), out int device) && device >= 1 && device <= 127 && device == ExpectedDevice, "device address");
            return new(bus, device);
        }
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
      public int Opens,Claims,Revalidates,FailRevalidate=-1;public int InitialFdValidations;public bool OwnClaim,BindBeforeClaim,PostClaimDangling;public string? Driver,DriverAfterClaim=UsbfsDriver;public int Calls,Fail=-1,ThrowAt=-1,Releases,Closes,Writes;public bool WrongReadback,ReleaseFail,CloseFail,OpenFail,ClaimFail,CallbackBad,ContextBad,RootBad,Dirty,ProfileBad,ValidateFail;public int Current=40;Spec? pending;
      void DriverGuard(){GuardDriver(OwnClaim,Driver,Driver,Driver!=null&&!PostClaimDangling,false);}
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
          if(s.Name=="R"){Profile.CopyTo(b,0);Put(b,0xc4,WrongReadback&&Writes>0?40:Current);if(Dirty)Put(b,0,1);if(ProfileBad)b[0x20]^=1;}
          if(s.Name=="Callback"){uint[] cb={0x2945d,0x293d1,0x294fb,0,0,0x28b85,0x28cf1,0x294f5};for(int i=0;i<cb.Length;i++)BitConverter.GetBytes(cb[i]).CopyTo(b,12+4*i);if(CallbackBad)b[12]^=1;}
          if(s.Name=="M"){BitConverter.GetBytes(RootBad?0x20020000u:0x20010000u).CopyTo(b,64);Put(b,12,ContextBad?1:2);b[56]=1;Put(b,22,500);Put(b,26,500);Put(b,38,3183);Put(b,40,500);}
          if(s.Name=="C"){Put(b,0,2160);Put(b,2,1920);Put(b,4,2880);b[6]=92;b[8]=3;}
        }return new(length,0);
      }
    }
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
      for(int i=0;i<256;i++){var a=(byte[])Profile.Clone();a[i]^=0x80;bool pass=true;try{GuardR(a,40);}catch{pass=false;}Check(pass==DynamicR(i),"profile rejection matrix "+i);}
      foreach(int fail in new[]{3,28}){f=new();var o=Test(f,false,new FakeClock{Fail=fail});Check(!o.Accepted&&f.Writes==0&&o.ProtocolPhase=="ReadyForHeader"&&f.Calls==(fail==3?0:10),"preheader clock failure sends no OUT");}
      f=new();var obligatory=Test(f,false,new FakeClock{Fail=29});Check(!obligatory.Accepted&&f.Calls==12&&f.Writes==1&&obligatory.ProtocolPhase=="ReadyForHeader","postheader clock failure completes payload then stops");
      foreach(int which in new[]{1,2}){f=new(){FailRevalidate=which};var o=Test(f);Check(!o.Accepted&&f.Calls==0&&f.Writes==0,"instance race rejects before first header");}
      f=new();var owned=Test(f);Check(owned.Accepted&&f.InitialFdValidations==1&&f.Revalidates==2&&f.Claims==1&&f.Releases==1&&!f.OwnClaim&&f.Driver==null,"successful claim bindsusbfs andpostclaim succeeds");
      foreach(var unexpected in new[]{new FakeOps{Driver=UsbfsDriver},new FakeOps{Driver="/sys/bus/usb/drivers/other"},new FakeOps{BindBeforeClaim=true},new FakeOps{DriverAfterClaim="/sys/bus/usb/drivers/other"},new FakeOps{DriverAfterClaim=null},new FakeOps{PostClaimDangling=true}}){var o=Test(unexpected);Check(!o.Accepted&&unexpected.Calls==0&&unexpected.Writes==0&&o.ProtocolPhase=="ReadyForHeader","unexpected orborrowed driver sendsnoheaders");}
      bool Policy(bool own,string? link,string? resolved,bool dir,bool file){try{GuardDriver(own,link,resolved,dir,file);return true;}catch{return false;}}
      Check(Policy(false,null,null,false,false),"unbound preclaim accepted");Check(Policy(true,"relative-usbfs",UsbfsDriver,true,false),"own exactdriver accepted");
      foreach(var x in new[]{(false,"usbfs",UsbfsDriver,true,false),(true,"usbfs",UsbfsDriver+"-other",true,false),(true,"usbfs",UsbfsDriver,false,false),(true,"usbfs",UsbfsDriver,true,true),(true,(string?)null,(string?)null,false,false),(false,"dangling",(string?)null,false,false)})Check(!Policy(x.Item1,x.Item2,x.Item3,x.Item4,x.Item5),"strict ownership driver policy");
      Check(WriteHeader.AsSpan().SequenceEqual(Convert.FromHexString("02010000c424014702000000")),"exact write header");
      Console.WriteLine(JsonSerializer.Serialize(new{selfTestsPassed=checks,targetOperations=0}));return 0;
    }
    [DllImport("libc.so.6",EntryPoint="open",SetLastError=true)] static extern int ReceiptOpen(string path,int flags,uint mode);
    [DllImport("libc.so.6",EntryPoint="statx",SetLastError=true)] static extern int ReceiptStat(int dirfd,string path,int flags,uint mask,[Out]byte[] data);
    [DllImport("libc.so.6",EntryPoint="getuid")] static extern uint ReceiptUid();
    [DllImport("libc.so.6",EntryPoint="geteuid")] static extern uint ReceiptEuid();
    static FileStream Receipt(string name) {
      Need(name=="selftest.receipt.json"||name=="native.receipt.json","fixed receipt name");
      string dir=Directory.GetCurrentDirectory(),prefix="/tmp/researcher-limit-dn-";Need(dir.StartsWith(prefix,StringComparison.Ordinal)&&dir.Length==prefix.Length+32,"private fixed stage path");
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
      if(!set&&!restoreAction){Console.WriteLine("{\"schema\":\"dn-fixed-limit-dry-v1\",\"targetOperations\":0,\"fixedAddress\":\"0x470124c4\",\"bytes\":2,\"automaticRestore\":false}");return args.Length==0?0:64;}
      if(!RealOps.AbiReady){Console.WriteLine("{\"error\":\"ARM32 ABI required before any native operation\"}");return 64;}
      using var nativeReceipt=Receipt("native.receipt.json");var outcome=Run(new RealOps(),new RealClock(),restoreAction);PublishReceipt(nativeReceipt,Serialize(outcome)+"\n");return outcome.Accepted?0:1;
    }

}
