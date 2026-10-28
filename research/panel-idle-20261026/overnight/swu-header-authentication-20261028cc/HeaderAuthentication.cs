using System;
using System.Buffers.Binary;
using System.Security.Cryptography;
using System.Text;

namespace SwuHeaderAuthentication
{
    public enum Rejection
    {
        None, InputCount, Anchor, PublicKeyPin, PublicKeyEncoding, PublicKeySize,
        RepresentationCrcMismatch, RepresentationAmbiguous, PublicKeyCrc,
        SignatureLength, SignatureInvalid, CryptoFailure, Truncated, TreeMagic,
        RootCount, PresenceCanonical, DescriptorExtent, UnsupportedTag,
        MandatoryCanonical, LeafExtent, TrailingBytes
    }
    public enum Representation { None, Raw4032, CanonicalPkcs7 }

    // This immutable pin must be supplied from independently reviewed bytes,
    // never derived from untrusted decrypted fields. Public constructor supports
    // separately anchored synthetic fixtures; Master is the fixed actual pin.
    public sealed record PublicPemPin(int ByteCount, string Sha256, uint Crc32,
                                      int RsaBits, int SignatureBytes, uint PlaintextCrc32)
    {
        public static PublicPemPin Master { get; } = new PublicPemPin(426,
            "ebf12ab9d4ef069e1a6030b8c3b117894746637715270f7e3d37d3cd737f71a3",
            0x860be2ed,2048,256,0xcbcf1d91);
    }

    // Fixed status/counts only: no buffer, key, signature, descriptor body,
    // payload identifier or caller-controlled diagnostic text escapes this API.
    public sealed record ValidationResult(bool Accepted, Rejection Reason,
        Representation Representation, int SelectedBytes, int PaddingBytes,
        int RootCount, int PresentRoots, int CheckedLeaves)
    {
        public bool SignatureAuthenticityValidated => Accepted;
        public bool FramingSubsetChecked => Accepted;
        public bool FullSchemaValidated => false;
        public bool MetadataPublished => false;
        public bool FirmwareApplicabilityValidated => false;
    }

    public static class Validator
    {
        public const int RawBytes = 4032;
        private const int MaxPemBytes = 8192;
        private static readonly byte[] Magic = Encoding.ASCII.GetBytes("Tizen Software Upgrade Tree Binary Format ver. 1.9\0");

        public static uint Crc32(ReadOnlySpan<byte> data)
        {
            uint crc=0xffffffff;
            foreach(byte b in data) {
                crc^=b;
                for(int bit=0;bit<8;bit++) crc=(crc>>1)^((crc&1)!=0?0xedb88320u:0);
            }
            return crc^0xffffffff;
        }
        private static ValidationResult Refuse(Rejection reason) =>
            new ValidationResult(false,reason,Representation.None,0,0,0,0,0);
        private static bool HexPin(string? pin)
        {
            if(pin==null || pin.Length!=64)return false;
            foreach(char c in pin)if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))return false;
            return true;
        }
        private static bool Anchor(PublicPemPin? pin) => pin!=null && pin.ByteCount>=64 &&
            pin.ByteCount<=MaxPemBytes && HexPin(pin.Sha256) && pin.RsaBits>=2048 &&
            pin.RsaBits<=8192 && pin.RsaBits%8==0 && pin.SignatureBytes==pin.RsaBits/8 &&
            pin.SignatureBytes<=RawBytes-6-51-4;

        // Positive length only, as emitted by the traced addPadding. A zero,
        // >16 or mismatched tail is NOT permission to discard any bytes.
        private static int CanonicalPadding(ReadOnlySpan<byte> data)
        {
            if(data.Length<16 || data.Length%16!=0)return 0;
            int n=data[data.Length-1];if(n<1 || n>16)return 0;
            for(int i=data.Length-n;i<data.Length;i++)if(data[i]!=n)return 0;
            return n;
        }
        private static bool PublicPem(byte[] bytes,out string text)
        {
            text="";
            foreach(byte b in bytes)if(b!=9 && b!=10 && b!=13 && (b<32 || b>126))return false;
            text=Encoding.ASCII.GetString(bytes);
            if(!PemEncoding.TryFind(text,out PemFields fields))return false;
            string label=text[fields.Label];
            if(label!="PUBLIC KEY" && label!="RSA PUBLIC KEY")return false;
            int begin=fields.Location.Start.GetOffset(text.Length),end=fields.Location.End.GetOffset(text.Length);
            for(int i=0;i<begin;i++)if(!char.IsWhiteSpace(text[i]))return false;
            for(int i=end;i<text.Length;i++)if(!char.IsWhiteSpace(text[i]))return false;
            return true;
        }

        // No file/console/network/TEE/native-platform calls. Callers own and
        // must wipe their original private buffer; this method wipes snapshots.
        public static ValidationResult Authenticate4032(byte[]? raw,byte[]? publicPem,PublicPemPin? pin)
        {
            if(raw==null || raw.Length!=RawBytes)return Refuse(Rejection.InputCount);
            if(!Anchor(pin))return Refuse(Rejection.Anchor);
            if(publicPem==null || publicPem.Length!=pin!.ByteCount || publicPem.Length>MaxPemBytes)
                return Refuse(Rejection.PublicKeyPin);
            byte[] data=(byte[])raw.Clone(),pem=Array.Empty<byte>();
            try {
                pem=(byte[])publicPem.Clone();
                byte[] expected=Convert.FromHexString(pin.Sha256);
                byte[] observed=SHA256.HashData(pem);
                if(!CryptographicOperations.FixedTimeEquals(expected,observed) || Crc32(pem)!=pin.Crc32)
                    return Refuse(Rejection.PublicKeyPin);
                if(!PublicPem(pem,out string text))return Refuse(Rejection.PublicKeyEncoding);
                using RSA rsa=RSA.Create();
                try { rsa.ImportFromPem(text); }
                catch(ArgumentException) {return Refuse(Rejection.PublicKeyEncoding);}
                catch(CryptographicException) {return Refuse(Rejection.PublicKeyEncoding);}
                if(rsa.KeySize!=pin.RsaBits || (rsa.KeySize+7)/8!=pin.SignatureBytes)
                    return Refuse(Rejection.PublicKeySize);

                // Only two source-backed candidates exist: exact raw aggregate,
                // or removal of one canonical 1..16-byte PKCS7 tail. First
                // require exactly ONE whole-stream CRC match. No fallback after
                // a later RSA/framing failure and no tail-based guess.
                int padding=CanonicalPadding(data);
                bool rawFits=Crc32(data)==pin.PlaintextCrc32;
                bool paddedFits=padding>0 && Crc32(data.AsSpan(0,data.Length-padding))==pin.PlaintextCrc32;
                if(rawFits && paddedFits)return Refuse(Rejection.RepresentationAmbiguous);
                if(!rawFits && !paddedFits)return Refuse(Rejection.RepresentationCrcMismatch);
                int selected=rawFits?data.Length:data.Length-padding;
                Representation form=rawFits?Representation.Raw4032:Representation.CanonicalPkcs7;
                ReadOnlySpan<byte> plain=data.AsSpan(0,selected);
                if(plain.Length<6+pin.SignatureBytes+Magic.Length+4)return Refuse(Rejection.Truncated);
                if(BinaryPrimitives.ReadUInt32LittleEndian(plain)!=pin.Crc32)return Refuse(Rejection.PublicKeyCrc);
                if(BinaryPrimitives.ReadUInt16LittleEndian(plain.Slice(4,2))!=pin.SignatureBytes)
                    return Refuse(Rejection.SignatureLength);
                ReadOnlySpan<byte> signature=plain.Slice(6,pin.SignatureBytes);
                ReadOnlySpan<byte> signed=plain.Slice(6+pin.SignatureBytes);
                bool verified;
                try {verified=rsa.VerifyData(signed,signature,HashAlgorithmName.SHA512,RSASignaturePadding.Pkcs1);}
                catch(CryptographicException) {return Refuse(Rejection.CryptoFailure);}
                if(!verified)return Refuse(Rejection.SignatureInvalid);
                Rejection reason=Framing(signed,out int roots,out int present,out int leaves);
                if(reason!=Rejection.None)return Refuse(reason);
                return new ValidationResult(true,Rejection.None,form,selected,rawFits?0:padding,roots,present,leaves);
            } catch(CryptographicException) {
                return Refuse(Rejection.CryptoFailure);
            } finally {
                CryptographicOperations.ZeroMemory(data);
                CryptographicOperations.ZeroMemory(pem);
            }
        }

        private static bool Known(uint tag) => tag==1 || tag==2 || tag==7 || tag==10 || tag==11 ||
            tag==14 || tag==16 || tag==18 || tag==19 || tag==21 || tag==25 || tag==35 ||
            tag==53 || tag==55 || tag==56 || tag==57 || tag==58 || tag==59 || tag==60 || tag==61 || tag==62;
        private static Rejection Framing(ReadOnlySpan<byte> signed,out int roots,out int present,out int leaves)
        {
            roots=0;present=0;leaves=0;
            if(signed.Length<Magic.Length+4)return Rejection.Truncated;
            if(!signed.Slice(0,Magic.Length).SequenceEqual(Magic))return Rejection.TreeMagic;
            int at=Magic.Length;
            uint count=BinaryPrimitives.ReadUInt32LittleEndian(signed.Slice(at,4));at+=4;
            if(count>(uint)(signed.Length-at))return Rejection.RootCount;
            roots=(int)count;
            for(int i=0;i<roots;i++) {
                if(at>=signed.Length)return Rejection.Truncated;
                byte flag=signed[at++];
                if(flag>1)return Rejection.PresenceCanonical;
                if(flag==0)continue;
                present++;
                if(signed.Length-at<4)return Rejection.Truncated;
                uint length=BinaryPrimitives.ReadUInt32LittleEndian(signed.Slice(at,4));at+=4;
                if(length<5 || length>(uint)(signed.Length-at))return Rejection.DescriptorExtent;
                ReadOnlySpan<byte> body=signed.Slice(at,(int)length);at+=(int)length;
                uint tag=BinaryPrimitives.ReadUInt32LittleEndian(body);
                if(!Known(tag))return Rejection.UnsupportedTag;
                if(body[4]>1)return Rejection.MandatoryCanonical;
                if(tag==18) {
                    if(body.Length!=9)return Rejection.LeafExtent;
                    leaves++;
                } else if(tag==16) {
                    if(body.Length<11)return Rejection.LeafExtent;
                    int signature=BinaryPrimitives.ReadUInt16LittleEndian(body.Slice(9,2));
                    if(signature!=body.Length-11)return Rejection.LeafExtent;
                    leaves++;
                }
                // Other known bodies remain opaque. No nested item/group,
                // payload names, offsets, key fields or applicability guessed.
            }
            return at==signed.Length?Rejection.None:Rejection.TrailingBytes;
        }
    }
}
