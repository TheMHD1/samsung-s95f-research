using Mono.Cecil;
using Mono.Cecil.Cil;
using System.Reflection;
using System.Security.Cryptography;
string Sha(string p)=>Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(p))).ToLowerInvariant();
if(Sha(args[0])!="3775f9034395384399fb312c47d937497aa145e8618bbcfdac3eeb48c566d10d")throw new Exception("Unexpected original Apps assembly");
var resolver=new DefaultAssemblyResolver();resolver.AddSearchDirectory(Path.GetFullPath(Path.Combine(Path.GetDirectoryName(args[0])!,"../live-cast/framework")));resolver.AddSearchDirectory(Path.GetDirectoryName(typeof(object).Assembly.Location)!);
using var a=AssemblyDefinition.ReadAssembly(args[0],new ReaderParameters{AssemblyResolver=resolver});var mod=a.MainModule;
MethodDefinition Method(string type,string method)=>mod.Types.Single(t=>t.Name==type).Methods.Single(m=>m.Name==method);
void ArrayResult(MethodDefinition m,string[] items){m.Body=new Mono.Cecil.Cil.MethodBody(m);var il=m.Body.GetILProcessor();il.Emit(OpCodes.Ldarg_1);il.Emit(OpCodes.Ldc_I4,items.Length);il.Emit(OpCodes.Newarr,mod.TypeSystem.String);for(int i=0;i<items.Length;i++){il.Emit(OpCodes.Dup);il.Emit(OpCodes.Ldc_I4,i);il.Emit(OpCodes.Ldstr,items[i]);il.Emit(OpCodes.Stelem_Ref);}il.Emit(OpCodes.Stind_Ref);il.Emit(OpCodes.Ldc_I4_1);il.Emit(OpCodes.Ret);}
void Reflect(ILProcessor il,Instruction before,string method,MethodReference idGetter){
 var code=new List<Instruction>{il.Create(OpCodes.Ldstr,"/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res/HabibiHomeShortcuts.dll"),il.Create(OpCodes.Call,mod.ImportReference(typeof(Assembly).GetMethod("LoadFrom",new[]{typeof(string)})!)),il.Create(OpCodes.Ldstr,"researcher.Home.Entry"),il.Create(OpCodes.Callvirt,mod.ImportReference(typeof(Assembly).GetMethod("GetType",new[]{typeof(string)})!)),il.Create(OpCodes.Ldstr,method),il.Create(OpCodes.Callvirt,mod.ImportReference(typeof(Type).GetMethod("GetMethod",new[]{typeof(string)})!)),il.Create(OpCodes.Ldnull),il.Create(OpCodes.Ldc_I4,idGetter==null?0:1),il.Create(OpCodes.Newarr,mod.TypeSystem.Object)};
 if(idGetter!=null)code.AddRange(new[]{il.Create(OpCodes.Dup),il.Create(OpCodes.Ldc_I4_0),il.Create(OpCodes.Ldarg_0),il.Create(OpCodes.Call,idGetter),il.Create(OpCodes.Stelem_Ref)});
 code.Add(il.Create(OpCodes.Callvirt,mod.ImportReference(typeof(MethodBase).GetMethod("Invoke",new[]{typeof(object),typeof(object[])})!)));
 foreach(var i in code){if(before==null)il.Append(i);else il.InsertBefore(before,i);}
}
var cache=Method("CompAppsTabCache","GetItems");cache.Body=new Mono.Cecil.Cil.MethodBody(cache);var cil=cache.Body.GetILProcessor();cil.Emit(OpCodes.Ldarg_1);Reflect(cil,null,"PrepareNativeApps",null);cil.Emit(OpCodes.Castclass,new ArrayType(mod.TypeSystem.String));cil.Emit(OpCodes.Stind_Ref);cil.Emit(OpCodes.Ldc_I4_1);cil.Emit(OpCodes.Ret);
ArrayResult(Method("CompATCategoryList","GetItems"),new[]{"d/apps.tab.content.layer@DOWNLOADED-0"});
ArrayResult(Method("CompATCategoryLayerList","GetItems"),new[]{"d/apps.tab.content.layer.tile@DOWNLOADED-0-3201606009684","d/apps.tab.content.layer.tile@DOWNLOADED-0-3201910019365","d/apps.tab.content.layer.tile@DOWNLOADED-0-3201907018807","d/apps.tab.content.layer.tile@DOWNLOADED-0-3202007021208","d/apps.tab.content.layer.tile@OWNER_TVPLUS"});
var getter=(MethodReference)Method("CompATCategoryTile","Run").Body.Instructions.First(i=>i.OpCode==OpCodes.Call&&i.Operand is MethodReference r&&r.Name=="get_InstanceID").Operand;
var selected=Method("CompATCategoryTile","OnSelected");var first=selected.Body.Instructions[0];var sil=selected.Body.GetILProcessor();Reflect(sil,first,"TryActivate",getter);sil.InsertBefore(first,sil.Create(OpCodes.Unbox_Any,mod.TypeSystem.Boolean));sil.InsertBefore(first,sil.Create(OpCodes.Brfalse,first));sil.InsertBefore(first,sil.Create(OpCodes.Ret));
a.Write(args[1]);Console.WriteLine(Sha(args[1]));
