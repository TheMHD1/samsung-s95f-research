using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;

var input=File.ReadAllBytes(args[0]);
var original=Convert.ToHexString(SHA256.HashData(input)).ToLowerInvariant();
if(original!="b05655edcc7de8557e306cb980d4098ae2a1f79db69b0b215b2dfafc7b7fe9f1") throw new Exception("Exact original provider hash mismatch");
using var stream=new MemoryStream(input);
using var pe=new PEReader(stream);
var md=pe.GetMetadataReader();
var method=md.GetMethodDefinition(MetadataTokens.MethodDefinitionHandle(8));
var type=md.GetTypeDefinition(method.GetDeclaringType());
if(md.GetString(method.Name)!="get_UGSupportType" || md.GetString(type.Namespace)!="ContentsBrowser" || md.GetString(type.Name)!="CBConfig") throw new Exception("Method guard mismatch");
var body=pe.GetMethodBody(method.RelativeVirtualAddress);
var il=body.GetILBytes()!;
if(il.Length!=0x89 || il[0]!=0x7e || il[^1]!=0x2a || body.ExceptionRegions.Length!=0) throw new Exception("Body guard mismatch");
var section=pe.PEHeaders.SectionHeaders.Single(s=>method.RelativeVirtualAddress>=s.VirtualAddress && method.RelativeVirtualAddress<s.VirtualAddress+s.VirtualSize);
int offset=section.PointerToRawData+method.RelativeVirtualAddress-section.VirtualAddress;
int header=(input[offset]&3)==2?1:(BitConverter.ToUInt16(input,offset)>>12)*4;
var output=(byte[])input.Clone();
Array.Clear(output,offset+header,il.Length);
output[offset+header]=0x19; // ldc.i4.3: provider's existing UNSUPPORT mode
output[offset+header+1]=0x2a; // ret
File.WriteAllBytes(args[1],output);
Console.WriteLine("ContentsBrowser.CBConfig.UGSupportType now returns its existing UNSUPPORT enum (3); remaining methods and metadata preserved.");
Console.WriteLine(Convert.ToHexString(SHA256.HashData(output)).ToLowerInvariant());
