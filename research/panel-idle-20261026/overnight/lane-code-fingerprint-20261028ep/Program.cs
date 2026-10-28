using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text.Json;
internal static partial class Program
{
 const int TimeoutMs=2000;
 static int ExpectedDevice;
 const string ExpectedBoot="00000000-0000-4000-8000-000000000000";
 const string UsbRoot="/sys/bus/usb/devices/7-1";
 const string DeviceHex="12010002ef020140e8040120500201020301";
 const string AllDescriptorsHex=DeviceHex+"090262000301048032080b00020202010a09040000010202010a052400100105240100010424020205240600010705830308001009040100020a00000a07050102400010070581024000000904020002ff0000000705820200020007050202000200";
 readonly record struct Identity(int Bus,int Device) {public string Node=>$"/dev/bus/usb/{Bus:D3}/{Device:D3}";}
 readonly record struct NativeResult(int Value,int Errno);
 sealed record Spec(string Name,uint Address,int Length);
 static readonly Spec[] Specs={new("root-getter",0x460038fc,12),new("root-save",0x4600bd6c,8),new("operating-mode-and-SB",0x4600be0c,44),new("four-unrolled-local-gates",0x4600beb4,228),new("gate-literal-pool",0x4600c030,32)};
 static readonly string[] Fingerprints={"d495280b4557a25b3c9154ca8d64678afb7b949c089d353ef884a74e68790268","bc6728d90e8693c9f3ef034a61687cdcc130797d4015863c5f49e809c7eafc3e","3864a39cd1178e7c986cbcdaaccae42843430e6a38d13de7723d115417232fcd","044752267f71da1f8c28f8bca423972ac77ca099b1deb089e23ac42cde138d19","c629789db4bcbc06d85c7b04c6c880cb8ec1a4585b836dc28a72f83f5fd1808c"};
 static byte[] Header(Spec s){byte[] b=new byte[12];BitConverter.GetBytes(0x101u).CopyTo(b,0);BitConverter.GetBytes(s.Address).CopyTo(b,4);BitConverter.GetBytes(s.Length).CopyTo(b,8);return b;}
 static bool AllowedHeader(byte[] b){foreach(var s in Specs)if(b.AsSpan().SequenceEqual(Header(s)))return true;return false;}
 static bool InputLength(int n){foreach(var s in Specs)if(s.Length==n)return true;return false;}
 static void Need(bool b,string s){if(!b)throw new InvalidOperationException(s);}
 static string Sha(byte[] b)=>Convert.ToHexString(SHA256.HashData(b)).ToLowerInvariant();
 interface IOps {IReadOnlyList<BindingCheck> BindingChecks{get;}Identity Preflight();NativeResult Open(Identity i);void ValidateFd(int fd,Identity i);void Revalidate(Identity i);NativeResult Claim(int fd);NativeResult Bulk(int fd,bool input,byte[] data,int length);NativeResult Release(int fd);NativeResult Close(int fd);}
 interface IClock {long NowUs();}
 sealed record Step(string Name,string Direction,int Expected,int? Count,int Errno,long BeforeUs,long AfterUs,string Before,string After);
 sealed record Window(string Name,uint Address,int Bytes,string Sha256,string Base64);
 static string ShortError(string value){if(value.Length>128)value=value.Substring(0,128);while(System.Text.Encoding.UTF8.GetByteCount(JsonSerializer.Serialize(value))>128)value=value.Substring(0,value.Length-1);return value;}
 sealed class BoundedErrors:List<string>{public new void Add(string value)=>base.Add(ShortError(value));}
 sealed class Outcome {
  public string Schema{get;set;}="ep-lane-code-fingerprint-v1";public string ProtocolPhase{get;set;}="ReadyForHeader";public int Device{get;set;}
  public bool Opened{get;set;} public bool Claimed{get;set;} public bool Released{get;set;}=true;public bool Closed{get;set;}=true;public bool Accepted{get;set;}
  public int HeadersSent{get;set;}public int BulkTransfers{get;set;}public int Writes{get;set;}public int UiOperations{get;set;}public bool AtomicSnapshot{get;set;}public bool PhysicalPictureObserved{get;set;}public bool SampledCodeMatch{get;set;}public bool WholeRunningImageAttested{get;set;}public bool ExecutableWriteQualified{get;set;}
  public List<BindingCheck> BindingChecks{get;}=new();
  public List<Step> Steps{get;}=new(10);public List<Window> Windows{get;}=new(5);public BoundedErrors Errors{get;}=new();
 }
 sealed class Controller {
  readonly IOps ops;readonly IClock clock;readonly Outcome o;readonly int fd;readonly long deadline;long last=-1;
  public Controller(IOps p,IClock c,Outcome r,int f,long d){ops=p;clock=c;o=r;fd=f;deadline=d;}
  long Time(){long v=clock.NowUs();Need(v>=last,"clock backwards");last=v;return v;}
  void Transfer(string name,bool input,byte[] b,string next){string before=o.ProtocolPhase;long at=last<0?0:last;try{at=Time();}catch(Exception e){o.Errors.Add(e.Message);if(before=="ReadyForHeader")throw;}
   o.ProtocolPhase="Unknown";NativeResult n;
   try{n=ops.Bulk(fd,input,b,b.Length);}catch{++o.BulkTransfers;if(!input)++o.HeadersSent;o.Steps.Add(new(name,input?"IN":"OUT",b.Length,null,0,at,at,before,"Unknown"));throw;}
   ++o.BulkTransfers;if(!input)++o.HeadersSent;if(n.Value==b.Length)o.ProtocolPhase=next;
   long end=at;try{end=Time();}catch(Exception e){o.Errors.Add(e.Message);}
   o.Steps.Add(new(name,input?"IN":"OUT",b.Length,n.Value,n.Errno,at,end,before,o.ProtocolPhase));Need(n.Value==b.Length,"short/failed "+name);
  }
  public void Read(Spec s,byte[] header,byte[] raw){Need(o.ProtocolPhase=="ReadyForHeader","header phase");Need(Time()+4_000_000<=deadline,"transaction budget");Transfer(s.Name+"-header",false,header,"ExpectingIn");Transfer(s.Name+"-data",true,raw,"ReadyForHeader");o.Windows.Add(new(s.Name,s.Address,raw.Length,Sha(raw),Convert.ToBase64String(raw)));Need(o.Errors.Count==0,"clock failure after completed pair");}
 }
 static Outcome Run(IOps p,IClock c){var o=new Outcome();var headers=new byte[Specs.Length][];var raws=new byte[Specs.Length][];for(int i=0;i<Specs.Length;i++){headers[i]=Header(Specs[i]);raws[i]=new byte[Specs[i].Length];}int fd=-1;
  try{long deadline=checked(c.NowUs()+40_000_000);var id=p.Preflight();o.Device=id.Device;fd=p.Open(id).Value;Need(fd>=0,"open");o.Opened=true;o.Closed=false;p.ValidateFd(fd,id);p.Revalidate(id);Need(p.Claim(fd).Value==0,"claim");o.Claimed=true;o.Released=false;p.Revalidate(id);var engine=new Controller(p,c,o,fd,deadline);for(int i=0;i<Specs.Length;i++){engine.Read(Specs[i],headers[i],raws[i]);Need(Sha(raws[i])==Fingerprints[i],"sampled code fingerprint mismatch "+Specs[i].Name);}o.SampledCodeMatch=true;}
  catch(Exception e){o.Errors.Add(e.GetType().Name+": "+e.Message);}
  finally{if(o.Claimed)try{o.Released=p.Release(fd).Value==0;if(!o.Released)o.Errors.Add("release failed");}catch(Exception e){o.Errors.Add("release "+e.Message);}if(fd>=0)try{o.Closed=p.Close(fd).Value==0;if(!o.Closed)o.Errors.Add("close failed");}catch(Exception e){o.Errors.Add("close "+e.Message);}o.BindingChecks.AddRange(p.BindingChecks);}
  o.Accepted=o.Errors.Count==0&&o.Windows.Count==5&&o.SampledCodeMatch&&o.ProtocolPhase=="ReadyForHeader"&&o.Released&&o.Closed;return o;
 }
 static string Serialize(Outcome o)=>JsonSerializer.Serialize(o,new JsonSerializerOptions{PropertyNamingPolicy=JsonNamingPolicy.CamelCase});
 static byte[] ReadCachedDescriptors(Stream s){byte[] b=new byte[117];int used=0;while(used<b.Length){int n=s.Read(b,used,b.Length-used);if(n==0)return b.AsSpan(0,used).ToArray();Need(n>0&&n<=b.Length-used,"descriptor count");used+=n;}throw new InvalidOperationException("descriptors exceed116");}
 static byte[] ReadCachedDescriptors(string p){using var s=File.OpenRead(p);return ReadCachedDescriptors(s);}
}
