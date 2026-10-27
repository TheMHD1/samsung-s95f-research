using Mono.Cecil;
using Mono.Cecil.Cil;
using System.Reflection;
using System.Security.Cryptography;
string Sha(string path)=>Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
bool terra=args[0].Contains("Terra");
if(Sha(args[0])!=(terra?"b085608b9da114f46b4cf162d9faf73f552fb5fe27d74cb37f8b6edc3ddf9c4f":"a459badb5665b6c1b60da459f4676cff0da1d231e63381fe83695331a4a4cade"))throw new Exception("Current Home patch hash mismatch");
var resolver=new DefaultAssemblyResolver();
resolver.AddSearchDirectory(Path.GetFullPath(Path.Combine(Path.GetDirectoryName(args[0])!,"../framework")));
resolver.AddSearchDirectory(Path.GetDirectoryName(typeof(object).Assembly.Location)!);
var asm=AssemblyDefinition.ReadAssembly(args[0],new ReaderParameters{AssemblyResolver=resolver});var mod=asm.MainModule;
void ReflectionCall(ILProcessor il,Instruction before,string method,bool withManager){
 var instructions=new List<Instruction>{il.Create(OpCodes.Ldstr,"/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res/HabibiHomeShortcuts.dll"),il.Create(OpCodes.Call,mod.ImportReference(typeof(Assembly).GetMethod("LoadFrom",new[]{typeof(string)})!)),il.Create(OpCodes.Ldstr,"researcher.Home.Entry"),il.Create(OpCodes.Callvirt,mod.ImportReference(typeof(Assembly).GetMethod("GetType",new[]{typeof(string)})!)),il.Create(OpCodes.Ldstr,method),il.Create(OpCodes.Callvirt,mod.ImportReference(typeof(Type).GetMethod("GetMethod",new[]{typeof(string)})!)),il.Create(OpCodes.Ldnull),il.Create(OpCodes.Ldc_I4,withManager?1:0),il.Create(OpCodes.Newarr,mod.TypeSystem.Object)};
 if(withManager) instructions.AddRange(new[]{il.Create(OpCodes.Dup),il.Create(OpCodes.Ldc_I4_0),il.Create(OpCodes.Ldarg_1),il.Create(OpCodes.Ldind_Ref),il.Create(OpCodes.Stelem_Ref)});
 instructions.Add(il.Create(OpCodes.Callvirt,mod.ImportReference(typeof(MethodBase).GetMethod("Invoke",new[]{typeof(object),typeof(object[])})!)));
 foreach(var x in instructions){if(before==null)il.Append(x);else il.InsertBefore(before,x);}
}
if(terra){
 var m=mod.Types.Single(t=>t.Name=="CompUGTabCache").Methods.Single(m=>m.Name=="GetItems");
 m.Body=new Mono.Cecil.Cil.MethodBody(m);var il=m.Body.GetILProcessor();
 il.Emit(OpCodes.Ldarg_1);il.Emit(OpCodes.Ldc_I4_1);il.Emit(OpCodes.Newarr,mod.TypeSystem.String);il.Emit(OpCodes.Dup);il.Emit(OpCodes.Ldc_I4_0);il.Emit(OpCodes.Ldstr,"d/launcher");il.Emit(OpCodes.Stelem_Ref);il.Emit(OpCodes.Stind_Ref);il.Emit(OpCodes.Ldc_I4_1);il.Emit(OpCodes.Ret);
}else{
 var factory=mod.Types.Single(t=>t.Name=="Factory").Methods.Single(m=>m.Name=="GetComponents");
 var il=factory.Body.GetILProcessor();var first=factory.Body.Instructions[0];ReflectionCall(il,first,"Register",true);il.InsertBefore(first,il.Create(OpCodes.Pop));
 var m=mod.Types.Single(t=>t.Name=="CompLauncherLayerCache").Methods.Single(m=>m.Name=="GetItems");
 m.Body=new Mono.Cecil.Cil.MethodBody(m);il=m.Body.GetILProcessor();il.Emit(OpCodes.Ldarg_1);ReflectionCall(il,null,"GetTiles",false);il.Emit(OpCodes.Castclass,new ArrayType(mod.TypeSystem.String));il.Emit(OpCodes.Stind_Ref);il.Emit(OpCodes.Ldc_I4_1);il.Emit(OpCodes.Ret);
}
asm.Write(args[1]);Console.WriteLine(Sha(args[1]));
