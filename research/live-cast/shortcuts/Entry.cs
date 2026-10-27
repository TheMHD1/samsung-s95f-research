using System.Reflection;
using System.Text.Json;
using Tizen.TV.Service.CoBA.Core;
using Tizen.TV.Service.CoBA.BPI;
using Tizen.TV.Service.CoBA.Core.Util;

namespace researcher.Home;
public static class Entry
{
    public const string ClassID="d/owner.shortcut";
    const string Build="BUILD_ID=T-RSMFAKUC-0090-REL-202607141953";
    public static void Register(object manager)
    {
        if(!File.ReadAllLines("/etc/tizen-release").Contains(Build)) throw new InvalidOperationException("Unsupported TV build");
        ((ComponentVersionManager)manager).Add(ClassID,new ComponentAgent((parent,id)=>new Shortcut(parent,id),1));
    }
    public static string[] GetTiles(){
        if(!File.ReadAllLines("/etc/tizen-release").Contains(Build)) return new[]{"s/livetv@TVPLUS"};
        ComponentManager.GetInstance().AddComponent(ClassID,(parent,id)=>new Shortcut(parent,id),1);
        return new[]{"s/livetv@TVPLUS",ClassID+"@Netflix",ClassID+"@Prime",ClassID+"@HDMI1",ClassID+"@HDMI2",ClassID+"@HDMI3",ClassID+"@HDMI4",ClassID+"@Cast",ClassID+"@AirPlay",ClassID+"@Settings"};
    }
    public static void Activate(string id)
    {
        if(id.StartsWith("HDMI") && id.Length==5 && id[4]>='1' && id[4]<='4') {
            // Use the same native source-list API used by Samsung's source tiles.
            var assembly=Assembly.LoadFrom("/usr/share/dotnet.tizen/framework/Tizen.TV.Service.SourceList.dll");
            var type=assembly.GetType("Tizen.TV.Service.SourceList.SourceList",true)!;
            var source=(int)Enum.Parse(typeof(Tizen.TV.Service.CoBA.Core.Manager.SourceType),id);
            type.GetMethod("ChangeSource",new[]{typeof(int)})!.Invoke(null,new object[]{source});
            AppLauncher.LaunchApp("org.tizen.tv-viewer",null,false);
        } else {
            var app=id switch {"Cast"=>"ByJlgt0XeD.CastSettingsApp","AirPlay"=>"com.samsung.tv.airplay-app-2","Settings"=>"org.tizen.menu","Netflix"=>"org.tizen.netflix-app","Prime"=>"org.tizen.primevideo",_=>throw new ArgumentException("Unknown shortcut")};
            AppLauncher.LaunchApp(app,null,false);
        }
    }
}
public sealed class Shortcut:Component
{
    public Shortcut(Component parent,string id):base(parent,Entry.ClassID,id)
    {
        Elements=new Element[]{new Tile(this,id)};
        CurrentElement=Elements[0];
        m_control=new ComponentControl(this,new ComponentCache());
        Visible=true;
    }
    public override void Run(int syncCount){Visible=true;base.Run(syncCount);Visible=true;UpdateItem();}
    public override void OnSelected(Element element)
    {
        base.OnSelected(element);
        try {Entry.Activate(InstanceID);}
        catch(Exception) {Console.Error.WriteLine("Home shortcut could not open: "+InstanceID);}
    }
}
public sealed class Tile:Element
{
    readonly string id;
    public Tile(Entity parent,string id):base(parent,"shortcut"){this.id=id;Focusable=true;Update();}
    public override void Update()
    {
        string title=id switch {"Cast"=>"Google Cast","AirPlay"=>"Apple AirPlay","Settings"=>"Settings","Netflix"=>"Netflix","Prime"=>"Prime Video",_=>id.Insert(4," ")};
        var icon="/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res/researcher-"+(id.StartsWith("HDMI")?"hdmi":id=="Settings"?"settings":id=="Netflix"?"netflix":id=="Prime"?"prime":"cast")+".svg";
        UIJson=JsonSerializer.Serialize(new {title,subtitle=(string)null,focused_icon=icon,unfocused_icon=icon,type="Content",item_separator=false,default_focus=false,select_loading_time=20,select_loading_visible=true});
    }
}
