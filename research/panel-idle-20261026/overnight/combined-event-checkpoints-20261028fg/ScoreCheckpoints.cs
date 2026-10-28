using System;
using System.Security.Cryptography;
using System.Text.Json;
internal static partial class Program
{
 sealed class ScoreCheckpointBuffer
 {
  const int Size=58, Capacity=56;
  readonly byte[] raw=new byte[Size*Capacity];
  public string Schema=>"fg-stockevent-checkpoints-v1";
  public int RecordBytes=>Size;
  public int Count{get;private set;}
  public string RawBase64=>Convert.ToBase64String(raw,0,Count*Size);
  public string Sha256=>Convert.ToHexString(SHA256.HashData(raw.AsSpan(0,Count*Size))).ToLowerInvariant();
  void U32(int at,uint value)=>BitConverter.TryWriteBytes(raw.AsSpan(at,4),value);
  uint Delta(long? value,long start){Need(value.HasValue&&value.Value>=start&&value.Value-start<=uint.MaxValue,"checkpoint timestamp extent");return (uint)(value!.Value-start);}
  public void Add(Capture c,long start){
   Need(Count<Capacity&&c.CycleIndex==Count+1&&c.WindowCount==8&&c.TransferCount==16,"checkpoint complete sequential cycle capacity");
   for(int i=0;i<8;i++)Need(c.Windows[i].Spec==CycleSpecs[i]&&c.Windows[i].Count==CycleSpecs[i].Length,"checkpoint fixed complete windows");
   int at=Count*Size;byte[] r=c.Windows[0].Buffer, e=c.Windows[7].Buffer, h=c.Windows[5].Buffer,n=c.Windows[4].Buffer;
   raw[at]=(byte)(((byte)ClassifyRt(r)<<4)|(byte)ClassifyRt(e));raw[at+1]=c.Windows[2].Buffer[7];
   Array.Copy(r,0xc4,raw,at+2,2);Array.Copy(e,0xc4,raw,at+4,2);
   Array.Copy(h,4,raw,at+6,4);Array.Copy(h,28,raw,at+10,2);Array.Copy(h,40,raw,at+12,8);
   Array.Copy(n,0,raw,at+20,4);
   U32(at+24,Delta(c.Transfers[10].BeforeUs,start));U32(at+28,Delta(c.Transfers[11].AfterUs,start));
   Array.Copy(c.Windows[1].Buffer,42,raw,at+32,2);
   // Appended source bytes only: earlier M/P reads and the completed end-R.
   byte[] m=c.Windows[1].Buffer,p=c.Windows[3].Buffer;
   Array.Copy(m,2,raw,at+34,2);Array.Copy(m,4,raw,at+36,2);
   Array.Copy(m,0x22,raw,at+38,2);Array.Copy(m,0x24,raw,at+40,2);
   Array.Copy(e,0x60,raw,at+42,2);Array.Copy(e,0x6e,raw,at+44,2);
   Array.Copy(p,4,raw,at+46,4);Array.Copy(p,8,raw,at+50,4);
   Array.Copy(e,0xca,raw,at+54,2);Array.Copy(e,0x68,raw,at+56,2);
   Count++;
  }
 }
}
