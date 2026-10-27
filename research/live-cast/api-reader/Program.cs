using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;
using System.Collections.Immutable;
using var f=File.OpenRead(args[0]); using var pe=new PEReader(f); var md=pe.GetMetadataReader(); var p=new Names();
foreach(var h in md.TypeDefinitions) {
 var t=md.GetTypeDefinition(h); var name=p.GetTypeFromDefinition(md,h,0);
 if(args.Length>1&&!name.Contains(args[1]))continue;
 Console.WriteLine($"TYPE {t.Attributes} {name} : {p.Handle(md,t.BaseType)}");
 foreach(var x in t.GetInterfaceImplementations())Console.WriteLine(" INTERFACE "+p.Handle(md,md.GetInterfaceImplementation(x).Interface));
 foreach(var x in t.GetFields()){var a=md.GetFieldDefinition(x);Console.WriteLine($" FIELD {MetadataTokens.GetToken(x):x8} {a.Attributes} {a.DecodeSignature(p,null)} {md.GetString(a.Name)}");}
 foreach(var x in t.GetMethods()){var a=md.GetMethodDefinition(x);var s=a.DecodeSignature(p,null);Console.WriteLine($" METHOD {MetadataTokens.GetToken(x):x8} {a.Attributes} {s.ReturnType} {md.GetString(a.Name)}({string.Join(",",s.ParameterTypes)})");}
}
class Names:ISignatureTypeProvider<string,object>{
 public string Handle(MetadataReader r,EntityHandle h)=>h.IsNil?"":h.Kind switch{HandleKind.TypeDefinition=>GetTypeFromDefinition(r,(TypeDefinitionHandle)h,0),HandleKind.TypeReference=>GetTypeFromReference(r,(TypeReferenceHandle)h,0),HandleKind.TypeSpecification=>GetTypeFromSpecification(r,null,(TypeSpecificationHandle)h,0),_=>h.Kind.ToString()};
 public string GetTypeFromDefinition(MetadataReader r,TypeDefinitionHandle h,byte k){var t=r.GetTypeDefinition(h);return r.GetString(t.Namespace)+"."+r.GetString(t.Name);}
 public string GetTypeFromReference(MetadataReader r,TypeReferenceHandle h,byte k){var t=r.GetTypeReference(h);return r.GetString(t.Namespace)+"."+r.GetString(t.Name);}
 public string GetTypeFromSpecification(MetadataReader r,object c,TypeSpecificationHandle h,byte k)=>r.GetTypeSpecification(h).DecodeSignature(this,c);
 public string GetArrayType(string e,ArrayShape s)=>e+"[,]";
 public string GetByReferenceType(string e)=>e+"&";
 public string GetFunctionPointerType(MethodSignature<string>s)=>"fn";
 public string GetGenericInstantiation(string e,ImmutableArray<string>a)=>e+"<"+string.Join(",",a)+">";
 public string GetGenericMethodParameter(object c,int i)=>"!!"+i;
 public string GetGenericTypeParameter(object c,int i)=>"!"+i;
 public string GetModifiedType(string m,string e,bool r)=>e;
 public string GetPinnedType(string e)=>e;
 public string GetPointerType(string e)=>e+"*";
 public string GetPrimitiveType(PrimitiveTypeCode c)=>c.ToString();
 public string GetSZArrayType(string e)=>e+"[]";
}
