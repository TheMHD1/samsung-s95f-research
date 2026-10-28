using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json;
using SwuHeaderAuthentication;
internal static class IndependentBindings
{
 static int checks,cases;
 static void Need(bool good,string code){if(!good)throw new InvalidOperationException(code);checks++;}
 static string Hash(byte[] data)=>Convert.ToHexString(SHA256.HashData(data));
 static void Test(byte[] raw,byte[] pem,PublicPemPin pin,Rejection expected)
 {
  string before=Hash(raw),keyBefore=Hash(pem);
  ValidationResult result=Validator.Authenticate4032(raw,pem,pin);
  Need(result.Reason==expected && result.Accepted==(expected==Rejection.None),"bound reason");
  Need(Hash(raw)==before && Hash(pem)==keyBefore,"caller buffers unchanged");
  Need(!result.FullSchemaValidated && !result.MetadataPublished && !result.FirmwareApplicabilityValidated,"limited claims");
  if(expected!=Rejection.None)Need(result.SelectedBytes==0 && result.PaddingBytes==0 && result.Representation==Representation.None && !result.SignatureAuthenticityValidated,"failure publishes no selected fields");
  cases++;
 }
 static int Main(string[] args)
 {
  try {
   Need(args.Length==3,"arguments");string cc=args[0],own=args[1];
   byte[] actual=File.ReadAllBytes(args[2]),pem=File.ReadAllBytes(Path.Combine(cc,"fixtures/synthetic-public.pem")),raw=File.ReadAllBytes(Path.Combine(cc,"fixtures/raw-no-padding.bin"));
   using JsonDocument manifest=JsonDocument.Parse(File.ReadAllBytes(Path.Combine(cc,"fixtures/manifest.json")));
   JsonElement root=manifest.RootElement,anchor=root.GetProperty("primary"),good=root.GetProperty("fixtures").EnumerateArray().Single(x=>x.GetProperty("name").GetString()=="raw-no-padding");
   PublicPemPin synth=new PublicPemPin(anchor.GetProperty("pemBytes").GetInt32(),anchor.GetProperty("pemSha256").GetString()!,Convert.ToUInt32(anchor.GetProperty("pemCrc32").GetString(),16),2048,256,Convert.ToUInt32(good.GetProperty("plaintextCrc32").GetString(),16));
   Test(raw,pem,synth,Rejection.None);
   Test(raw,pem,PublicPemPin.Master,Rejection.PublicKeyPin);
   Test(raw,actual,PublicPemPin.Master,Rejection.RepresentationCrcMismatch);
   Test(raw,actual,PublicPemPin.Master with {PlaintextCrc32=synth.PlaintextCrc32},Rejection.PublicKeyCrc);
   using JsonDocument extra=JsonDocument.Parse(File.ReadAllBytes(Path.Combine(own,"extra-binding-cases.json")));
   foreach(JsonElement row in extra.RootElement.GetProperty("cases").EnumerateArray()) {
    string name=row.GetProperty("name").GetString()!;byte[] changed=File.ReadAllBytes(Path.Combine(own,row.GetProperty("path").GetString()!));uint crc=row.GetProperty("plaintextCrc32").GetUInt32();
    bool master=name=="actual-key-crc-synthetic-signature";
    Test(changed,master?actual:pem,(master?PublicPemPin.Master:synth) with {PlaintextCrc32=crc},name=="declared-signature255"?Rejection.SignatureLength:Rejection.SignatureInvalid);
   }
   foreach(string name in new[]{"wrong-signature","wrong-signed-remainder","wrong-digest-sha256","wrong-rsa-padding-pss","ambiguous-crc"}) {
    JsonElement row=root.GetProperty("fixtures").EnumerateArray().Single(x=>x.GetProperty("name").GetString()==name);
    Test(File.ReadAllBytes(Path.Combine(cc,"fixtures",row.GetProperty("path").GetString()!)),pem,synth with {PlaintextCrc32=Convert.ToUInt32(row.GetProperty("plaintextCrc32").GetString(),16)},name=="ambiguous-crc"?Rejection.RepresentationAmbiguous:Rejection.SignatureInvalid);
   }
   byte[] changedPem=(byte[])actual.Clone();changedPem[changedPem.Length-1]^=1;
   Test(raw,changedPem,PublicPemPin.Master,Rejection.PublicKeyPin);
   Console.WriteLine(JsonSerializer.Serialize(new {checks,cases,compiled_frozen_source=true,synthetic_only=true,actual_public_key_only=true,target_operations=0,metadata_published=false}));return 0;
  }catch{Console.WriteLine("INDEPENDENT_BINDING_CHECK_FAILED no_content_logged=1");return 1;}
 }
}
