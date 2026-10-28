using System;
using System.Buffers.Binary;
using System.Runtime.InteropServices;
using System.Security.Cryptography;

namespace SwuSectionStream
{
    // Same widths and call shape as the proven BZ Block/BlockView/ITeec model.
    // Runtime allocation only: no target library, syscall or live binding here.
    public sealed class Block : IDisposable
    {
        public readonly int Size;
        public IntPtr Pointer { get; private set; }
        public Block(int size) {
            if(size<1 || size>65536)throw new ArgumentOutOfRangeException(nameof(size));
            Size=size;Pointer=Marshal.AllocHGlobal(size);Clear();
        }
        public unsafe Span<byte> Bytes {
            get {if(Pointer==IntPtr.Zero)throw new ObjectDisposedException(nameof(Block));return new Span<byte>((void*)Pointer,Size);}
        }
        public void Clear()=>CryptographicOperations.ZeroMemory(Bytes);
        public uint Get(int offset)=>BinaryPrimitives.ReadUInt32LittleEndian(Bytes.Slice(offset,4));
        public void Put(int offset,uint value)=>BinaryPrimitives.WriteUInt32LittleEndian(Bytes.Slice(offset,4),value);
        public void Dispose() {if(Pointer!=IntPtr.Zero){Clear();Marshal.FreeHGlobal(Pointer);Pointer=IntPtr.Zero;}}
    }
    public readonly struct BlockView
    {
        public readonly IntPtr Pointer;
        public readonly int Size;
        public BlockView(IntPtr pointer,int size){Pointer=pointer;Size=size;}
        public unsafe Span<byte> Bytes=>new Span<byte>((void*)Pointer,Size);
        public void Clear()=>CryptographicOperations.ZeroMemory(Bytes);
    }
    public interface ITeec
    {
        uint Initialize(Block context);
        uint Allocate(Block context,Block shared);
        uint Open(Block context,Block session,Block uuid,out uint origin);
        uint Invoke(Block session,uint command,Block operation,out uint origin);
        void Close(Block session);
        void Release(Block shared);
        void FinalizeContext(Block context);
        uint Address(Block block);
        BlockView Map(Block shared);
    }
    public interface IChunkSource
    {
        // Synchronous consumption only; zero means EOF. Positive short reads
        // are ordinary progress, not retries of a failed read or TEEC command.
        int Read(Span<byte> destination);
    }
    public interface IChunkSink
    {
        // All writes are provisional. CompleteRaw means raw transport completion,
        // never payload authentication, schema validation or installation.
        void Begin(SectionPlan plan);
        int Write(ReadOnlySpan<byte> plaintext);
        void CompleteRaw();
        void Abort();
    }
    public sealed record SectionPlan(long CipherBytes,string CipherSha256,
                                     string MasterBlobSha256,string MetadataPlanSha256)
    {
        public long MaximumRawOutputBytes=>CipherBytes;
        public long MaximumUpdateCalls=>(CipherBytes+StreamingEngine.SharedBytes-1)/StreamingEngine.SharedBytes;
    }
    public enum Stage
    {
        None, Arguments, Plan, SecretPin, AllocateLocal, Guard, SinkBegin,
        Initialize, Allocate0, Allocate1, Allocate2, Map0, Map1, Map2,
        Session, Command0, InputRead, InputCount, Command1, UpdateCount,
        SinkWrite, SinkCount, InputEof, InputDigest, Command2, FinalCount,
        OutputDigest, Close, WipeShared, Release2, Release1, Release0,
        FinalizeContext, WipeLocal, SinkComplete, SinkAbort
    }
    public sealed class StreamResult
    {
        public Stage FirstFailure {get;internal set;}
        public uint Code {get;internal set;}
        public uint Origin {get;internal set;}=uint.MaxValue;
        public Stage FirstCleanupFailure {get;internal set;}
        public int CleanupFailures {get;internal set;}
        public int GuardCalls {get;internal set;}
        public int Command0Attempts {get;internal set;}
        public long UpdateAttempts {get;internal set;}
        public int FinalAttempts {get;internal set;}
        public long ReadCalls {get;internal set;}
        public long CipherBytesRead {get;internal set;}
        public long RawBytesProduced {get;internal set;}
        public long SinkBytesConfirmed {get;internal set;}
        public int MaximumInputChunk {get;internal set;}
        public int MaximumOutputChunk {get;internal set;}
        public bool SinkWriteMayHaveOccurred {get;internal set;}
        public bool InputEofObserved {get;internal set;}
        public bool CipherDigestMatchedAtEof {get;internal set;}
        public bool BackendExceptionObserved {get;internal set;}
        public bool ResourceOwnershipUncertain {get;internal set;}
        public bool SessionClosed {get;internal set;}
        public int Released {get;internal set;}
        public bool ContextFinalized {get;internal set;}
        public bool OwnedBuffersWipeConfirmed {get;internal set;}
        public bool SinkCompletionAttempted {get;internal set;}
        public bool SinkCompletedRaw {get;internal set;}
        public bool SinkAbortAttempted {get;internal set;}
        public bool SinkAbortReturned {get;internal set;}
        public string? RawEmittedSha512 {get;internal set;}
        public uint? RawEmittedCrc32 {get;internal set;}
        public bool Accepted=>FirstFailure==Stage.None && CipherDigestMatchedAtEof &&
            SessionClosed && Released==3 && ContextFinalized && OwnedBuffersWipeConfirmed && SinkCompletedRaw;
        public bool PaddingRemoved=>false;
        public bool PayloadAuthenticityValidated=>false;
        public bool WireSchemaComplete=>false;
        public bool FullSchemaValidated=>false;
        public bool FirmwareApplicabilityValidated=>false;
        public int TeecRetries=>0;
        internal void Fail(Stage stage,uint code=0xffff0006,uint origin=uint.MaxValue) {
            if(FirstFailure==Stage.None){FirstFailure=stage;Code=code;Origin=origin;}
        }
        internal void CleanupFail(Stage stage) {
            CleanupFailures++;if(FirstCleanupFailure==Stage.None)FirstCleanupFailure=stage;Fail(stage);
        }
    }

    public static class StreamingEngine
    {
        public const int SharedBytes=65536,MasterBlobBytes=416,SaltBytes=8,OperationBytes=60;
        public const long MaximumCipherBytes=2147483648; // bounded prototype policy; long counters
        private sealed class Stop:Exception { }
        private static bool Hex(string? s) {
            if(s==null || s.Length!=64)return false;
            foreach(char c in s)if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))return false;return true;
        }
        private static void Need(bool ok,StreamResult result,Stage stage) {
            if(!ok){result.Fail(stage);throw new Stop();}
        }
        private static void NativeCode(uint code,uint origin,StreamResult result,Stage stage) {
            if(code!=0){result.Fail(stage,code,origin);throw new Stop();}
        }
        private static string Digest(ReadOnlySpan<byte> data)=>Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();
        private static ulong Pointer(IntPtr pointer)=>IntPtr.Size==4?unchecked((uint)pointer.ToInt32()):unchecked((ulong)pointer.ToInt64());
        private static bool Separate(BlockView a,BlockView b) {
            ulong x=Pointer(a.Pointer),y=Pointer(b.Pointer);
            return x<y?y-x>=(ulong)SharedBytes:x-y>=(ulong)SharedBytes;
        }
        private static void Mem(Block op,int offset,uint parent,int size) {op.Put(offset,parent);op.Put(offset+4,(uint)size);}
        public static void Frame(Block op,uint command,uint input,uint output,uint salt,int inputBytes=0)
        {
            if(op.Size!=OperationBytes || command>2 || (command==1 && (inputBytes<1 || inputBytes>SharedBytes || inputBytes%16!=0)))
                throw new ArgumentException("fixed frame contract");
            op.Clear();
            if(command==0){op.Put(4,0x01010d0d);Mem(op,8,input,MasterBlobBytes);Mem(op,20,salt,SaltBytes);op.Put(36,1);op.Put(44,1);op.Put(48,0x201);}
            if(command==1){op.Put(4,0x00020e0d);Mem(op,8,input,inputBytes);Mem(op,20,output,SharedBytes);}
            if(command==2){op.Put(4,0x0000020e);Mem(op,8,output,SharedBytes);}
        }
        private static uint Crc(uint crc,ReadOnlySpan<byte> bytes) {
            foreach(byte b in bytes){crc^=b;for(int bit=0;bit<8;bit++)crc=(crc>>1)^((crc&1)!=0?0xedb88320u:0);}return crc;
        }

        public static StreamResult Run(ITeec api,SectionPlan plan,byte[] encryptedMasterBlob,
                                       byte[] salt,IChunkSource source,IChunkSink sink,Action guard)
        {
            StreamResult result=new StreamResult();
            if(api==null || plan==null || source==null || sink==null || guard==null ||
               encryptedMasterBlob==null || salt==null || encryptedMasterBlob.Length!=MasterBlobBytes || salt.Length!=SaltBytes){result.Fail(Stage.Arguments);return result;}
            if(plan.CipherBytes<16 || plan.CipherBytes>MaximumCipherBytes || plan.CipherBytes%16!=0 ||
               !Hex(plan.CipherSha256) || !Hex(plan.MasterBlobSha256) || !Hex(plan.MetadataPlanSha256)){result.Fail(Stage.Plan);return result;}
            // Only a caller-provided expected identity is known here. The rolling
            // cipher digest is checked AT EOF, after updates, never before cmd0.
            Stage stage=Stage.AllocateLocal;
            Block? context=null,session=null,uuid=null,operation=null;
            Block?[] shared=new Block?[3];BlockView[] view=new BlockView[3];uint[] parent=new uint[3];
            byte[] masterCopy=Array.Empty<byte>(),saltCopy=Array.Empty<byte>();
            IncrementalHash? inputHash=null,outputHash=null;
            bool initialized=false,opened=false,sinkAttempted=false,bodyComplete=false;
            int allocated=0,mapped=0;uint outputCrc=0xffffffff;
            try {
                masterCopy=(byte[])encryptedMasterBlob.Clone();saltCopy=(byte[])salt.Clone();
                stage=Stage.SecretPin;Need(Digest(masterCopy)==plan.MasterBlobSha256,result,stage);
                stage=Stage.AllocateLocal;context=new Block(4);session=new Block(4);uuid=new Block(16);operation=new Block(OperationBytes);
                for(int i=0;i<3;i++)shared[i]=new Block(36);
                inputHash=IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
                outputHash=IncrementalHash.CreateHash(HashAlgorithmName.SHA512);
                stage=Stage.Guard;result.GuardCalls++;guard();
                stage=Stage.SinkBegin;sinkAttempted=true;sink.Begin(plan);
                stage=Stage.Initialize;NativeCode(api.Initialize(context),uint.MaxValue,result,stage);initialized=true;
                for(int i=0;i<3;i++) {
                    stage=(Stage)((int)Stage.Allocate0+i);shared[i]!.Put(4,SharedBytes);shared[i]!.Put(8,3);
                    NativeCode(api.Allocate(context,shared[i]!),uint.MaxValue,result,stage);allocated++;
                    Need(shared[i]!.Get(4)==SharedBytes && shared[i]!.Get(8)==3 && shared[i]!.Get(0)!=0,result,stage);
                    stage=(Stage)((int)Stage.Map0+i);BlockView candidate=api.Map(shared[i]!);
                    Need(candidate.Pointer!=IntPtr.Zero && candidate.Size==SharedBytes,result,stage);
                    uint address=api.Address(shared[i]!);Need(address!=0 && (address&3)==0,result,stage);
                    for(int j=0;j<i;j++)Need(parent[j]!=address && Separate(candidate,view[j]),result,stage);
                    view[i]=candidate;parent[i]=address;mapped++;view[i].Clear();
                }
                uuid.Put(0,0x22222221);uuid.Bytes[15]=1;
                stage=Stage.Session;uint origin;NativeCode(api.Open(context,session,uuid,out origin),origin,result,stage);opened=true;
                stage=Stage.Guard;result.GuardCalls++;guard();
                masterCopy.CopyTo(view[0].Bytes);saltCopy.CopyTo(view[2].Bytes);
                try {
                    Frame(operation,0,parent[0],parent[1],parent[2]);stage=Stage.Command0;result.Command0Attempts++;
                    uint code=api.Invoke(session,0,operation,out origin);NativeCode(code,origin,result,stage);
                } finally {view[0].Clear();view[2].Clear();CryptographicOperations.ZeroMemory(masterCopy);CryptographicOperations.ZeroMemory(saltCopy);}

                long remaining=plan.CipherBytes;
                while(remaining>0) {
                    stage=Stage.Guard;result.GuardCalls++;guard();
                    int wanted=(int)Math.Min(SharedBytes,remaining),at=0;
                    result.MaximumInputChunk=Math.Max(result.MaximumInputChunk,wanted);
                    try {
                        while(at<wanted) {
                            stage=Stage.InputRead;result.ReadCalls++;
                            int count=source.Read(view[0].Bytes.Slice(at,wanted-at));
                            Need(count>0 && count<=wanted-at,result,Stage.InputCount);
                            at+=count;result.CipherBytesRead+=count;
                        }
                        inputHash.AppendData(view[0].Bytes.Slice(0,wanted));
                        Frame(operation,1,parent[0],parent[1],parent[2],wanted);
                        stage=Stage.Command1;result.UpdateAttempts++;
                        uint code=api.Invoke(session,1,operation,out origin);NativeCode(code,origin,result,stage);
                        uint output=operation.Get(32);
                        stage=Stage.UpdateCount;
                        Need(output<=SharedBytes && output<=(ulong)(plan.MaximumRawOutputBytes-result.RawBytesProduced),result,stage);
                        Emit((int)output);
                    } finally {view[0].Clear();view[1].Clear();}
                    remaining-=wanted;
                }
                stage=Stage.InputEof;Span<byte> probe=stackalloc byte[1];
                try {result.ReadCalls++;Need(source.Read(probe)==0,result,stage);result.InputEofObserved=true;}
                finally {CryptographicOperations.ZeroMemory(probe);}
                stage=Stage.InputDigest;
                byte[] digest=inputHash.GetHashAndReset();
                try {Need(CryptographicOperations.FixedTimeEquals(digest,Convert.FromHexString(plan.CipherSha256)),result,stage);result.CipherDigestMatchedAtEof=true;}
                finally {CryptographicOperations.ZeroMemory(digest);}
                stage=Stage.Guard;result.GuardCalls++;guard();
                try {
                    Frame(operation,2,parent[0],parent[1],parent[2]);stage=Stage.Command2;result.FinalAttempts++;
                    uint code=api.Invoke(session,2,operation,out origin);NativeCode(code,origin,result,stage);
                    uint output=operation.Get(20);stage=Stage.FinalCount;
                    Need(output<=SharedBytes && output<=(ulong)(plan.MaximumRawOutputBytes-result.RawBytesProduced),result,stage);
                    Emit((int)output);
                } finally {view[1].Clear();}
                stage=Stage.Guard;result.GuardCalls++;guard();
                stage=Stage.OutputDigest;byte[] finalHash=outputHash.GetHashAndReset();
                try {result.RawEmittedSha512=Convert.ToHexString(finalHash).ToLowerInvariant();result.RawEmittedCrc32=outputCrc^0xffffffff;}
                finally {CryptographicOperations.ZeroMemory(finalHash);}
                bodyComplete=true;

                void Emit(int count) {
                    if(count==0)return;
                    result.MaximumOutputChunk=Math.Max(result.MaximumOutputChunk,count);
                    ReadOnlySpan<byte> chunk=view[1].Bytes.Slice(0,count);
                    result.RawBytesProduced+=count;outputHash.AppendData(chunk);outputCrc=Crc(outputCrc,chunk);
                    stage=Stage.SinkWrite;result.SinkWriteMayHaveOccurred=true;
                    int written=sink.Write(chunk);
                    if(written>0 && written<=count)result.SinkBytesConfirmed+=written;
                    Need(written==count,result,Stage.SinkCount);
                }
            } catch(Stop) { }
            catch(Exception) {
                result.Fail(stage);
                if(stage==Stage.Initialize || stage==Stage.Allocate0 || stage==Stage.Allocate1 || stage==Stage.Allocate2 ||
                   stage==Stage.Session || stage==Stage.Command0 || stage==Stage.Command1 || stage==Stage.Command2)
                    result.BackendExceptionObserved=true;
                if(stage==Stage.Initialize || stage==Stage.Allocate0 || stage==Stage.Allocate1 || stage==Stage.Allocate2 || stage==Stage.Session)
                    result.ResourceOwnershipUncertain=true;
            }
            finally {
                // Match proven reverse cleanup: close session, wipe/release
                // shares2/1/0, finalize context. A cleanup error never replaces
                // an earlier native/source/sink failure or its original code.
                if(opened)try{api.Close(session!);result.SessionClosed=true;}catch{result.CleanupFail(Stage.Close);}
                int wiped=0;
                for(int i=allocated-1;i>=0;i--) {
                    if(i<mapped)try{view[i].Clear();wiped++;}catch{result.CleanupFail(Stage.WipeShared);}
                    try{api.Release(shared[i]!);result.Released++;}catch{result.CleanupFail((Stage)((int)Stage.Release2+(2-i)));}
                }
                if(initialized)try{api.FinalizeContext(context!);result.ContextFinalized=true;}catch{result.CleanupFail(Stage.FinalizeContext);}
                try {
                    CryptographicOperations.ZeroMemory(masterCopy);CryptographicOperations.ZeroMemory(saltCopy);
                    operation?.Dispose();uuid?.Dispose();session?.Dispose();context?.Dispose();
                    for(int i=2;i>=0;i--)shared[i]?.Dispose();
                    result.OwnedBuffersWipeConfirmed=wiped==allocated;
                } catch{result.CleanupFail(Stage.WipeLocal);}
                try{inputHash?.Dispose();}catch{result.CleanupFail(Stage.WipeLocal);}
                try{outputHash?.Dispose();}catch{result.CleanupFail(Stage.WipeLocal);}
            }
            if(bodyComplete && result.FirstFailure==Stage.None) {
                try {result.SinkCompletionAttempted=true;sink.CompleteRaw();result.SinkCompletedRaw=true;}
                catch{result.Fail(Stage.SinkComplete);}
            }
            if(sinkAttempted && !result.SinkCompletedRaw) {
                try{result.SinkAbortAttempted=true;sink.Abort();result.SinkAbortReturned=true;}
                catch{result.CleanupFail(Stage.SinkAbort);}
            }
            return result;
        }
    }
}
