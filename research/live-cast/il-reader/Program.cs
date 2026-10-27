using System.Reflection;
using System.Reflection.Emit;
using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;

using var stream=File.OpenRead(args[0]);
using var pe=new PEReader(stream);
var md=pe.GetMetadataReader();
string Name(EntityHandle handle) {
    try {
        return handle.Kind switch {
            HandleKind.MethodDefinition => md.GetString(md.GetMethodDefinition((MethodDefinitionHandle)handle).Name),
            HandleKind.MemberReference => Name(md.GetMemberReference((MemberReferenceHandle)handle).Parent)+"::"+md.GetString(md.GetMemberReference((MemberReferenceHandle)handle).Name),
            HandleKind.TypeReference => md.GetString(md.GetTypeReference((TypeReferenceHandle)handle).Namespace)+"."+md.GetString(md.GetTypeReference((TypeReferenceHandle)handle).Name),
            HandleKind.TypeDefinition => md.GetString(md.GetTypeDefinition((TypeDefinitionHandle)handle).Namespace)+"."+md.GetString(md.GetTypeDefinition((TypeDefinitionHandle)handle).Name),
            HandleKind.MethodSpecification => Name(md.GetMethodSpecification((MethodSpecificationHandle)handle).Method),
            _ => handle.Kind+":"+MetadataTokens.GetToken(handle).ToString("x8")
        };
    } catch { return "?"; }
}
var codes=typeof(OpCodes).GetFields(BindingFlags.Public|BindingFlags.Static).Where(f=>f.FieldType==typeof(OpCode)).Select(f=>(OpCode)f.GetValue(null)!).ToDictionary(c=>unchecked((ushort)c.Value));
foreach(var th in md.TypeDefinitions) {
    var t=md.GetTypeDefinition(th);
    foreach(var mh in t.GetMethods()) {
        var m=md.GetMethodDefinition(mh);
        string full=Name(th)+"::"+md.GetString(m.Name);
        if(args.Length>1 && !full.Contains(args[1],StringComparison.OrdinalIgnoreCase)) continue;
        Console.WriteLine("METHOD "+MetadataTokens.GetToken(mh).ToString("x8")+" "+full);
        if(m.RelativeVirtualAddress==0) continue;
        var bytes=pe.GetMethodBody(m.RelativeVirtualAddress).GetILBytes()!;
        for(int i=0;i<bytes.Length;) {
            int at=i;
            ushort value=bytes[i++]; if(value==0xfe) value=(ushort)(0xfe00|bytes[i++]);
            var op=codes[value];
            int size=op.OperandType switch {
                OperandType.InlineNone=>0,
                OperandType.ShortInlineI or OperandType.ShortInlineVar or OperandType.ShortInlineBrTarget=>1,
                OperandType.InlineVar=>2,
                OperandType.InlineI8 or OperandType.InlineR=>8,
                OperandType.InlineSwitch=>4+4*BitConverter.ToInt32(bytes,i),
                _=>4
            };
            string arg=size==0?"":Convert.ToHexString(bytes.AsSpan(i,size));
            if(op.OperandType==OperandType.InlineString) arg=System.Text.Json.JsonSerializer.Serialize(md.GetUserString(MetadataTokens.UserStringHandle(BitConverter.ToInt32(bytes,i))));
            else if(op.OperandType is OperandType.InlineMethod or OperandType.InlineField or OperandType.InlineType or OperandType.InlineTok) arg=Name(MetadataTokens.EntityHandle(BitConverter.ToInt32(bytes,i)));
            Console.WriteLine($" {at:x4}: {op.Name} {arg}"); i+=size;
        }
    }
}
