using System;
using System.IO;
using System.Text.Json;
using SwuSectionStream;
using SwuStreamTransport;
class ClientTests
{
    static int Main(string[] args)
    {
        try {
            using var doc=JsonDocument.Parse(File.ReadAllBytes(args[0]));var root=doc.RootElement;
            long count=root.GetProperty("cipher_bytes").GetInt64();string sha=root.GetProperty("cipher_sha256").GetString()!;
            var options=new ChannelOptions(root.GetProperty("host").GetString()!,root.GetProperty("port").GetInt32(),root.GetProperty("certificate_sha256").GetString()!,Convert.FromHexString(root.GetProperty("nonce").GetString()!),count,sha,root.GetProperty("maximum_output_bytes").GetInt64(),root.GetProperty("io_timeout_seconds").GetInt32(),root.GetProperty("total_timeout_seconds").GetInt32());
            string mode=root.GetProperty("mode").GetString()!;
            using var channel=new TlsSectionChannel(options);
            channel.Begin(new SectionPlan(count,sha,new string('0',64),new string('1',64)));
            if(mode=="early_complete"){channel.CompleteRaw();return 2;}
            byte[] buffer=new byte[65536];long seen=0;
            if(mode=="abort"){int n=channel.Read(buffer.AsSpan(0,16));if(n!=16)throw new Exception();Array.Fill(buffer,(byte)0xa5);channel.Write(buffer.AsSpan(0,16));channel.Abort();Console.WriteLine("aborted");return 0;}
            if(mode=="overflow"){Array.Fill(buffer,(byte)0xa5);channel.Write(buffer.AsSpan(0,(int)Math.Min(count,65536)));channel.Write(buffer.AsSpan(0,1));return 2;}
            while(seen<count){int n=channel.Read(buffer.AsSpan(0,(int)Math.Min(buffer.Length,count-seen)));for(int i=0;i<n;i++)if(buffer[i]!=(byte)((seen+i)*17+3))throw new Exception();seen+=n;Array.Fill(buffer,(byte)0xa5);channel.Write(buffer.AsSpan(0,n));}
            if(channel.Read(buffer.AsSpan(0,1))!=0)throw new Exception();
            channel.CompleteRaw();if(!channel.RawCompletionAcknowledged || channel.CipherBytesReceived!=count || channel.RawBytesAcknowledged!=count)throw new Exception();
            Console.WriteLine("raw_complete");return 0;
        } catch {Console.WriteLine("client_failed");return 1;}
    }
}
