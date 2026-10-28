using System;
using System.Buffers.Binary;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using SwuHeaderAuthentication;

internal static class HostTests
{
    static int checks,fixtures;
    static void Need(bool ok,string code) {if(!ok)throw new InvalidOperationException(code);checks++;}
    static string Hash(byte[] b)=>Convert.ToHexString(SHA256.HashData(b)).ToLowerInvariant();
    static uint Hex(JsonElement node,string key)=>Convert.ToUInt32(node.GetProperty(key).GetString(),16);
    static PublicPemPin Pin(JsonElement node,uint crc)=>new PublicPemPin(node.GetProperty("pemBytes").GetInt32(),
        node.GetProperty("pemSha256").GetString()!,Hex(node,"pemCrc32"),node.GetProperty("rsaBits").GetInt32(),
        node.GetProperty("signatureBytes").GetInt32(),crc);
    static void Rejected(byte[]? raw,byte[]? pem,PublicPemPin? pin,Rejection why)
    {
        ValidationResult r=Validator.Authenticate4032(raw,pem,pin);
        Need(!r.Accepted && r.Reason==why,"unexpected-refusal-code");
        Need(!r.FullSchemaValidated && !r.MetadataPublished && !r.FirmwareApplicabilityValidated &&
             !r.SignatureAuthenticityValidated && r.SelectedBytes==0 && r.Representation==Representation.None,"refusal-no-export");
    }
    static int Main(string[] args)
    {
        try {
            Need(args.Length==2,"host-arguments");string directory=args[0];
            using JsonDocument doc=JsonDocument.Parse(File.ReadAllBytes(Path.Combine(directory,"manifest.json")));
            JsonElement root=doc.RootElement;
            Need(root.GetProperty("schema").GetString()=="synthetic-only-swu-authentication-fixtures-v1" &&
                 !root.GetProperty("actualPlaintextUsed").GetBoolean(),"synthetic-fixture-contract");
            foreach(JsonProperty row in root.GetProperty("assets").EnumerateObject()) {
                byte[] b=File.ReadAllBytes(Path.Combine(directory,row.Name));
                Need(b.Length==row.Value.GetProperty("bytes").GetInt32() && Hash(b)==row.Value.GetProperty("sha256").GetString(),"synthetic-asset-pin");
            }
            byte[] pem=File.ReadAllBytes(Path.Combine(directory,"synthetic-public.pem")),
                   wrong=File.ReadAllBytes(Path.Combine(directory,"synthetic-wrong-public.pem"));
            byte[] goodRaw=Array.Empty<byte>();PublicPemPin? goodPin=null;int accepted=0,rejected=0;
            foreach(JsonElement row in root.GetProperty("fixtures").EnumerateArray()) {
                string name=row.GetProperty("name").GetString()!;
                byte[] raw=File.ReadAllBytes(Path.Combine(directory,row.GetProperty("path").GetString()!));
                Need(raw.Length==4032 && Hash(raw)==row.GetProperty("sha256").GetString(),"fixture-pin");
                string which=row.GetProperty("anchor").GetString()!;
                PublicPemPin pin=Pin(root.GetProperty(which),Hex(row,"plaintextCrc32"));
                byte[] selectedPem=which=="primary"?pem:wrong;
                string before=Hash(raw),keyBefore=Hash(selectedPem);
                ValidationResult result=Validator.Authenticate4032(raw,selectedPem,pin);
                bool expected=row.GetProperty("accepted").GetBoolean();
                Need(result.Accepted==expected && result.Reason.ToString()==row.GetProperty("reason").GetString(),"fixture-result");
                Need(Hash(raw)==before && Hash(selectedPem)==keyBefore,"caller-input-unchanged");
                Need(!result.FullSchemaValidated && !result.MetadataPublished && !result.FirmwareApplicabilityValidated,"bounded-scope");
                if(expected) {
                    accepted++;
                    Need(result.SignatureAuthenticityValidated && result.FramingSubsetChecked &&
                         result.Representation.ToString()==row.GetProperty("representation").GetString() &&
                         result.SelectedBytes==row.GetProperty("selectedBytes").GetInt32() &&
                         result.PaddingBytes==row.GetProperty("paddingBytes").GetInt32(),"representation-no-byte-guess");
                    Need(result.RootCount>0 && result.PresentRoots==1,"bounded-root-counts");
                    if(name.StartsWith("known-leaf-",StringComparison.Ordinal))Need(result.CheckedLeaves==1,"known-leaf-layout");
                    else Need(result.CheckedLeaves==0,"opaque-body-no-schema-guess");
                    if(name=="raw-no-padding"){goodRaw=raw;goodPin=pin;}
                    Rejected(raw,selectedPem,pin with {PlaintextCrc32=Hex(row,"ouiOnlyCrc32")},Rejection.RepresentationCrcMismatch);
                } else {rejected++;Need(!result.SignatureAuthenticityValidated && result.SelectedBytes==0,"no-failed-plaintext-result");}
                if(name.StartsWith("pkcs7-",StringComparison.Ordinal)) {
                    byte[] broken=(byte[])raw.Clone();int n=row.GetProperty("paddingBytes").GetInt32();
                    // The selected stream remains untouched; destroy exactly the
                    // claimed padding form and keep the independently fixed CRC.
                    broken[broken.Length-n]^=0x40;
                    Rejected(broken,selectedPem,pin,Rejection.RepresentationCrcMismatch);
                }
                fixtures++;
            }
            Need(goodPin!=null,"valid-anchor-fixture");
            Rejected(null,pem,goodPin,Rejection.InputCount);
            foreach(int length in new[]{0,1,16,261,4031,4033,8192})Rejected(new byte[length],pem,goodPin,Rejection.InputCount);
            Rejected(goodRaw,pem,null,Rejection.Anchor);
            Rejected(goodRaw,null,goodPin,Rejection.PublicKeyPin);
            Rejected(goodRaw,wrong,goodPin,Rejection.PublicKeyPin);
            Rejected(goodRaw,pem,goodPin! with {Sha256="x"},Rejection.Anchor);
            Rejected(goodRaw,pem,goodPin! with {ByteCount=9000},Rejection.Anchor);
            Rejected(goodRaw,pem,goodPin! with {SignatureBytes=257},Rejection.Anchor);
            Rejected(goodRaw,pem,goodPin! with {RsaBits=4096,SignatureBytes=512},Rejection.PublicKeySize);
            Rejected(goodRaw,pem,goodPin! with {Crc32=goodPin!.Crc32^1},Rejection.PublicKeyPin);
            byte[] changedPem=(byte[])pem.Clone();changedPem[changedPem.Length-1]^=1;
            Rejected(goodRaw,changedPem,goodPin,Rejection.PublicKeyPin);
            byte[] padLooking16=File.ReadAllBytes(Path.Combine(directory,"raw-padding-looking-16.bin"));
            JsonElement raw16=default;
            foreach(JsonElement row in root.GetProperty("fixtures").EnumerateArray())
                if(row.GetProperty("name").GetString()=="raw-padding-looking-16")raw16=row;
            PublicPemPin raw16Pin=Pin(root.GetProperty("primary"),Hex(raw16,"plaintextCrc32"));
            // Exhaust every noncanonical padding-value byte, keeping independent
            // original CRC fixed. Every valid1..16 pattern and mismatched pattern
            // was separately covered by the independently signed fixtures.
            for(int tail=0;tail<=255;tail++) {
                if(tail>=1 && tail<=16)continue;
                byte[] changed=(byte[])padLooking16.Clone();changed[changed.Length-1]=(byte)tail;
                Rejected(changed,pem,raw16Pin,Rejection.RepresentationCrcMismatch);
            }
            byte[] privatePem=File.ReadAllBytes(Path.Combine(directory,"synthetic-only-private.pem"));
            PublicPemPin shape=goodPin! with {ByteCount=privatePem.Length,Sha256=Hash(privatePem),Crc32=Validator.Crc32(privatePem)};
            Rejected(goodRaw,privatePem,shape,Rejection.PublicKeyEncoding);
            byte[] doubled=new byte[pem.Length*2];pem.CopyTo(doubled,0);pem.CopyTo(doubled,pem.Length);
            shape=goodPin! with {ByteCount=doubled.Length,Sha256=Hash(doubled),Crc32=Validator.Crc32(doubled)};
            Rejected(goodRaw,doubled,shape,Rejection.PublicKeyEncoding);
            Need(Validator.Crc32(Encoding.ASCII.GetBytes("123456789"))==0xcbf43926 && Validator.Crc32(Array.Empty<byte>())==0,"independent-crc-kats");
            // Actual selected public file: parse and verify public anchors only.
            // No actual plaintext is present, authenticated, generated or read.
            byte[] actual=File.ReadAllBytes(args[1]);PublicPemPin master=PublicPemPin.Master;
            Need(actual.Length==master.ByteCount && Hash(actual)==master.Sha256 && Validator.Crc32(actual)==master.Crc32,"actual-public-key-pin");
            using RSA rsa=RSA.Create();rsa.ImportFromPem(Encoding.ASCII.GetString(actual));
            Need(rsa.KeySize==master.RsaBits && (rsa.KeySize+7)/8==master.SignatureBytes,"actual-public-key-parse-only");
            Console.WriteLine(JsonSerializer.Serialize(new {host_only=true,target_operations=0,actual_plaintext_used=false,
                actual_public_key_parse_only=true,synthetic_fixtures=fixtures,accepted_synthetic=accepted,rejected_synthetic=rejected,
                checks,full_schema_validated=false,metadata_published=false}));
            return 0;
        } catch {Console.WriteLine("HOST_AUTHENTICATION_TEST_FAILED no_content_logged=1");return 1;}
    }
}
