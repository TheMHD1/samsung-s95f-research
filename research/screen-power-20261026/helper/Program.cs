using System.Reflection;
using System.Runtime.Loader;
using System.Runtime.InteropServices;
using System.Text.Json;
class Program {
 [DllImport("libc")]static extern uint getuid();
 static readonly Dictionary<string,string> Targets=new(){["brightness-optimization"]="0",["auto-screen-dim"]="0",["auto-power-off"]="0",["sleeptimer"]="0",["offtimer1-setup"]="SID_OFF",["energy-saving-solution"]="0",["motion-lighting"]="0"};
 static Type Api=null!;
 static object Call(string name,params object[] args)=>Api.GetMethods().Single(m=>m.Name==name&&m.GetParameters().Length==args.Length).Invoke(null,args)!;
 record Item(string Id,bool Read,bool Visible,bool Enabled,string Value,string Display,string[] Choices);
 static Item Query(string id){
  object[] value={id,null!,null!};bool read=(bool)Call("GetItemValue",value);
  object[] visible={id,false};bool vr=(bool)Call("GetItemVisible",visible);
  object[] enabled={id,false};bool er=(bool)Call("GetItemEnable",enabled);
  object[] list={id,null!};bool lr=(bool)Call("GetItemDataList",list);
  return new(id,read,vr&&(bool)visible[1],er&&(bool)enabled[1],value[2] as string??"",value[1] as string??"",lr&&list[1] is List<string> l?l.ToArray():Array.Empty<string>());
 }
 static int Main(string[] args){try{
  if(getuid()!=901||IntPtr.Size!=4||!File.ReadAllLines("/etc/tizen-release").Contains("BUILD_ID=T-RSMFAKUC-0090-REL-202607141953"))throw new Exception("SDK/exact-build guard failed");
  AssemblyLoadContext.Default.Resolving+=(context,name)=>{foreach(var dir in new[]{"/usr/share/dotnet.tizen/framework/","/usr/share/dotnet.tizen/tvappapi/"}){var p=dir+name.Name+".dll";if(File.Exists(p))return context.LoadFromAssemblyPath(p);}return null;};
  if(args.Length==1&&(args[0]=="display"||args[0]=="wake-display")){
   var type=Assembly.LoadFrom("/usr/share/dotnet.tizen/framework/Tizen.System.dll").GetType("Tizen.System.Display",true)!;
   var property=type.GetProperty("State")!;var screenBefore=property.GetValue(null)!.ToString();bool requested=false;
   if(args[0]=="wake-display"&&screenBefore!="Normal"){property.SetValue(null,Enum.Parse(property.PropertyType,"Normal"));requested=true;}
   Console.WriteLine(JsonSerializer.Serialize(new {before=screenBefore,normalRequested=requested,after=property.GetValue(null)!.ToString()}));return 0;
  }
  Api=Assembly.LoadFrom("/usr/share/dotnet.tizen/framework/Tizen.TV.Service.Settings.dll").GetType("Tizen.TV.Service.Settings.Settings",true)!;
  if(args.Length==1&&args[0]=="query"){Console.WriteLine(JsonSerializer.Serialize(Targets.Keys.Select(Query)));return 0;}
  if(args.Length!=1||args[0]!="apply")throw new Exception("Use query or apply");
  const string backup="/home/researcher/share/tmp/sdk_tools/researcher-live-cast/power-settings-before.json";
  if(File.Exists(backup))throw new Exception("Backup already exists");
  var before=Targets.Keys.Select(Query).ToArray();File.WriteAllText(backup,JsonSerializer.Serialize(before));
  var changed=new List<Item>();
  try{foreach(var item in before){
   if(!item.Read||!item.Visible||!item.Enabled||item.Value==Targets[item.Id])continue;
   if(!item.Choices.Any(c=>c.Split(',',2)[0]==Targets[item.Id]))throw new Exception("Off option not confirmed for "+item.Id);
   changed.Add(item);
   if(!(bool)Call("SetItemValue",item.Id,Targets[item.Id])||Query(item.Id).Value!=Targets[item.Id])throw new Exception("Write/readback failed: "+item.Id);
  }}catch{foreach(var item in changed.AsEnumerable().Reverse())Call("SetItemValue",item.Id,item.Value);throw;}
  Console.WriteLine(JsonSerializer.Serialize(new {before,changed=changed.Select(x=>x.Id),after=Targets.Keys.Select(Query)}));return 0;
 }catch(Exception e){Console.Error.WriteLine(e.ToString());return 1;}}
}
