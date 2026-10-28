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
internal static class Core
{
    internal static void Require(bool condition,string message) {if(!condition)throw new InvalidOperationException(message);}
    internal static string Hash(ReadOnlySpan<byte> bytes)=>Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
}
