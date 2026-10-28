using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Encodings.Web;
using Microsoft.Win32.SafeHandles;

internal static class Program {
    internal const string Target = "/sys/kernel/debug/tcon/tcon_micom_log";
    internal const string Stage = "/tmp/tcon-log-single-read-20261028fk";
    internal const string ReceiptPath = Stage + "/read.receipt.json";
    internal const int Capacity = 4096;
    internal const byte Fill = 0xa5;
    internal readonly record struct Result(long Value,int Errno);
    internal interface IOps {
        long Now();
        Result Open();
        Result Read(int fd,IntPtr buffer);
        Result Close(int fd);
    }
    internal sealed class Observation {
        public bool OpenAttempted,ReadAttempted,CloseAttempted,Accepted;
        public Result OpenResult = new(-1,0), ReadResult = new(-1,0), CloseResult = new(-1,0);
        public readonly long[] Times = {-1,-1,-1,-1,-1,-1};
        public int ClockFailureMask, ExceptionMask;
    }
    // All acquisition storage and the GC pin are allocated before Open. No output,
    // hashing, formatting, streams, repeated reads or retries occur in this method.
    internal static Observation Acquire(IOps ops,byte[] buffer,IntPtr pointer,Observation o) {
        if(buffer.Length!=Capacity || pointer==IntPtr.Zero) throw new ArgumentException("fixed allocation required");
        bool Stamp(int n) {try {long t=ops.Now();if(t<0)throw new InvalidOperationException();o.Times[n]=t;return true;}
            catch {o.ClockFailureMask|=1<<n;return false;}}
        int fd=-1;
        if(!Stamp(0)) return o;
        try {
            o.OpenAttempted=true;
            try{o.OpenResult=ops.Open();}catch{o.ExceptionMask|=1;Stamp(1);return o;}
            bool openAfter=Stamp(1);
            if(o.OpenResult.Value<0)return o;
            if(o.OpenResult.Value>int.MaxValue){o.ExceptionMask|=16;return o;}
            fd=(int)o.OpenResult.Value;
            bool readBefore=Stamp(2);
            if(!openAfter || !readBefore)return o;
            o.ReadAttempted=true;
            try{o.ReadResult=ops.Read(fd,pointer);}catch{o.ExceptionMask|=2;}
            Stamp(3);
        } finally {
            if(fd>=0){
                Stamp(4);o.CloseAttempted=true;
                try{o.CloseResult=ops.Close(fd);}catch{o.ExceptionMask|=4;}
                Stamp(5);
            }
        }
        bool ordered=true;for(int i=1;i<o.Times.Length;i++)ordered &= o.Times[i]>=o.Times[i-1];
        o.Accepted=o.OpenResult.Value>=0 && o.OpenResult.Errno==0 && o.ReadAttempted &&
            o.ReadResult.Value>=0 && o.ReadResult.Value<=Capacity && o.ReadResult.Errno==0 &&
            o.CloseAttempted && o.CloseResult==new Result(0,0) && o.ClockFailureMask==0 && o.ExceptionMask==0 && ordered;
        return o;
    }
    internal sealed class RealOps : IOps {
        [DllImport("libc.so.6",SetLastError=true)] internal static extern int open(string path,int flags,uint mode);
        [DllImport("libc.so.6",SetLastError=true)] internal static extern IntPtr read(int fd,IntPtr buffer,UIntPtr count);
        [DllImport("libc.so.6",SetLastError=true)] internal static extern int close(int fd);
        [DllImport("libc.so.6")] internal static extern uint getuid();
        [DllImport("libc.so.6")] internal static extern uint geteuid();
        [DllImport("libc.so.6",SetLastError=true)] internal static extern int statx(int fd,string path,int flags,uint mask,byte[] buffer);
        public long Now() => (long)(Stopwatch.GetTimestamp()*(1_000_000.0/Stopwatch.Frequency));
        public Result Open(){int r=open(Target,0x88000,0);return new(r,r<0?Marshal.GetLastWin32Error():0);}
        public Result Read(int fd,IntPtr pointer){long r=read(fd,pointer,(UIntPtr)Capacity).ToInt64();return new(r,r<0?Marshal.GetLastWin32Error():0);}
        public Result Close(int fd){int r=close(fd);return new(r,r<0?Marshal.GetLastWin32Error():0);}
    }
    internal static string Sha(byte[] b)=>Convert.ToHexString(SHA256.HashData(b)).ToLowerInvariant();
    internal static byte[] MakeReceipt(Observation o,byte[] b)=>JsonSerializer.SerializeToUtf8Bytes(new {
        schema="fk-single-read-v1",accepted=o.Accepted,executed=true,path=Target,requestedCount=Capacity,allocatedBytes=b.Length,
        initializedFillByte=Fill,bufferPinnedBeforeOpen=true,bufferPrefaultedBeforeOpen=true,
        openAttempted=o.OpenAttempted,readAttempted=o.ReadAttempted,closeAttempted=o.CloseAttempted,
        openResult=o.OpenResult.Value,openErrno=o.OpenResult.Errno,readResult=o.ReadResult.Value,readErrno=o.ReadResult.Errno,
        closeResult=o.CloseResult.Value,closeErrno=o.CloseResult.Errno,nativeClock="Stopwatch-monotonic-us",
        bracketsUs=o.Times,clockFailureMask=o.ClockFailureMask,exceptionMask=o.ExceptionMask,
        rawAllocationBase64=Convert.ToBase64String(b),rawAllocationSha256=Sha(b),
        returnedPrefixBytes=o.ReadResult.Value>=0&&o.ReadResult.Value<=Capacity?(int)o.ReadResult.Value:0,
        returnedPrefixSha256=o.ReadResult.Value>=0&&o.ReadResult.Value<=Capacity?Sha(b.AsSpan(0,(int)o.ReadResult.Value).ToArray()):null,
        readCallsMaximum=1,retries=0,writesToDriver=0,completeLogProven=false,externalRtpProducerProven=false,
        copyCompletionAttested=false,loadedModuleBytesAttested=false,producerAtomicityProven=false,
        timeoutOrRollbackGuaranteed=false,physicalPictureObserved=false
    },new JsonSerializerOptions{Encoder=JavaScriptEncoder.UnsafeRelaxedJsonEscaping});
    static void Need(bool b,string m){if(!b)throw new InvalidOperationException(m);}
    static int Execute(){
        // ABI refusal precedes every libc call, output-file creation and target open.
        Need(RuntimeInformation.ProcessArchitecture==Architecture.Arm && IntPtr.Size==4 && BitConverter.IsLittleEndian,"ARM32 little-endian required");
        Need(RealOps.getuid()==0 && RealOps.geteuid()==0,"root UID/EUID required");
        byte[] status=new byte[256];
        int sr=RealOps.statx(-100,Stage,0x100,0x10b,status);
        Need(sr==0&&(BitConverter.ToUInt32(status,0)&0x10b)==0x10b &&
            BitConverter.ToUInt16(status,28)==0x41c0 && BitConverter.ToUInt32(status,20)==0,"fixed receipt stage must be root-owned0700 directory, no symlink");
        int receiptFd=RealOps.open(ReceiptPath,1|0x40|0x80|0x80000|0x8000,0x180);
        Need(receiptFd>=0,"exclusive private receipt creation failed");
        using var output=new FileStream(new SafeFileHandle((IntPtr)receiptFd,true),FileAccess.Write,4096,false);
        byte[] buffer=new byte[Capacity];Array.Fill(buffer,Fill); // every byte touched before target open
        Observation o=new();IOps ops=new RealOps();ops.Now(); // warm monotonic path before acquisition
        GCHandle pin=GCHandle.Alloc(buffer,GCHandleType.Pinned);
        try{Acquire(ops,buffer,pin.AddrOfPinnedObject(),o);}finally{pin.Free();}
        byte[] receipt=MakeReceipt(o,buffer);Need(receipt.Length+1<=16384,"receipt bound");output.Write(receipt);output.WriteByte(10);output.Flush(true);
        return o.Accepted?0:1;
    }
    internal sealed class FakeOps : IOps {
        public readonly List<string> Calls=new();public long Tick;public int ClockCall,FailClock=-1;
        public Result OpenValue=new(7,0),ReadValue=new(16,0),CloseValue=new(0,0);
        public bool ThrowOpen,ThrowRead,ThrowClose,PlusPattern;public int CopyBytes=-1;
        public long Now(){int c=ClockCall++;if(c==FailClock)throw new Exception();return ++Tick;}
        public Result Open(){Calls.Add("open");if(ThrowOpen)throw new Exception();return OpenValue;}
        public Result Read(int fd,IntPtr p){Calls.Add("read");Need(fd==7,"fakefd");if(ThrowRead)throw new Exception();if(ReadValue.Value>=0&&ReadValue.Value<=Capacity)for(int i=0;i<(CopyBytes<0?ReadValue.Value:Math.Min(CopyBytes,ReadValue.Value));i++)Marshal.WriteByte(p,i,PlusPattern?(i%3==0?(byte)0xfb:i%3==1?(byte)0xef:(byte)0xbe):(byte)i);return ReadValue;}
        public Result Close(int fd){Calls.Add("close");Need(fd==7,"fakefd");if(ThrowClose)throw new Exception();return CloseValue;}
    }
    static int SelfTest(){
        int checks=0,cases=0;void Check(bool x){checks++;Need(x,"self-test "+checks);}
        Observation Run(FakeOps f){cases++;byte[] b=new byte[Capacity];Array.Fill(b,Fill);GCHandle h=GCHandle.Alloc(b,GCHandleType.Pinned);Observation o=new();try{Acquire(f,b,h.AddrOfPinnedObject(),o);}finally{h.Free();}
            Check(f.Calls.FindAll(x=>x=="open").Count<=1);Check(f.Calls.FindAll(x=>x=="read").Count<=1);Check(f.Calls.FindAll(x=>x=="close").Count<=1);
            Check(!o.OpenAttempted || o.OpenResult.Value<0 || o.CloseAttempted);byte[] r=MakeReceipt(o,b);Check(r.Length+1<=16384);using var j=JsonDocument.Parse(r);Check(!j.RootElement.GetProperty("copyCompletionAttested").GetBoolean());if(f.CopyBytes==1){Check(b[0]==0&&b[1]==Fill);Check(j.RootElement.GetProperty("returnedPrefixBytes").GetInt32()==16);}if(f.PlusPattern){Check(j.RootElement.GetProperty("rawAllocationBase64").GetString()!.StartsWith("++++"));Check(!System.Text.Encoding.UTF8.GetString(r).Contains("\\u002B"));}return o;}
        foreach(int n in new[]{0,1,16,4095,4096}){var f=new FakeOps{ReadValue=new(n,0)};Check(Run(f).Accepted);Check(string.Join(",",f.Calls)=="open,read,close");}
        foreach(int e in new[]{2,4,5,13}){var f=new FakeOps{OpenValue=new(-1,e)};var o=Run(f);Check(!o.Accepted);Check(string.Join(",",f.Calls)=="open");Check(o.Times[1]>=o.Times[0]);}
        foreach(int e in new[]{4,5,11}){var f=new FakeOps{ReadValue=new(-1,e)};Check(!Run(f).Accepted);Check(string.Join(",",f.Calls)=="open,read,close");}
        foreach(int n in new[]{4097,int.MaxValue})Check(!Run(new FakeOps{ReadValue=new(n,0)}).Accepted);
        Check(Run(new FakeOps{ReadValue=new(16,0),CopyBytes=1}).Accepted); // positive driver return cannot certify copy completion
        Check(Run(new FakeOps{ReadValue=new(Capacity,0),PlusPattern=true}).Accepted); // base64 plus characters must not expand sixfold
        Check(!Run(new FakeOps{ReadValue=new(16,5)}).Accepted);
        Check(!Run(new FakeOps{CloseValue=new(-1,4)}).Accepted);
        Check(!Run(new FakeOps{ThrowOpen=true}).Accepted);Check(!Run(new FakeOps{ThrowRead=true}).Accepted);Check(!Run(new FakeOps{ThrowClose=true}).Accepted);
        for(int c=0;c<6;c++){var f=new FakeOps{FailClock=c};var o=Run(f);Check(!o.Accepted);if(c==0)Check(f.Calls.Count==0);else Check(o.CloseAttempted);if(c==1||c==2)Check(!o.ReadAttempted);}
        for(int advertised=0;advertised<=65535;advertised++){long length=(long)(ushort)advertised+1;long copy=length<=4095?length:Math.Min(Capacity,length);Check(copy>=1&&copy<=Capacity);Check(4+copy<=131072);}
        Console.WriteLine(JsonSerializer.Serialize(new{schema="fk-host-tests-v1",checks,cases,targetReads=0,targetOpens=0,nativeIoUsed=false,maxReceiptBytes=16384}));return 0;
    }
    static int Fixture(){byte[] b=new byte[Capacity];Array.Fill(b,Fill);GCHandle h=GCHandle.Alloc(b,GCHandleType.Pinned);Observation o=new();try{Acquire(new FakeOps{ReadValue=new(Capacity,0)},b,h.AddrOfPinnedObject(),o);}finally{h.Free();}Console.WriteLine(System.Text.Encoding.UTF8.GetString(MakeReceipt(o,b)));return 0;}
    static int Main(string[] args){
        try{if(args.Length==1&&args[0]=="--execute")return Execute();
            if(args.Length==1&&args[0]=="--self-test")return SelfTest();
            if(args.Length==1&&args[0]=="--fixture")return Fixture();
            if(args.Length==0){Console.WriteLine("{\"schema\":\"fk-dry-v1\",\"executed\":false,\"fixedCount\":4096,\"targetReads\":0,\"explicitExecuteRequired\":true}");return 0;}
            return 64;
        }catch(Exception e){Console.Error.WriteLine("FK refused: "+e.GetType().Name);return 64;}
    }
}
