from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;B=P.parent
parent=B/'firmware-rtp-producer-20261028df/capture/Program.cs'; raw=parent.read_bytes();assert hashlib.sha256(raw).hexdigest()=='bdfb71a425a66ce2cea5f56d14dad79812e8114f5eb65f005e1b430d773d94fd'
text=raw.decode(); real=text[text.index('    static byte[] ReadCachedDescriptors(Stream stream)'):text.index('    sealed class FakeClock')]
real=real.replace('public static bool AbiReady => IntPtr.Size == 4', 'public static bool AbiReady => RuntimeInformation.ProcessArchitecture == Architecture.Arm && IntPtr.Size == 4')
real=real.replace('device >= 1 && device <= 127', 'device >= 1 && device <= 127 && device == ExpectedDevice')
real=real.replace('        public NativeResult Open(Identity id)', '        public void Revalidate(Identity id) { Need(Preflight() == id, "USB instance changed"); }\n        public NativeResult Open(Identity id)')
real=real.replace('public Identity Preflight()\n        {', 'public Identity Preflight()\n        {\n            Need(getuid() == 0 && geteuid() == 0, "root UID/EUID required");')
real=real.replace('        const uint ClaimRequest', '        [DllImport("libc.so.6")] static extern uint getuid();\n        [DllImport("libc.so.6")] static extern uint geteuid();\n        const uint ClaimRequest')
real=real.replace('if (input) Need(data.Length == 256 && IsInputLength(length), "fixed input only");\n            else Need(length == 12 && data.Length == 12 && FindHeader(data) != null, "fixed header only");','if (input) Need(data.Length == length && (length == 64 || length == 256 || length == 68 || length == 16), "fixed input length");\n            else Need((length == 12 && AllowedHeader(data)) || (length == 2 && data.Length == 2 && (Half(data,0) == 40 || Half(data,0) == 200)), "fixed OUT only");')
q=B/'autonomous-fault-harness-20261028dh/menu-onset-01/controller-capture';r=(q/'retained-00-trigger_baseline-cycle001-00-R.bin').read_bytes()
prefix='''using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;
using System.Threading;
internal static class Program
{
    const int TimeoutMs=2000;
    static int ExpectedDevice;
    const string ExpectedBoot="00000000-0000-4000-8000-000000000000";
    const string UsbRoot="/sys/bus/usb/devices/7-1";
    const string DeviceHex="12010002ef020140e8040120500201020301";
    const string AllDescriptorsHex=DeviceHex+"090262000301048032080b00020202010a09040000010202010a052400100105240100010424020205240600010705830308001009040100020a00000a07050102400010070581024000000904020002ff0000000705820200020007050202000200";
    readonly record struct Identity(int Bus,int Device) { public string Node=>$"/dev/bus/usb/{Bus:D3}/{Device:D3}"; }
    readonly record struct NativeResult(int Value,int Errno);
    sealed record Spec(string Name,uint Address,int Length);
    static readonly Spec Callback=new("Callback",0x45000580,64), R=new("R",0x47012400,256), M=new("M",0x470004a0,68), C=new("C",0x47000bc0,16);
    static readonly byte[] WriteHeader=Convert.FromHexString("02010000c424014702000000");
    static byte[] Header(Spec s) {byte[] b=new byte[12];BitConverter.GetBytes(0x101u).CopyTo(b,0);BitConverter.GetBytes(s.Address).CopyTo(b,4);BitConverter.GetBytes(s.Length).CopyTo(b,8);return b;}
    static bool AllowedHeader(byte[] b) {if(b.AsSpan().SequenceEqual(WriteHeader))return true;foreach(var s in new[]{Callback,R,M,C})if(b.AsSpan().SequenceEqual(Header(s)))return true;return false;}
    static void Need(bool b,string s){if(!b)throw new InvalidOperationException(s);}
    static int Half(byte[] b,int i)=>b[i]|b[i+1]<<8;
    static string Sha(byte[] b)=>Convert.ToHexString(SHA256.HashData(b)).ToLowerInvariant();
    static string ShortError(Exception e)=>e.GetType().Name+": "+e.Message;
    interface IOps {Identity Preflight();NativeResult Open(Identity id);void ValidateFd(int fd,Identity id);void Revalidate(Identity id);NativeResult Claim(int fd);NativeResult Bulk(int fd,bool input,byte[] data,int length);NativeResult Release(int fd);NativeResult Close(int fd);}
    interface IClock {long NowUs();void SleepUs(long us);}
    sealed record Step(string Name,string Direction,int Expected,int? Count,int Errno,long BeforeUs,long AfterUs,string Before,string After);
    sealed record Window(string Name,int Bytes,string Sha256,string Base64);
    sealed class Outcome {
      public int Device{get;set;} public string Schema{get;set;}="dj-fixed-limit-v1";public string Action{get;set;}="";public string ProtocolPhase{get;set;}="ReadyForHeader";public string Stage{get;set;}="preflight";
      public bool Opened{get;set;} public bool Claimed{get;set;} public bool Released{get;set;}=true;public bool Closed{get;set;}=true;
      public bool WriteAttempted{get;set;} public bool WriteTransportComplete{get;set;} public bool ReadbackVerified{get;set;} public bool LimitMayHaveChanged{get;set;} public bool Accepted{get;set;}
      public bool PhysicalPictureObserved{get;set;} public bool RootCauseFixEstablished{get;set;} public int HeadersSent{get;set;} public int BulkTransfers{get;set;}
      public List<Step> Steps{get;}=new();public List<Window> Windows{get;}=new();public List<string> Errors{get;}=new();
    }
'''
prefix+='    static readonly byte[] Profile=Convert.FromHexString("'+r.hex()+'");\n'
body='''
    // Only historical action buckets, record/event latches and q-publication latch are
    // excluded from profile equality. Stop/fault/gates are independently strict.
    static bool DynamicR(int i)=>(i>=0x86&&i<0x8a)||(i>=0x8c&&i<0x8e)||(i>=0x90&&i<0x94)||(i>=0xa2&&i<0xa4);
    static void GuardR(byte[] r,int expected) {
      Need(r.Length==256,"R extent");
      for(int i=0;i<256;i++)if(!DynamicR(i)&&i!=0xc4&&i!=0xc5&&i!=0xca)Need(r[i]==Profile[i],"R profile byte "+i);
      Need(r[0xca]<=1,"R observed selector domain");
      Need(Half(r,0)==0&&Half(r,0xa)==0&&Half(r,0xe)==1&&Half(r,6)==0,"R clean/gate/logger");
      Need(Half(r,0xc4)==expected&&Half(r,0x30)==200&&Half(r,0xc0)==200,"R limit");
      Need(Half(r,0x9e)==1&&Half(r,0x4a)==0&&Half(r,0x4e)==0&&Half(r,0x9a)==0&&Half(r,0x9c)==0,"R alternative gates/latches");
    }
    static void GuardContext(byte[] m,byte[] c) {
      Need(m.Length==68&&c.Length==16,"context extent");
      Need(BitConverter.ToUInt32(m,64)==0x20010000,"root");Need(Half(m,10)==0&&Half(m,12)==2,"mode1 flags");Need(m[56]==1,"scan enable");
      Need(Half(m,22)==500&&Half(m,24)==0&&Half(m,26)==500&&Half(m,28)==0&&Half(m,38)==3183&&Half(m,40)==500,"numeric profile");
      Need(Half(c,0)==2160&&Half(c,2)==1920&&Half(c,4)==2880&&c[6]==92&&c[7]<=1&&c[8]==3,"C geometry/profile/selector");
    }
    static void GuardCallbacks(byte[] b){uint[] cb={0x2945d,0x293d1,0x294fb,0,0,0x28b85,0x28cf1,0x294f5};Need(b.Length==64,"callback extent");for(int i=0;i<cb.Length;i++)Need(BitConverter.ToUInt32(b,12+i*4)==cb[i],"callback tuple");}
    sealed class Controller {
      readonly IOps ops;readonly IClock clock;readonly Outcome o;readonly int fd;readonly long deadline;long last=-1;
      public Controller(IOps ops,IClock clock,Outcome o,int fd,long deadline){this.ops=ops;this.clock=clock;this.o=o;this.fd=fd;this.deadline=deadline;}
      long Time(){long v=clock.NowUs();Need(v>=last,"clock backwards");last=v;return v;}
      void Budget(){Need(o.ProtocolPhase=="ReadyForHeader","new header forbidden");Need(Time()+4_000_000<=deadline,"transaction budget");}
      void Transfer(string name,bool input,byte[] b,string after){string before=o.ProtocolPhase;long at=last<0?0:last;try{at=Time();}catch(Exception e){o.Errors.Add(ShortError(e));if(before=="ReadyForHeader")throw;}o.ProtocolPhase="Unknown";NativeResult n;try{n=ops.Bulk(fd,input,b,b.Length);}catch{ o.Steps.Add(new(name,input?"IN":"OUT",b.Length,null,0,at,at,before,"Unknown"));o.BulkTransfers++;if(b.Length==12)o.HeadersSent++;throw;}
        o.BulkTransfers++;if(!input&&b.Length==12)o.HeadersSent++;if(n.Value==b.Length)o.ProtocolPhase=after;
        // Accepted header creates a matching transfer obligation even if the clock fails.
        long end=at;try{end=Time();}catch(Exception e){o.Errors.Add(ShortError(e));}
        o.Steps.Add(new(name,input?"IN":"OUT",b.Length,n.Value,n.Errno,at,end,before,o.ProtocolPhase));Need(n.Value==b.Length,"short/failed transfer "+name);
      }
      public byte[] Read(string name,Spec s){Budget();Transfer(name+"-header",false,Header(s),"ExpectingReadIn");byte[] b=new byte[s.Length];Transfer(name+"-data",true,b,"ReadyForHeader");o.Windows.Add(new(name,b.Length,Sha(b),Convert.ToBase64String(b)));Need(o.Errors.Count==0,"clock error after completed read");return b;}
      public void Write(int value){Budget();o.WriteAttempted=true;o.LimitMayHaveChanged=true;Transfer("write-header",false,(byte[])WriteHeader.Clone(),"ExpectingWritePayload");Transfer("write-payload",false,new[]{(byte)value,(byte)0},"ReadyForHeader");o.WriteTransportComplete=true;Need(o.Errors.Count==0,"clock error after completed write");}
    }
    static Outcome Run(IOps ops,IClock clock,bool restore){Outcome o=new(){Action=restore?"restore200to40":"set40to200"};int fd=-1;try{
      long deadline=checked(clock.NowUs()+40_000_000);var id=ops.Preflight();o.Device=id.Device;fd=ops.Open(id).Value;Need(fd>=0,"open");o.Opened=true;o.Closed=false;ops.ValidateFd(fd,id);ops.Revalidate(id);Need(ops.Claim(fd).Value==0,"claim");o.Claimed=true;o.Released=false;ops.Revalidate(id);
      var x=new Controller(ops,clock,o,fd,deadline);int old=restore?200:40,value=restore?40:200;
      GuardCallbacks(x.Read("callbacks",Callback));var baseline=x.Read("baseline-R",R);GuardR(baseline,old);var m=x.Read("pre-M",M);var c=x.Read("pre-C",C);GuardContext(m,c);var fresh=x.Read("fresh-R",R);GuardR(fresh,old);Need(fresh[0xca]==baseline[0xca],"selector changed during preflight");
      o.Stage="write";x.Write(value);o.Stage="readback";var after=x.Read("readback-R",R);GuardR(after,value);
      // Every non-status byte, including the unknown selector byte, must remain exact.
      for(int i=0;i<256;i++)if(!DynamicR(i)&&i!=0xc4)Need(after[i]==fresh[i],"unexpected R mutation "+i);
      o.ReadbackVerified=true;o.LimitMayHaveChanged=false;
    }catch(Exception e){o.Errors.Add(ShortError(e));}
    finally{if(o.Claimed)try{var n=ops.Release(fd);o.Released=n.Value==0;if(!o.Released)o.Errors.Add("release failed");}catch(Exception e){o.Errors.Add("release "+ShortError(e));}
      if(fd>=0)try{var n=ops.Close(fd);o.Closed=n.Value==0;if(!o.Closed)o.Errors.Add("close failed");}catch(Exception e){o.Errors.Add("close "+ShortError(e));}}
    o.Accepted=o.Errors.Count==0&&o.ReadbackVerified&&o.WriteTransportComplete&&o.ProtocolPhase=="ReadyForHeader"&&o.Released&&o.Closed;o.Stage=o.Accepted?"complete":"rejected";return o;}
'''
# Atomic matching transfer must not be suppressed by a timestamp exception before transfer.
# Clock refusal at a new-header boundary never sends OUT; pending data remains obligatory.
(P/'Program.cs').write_text(prefix+body+real+'\n'+(P/'tests-part.cs.txt').read_text()+'\n}\n')
(P/'FixedLimit.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net6.0</TargetFramework><ImplicitUsings>disable</ImplicitUsings><Nullable>enable</Nullable><UseAppHost>false</UseAppHost><DebugType>none</DebugType><Deterministic>true</Deterministic><EnableNETAnalyzers>false</EnableNETAnalyzers></PropertyGroup></Project>\n')
(P/'source-lineage.json').write_text(json.dumps({'parent_usb_source':str(parent.relative_to(B)),'parent_usb_source_sha256':hashlib.sha256(raw).hexdigest(),'golden_R_source':str((q/'retained-00-trigger_baseline-cycle001-00-R.bin').relative_to(B)),'golden_R_sha256':hashlib.sha256(r).hexdigest(),'R_other_observed_template':'same profile with byte0xca=1; domain guard and preflight/readback equality; no semantic name assigned','target_operations':0},indent=2)+'\n')
