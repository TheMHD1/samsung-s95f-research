using System;
using System.IO;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Threading;
internal static partial class Program
{
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
        bool loggerPayloadPending;
        public NativeResult Bulk(int fd, bool input, byte[] data, int length)
        {
            Need(AbiReady, "bulk ABI");Need(ownClaim&&fd==claimFd&&fd==openedFd,"bulk requires own successful claim");
            bool writeHeader=!input&&length==12&&data.AsSpan().SequenceEqual(LoggerHeader);
            bool writePayload=!input&&length==2&&data.Length==2&&data[1]==0&&(data[0]==0||data[0]==1);
            if(loggerPayloadPending)Need(writePayload,"only fixed matching logger payload");
            else if(input)Need((data.Length==256&&length!=Ring.Length||data.Length==Ring.Length&&length==Ring.Length)&&IsInputLength(length),"fixed input length");
            else Need(length==12&&data.Length==12&&(FindHeader(data)!=null||writeHeader),"fixed read/logger header only");
            GCHandle pinned = GCHandle.Alloc(data, GCHandleType.Pinned);
            try
            {
                Transfer transfer = new() { Ep = input ? 0x82u : 0x02u, Length = (uint)length, Timeout = TimeoutMs, Data = pinned.AddrOfPinnedObject() };
                var answer=Result(ioctlTransfer(fd, BulkRequest, ref transfer));
                if(writeHeader&&answer.Value==12)loggerPayloadPending=true;else if(loggerPayloadPending)loggerPayloadPending=false;return answer;
            }
            finally { pinned.Free(); }
        }
    }


}
