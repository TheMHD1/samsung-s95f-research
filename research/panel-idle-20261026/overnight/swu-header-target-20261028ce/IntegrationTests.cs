using System;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;

internal static class IntegrationTests
{
    sealed class CountMock:ITeec,IDisposable
    {
        readonly Mock inner=new Mock();
        readonly uint update,final;
        internal CountMock(uint update,uint final){this.update=update;this.final=final;}
        public uint Initialize(Block b)=>inner.Initialize(b);
        public uint Allocate(Block a,Block b)=>inner.Allocate(a,b);
        public uint Open(Block a,Block b,Block c,out uint o)=>inner.Open(a,b,c,out o);
        public uint Invoke(Block session,uint cmd,Block op,out uint origin)
        {
            uint code=inner.Invoke(session,cmd,op,out origin);
            if(code==0 && cmd==1)op.Put(32,update);
            if(code==0 && cmd==2)op.Put(20,final);
            return code;
        }
        public void Close(Block b)=>inner.Close(b);
        public void Release(Block b)=>inner.Release(b);
        public void FinalizeContext(Block b)=>inner.FinalizeContext(b);
        public uint Address(Block b)=>inner.Address(b);
        public BlockView Map(Block b)=>inner.Map(b);
        public void Dispose()=>inner.Dispose();
    }
    internal static int Run()
    {
        Core.Require(RuntimeInformation.ProcessArchitecture==Architecture.X64,"host only");
        int checks=0;
        foreach(bool failInspection in new[]{false,true}) {
            using Mock mock=new Mock();
            byte[] envelope=new byte[Core.Envelope],blob=new byte[Core.Blob];
            int inspected=0;
            Result r=Core.Run(mock,envelope,blob,()=>{},plain=> {
                Core.Require(mock.Commands==3 && mock.Closed==0,"inspection after commands before cleanup");
                Core.Require(plain.Length==4032 && plain.ToArray().All(b=>b==0xa5),"full update plus final count");
                inspected++;
                if(failInspection)throw new InvalidOperationException("synthetic inspection failure");
            });
            Core.Require(inspected==1 && r.LocalFailure==failInspection,"one callback with retained failure");
            Core.Require(r.SessionClosed && r.Released==3 && r.ContextFinalized,"cleanup follows callback");
            Core.Require(blob.All(b=>b==0),"blob wiped");
            Core.Require(r.Stage==(failInspection?"inspection":"quarantined"),"inspection stage");
            checks+=6;
        }
        for(int failure=0;failure<8;failure++) {
            using Mock mock=new Mock{Fail=failure};int inspected=0;
            Result r=Core.Run(mock,new byte[Core.Envelope],new byte[Core.Blob],()=>{},_=>inspected++);
            Core.Require(inspected==0,"no inspection after native failure");checks++;
        }
        foreach(int badCount in new[]{2,3,4}) {
            using Mock mock=new Mock{Mode=badCount};int inspected=0;
            Result r=Core.Run(mock,new byte[Core.Envelope],new byte[Core.Blob],()=>{},_=>inspected++);
            Core.Require(inspected==0 && r.LocalFailure,"no inspection after count violation");checks++;
        }
        foreach(uint update in new uint[]{4032,4031}) {
            using CountMock mock=new CountMock(update,0);int inspected=0;
            Result r=Core.Run(mock,new byte[Core.Envelope],new byte[Core.Blob],()=>{},plain=> {
                inspected++;Core.Require(plain.Length==4032 && plain.ToArray().All(b=>b==0xa5),"exact observed4032+0 representation");
            });
            Core.Require(inspected==(update==4032?1:0) && r.LocalFailure==(update!=4032),"exact count, not capacity, gates inspection");
            Core.Require(r.Counts[0]==update && r.Counts[1]==0 && r.SessionClosed && r.Released==3 && r.ContextFinalized,"count-form cleanup");checks+=2;
        }
        Core.Require(PrivateHeaderFile.CreateFlags(Architecture.Arm)==0xa80c1 &&
                     PrivateHeaderFile.CreateFlags(Architecture.X64)==0xa00c1,"architecture exclusive output flags");checks++;
        string directory=Path.Combine(Path.GetTempPath(),"swu-private-fixture-"+Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);string output=Path.Combine(directory,"header.bin"),link=Path.Combine(directory,"link");
        byte[] fixture=Enumerable.Repeat((byte)0xa5,4032).ToArray();
        try {
            PrivateHeaderFile.SaveHostFixture(output,fixture);
            Core.Require(File.ReadAllBytes(output).SequenceEqual(fixture),"private output disk bytes");checks++;
            bool refused=false;try{PrivateHeaderFile.SaveHostFixture(output,fixture);}catch{refused=true;}
            Core.Require(refused && File.ReadAllBytes(output).SequenceEqual(fixture),"existing file untouched");checks++;
            File.CreateSymbolicLink(link,output);refused=false;
            try{PrivateHeaderFile.SaveHostFixture(link,fixture);}catch{refused=true;}
            Core.Require(refused && File.ReadAllBytes(output).SequenceEqual(fixture),"symlink not followed");checks++;
            refused=false;try{PrivateHeaderFile.SaveHostFixture(Path.Combine(directory,"short"),new byte[4031]);}catch{refused=true;}
            Core.Require(refused && !File.Exists(Path.Combine(directory,"short")),"bad count before create");checks++;
        } finally {Directory.Delete(directory,true);}
        Console.WriteLine($"PASS integration_host_only=1 checks={checks} real_tee_calls=0 target_operations=0 private_output_fixture_bytes=4032");
        return 0;
    }
}
