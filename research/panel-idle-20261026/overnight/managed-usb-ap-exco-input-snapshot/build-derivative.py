#!/usr/bin/env python3
"""Generate fixed AP_EXCO snapshot sources from the reviewed O reader."""
from pathlib import Path
import hashlib, json

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/"managed-usb-ap-exco-callback-read"
PINS={"Program.cs":"cc90506197ba2784d0918b5cc9567d7fd78c5bcb10973c6b7bb90870080842be","ManagedUsbRtBlockReadOnce.csproj":"05893d224110307cdce9838c9620aba3ed1326901288ad105279cfc9eed3f187","NuGet.Config":"5256a7e3e07d2c5c94f7a1e6c45f39aab011c659c5e2d53e452dea525ce04575","root-with-margin.py":"bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a","run-once.py":"a7d50ab656c727c2aab080410a1360db27f64051c0b488398eb9836651d0feae","build-manifest.json":"48b202a87cd714dab866a32cb36cb716a65cdec6745519463a346bab9d35f00a"}
def sha(x):return hashlib.sha256(x).hexdigest()
def need(x,m):
 if not x:raise RuntimeError(m)
def one(s,a,b):
 need(s.count(a)==1,"replace "+a[:70]);return s.replace(a,b)
def section(s,a,b,r):
 i=s.index(a);j=s.index(b,i);return s[:i]+r+s[j:]

def program():
 p=(PARENT/"Program.cs").read_text()
 p=one(p,'const int PointerLength = 32, BaseLength = 16, TailLength = 32, TimeoutMs = 2000;','const int PointerLength = 32, OrdinaryLength = 824, DerivedLength = 1004, TimeoutMs = 2000;')
 p=one(p,'static readonly byte[] BaseHeader = Convert.FromHexString("01010000A858014510000000");\n    static readonly byte[] TailHeader = Convert.FromHexString("01010000705C014520000000");','static readonly byte[] OrdinaryHeader = Convert.FromHexString("0101000014FF004538030000");\n    static readonly byte[] DerivedHeader = Convert.FromHexString("01010000A8580145EC030000");')
 p=one(p,'enum ProtocolPhase { ReadyForHeader, ExpectingPointerIn, ExpectingBaseIn, ExpectingTailIn, Unknown }','enum ProtocolPhase { ReadyForHeader, ExpectingPointerIn, ExpectingOrdinaryIn, ExpectingDerivedIn, Unknown }')
 p=one(p,'managed-usb-ap-exco-callback-read-v1','managed-usb-ap-exco-input-snapshot-v1')
 props='''        public string? PointerBase64 { get; set; }
        public string? PointerSha256 { get; set; }
        public string? OrdinaryBase64 { get; set; }
        public string? OrdinarySha256 { get; set; }
        public string? DerivedBase64 { get; set; }
        public string? DerivedSha256 { get; set; }
        public uint? OrdinaryPointer { get; set; }
        public uint? DerivedPointer { get; set; }
        public bool PointerMatches { get; set; }
        public ushort? OrdinaryGateCa { get; set; }
        public ushort? OrdinaryGate116 { get; set; }
        public ushort? OrdinaryX10A { get; set; }
        public ushort? OrdinaryX10C { get; set; }
        public ushort? OrdinaryOutputE6 { get; set; }
        public ushort? OrdinaryOutput2Fc { get; set; }
        public ushort? OrdinaryCounter300 { get; set; }
        public ushort? OrdinaryCounter302 { get; set; }
        public byte? DerivedByteZero { get; set; }
        public byte? DerivedByteOne { get; set; }
        public byte? DerivedByte3D8 { get; set; }
        public bool InterpretationAccepted { get; set; }
        public string Interpretation { get; set; } = "not-decoded";
'''
 p=section(p,'        public string? PointerBase64','        public bool PhysicalPictureObserved',props)
 p=one(p,'byte[] sourceBase = new byte[BaseLength];\n        byte[] sourceTail = new byte[TailLength];','byte[] ordinary = new byte[OrdinaryLength];\n        byte[] derived = new byte[DerivedLength];')
 reads='''            Read("pointer", PointerHeader, pointer, ProtocolPhase.ExpectingPointerIn);
            result.PointerBase64 = Convert.ToBase64String(pointer);
            result.PointerSha256 = Convert.ToHexString(SHA256.HashData(pointer)).ToLowerInvariant();
            result.OrdinaryPointer = BitConverter.ToUInt32(pointer, 4);
            result.DerivedPointer = BitConverter.ToUInt32(pointer, 12);
            result.PointerMatches = result.OrdinaryPointer == 0x4500FF14u && result.DerivedPointer == 0x450158A8u;
            Need(result.PointerMatches, "pointer anchors mismatch");
            Read("ordinary", OrdinaryHeader, ordinary, ProtocolPhase.ExpectingOrdinaryIn);
            result.OrdinaryBase64 = Convert.ToBase64String(ordinary);
            result.OrdinarySha256 = Convert.ToHexString(SHA256.HashData(ordinary)).ToLowerInvariant();
            result.OrdinaryGateCa = BitConverter.ToUInt16(ordinary, 0xCA);
            result.OrdinaryGate116 = BitConverter.ToUInt16(ordinary, 0x116);
            result.OrdinaryX10A = BitConverter.ToUInt16(ordinary, 0x10A);
            result.OrdinaryX10C = BitConverter.ToUInt16(ordinary, 0x10C);
            result.OrdinaryOutputE6 = BitConverter.ToUInt16(ordinary, 0xE6);
            result.OrdinaryOutput2Fc = BitConverter.ToUInt16(ordinary, 0x2FC);
            result.OrdinaryCounter300 = BitConverter.ToUInt16(ordinary, 0x300);
            result.OrdinaryCounter302 = BitConverter.ToUInt16(ordinary, 0x302);
            Read("derived", DerivedHeader, derived, ProtocolPhase.ExpectingDerivedIn);
            result.DerivedBase64 = Convert.ToBase64String(derived);
            result.DerivedSha256 = Convert.ToHexString(SHA256.HashData(derived)).ToLowerInvariant();
            result.DerivedByteZero = derived[0]; result.DerivedByteOne = derived[1]; result.DerivedByte3D8 = derived[0x3D8];
            result.InterpretationAccepted = true;
            result.Interpretation = "pointer-gated-sequential-object-snapshot";
'''
 p=section(p,'            Read("pointer", PointerHeader, pointer, ProtocolPhase.ExpectingPointerIn);','            result.Stage = "complete";',reads)
 p=one(p,'result.PointerBase64 != null && result.BaseBase64 != null && result.TailBase64 != null &&','result.PointerBase64 != null && result.OrdinaryBase64 != null && result.DerivedBase64 != null &&')
 p=one(p,'Need(input ? data.Length == PointerLength || data.Length == BaseLength || data.Length == TailLength :\n                data.AsSpan().SequenceEqual(PointerHeader) || data.AsSpan().SequenceEqual(BaseHeader) ||\n                data.AsSpan().SequenceEqual(TailHeader), "fixed transfer only");','Need(input ? data.Length == PointerLength || data.Length == OrdinaryLength || data.Length == DerivedLength :\n                data.AsSpan().SequenceEqual(PointerHeader) || data.AsSpan().SequenceEqual(OrdinaryHeader) ||\n                data.AsSpan().SequenceEqual(DerivedHeader), "fixed transfer only");')
 p=one(p,'public int[] BulkReturns = { 12, PointerLength, 12, BaseLength, 12, TailLength };','public int[] BulkReturns = { 12, PointerLength, 12, OrdinaryLength, 12, DerivedLength };')
 p=one(p,'public uint PointerValue = 0x450158A8u;\n        public byte ByteZero = 3, ByteOne = 7, Byte3D8 = 1;','public uint OrdinaryPointer = 0x4500FF14u, DerivedPointer = 0x450158A8u;')
 p=one(p,'0 => "pointer-out", 1 => "pointer-in", 2 => "source-base-out",\n                3 => "source-base-in", 4 => "source-tail-out", 5 => "source-tail-in",','0 => "pointer-out", 1 => "pointer-in", 2 => "ordinary-out",\n                3 => "ordinary-in", 4 => "derived-out", 5 => "derived-in",')
 old='''                if (index == 1) BitConverter.GetBytes(PointerValue).CopyTo(data, 0x0C);
                if (index == 3) { data[0] = ByteZero; data[1] = ByteOne; }
                if (index == 5) data[0x10] = Byte3D8;'''
 new='''                if (index == 1) { BitConverter.GetBytes(OrdinaryPointer).CopyTo(data, 4); BitConverter.GetBytes(DerivedPointer).CopyTo(data, 12); }
                if (index == 3) { BitConverter.GetBytes((ushort)1).CopyTo(data, 0xCA); BitConverter.GetBytes((ushort)1).CopyTo(data, 0x116); BitConverter.GetBytes((ushort)9).CopyTo(data, 0x10A); BitConverter.GetBytes((ushort)10).CopyTo(data, 0x10C); BitConverter.GetBytes((ushort)1).CopyTo(data, 0xE6); BitConverter.GetBytes((ushort)2).CopyTo(data, 0x2FC); BitConverter.GetBytes((ushort)7).CopyTo(data, 0x300); BitConverter.GetBytes((ushort)8).CopyTo(data, 0x302); }
                if (index == 5) { data[0] = 3; data[1] = 10; data[0x3D8] = 1; }'''
 p=one(p,old,new)
 p=one(p,'0 => PointerHeader, 2 => BaseHeader, 4 => TailHeader,','0 => PointerHeader, 2 => OrdinaryHeader, 4 => DerivedHeader,')
 start='''        Outcome success = Run(new FakeOps());''';end='''        Case("open-fail",'''
 tests='''        Outcome success = Run(new FakeOps());
        Need(success.Accepted && success.InterpretationAccepted && success.PointerMatches &&
             success.OrdinaryPointer == 0x4500FF14u && success.DerivedPointer == 0x450158A8u &&
             success.OrdinaryGateCa == 1 && success.OrdinaryGate116 == 1 && success.OrdinaryX10A == 9 && success.OrdinaryX10C == 10 &&
             success.OrdinaryOutputE6 == 1 && success.OrdinaryOutput2Fc == 2 && success.OrdinaryCounter300 == 7 && success.OrdinaryCounter302 == 8 &&
             success.DerivedByteZero == 3 && success.DerivedByteOne == 10 && success.DerivedByte3D8 == 1 &&
             Convert.FromBase64String(success.PointerBase64!).Length == PointerLength && Convert.FromBase64String(success.OrdinaryBase64!).Length == OrdinaryLength &&
             Convert.FromBase64String(success.DerivedBase64!).Length == DerivedLength && success.Steps.Count == 10, "success"); tests++;
        Outcome mismatch = Run(new FakeOps { OrdinaryPointer = 0x12345678u });
        Need(!mismatch.Accepted && mismatch.PointerBase64 != null && mismatch.OrdinaryBase64 == null &&
             !mismatch.Steps.Exists(x => x.Name == "ordinary-header"), "ordinary pointer gate"); tests++;
        mismatch = Run(new FakeOps { DerivedPointer = 0x12345678u });
        Need(!mismatch.Accepted && mismatch.PointerBase64 != null && mismatch.DerivedBase64 == null &&
             !mismatch.Steps.Exists(x => x.Name == "ordinary-header"), "derived pointer gate"); tests++;
        Outcome baseShort = Run(new FakeOps { BulkReturns = new[] { 12, PointerLength, 12, OrdinaryLength - 1, 12, DerivedLength } });
        Need(!baseShort.Accepted && baseShort.PointerBase64 != null && baseShort.OrdinaryBase64 == null && baseShort.DerivedBase64 == null, "pointer retained"); tests++;
        Outcome tailShort = Run(new FakeOps { BulkReturns = new[] { 12, PointerLength, 12, OrdinaryLength, 12, DerivedLength - 1 } });
        Need(!tailShort.Accepted && tailShort.PointerBase64 != null && tailShort.OrdinaryBase64 != null && tailShort.DerivedBase64 == null, "prior retained"); tests++;
'''
 p=section(p,start,end,tests)
 p=p.replace('int[] exacts = { 12, PointerLength, 12, BaseLength, 12, TailLength };','int[] exacts = { 12, PointerLength, 12, OrdinaryLength, 12, DerivedLength };')
 p=p.replace('0 => "pointer-in", 1 => "source-base-out", 2 => "source-base-in",\n                    3 => "source-tail-out", 4 => "source-tail-in", _ => null','0 => "pointer-in", 1 => "ordinary-out", 2 => "ordinary-in",\n                    3 => "derived-out", 4 => "derived-in", _ => null')
 p=p.replace('"source-base-out"', '"ordinary-out"').replace('"source-base-in"', '"ordinary-in"')
 p=p.replace('"source-tail-out"', '"derived-out"').replace('"source-tail-in"', '"derived-in"')
 p=one(p,'Convert.ToHexString(BaseHeader) == "01010000A858014510000000" &&\n             Convert.ToHexString(TailHeader) == "01010000705C014520000000"','Convert.ToHexString(OrdinaryHeader) == "0101000014FF004538030000" &&\n             Convert.ToHexString(DerivedHeader) == "01010000A8580145EC030000"')
 p=one(p,'schema = "managed-usb-ap-exco-callback-read-dry-v1"','schema = "managed-usb-ap-exco-input-snapshot-dry-v1"')
 p=one(p,'new { address = "0x450158a8", headerHex = Convert.ToHexString(BaseHeader), length = BaseLength },\n                    new { address = "0x45015c70", headerHex = Convert.ToHexString(TailHeader), length = TailLength }','new { address = "0x4500ff14", headerHex = Convert.ToHexString(OrdinaryHeader), length = OrdinaryLength },\n                    new { address = "0x450158a8", headerHex = Convert.ToHexString(DerivedHeader), length = DerivedLength }')
 return p

def wrapper():
 w=(PARENT/"run-once.py").read_text()
 w=one(w,'fixed three-read AP_EXCO helper','fixed AP_EXCO input snapshot')
 w=one(w,'managed-usb-ap-exco-callback-read-build-v1','managed-usb-ap-exco-input-snapshot-build-v1')
 w=one(w,'MAX_NATIVE_STDOUT = 8192','MAX_NATIVE_STDOUT = 16384')
 w=one(w,'ap_exco_source_root_transport','ap_exco_input_snapshot_root_transport')
 w=one(w,'def saved_context_candidate(pointer_matches, byte_zero, byte_3d8):\n    return pointer_matches is True and byte_zero == 3 and byte_3d8 == 1\n\n\n','')
 w=one(w,'{"selfTestsPassed": 47, "targetOperations": 0}','{"selfTestsPassed": 48, "targetOperations": 0}')
 parse='''def parse_native(text):
    rows, gc = parse_lines_with_gc(text)
    need(len(rows) == 1 and isinstance(rows[0], dict), "one native outcome")
    value = rows[0]
    need(value.get("Schema") == "managed-usb-ap-exco-input-snapshot-v1", "native schema")
    need(value.get("Stage") == "complete" and value.get("ProtocolPhase") == "ReadyForHeader", "terminal phase")
    for key in ("Opened", "Claimed", "Released", "Closed", "Accepted", "PointerMatches", "InterpretationAccepted"):
        need(value.get(key) is True, "native " + key)
    need(value.get("PhysicalPictureObserved") is False and value.get("BusContentsAltered") is False, "bounded claims")
    pointer = base64.b64decode(value.get("PointerBase64", ""), validate=True)
    ordinary = base64.b64decode(value.get("OrdinaryBase64", ""), validate=True)
    derived = base64.b64decode(value.get("DerivedBase64", ""), validate=True)
    need(len(pointer) == 32 and sha(pointer) == value.get("PointerSha256"), "pointer raw")
    need(len(ordinary) == 824 and sha(ordinary) == value.get("OrdinarySha256"), "ordinary raw")
    need(len(derived) == 1004 and sha(derived) == value.get("DerivedSha256"), "derived raw")
    op, dp = int.from_bytes(pointer[4:8], "little"), int.from_bytes(pointer[12:16], "little")
    need((op, dp) == (0x4500FF14, 0x450158A8), "pointer anchors")
    u16 = lambda raw, offset: int.from_bytes(raw[offset:offset + 2], "little")
    decoded = {"ordinary_gate_ca": u16(ordinary, 0xCA), "ordinary_gate_116": u16(ordinary, 0x116),
               "ordinary_x_10a": u16(ordinary, 0x10A), "ordinary_x_10c": u16(ordinary, 0x10C),
               "ordinary_output_e6": u16(ordinary, 0xE6), "ordinary_output_2fc": u16(ordinary, 0x2FC),
               "ordinary_counter_300": u16(ordinary, 0x300), "ordinary_counter_302": u16(ordinary, 0x302),
               "derived_byte_zero": derived[0], "derived_byte_one": derived[1], "derived_byte_3d8": derived[0x3D8]}
    fields = (("ordinary_gate_ca", "OrdinaryGateCa"), ("ordinary_gate_116", "OrdinaryGate116"),
              ("ordinary_x_10a", "OrdinaryX10A"), ("ordinary_x_10c", "OrdinaryX10C"),
              ("ordinary_output_e6", "OrdinaryOutputE6"), ("ordinary_output_2fc", "OrdinaryOutput2Fc"),
              ("ordinary_counter_300", "OrdinaryCounter300"), ("ordinary_counter_302", "OrdinaryCounter302"),
              ("derived_byte_zero", "DerivedByteZero"), ("derived_byte_one", "DerivedByteOne"),
              ("derived_byte_3d8", "DerivedByte3D8"))
    for key, native_key in fields: need(value.get(native_key) == decoded[key], "decoded " + key)
    need(value.get("OrdinaryPointer") == op and value.get("DerivedPointer") == dp and
         value.get("Interpretation") == "pointer-gated-sequential-object-snapshot", "interpretation")
    expected = [("open", "LOCAL", 0), ("claim", "LOCAL", 0), ("pointer-header", "OUT", 12),
                ("pointer-data", "IN", 32), ("ordinary-header", "OUT", 12), ("ordinary-data", "IN", 824),
                ("derived-header", "OUT", 12), ("derived-data", "IN", 1004),
                ("release", "LOCAL", 0), ("close", "LOCAL", 0)]
    steps = value.get("Steps"); need(isinstance(steps, list) and len(steps) == 10, "steps")
    for row, (name, direction, count) in zip(steps, expected):
        need(row.get("Name") == name and row.get("Direction") == direction and row.get("Expected") == count and
             row.get("Error") is None, "step " + name)
        if direction in ("OUT", "IN") or name in ("claim", "release", "close"):
            need(row.get("Count") == count and row.get("Errno") == 0, "exact " + name)
        else: need(isinstance(row.get("Count"), int) and row.get("Count") >= 0 and row.get("Errno") == 0, "open")
    return value, pointer, ordinary, derived, decoded, gc


'''
 w=section(w,'def parse_native(text):','def parse_envelope(text):',parse)
 need(w.count('{"target": "0x101", "address": "0x450158a8", "length": 16}')==2,"base request blocks")
 need(w.count('{"target": "0x101", "address": "0x45015c70", "length": 32}')==2,"tail request blocks")
 w=w.replace('{"target": "0x101", "address": "0x450158a8", "length": 16}',
             '{"target": "0x101", "address": "0x4500ff14", "length": 824}')
 w=w.replace('{"target": "0x101", "address": "0x45015c70", "length": 32}',
             '{"target": "0x101", "address": "0x450158a8", "length": 1004}')
 w=one(w,'managed-usb-ap-exco-callback-wrapper-dry-v1','managed-usb-ap-exco-input-snapshot-wrapper-dry-v1')
 w=one(w,'managed-usb-ap-exco-callback-wrapper-record-v1','managed-usb-ap-exco-input-snapshot-wrapper-record-v1')
 w=one(w,'/tmp/researcher-ap-exco-callback-','/tmp/researcher-ap-exco-input-')
 w=one(w,'native, pointer, source_base, source_tail, gc = parse_native(native_stdout.decode("utf-8"))\n    (args.output / "pointer-window.bin").write_bytes(pointer)\n    (args.output / "callback-base-window.bin").write_bytes(source_base)\n    (args.output / "callback-tail-window.bin").write_bytes(source_tail)','native, pointer, ordinary, derived, decoded, gc = parse_native(native_stdout.decode("utf-8"))\n    (args.output / "pointer-window.bin").write_bytes(pointer)\n    (args.output / "ordinary-ap-exco-prefix.bin").write_bytes(ordinary)\n    (args.output / "derived-ap-exco.bin").write_bytes(derived)')
 result='''    result = {"schema": "managed-usb-ap-exco-input-snapshot-wrapper-result-v1",
              "transport_accepted": True, "interpretation_accepted": True,
              "interpretation": native["Interpretation"], "manifest_sha256": sha(manifest_raw),
              "record": str(record_path), "pointer_raw_sha256": sha(pointer), "pointer_raw_length": len(pointer),
              "ordinary_raw_sha256": sha(ordinary), "ordinary_raw_length": len(ordinary),
              "derived_raw_sha256": sha(derived), "derived_raw_length": len(derived),
              "ordinary_pointer_raw": native["OrdinaryPointer"], "derived_pointer_raw": native["DerivedPointer"],
              "pointer_matches_expected": True, "decoded": decoded,
              "derived_composite_recomputed": bool((decoded["ordinary_output_e6"] & 1) or decoded["ordinary_output_2fc"]),
              "derived_composite_matches": decoded["derived_byte_3d8"] == int(bool((decoded["ordinary_output_e6"] & 1) or decoded["ordinary_output_2fc"])),
              "samples_sequential_not_atomic": True, "event_time_inferred": False,
              "physical_cause_inferred": False, "native_gc_lines": len(gc),
              "cleanup": "STAGE_ABSENT", "bus_contents_altered": False, "physical_picture_observed": False}
'''
 w=section(w,'    pointer_matches = native["PointerMatches"] is True\n','    save(args.output / "result.json", result)',result)
 return w

def main():
 for n,d in PINS.items():need(sha((PARENT/n).read_bytes())==d,"parent pin "+n)
 for n in ("ManagedUsbRtBlockReadOnce.csproj","NuGet.Config","root-with-margin.py"):(HERE/n).write_bytes((PARENT/n).read_bytes())
 (HERE/"Program.cs").write_text(program());(HERE/"run-once.py").write_text(wrapper())
 print(json.dumps({"schema":"ap-exco-input-snapshot-derivation-v1","parentManifest":PINS["build-manifest.json"],"targetOperations":0},separators=(",",":")))
if __name__=="__main__":main()
