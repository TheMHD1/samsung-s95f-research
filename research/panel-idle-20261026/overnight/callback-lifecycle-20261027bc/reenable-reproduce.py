#!/usr/bin/env python3
"""Offline positive checks for selected-image descriptor-8 IRQ lifecycle."""
import hashlib, json, struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
PACKAGE_SHA = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
BA = OVERNIGHT / "mute-request-consumer-20261027ba/staged-consumer.md"
BA_SHA = "7e3b2a3b25360f022af1399b166afb9413bef698ca1bf579e2f36d0d929ee7a2"

def need(ok, why):
    if not ok: raise ValueError(why)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def u32(raw, at): return struct.unpack_from("<I", raw, at)[0]
def sx(value, bits):
    sign=1 << (bits-1); return (value ^ sign)-sign
def bl_target(image, at):
    if at < 0 or at+4 > len(image) or at&1: return None
    a,b=struct.unpack_from("<HH",image,at)
    if a&0xf800 != 0xf000 or b&0xd000 != 0xd000: return None
    s=(a>>10)&1; j1=(b>>13)&1; j2=(b>>11)&1
    i1=1^(j1^s); i2=1^(j2^s)
    encoded=(s<<24)|(i1<<23)|(i2<<22)|((a&0x3ff)<<12)|((b&0x7ff)<<1)
    return at+4+sx(encoded,25)
def callers(image, target):
    return [at for at in range(0,len(image)-3,2) if bl_target(image,at)==target]

package=PACKAGE.read_bytes()
need(len(package)==5_242_880 and sha(package)==PACKAGE_SHA,"package identity")
need(sha(BA.read_bytes())==BA_SHA,"BA source identity")
image=package[0x200:0x40200]
need(len(image)==0x40000,"image0 extent")

slices={
 "registration_enclosing":(0x1e47c,0x1eb36,"318d15a1c1cb53a00219e72b355f297ca210e4e141c4b64ea5b6db97b6d6eadf"),
 "startup_call_context":(0x39b60,0x39bb0,"1d588034fe1142f5a5cf29e460295cb9eb8ff55525f0df6ae1b7d94c1ace2a22"),
 "descriptor8_callback":(0x132c0,0x13346,"2e472ef163d2a285a67628abaef6195cdc824f781654e471f4e9659eb51e7a25"),
 "descriptor1c_callback":(0x13464,0x1375a,"ceb2219987046cb185913963cda6583abc9822e845ddbfdab30053f50c735d5f"),
 "reenable_gate":(0x134ac,0x13552,"1eda93f58a7aaa3a35f4d9f891e6f2f97321f17e7f5a2c48aac38c4754b999d6"),
 "descriptor_claim":(0x13aa8,0x13ad6,"4f160a140ffebfdcc7a428da7829be6c682cf040a35167439cf25bf50c0a11fa"),
 "descriptor_lookup":(0x38c24,0x38c38,"287a309773f5f64fae4fac7d201097180674aa4480a6dd708fe5d84afc204df6"),
 "clear_pending":(0x1b024,0x1b03c,"91c14e2a69ee54b1a85f6ca9fba1b7004f0c9178c21cd2e2f363852488f9d02f"),
 "disable_variant":(0x1b0b8,0x1b0d0,"6d4da6c2ee0a19e412c80eba27610a4c0040d66bae19a1a1222c5910c7ad294a"),
 "fault_disable":(0x1b0e8,0x1b100,"6d4da6c2ee0a19e412c80eba27610a4c0040d66bae19a1a1222c5910c7ad294a"),
 "enable":(0x1b16e,0x1b184,"a4940f4a39907bf72dcf887e531703a4c0b564813da44480efc432e5b0bae667"),
 "fault_teardown":(0x96d8,0x9746,"9bdc29f2519b7a6ac90e2e3bc5fea5054249f4218d6b99d8591f454e6f4a212d"),
}
for name,(start,end,want) in slices.items(): need(sha(image[start:end])==want,"slice: "+name)

# Startup invokes the sole direct registration body caller.
need(bl_target(image,0x39b8e)==0x1e47c,"startup registration call")
need(callers(image,0x1e47c)==[0x39b8e],"finite direct registration callers")

# Descriptor 8 claim, lookup, saved pointer, and callback installation.
need(image[0x1e702:0x1e704]==bytes.fromhex("0820"),"descriptor8 index")
need(bl_target(image,0x1e704)==0x13aa8 and bl_target(image,0x1e70c)==0x38c24,"claim/lookup")
need(u32(image,0x1e8a0)==0x20000884 and u32(image,0x1e8a4)==0x132c1,"descriptor8 literals")
need(image[0x1e712:0x1e714]==bytes.fromhex("0860") and image[0x1e79c:0x1e79e]==bytes.fromhex("8860"),"saved pointer/callback stores")

# Descriptor 0x1c receives callback 0x13465 and is itself enabled at startup.
need(image[0x1e7aa:0x1e7ac]==bytes.fromhex("1c20") and bl_target(image,0x1e7ac)==0x38c24,"descriptor1c lookup")
need(u32(image,0x1e8a8)==0x13465 and image[0x1e7f6:0x1e7fa]==bytes.fromhex("2c48a060"),"descriptor1c callback store")
need(bl_target(image,0x1e7fe)==0x1b024 and bl_target(image,0x1e806)==0x1b16e,"descriptor1c startup clear/enable")

# Descriptor 8's own callback disables the saved descriptor IRQ, then clears
# pending at completion, but the disable/work is only on its bit3=1 branch.
need(image[0x132ca:0x132d6]==bytes.fromhex("20680068c0f3c000002832d0"),"descriptor8 bit3 gate")
need(u32(image,0x13350)==0x20000884,"saved descriptor literal in callback")
need(bl_target(image,0x132ee)==0x1b0b8 and bl_target(image,0x13340)==0x1b024,"descriptor8 callback disable/clear")

# The distinct descriptor-0x1c callback gates on its descriptor word bit 3.
# Two separate loads must each observe 0x2000087c nonzero; either zero path
# primes 0x2000087c to one and returns. The continuing branch separately
# clears 0x2000087e before reaching the saved-pointer test.
need(image[0x134ac:0x134b6]==bytes.fromhex("38680068c0f3c0000028"),"descriptor1c bit3 gate")
need(u32(image,0x1375c)==0x2000087c and u32(image,0x13760)==0x2000087e and
     u32(image,0x13770)==0x20000884,"state/saved-pointer literals")
need(image[0x134c2:0x134c8]==bytes.fromhex("a648007890b9") and
     image[0x134ee:0x134f4]==bytes.fromhex("9b48007818b9"),"two 0x2000087c reads/gates")
need(image[0x134fc:0x13502]==bytes.fromhex("002098490870"),"separate 0x2000087e clear")
need(image[0x1351e:0x13524]==bytes.fromhex("94480068b0b1"),"saved pointer null gate")
need(bl_target(image,0x13542)==0x1b024 and bl_target(image,0x1354e)==0x1b16e,"ordinary handoff clear/enable")
need(callers(image,0x13464)==[],"descriptor1c callback has no direct BL callers")
need(callers(image,0x132c0)==[],"descriptor8 callback has no direct BL callers")

# Exact NVIC-class register families: ICER, ICPR, and ISER respectively.
need(u32(image,0x1b0cc)==0xe000e180 and u32(image,0x1b0fc)==0xe000e180,"disable bases")
need(u32(image,0x1b038)==0xe000e280,"clear-pending base")
need(image[0x1b17a:0x1b182]==bytes.fromhex("02f1e022c2f80011"),"enable e000e100 calculation/write")

# Fault teardown disables the owner descriptor 0x1c first, then descriptor 8.
need(image[0x96e4:0x96e6]==bytes.fromhex("1c20") and bl_target(image,0x96e6)==0x38c24 and bl_target(image,0x96f0)==0x1b0e8,"fault descriptor1c disable")
need(image[0x9724:0x9726]==bytes.fromhex("0820") and bl_target(image,0x9726)==0x38c24 and bl_target(image,0x9730)==0x1b0e8,"fault descriptor8 disable")

print(json.dumps({
 "accepted":True,"package_sha256":PACKAGE_SHA,"coordinate_model":"image0 FILE = VA + 0x200",
 "registration":{"body":"0x1e47c..0x1eb35","sole_direct_caller":"0x39b8e","descriptor8_saved_pointer":"0x20000884","descriptor8_callback":"0x132c1","claim_failure_checked_before_lookup":False},
 "descriptor8_callback":{"body":"0x132c0..0x13345","gate":"descriptor word bit3=1 enters disable/work; bit3=0 skips to completion clear","bit3_one_action":"saved IRQ -> ICER-class disable via 0x1b0b8","completion":"saved IRQ -> ICPR-class clear via 0x1b024","self_reenable_in_body":False},
 "ordinary_handoff_enable":{"owner_callback":"descriptor 0x1c callback 0x13465","owner_enabled_during_registration":True,"gates":["descriptor0x1c word bit3 = 1","two separate loads each observe CPU 0x2000087c nonzero","saved descriptor8 pointer nonzero"],"pre_action_separate_store":"CPU 0x2000087e = 0","actions":["descriptor8 pending clear via 0x1b024","descriptor8 enable via 0x1b16e"]},
 "fault_teardown":{"first_relevant_disable":"descriptor0x1c IRQ -> ICER-class 0x1b0e8","later_disable":"descriptor8 IRQ -> ICER-class 0x1b0e8"},
 "interpretation":"selected-code positive ordinary handoff edge, not a proved post-fault recovery because teardown disables its descriptor0x1c owner too; no live execution, IRQ state, or physical-effect proof",
 "slice_sha256":{name:row[2] for name,row in slices.items()},"target_operations":0
},indent=2,sort_keys=True))
