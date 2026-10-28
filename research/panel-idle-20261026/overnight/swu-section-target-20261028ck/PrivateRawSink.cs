using System;
using System.Buffers.Binary;
using System.Runtime.InteropServices;
using SwuSectionStream;
internal sealed class PrivateRawSink:IChunkSink,IDisposable {
 [DllImport("libc.so.6",EntryPoint="open",SetLastError=true)]private static extern int Create(string path,int flags,uint mode);
 [DllImport("libc.so.6",SetLastError=true)]private static extern IntPtr write(int fd,IntPtr bytes,UIntPtr count);
 [DllImport("libc.so.6",SetLastError=true)]private static extern int fsync(int fd);
 private readonly string path;private readonly long cap;private int fd=-1;private long count;private bool begun;
 internal PrivateRawSink(string path,long cap){this.path=path;this.cap=cap;}
 internal static int CreateFlags(Architecture a)=>Native.OpenFlags(a)|1|0x40|0x80;
 private void Stat(long size){byte[] s=Native.Stat(fd);ushort mode=BinaryPrimitives.ReadUInt16LittleEndian(s.AsSpan(28));Core.Require((mode&0xf000)==0x8000 && (mode&0xfff)==0x180 && BinaryPrimitives.ReadUInt32LittleEndian(s.AsSpan(16))==1 && BinaryPrimitives.ReadUInt32LittleEndian(s.AsSpan(20))==Native.geteuid() && BinaryPrimitives.ReadUInt64LittleEndian(s.AsSpan(40))==(ulong)size,"private raw stat");}
 public void Begin(SectionPlan p){Core.Require(!begun && p.MaximumRawOutputBytes==cap,"sink begin");begun=true;fd=Create(path,CreateFlags(RuntimeInformation.ProcessArchitecture),0x180);Core.Require(fd>=0,"exclusive output");Stat(0);}
 public unsafe int Write(ReadOnlySpan<byte> bytes){Core.Require(fd>=0 && bytes.Length>0 && bytes.Length<=cap-count,"output bound");long n;fixed(byte* p=bytes)n=write(fd,(IntPtr)p,(UIntPtr)bytes.Length).ToInt64();Core.Require(n>=0 && n<=bytes.Length,"output write");count+=n;return (int)n;}
 public void CompleteRaw(){Core.Require(fd>=0 && count==cap,"raw complete size");Core.Require(fsync(fd)==0,"raw sync");Stat(count);int old=fd;fd=-1;Core.Require(Native.close(old)==0,"raw close");}
 public void Abort(){if(fd>=0){int old=fd;fd=-1;Core.Require(Native.close(old)==0,"raw abort close");}}
 public void Dispose(){Abort();}
}
