using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using SwuSectionStream;
internal static class IntegrationTests {
 internal static int Run(){int checks=0;void Check(bool ok){if(!ok)throw new InvalidOperationException("host check");checks++;}
  void Refuse(Action action){bool rejected=false;try{action();}catch{rejected=true;}Check(rejected);}
  Check(Native.AlarmSeconds==1700);Check(Native.RequiredStatMask==0x3df);
  Check(Native.OpenFlags(System.Runtime.InteropServices.Architecture.Arm)==0xa8000);
  Check(Native.OpenFlags(System.Runtime.InteropServices.Architecture.X64)==0xa0000);
  byte[] plan=File.ReadAllBytes("private/section-plan.bin"),salt=Program.CheckPlan(plan);
  try{Check(plan.Length==72 && salt.Length==8);Check((Program.CipherBytes+65535)/65536==22209);Check((Program.CipherBytes+65535)/65536+6==22215);}
  finally{CryptographicOperations.ZeroMemory(salt);}
  foreach(int at in new[]{0,8,12,20,28,32,40,71}){byte[] bad=(byte[])plan.Clone();bad[at]^=1;try{Refuse(()=>Program.CheckPlan(bad));}finally{CryptographicOperations.ZeroMemory(bad);}}
  Refuse(()=>Program.CheckPlan(new byte[71]));Refuse(()=>Program.CheckPlan(new byte[73]));
  string valid="{\"server_ipv4\":\"198.51.100.10\",\"server_port\":49152,\"certificate_sha256\":\""+new string('b',64)+"\",\"nonce_hex\":\""+new string('a',64)+"\",\"io_timeout_seconds\":10,\"total_timeout_seconds\":1600}";
  RuntimeConfig cfg=RuntimeConfig.Parse(Encoding.UTF8.GetBytes(valid));byte[] held=cfg.Nonce;Check(cfg.Port==49152 && held.Length==32 && held.All(b=>b==0xaa));cfg.Dispose();Check(held.All(b=>b==0));
  string[] malformed={
   valid.Replace("198.51.100.10","198.51.100.10"),valid.Replace("198.51.100.10","host.local"),valid.Replace("49152","1023"),valid.Replace("49152","65536"),valid.Replace("49152","49152.0"),valid.Replace("49152","\"49152\""),
   valid.Replace(new string('b',64),new string('B',64)),valid.Replace(new string('b',64),new string('b',63)),valid.Replace(new string('a',64),new string('A',64)),valid.Replace(new string('a',64),new string('a',63)),valid.Replace(new string('a',64),new string('g',64)),
   valid.Replace(":10",":11"),valid.Replace(":1600",":1601"),valid.Replace(":1600",":null"),valid.Replace("\"server_port\":49152","\"server_port\":[]"),valid.Replace("\"server_ipv4\"","\"server_\\u0069pv4\""),
   valid[..^1]+",\"extra\":1}",valid[..^1]+",\"server_port\":49152}",valid[..^1]+",}",valid+"{}",valid[..^1],"[]","null","{}","/*x*/"+valid
  };
  foreach(string bad in malformed)Refuse(()=>RuntimeConfig.Parse(Encoding.UTF8.GetBytes(bad)));
  using(JsonDocument doc=JsonDocument.Parse(valid))foreach(JsonProperty removed in doc.RootElement.EnumerateObject()){
   string partial="{"+string.Join(",",doc.RootElement.EnumerateObject().Where(p=>p.Name!=removed.Name).Select(p=>JsonSerializer.Serialize(p.Name)+":"+p.Value.GetRawText()))+"}";Refuse(()=>RuntimeConfig.Parse(Encoding.UTF8.GetBytes(partial)));
  }
  Refuse(()=>RuntimeConfig.Parse(new byte[4097]));Refuse(()=>RuntimeConfig.Parse(Array.Empty<byte>()));
  byte[] actual=File.ReadAllBytes("private/tls-config.json");try{Check(RuntimeConfig.SealReady && actual.Length==ConfigPin.Bytes && Core.Hash(actual)==ConfigPin.Sha256);using RuntimeConfig pinned=RuntimeConfig.Parse(actual);Check(pinned.Nonce.Length==32);}finally{CryptographicOperations.ZeroMemory(actual);}
  using Block op=new Block(60);StreamingEngine.Frame(op,0,0x2000,0x2024,0x2048);Check(op.Get(4)==0x01010d0d&&op.Get(36)==1&&op.Get(44)==1&&op.Get(48)==0x201&&op.Get(56)==0);
  CryptographicOperations.ZeroMemory(plan);Console.WriteLine("CR_INTEGRATION_TESTS checks="+checks+" target_calls=0");return 0;
 }
}
