using System;
using System.IO;
using System.Runtime.InteropServices;
using SwuSectionStream;
internal static class IntegrationTests {
 internal static int Run(){int n=0;void Check(bool p){if(!p)throw new Exception("host test");n++;}
 Check(PrivateRawSink.CreateFlags(Architecture.Arm)==0xa80c1);Check(PrivateRawSink.CreateFlags(Architecture.X64)==0xa00c1);
 Check(Native.RequiredStatMask==0x3df);byte[] valid=File.ReadAllBytes("private/section-plan.bin");byte[] salt=Program.CheckPlan(valid);Check(salt.Length==8);
 foreach(int at in new[]{0,8,12,20,28,32,40,71}){byte[] bad=(byte[])valid.Clone();bad[at]^=1;bool refused=false;try{Program.CheckPlan(bad);}catch{refused=true;}Check(refused);}
 string dir=Path.Combine(Path.GetTempPath(),"swu-ci-test-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(dir);
 try{string path=Path.Combine(dir,"raw");var plan=new SectionPlan(166416,Program.CipherHash,Core.BlobHash,Program.PlanHash);using(var sink=new PrivateRawSink(path,166416)){sink.Begin(plan);Check(sink.Write(new byte[166416])==166416);sink.CompleteRaw();}Check(new FileInfo(path).Length==166416);int fd=Native.OpenReadOnlyNoFollow(path);try{Check(fd>=0);Check((System.Buffers.Binary.BinaryPrimitives.ReadUInt16LittleEndian(Native.Stat(fd).AsSpan(28))&511)==384);}finally{if(fd>=0)Native.close(fd);}
 bool exclusive=false;using(var sink=new PrivateRawSink(path,166416)){try{sink.Begin(plan);}catch{exclusive=true;}}Check(exclusive);
 path=Path.Combine(dir,"partial");using(var sink=new PrivateRawSink(path,166416)){sink.Begin(plan);Check(sink.Write(new byte[16])==16);bool early=false;try{sink.CompleteRaw();}catch{early=true;}Check(early);sink.Abort();}Check(new FileInfo(path).Length==16);
 path=Path.Combine(dir,"cap");using(var sink=new PrivateRawSink(path,166416)){sink.Begin(plan);bool cap=false;try{sink.Write(new byte[166417]);}catch{cap=true;}Check(cap);}
 }finally{Directory.Delete(dir,true);}Console.WriteLine("CI_INTEGRATION_TESTS checks="+n);return 0;
 }
}
