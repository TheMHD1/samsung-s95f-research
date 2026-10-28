using System;
using System.Security.Cryptography;
internal static class Core {
 internal const int Shared=65536,Blob=416;
 internal const string BlobHash="d8af420d63b9cb2643783c56ce7396a5fd4d809e48df0bd321781cfd025e8220";
 internal static void Require(bool ok,string reason) {if(!ok)throw new InvalidOperationException(reason);}
 internal static string Hash(ReadOnlySpan<byte> b)=>Convert.ToHexString(SHA256.HashData(b)).ToLowerInvariant();
}
