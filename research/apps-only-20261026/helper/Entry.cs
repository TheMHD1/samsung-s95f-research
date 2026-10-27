using System.Text.Json;
using Tizen.TV.Service.CoBA.Core;
using Tizen.TV.Service.CoBA.BPI;
using Tizen.TV.Service.CoBA.Core.Util;
namespace researcher.Home;
public static class Entry {
 public const string ClassID="d/owner.shortcut";
 const string Build="BUILD_ID=T-RSMFAKUC-0090-REL-202607141953";
 static readonly Dictionary<string,string> Apps=new(){["Spotify"]="rJeHak5zRg.Spotify",["Prime"]="org.tizen.primevideo",["Netflix"]="org.tizen.netflix-app",["Jellyfin"]="rTn6ClEurC.Jellyfin",["TVPlus"]="HEPsqFNie0.tvplusstandalone"};
 public static void Register(object manager){if(!File.ReadAllLines("/etc/tizen-release").Contains(Build))throw new InvalidOperationException("Unsupported TV build");((ComponentVersionManager)manager).Add(ClassID,new ComponentAgent((parent,id)=>new Shortcut(parent,id),1));}
 public static string[] GetTiles(){if(!File.ReadAllLines("/etc/tizen-release").Contains(Build))return new[]{"s/livetv@TVPLUS"};ComponentManager.GetInstance().AddComponent(ClassID,(parent,id)=>new Shortcut(parent,id),1);return Apps.Keys.Select(id=>ClassID+"@"+id).ToArray();}
 public static string[] PrepareNativeApps(){
  if(!File.ReadAllLines("/etc/tizen-release").Contains(Build))throw new InvalidOperationException("Unsupported TV build");
  var entries=JsonSerializer.Deserialize<Dictionary<string,string>>(File.ReadAllText("/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res/HabibiNativeApps.json"))!;
  var pm=PreviewManager.GetInstance();foreach(var item in entries)pm.Set(item.Key,item.Value,false);
  return new[]{"d/apps.tab.content@CategoryID_Content_DOWNLOADED"};
 }
 public static bool TryActivate(string id){if(id!="OWNER_TVPLUS")return false;try{if(!File.ReadAllLines("/etc/tizen-release").Contains(Build))throw new InvalidOperationException("Unsupported TV build");AppLauncher.LaunchApp("HEPsqFNie0.tvplusstandalone",null,false);}catch(Exception){Console.Error.WriteLine("Samsung TV Plus shortcut could not open");}return true;}
 public static void Activate(string id){if(!Apps.TryGetValue(id,out var app))throw new ArgumentException("Unknown shortcut");AppLauncher.LaunchApp(app,null,false);}
}
public sealed class Shortcut:Component {
 public Shortcut(Component parent,string id):base(parent,Entry.ClassID,id){Elements=new Element[]{new Tile(this,id)};CurrentElement=Elements[0];m_control=new ComponentControl(this,new ComponentCache());Visible=true;}
 public override void Run(int syncCount){Visible=true;base.Run(syncCount);Visible=true;UpdateItem();}
 public override void OnSelected(Element element){base.OnSelected(element);try{Entry.Activate(InstanceID);}catch(Exception){Console.Error.WriteLine("Home shortcut could not open: "+InstanceID);}}
}
public sealed class Tile:Element {
 readonly string id;
 public Tile(Entity parent,string id):base(parent,"shortcut"){this.id=id;Focusable=true;Update();}
 public override void Update(){string title=id switch{"Prime"=>"Prime Video","TVPlus"=>"Samsung TV Plus",_=>id};var icon="/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res/researcher-"+id.ToLowerInvariant()+".svg";UIJson=JsonSerializer.Serialize(new{title,subtitle=(string)null,focused_icon=icon,unfocused_icon=icon,type="Content",item_separator=false,default_focus=false,select_loading_time=20,select_loading_visible=true});}
}
