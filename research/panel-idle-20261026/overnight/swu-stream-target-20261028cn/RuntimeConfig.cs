using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text.Json;
internal sealed class RuntimeConfig:IDisposable {
 internal const int MaximumBytes=4096;
 internal const string Server="198.51.100.10";
 internal readonly int Port;
 internal readonly string CertificateSha256;
 internal readonly byte[] Nonce;
 internal const int IoTimeoutSeconds=10,TotalTimeoutSeconds=90;
 private RuntimeConfig(int port,string certificate,byte[] nonce){Port=port;CertificateSha256=certificate;Nonce=nonce;}
 internal static bool HashText(string text){if(text.Length!=64)return false;foreach(char c in text)if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))return false;return true;}
 internal static bool SealReady=>ConfigPin.Bytes>=2 && ConfigPin.Bytes<=MaximumBytes && HashText(ConfigPin.Sha256) && ConfigPin.Sha256!=new string('0',64);
 private static byte[] NonceValue(ref Utf8JsonReader reader){
  Core.Require(reader.TokenType==JsonTokenType.String && !reader.HasValueSequence && reader.ValueSpan.IndexOf((byte)92)<0 && reader.ValueSpan.Length==64,"nonce format");
  byte[] nonce=new byte[32];
  try{for(int i=0;i<32;i++){int a=Hex(reader.ValueSpan[i*2]),b=Hex(reader.ValueSpan[i*2+1]);Core.Require(a>=0&&b>=0,"nonce format");nonce[i]=(byte)((a<<4)|b);}return nonce;}
  catch{CryptographicOperations.ZeroMemory(nonce);throw;}
 }
 private static int Hex(byte c)=>c>=48&&c<=57?c-48:c>=97&&c<=102?c-87:-1;
 internal static RuntimeConfig Parse(ReadOnlySpan<byte> bytes){
  Core.Require(bytes.Length>=2 && bytes.Length<=MaximumBytes,"config bound");
  byte[]? nonce=null;int? port=null,io=null,total=null;string? server=null,certificate=null;
  try{
   Utf8JsonReader reader=new Utf8JsonReader(bytes,new JsonReaderOptions{AllowTrailingCommas=false,CommentHandling=JsonCommentHandling.Disallow,MaxDepth=2});
   Core.Require(reader.Read() && reader.TokenType==JsonTokenType.StartObject,"config object");
   HashSet<string> seen=new HashSet<string>(StringComparer.Ordinal);
   while(reader.Read() && reader.TokenType!=JsonTokenType.EndObject){
    Core.Require(reader.TokenType==JsonTokenType.PropertyName && !reader.HasValueSequence && reader.ValueSpan.IndexOf((byte)92)<0,"config field");string name=reader.GetString()!;
    Core.Require(seen.Add(name) && reader.Read(),"config duplicate or missing value");
    switch(name){
     case "server_ipv4":Core.Require(reader.TokenType==JsonTokenType.String,"server type");server=reader.GetString();break;
     case "server_port":Core.Require(reader.TokenType==JsonTokenType.Number && reader.TryGetInt32(out int p),"port type");port=reader.GetInt32();break;
     case "certificate_sha256":Core.Require(reader.TokenType==JsonTokenType.String,"certificate type");certificate=reader.GetString();break;
     case "nonce_hex":nonce=NonceValue(ref reader);break;
     case "io_timeout_seconds":Core.Require(reader.TokenType==JsonTokenType.Number && reader.TryGetInt32(out int i),"timeout type");io=reader.GetInt32();break;
     case "total_timeout_seconds":Core.Require(reader.TokenType==JsonTokenType.Number && reader.TryGetInt32(out int t),"timeout type");total=reader.GetInt32();break;
     default:throw new InvalidOperationException("unknown config field");
    }
   }
   Core.Require(reader.TokenType==JsonTokenType.EndObject && !reader.Read() && seen.Count==6,"config EOF/count");
   Core.Require(server==Server && port>=1024 && port<=65535 && certificate!=null && HashText(certificate) && nonce!=null && io==IoTimeoutSeconds && total==TotalTimeoutSeconds,"config values");
   RuntimeConfig result=new RuntimeConfig(port!.Value,certificate!,nonce!);nonce=null;return result;
  }finally{if(nonce!=null)CryptographicOperations.ZeroMemory(nonce);}
 }
 public void Dispose()=>CryptographicOperations.ZeroMemory(Nonce);
}
