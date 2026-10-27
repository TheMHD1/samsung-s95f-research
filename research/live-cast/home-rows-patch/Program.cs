using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;

var input=File.ReadAllBytes(args[0]);
var hash=Convert.ToHexString(SHA256.HashData(input)).ToLowerInvariant();
bool terra=hash=="b05655edcc7de8557e306cb980d4098ae2a1f79db69b0b215b2dfafc7b7fe9f1";
if(!terra && hash!="ec4541301a818efd308461c900efde0524f2243226c2db951b1f63674fcff35f") throw new Exception("Exact original hash mismatch");
using var stream=new MemoryStream(input);
using var pe=new PEReader(stream);
var md=pe.GetMetadataReader();
var method=md.GetMethodDefinition(MetadataTokens.MethodDefinitionHandle(terra?0x62e:0xf9));
var type=md.GetTypeDefinition(method.GetDeclaringType());
if(md.GetString(method.Name)!="GetItems" || md.GetString(type.Name)!=(terra?"CompUGTabCache":"CompMediaCategoryCache")) throw new Exception("Method guard mismatch");
var body=pe.GetMethodBody(method.RelativeVirtualAddress);
var il=body.GetILBytes()!;
var section=pe.PEHeaders.SectionHeaders.Single(s=>method.RelativeVirtualAddress>=s.VirtualAddress && method.RelativeVirtualAddress<s.VirtualAddress+s.VirtualSize);
int offset=section.PointerToRawData+method.RelativeVirtualAddress-section.VirtualAddress;
int header=(input[offset]&3)==2?1:(BitConverter.ToUInt16(input,offset)>>12)*4;
int code=offset+header;
var output=(byte[])input.Clone();
if(terra) {
    if(il.Length!=0x3c6 || il[0x102]!=0x03 || il[0x103]!=0x18 || il[0x104]!=0x8d || il[0x112]!=0xa2 || il[0x11b]!=0xa2 || body.ExceptionRegions.Any(e=>e.TryOffset<0x66 || e.HandlerOffset<0x66)) throw new Exception("Native fallback guard mismatch");
    if(md.GetUserString(MetadataTokens.UserStringHandle(BitConverter.ToInt32(il,0x10e)))!="d/recent.row@OnNow" || md.GetUserString(MetadataTokens.UserStringHandle(BitConverter.ToInt32(il,0x117)))!="d/launcher") throw new Exception("Fallback rows mismatch");
    // Reuse Samsung's own two-row fallback. Keep the entire provider,
    // tabs, launcher, application registration, and exception table.
    Array.Clear(output,code,0x66);
    Array.Copy(il,0x102,output,code,0x1a);
    output[code+0x1a]=0x17; output[code+0x1b]=0x2a;
} else {
    if(il[0x82]!=0x06 || il[0x83]!=0x72 || il[0x88]!=0x6f || il[0x8d]!=0 || md.GetUserString(MetadataTokens.UserStringHandle(BitConverter.ToInt32(il,0x84)))!="d/topbanner") throw new Exception("Banner guard mismatch");
    // Remove only the top-banner insertion, preserving the tabs insertion.
    Array.Clear(output,code+0x82,12);
}
File.WriteAllBytes(args[1],output);
Console.WriteLine(terra?"UG tab children: native Recent/OnNow row and launcher only":"Media category: omit top banner, keep native tabs");
Console.WriteLine(Convert.ToHexString(SHA256.HashData(output)).ToLowerInvariant());
