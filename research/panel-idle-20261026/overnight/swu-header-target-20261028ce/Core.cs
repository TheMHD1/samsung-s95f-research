using System;
using System.Buffers.Binary;
using System.Runtime.InteropServices;
using System.Security.Cryptography;

internal sealed class Block : IDisposable
{
    internal readonly int Size;
    internal IntPtr Pointer { get; private set; }
    internal Block(int size) { Size=size; Pointer=Marshal.AllocHGlobal(size); Clear(); }
    internal unsafe Span<byte> Bytes => new Span<byte>((void*)Pointer,Size);
    internal void Clear() => CryptographicOperations.ZeroMemory(Bytes);
    internal uint Get(int offset) => BinaryPrimitives.ReadUInt32LittleEndian(Bytes.Slice(offset,4));
    internal void Put(int offset,uint value) => BinaryPrimitives.WriteUInt32LittleEndian(Bytes.Slice(offset,4),value);
    public void Dispose() { if(Pointer!=IntPtr.Zero) { Clear(); Marshal.FreeHGlobal(Pointer); Pointer=IntPtr.Zero; } }
}
internal interface ITeec
{
    uint Initialize(Block context);
    uint Allocate(Block context,Block shared);
    uint Open(Block context,Block session,Block uuid,out uint origin);
    uint Invoke(Block session,uint command,Block operation,out uint origin);
    void Close(Block session);
    void Release(Block shared);
    void FinalizeContext(Block context);
    uint Address(Block block);
    BlockView Map(Block shared);
}
internal readonly struct BlockView
{
    internal readonly IntPtr Pointer;
    internal readonly int Size;
    internal BlockView(IntPtr pointer,int size) { Pointer=pointer; Size=size; }
    internal unsafe Span<byte> Bytes => new Span<byte>((void*)Pointer,Size);
    internal void Clear() => CryptographicOperations.ZeroMemory(Bytes);
}
internal sealed class Result
{
    internal string Stage="input";
    internal uint Code,Origin=uint.MaxValue;
    internal bool LocalFailure,ContextFinalized,SessionClosed;
    internal int Released;
    internal readonly uint[] Calls=new uint[3],Counts=new uint[2],Observed=new uint[2];
    internal void Print() => Console.WriteLine($"SWU_METADATA_DIAGNOSTIC stage={Stage} result=0x{Code:x8} origin=0x{Origin:x8} local={(LocalFailure?1:0)} calls={Calls[0]},{Calls[1]},{Calls[2]} counts={Counts[0]},{Counts[1]} observed={Observed[0]},{Observed[1]} closed={(SessionClosed?1:0)} released={Released} finalized={(ContextFinalized?1:0)} metadata_published=0");
}
internal delegate void PlaintextConsumer(ReadOnlySpan<byte> plaintext);
internal static class Core
{
    internal const int Shared=65536,Cipher=4032,Envelope=4056,Blob=416;
    internal const string EnvelopeHash="6da1e2386f0f97a180984f249febaf831febfee1adb35a8cefa96f89ad069e0d";
    internal const string BlobHash="d8af420d63b9cb2643783c56ce7396a5fd4d809e48df0bd321781cfd025e8220";
    internal static void Require(bool condition,string message) { if(!condition) throw new InvalidOperationException(message); }
    internal static string Hash(ReadOnlySpan<byte> bytes) => Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
    internal static void Validate(byte[] envelope,byte[] blob)
    {
        Require(envelope.Length==Envelope && blob.Length==Blob,"input sizes");
        Require(envelope.AsSpan(8,8).SequenceEqual("Salted__".u8compat()),"input marker");
        Require(Hash(envelope)==EnvelopeHash && Hash(blob)==BlobHash,"fixed input hashes");
    }
    private static byte[] u8compat(this string text) => System.Text.Encoding.ASCII.GetBytes(text);
    internal static void Frame(Block op,int cmd,uint input,uint output,uint salt)
    {
        Require(op.Size==60 && cmd>=0 && cmd<=2,"operation layout"); op.Clear();
        if(cmd==0) { op.Put(4,0x01010d0d); Mem(op,8,input,Blob); Mem(op,20,salt,8); op.Put(36,1); op.Put(44,1); op.Put(48,0x201); }
        if(cmd==1) { op.Put(4,0x00020e0d); Mem(op,8,input,Cipher); Mem(op,20,output,Cipher); }
        if(cmd==2) { op.Put(4,0x0000020e); Mem(op,8,output,Shared); }
    }
    private static void Mem(Block op,int offset,uint parent,uint size) { op.Put(offset,parent); op.Put(offset+4,size); }
    // Caller validates exact hashes. The separate synthetic test calls this core
    // without the real encrypted blob; the live path always calls Validate first.
    internal static Result Run(ITeec api,byte[] envelope,byte[] blob,Action selectorCheck,PlaintextConsumer? inspect=null)
    {
        Result r=new Result(); bool initialized=false,opened=false; int allocated=0;
        using Block context=new Block(4),session=new Block(4),uuid=new Block(16),op=new Block(60),plain=new Block(Cipher);
        Block[] sm={new Block(36),new Block(36),new Block(36)};
        BlockView[] view=new BlockView[3]; uint[] parent=new uint[3]; int total=0;
        try {
            selectorCheck(); r.Stage="context"; r.Code=api.Initialize(context);
            if(r.Code!=0) return r; initialized=true;
            for(int i=0;i<3;i++) {
                r.Stage="allocate"+i; r.Origin=uint.MaxValue;
                sm[i].Put(4,Shared); sm[i].Put(8,3); r.Code=api.Allocate(context,sm[i]);
                if(r.Code!=0) return r; allocated++;
                Require(sm[i].Get(4)==Shared && sm[i].Get(0)!=0,"returned allocation");
                view[i]=api.Map(sm[i]); Require(view[i].Pointer!=IntPtr.Zero && view[i].Size==Shared,"mapped allocation");
                parent[i]=api.Address(sm[i]); Require(parent[i]!=0,"parent address"); view[i].Clear();
            }
            uuid.Put(0,0x22222221); uuid.Bytes[15]=1;
            r.Stage="session"; r.Origin=uint.MaxValue; r.Code=api.Open(context,session,uuid,out r.Origin);
            if(r.Code!=0) return r; opened=true;
            selectorCheck(); // Stop before any TA command if selector drifted during open.
            blob.CopyTo(view[0].Bytes); envelope.AsSpan(16,8).CopyTo(view[2].Bytes);
            Frame(op,0,parent[0],parent[1],parent[2]); r.Stage="command0"; r.Origin=uint.MaxValue; r.Calls[0]++;
            r.Code=api.Invoke(session,0,op,out r.Origin);
            view[0].Clear(); view[2].Clear(); CryptographicOperations.ZeroMemory(blob);
            if(r.Code!=0) return r;
            envelope.AsSpan(24,Cipher).CopyTo(view[0].Bytes);
            Frame(op,1,parent[0],parent[1],parent[2]); r.Stage="command1"; r.Origin=uint.MaxValue; r.Calls[1]++;
            r.Code=api.Invoke(session,1,op,out r.Origin); if(r.Code!=0) return r;
            uint n=op.Get(32); r.Observed[0]=n;
            Require(n<=Cipher && n<=Shared && n<=Cipher-total,"update count");
            r.Counts[0]=n; view[1].Bytes.Slice(0,(int)n).CopyTo(plain.Bytes.Slice(total)); total+=(int)n; view[1].Clear();
            Frame(op,2,parent[0],parent[1],parent[2]); r.Stage="command2"; r.Origin=uint.MaxValue; r.Calls[2]++;
            r.Code=api.Invoke(session,2,op,out r.Origin); if(r.Code!=0) return r;
            n=op.Get(20); r.Observed[1]=n;
            Require(n<=Shared && n<=Cipher-total,"final count");
            r.Counts[1]=n; view[1].Bytes.Slice(0,(int)n).CopyTo(plain.Bytes.Slice(total)); total+=(int)n;
            selectorCheck();
            if(inspect!=null) { r.Stage="inspection"; Require(total==Cipher,"inspection total count"); inspect(plain.Bytes.Slice(0,total)); }
            r.Stage="quarantined";
        } catch(Exception) { r.LocalFailure=true; r.Code=0xffff0006; }
        finally {
            // Cleanup callbacks are native void methods. Later cleanup continues
            // if a managed adapter throws; it cannot replace first diagnostics.
            if(opened) try { api.Close(session); r.SessionClosed=true; } catch { }
            for(int i=allocated-1;i>=0;i--) {
                if(view[i].Pointer!=IntPtr.Zero) view[i].Clear();
                try { api.Release(sm[i]); r.Released++; } catch { }
            }
            if(initialized) try { api.FinalizeContext(context); r.ContextFinalized=true; } catch { }
            CryptographicOperations.ZeroMemory(blob); foreach(Block s in sm) s.Dispose();
        }
        return r;
    }
}
