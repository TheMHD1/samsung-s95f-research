using System;
using System.Buffers.Binary;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Security;
using System.Net.Sockets;
using System.Security.Authentication;
using System.Security.Cryptography;
using System.Threading;
using SwuSectionStream;

namespace SwuStreamTransport;
public sealed record ChannelOptions(string ServerIpv4,int Port,string CertificateSha256,byte[] Nonce,
    long CipherBytes,string CipherSha256,long MaximumOutputBytes,int IoTimeoutSeconds=10,int TotalTimeoutSeconds=90);

// Single-use synchronous duplex channel. No reconnect or TEEC retry. The only
// completion statement is private raw quarantine completion, never authentication.
public sealed class TlsSectionChannel : IChunkSource,IChunkSink,IDisposable
{
    readonly ChannelOptions options;
    readonly TcpClient tcp=new();
    SslStream? tls;
    readonly Stopwatch elapsed=Stopwatch.StartNew();
    Timer? timer;
    bool begun,terminal,faulted,eof;
    long input,output;
    public long CipherBytesReceived=>input;
    public long RawBytesAcknowledged=>output;
    public bool RawCompletionAcknowledged {get;private set;}
    public TlsSectionChannel(ChannelOptions value)
    {
        if(value is null || !IPAddress.TryParse(value.ServerIpv4,out var ip) || ip.AddressFamily!=AddressFamily.InterNetwork || value.Port<1 || value.Port>65535 ||
           !Hex(value.CertificateSha256) || !Hex(value.CipherSha256) || value.Nonce is null || value.Nonce.Length!=32 || value.CipherBytes<16 ||
           value.CipherBytes>2147483648L || value.CipherBytes%16!=0 || value.MaximumOutputBytes<1 || value.MaximumOutputBytes>value.CipherBytes ||
           value.IoTimeoutSeconds<1 || value.IoTimeoutSeconds>10 || value.TotalTimeoutSeconds<1 || value.TotalTimeoutSeconds>7200)
            throw new ArgumentException("channel_options");
        options=value with {Nonce=(byte[])value.Nonce.Clone()};
        try {
            timer=new Timer(_=>{try{tcp.Dispose();}catch{}},null,TimeSpan.FromSeconds(options.TotalTimeoutSeconds),Timeout.InfiniteTimeSpan);
            using(var cts=new CancellationTokenSource(TimeoutMilliseconds())) tcp.ConnectAsync(ip,options.Port,cts.Token).AsTask().GetAwaiter().GetResult();
            tcp.NoDelay=true;
            tls=new SslStream(tcp.GetStream(),false,(_,cert,_,_)=>{
                if(cert is null)return false;
                byte[] actual=SHA256.HashData(cert.GetRawCertData());
                byte[] expected=Convert.FromHexString(options.CertificateSha256);
                try{return CryptographicOperations.FixedTimeEquals(actual,expected);}finally{CryptographicOperations.ZeroMemory(actual);CryptographicOperations.ZeroMemory(expected);}
            });
            using(var cts=new CancellationTokenSource(TimeoutMilliseconds())) tls.AuthenticateAsClientAsync(new SslClientAuthenticationOptions {
                TargetHost=options.ServerIpv4,EnabledSslProtocols=SslProtocols.Tls12|SslProtocols.Tls13,
                CertificateRevocationCheckMode=System.Security.Cryptography.X509Certificates.X509RevocationMode.NoCheck
            },cts.Token).GetAwaiter().GetResult();
            Span<byte> hello=stackalloc byte[37];hello[0]=(byte)'H';hello[1]=67;hello[2]=71;hello[3]=84;hello[4]=49;options.Nonce.CopyTo(hello.Slice(5));
            try{Send(hello);Ack((byte)'H',0);}finally{CryptographicOperations.ZeroMemory(hello);CryptographicOperations.ZeroMemory(options.Nonce);}
        } catch {Fail();throw new IOException("channel_connect_failed");}
    }
    static bool Hex(string? value)=>value is not null && value.Length==64 && System.Text.RegularExpressions.Regex.IsMatch(value,"\\A[0-9a-f]{64}\\z");
    int TimeoutMilliseconds(){long left=(long)options.TotalTimeoutSeconds*1000-elapsed.ElapsedMilliseconds;if(left<=0)throw new IOException("channel_deadline");return (int)Math.Min(options.IoTimeoutSeconds*1000L,left);}
    void Check(){if(terminal || faulted || tls is null)throw new IOException("channel_closed");int ms=TimeoutMilliseconds();tls.ReadTimeout=ms;tls.WriteTimeout=ms;}
    void Send(ReadOnlySpan<byte> bytes){Check();tls!.Write(bytes);}
    void Exact(Span<byte> bytes){int offset=0;while(offset<bytes.Length){Check();int n=tls!.Read(bytes.Slice(offset));if(n<=0)throw new IOException("channel_eof");offset+=n;}}
    byte Tag(){Span<byte> tag=stackalloc byte[1];Exact(tag);if(tag[0]=='E'){Span<byte> code=stackalloc byte[2];Exact(code);throw new IOException("channel_peer_rejected");}return tag[0];}
    void Ack(byte operation,uint count){if(Tag()!='A')throw new IOException("channel_frame");Span<byte> body=stackalloc byte[5];Exact(body);if(body[0]!=operation || BinaryPrimitives.ReadUInt32BigEndian(body.Slice(1))!=count)throw new IOException("channel_ack");}
    void Fail(){faulted=true;terminal=true;try{tls?.Dispose();}catch{}try{tcp.Dispose();}catch{}timer?.Dispose();if(options is not null)CryptographicOperations.ZeroMemory(options.Nonce);}
    public void Begin(SectionPlan plan){if(begun || terminal || plan is null || plan.CipherBytes!=options.CipherBytes || plan.CipherSha256!=options.CipherSha256)throw new IOException("channel_plan");begun=true;}
    public int Read(Span<byte> destination)
    {
        if(!begun || destination.Length<1 || destination.Length>65536 || eof)throw new IOException("channel_read_state");
        try {
            Span<byte> request=stackalloc byte[5];request[0]=(byte)'R';BinaryPrimitives.WriteUInt32BigEndian(request.Slice(1),(uint)destination.Length);Send(request);
            if(Tag()!='D')throw new IOException("channel_frame");Span<byte> length=stackalloc byte[4];Exact(length);int n=BinaryPrimitives.ReadInt32BigEndian(length);
            if(n<0 || n>destination.Length || n>options.CipherBytes-input || (n==0 && input!=options.CipherBytes))throw new IOException("channel_read_count");
            Exact(destination.Slice(0,n));input+=n;if(n==0)eof=true;return n;
        } catch{Fail();throw new IOException("channel_read_failed");}
    }
    public int Write(ReadOnlySpan<byte> plaintext)
    {
        if(!begun || plaintext.Length<1 || plaintext.Length>65536 || plaintext.Length>options.MaximumOutputBytes-output)throw new IOException("channel_write_state");
        try{Span<byte> request=stackalloc byte[5];request[0]=(byte)'W';BinaryPrimitives.WriteUInt32BigEndian(request.Slice(1),(uint)plaintext.Length);Send(request);Send(plaintext);Ack((byte)'W',(uint)plaintext.Length);output+=plaintext.Length;return plaintext.Length;}
        catch{Fail();throw new IOException("channel_write_failed");}
    }
    public void CompleteRaw()
    {
        if(!begun || terminal || !eof || input!=options.CipherBytes)throw new IOException("channel_complete_state");
        try{Span<byte> request=stackalloc byte[1];request[0]=(byte)'C';Send(request);Ack((byte)'C',0);RawCompletionAcknowledged=true;terminal=true;Dispose();}
        catch{Fail();throw new IOException("channel_complete_failed");}
    }
    public void Abort(){if(terminal)return;try{Span<byte> request=stackalloc byte[1];request[0]=(byte)'F';Send(request);Ack((byte)'F',0);}finally{terminal=true;Dispose();}}
    public void Dispose(){terminal=true;timer?.Dispose();try{tls?.Dispose();}finally{tcp.Dispose();CryptographicOperations.ZeroMemory(options.Nonce);}}
}
