# RTP input buffer selector and software producer closure

**The two dispatcher inputs have a positive software producer chain, but the physical aperture producer and input epochs remain unresolved.** Image1 `0x18ce0` is a complete, callee-free slot selector. Image1 `0x18ae8` copies two descriptor-selected aperture regions into a three-slot SRAM ring using the real CPU copy routine `0x334`. Refresh `0x3934` prepares the two descriptors from an old scratch tail and a new, conditionally filtered register sample. This work adds an exact selector closure, independently executes the producer/copy closure, and qualifies the descriptor filtering and read boundaries. DF already established the broad producer/slot-age chain; EJ already established the timer callback registration. Those findings are cited rather than claimed as new discoveries.

No TV, root transport, network, helper deployment, physical memory access, firmware installation or public export was performed. The isolated emulator executes selected instructions against synthetic host memory only. Original firmware bytes are read in place and are not copied here.

## Source identity and reproduction

Selected package: `selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`, 5,242,880 bytes, SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. All instruction addresses below are **image1 linked VAs**, mapped to package file offset `VA+0x40200`. Image0 CPU addresses must remain a separate domain. `validation.normal.json` pins 11 bounded source spans, predecessor reports, and the retained Capstone5.0.7/Unicorn2.1.4 module/native-library files used. No new tool installation was needed.

Run from this directory with the retained dependencies already present:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B audit.py > validation.normal.json
PYTHONDONTWRITEBYTECODE=1 python3 -B -O audit.py > validation.optimized.json
```

The normal and optimized outputs are byte-identical. Explicit checks remain enabled under `-O`. The finite runs include 1,024 real-selector cases, three full real software-producer/copy cases, 20 source-address-prefix cases stopped before copying, six partial refresh cases, and ten real mapper cases. The refresh cases stub only `0xbb58`, the profile-parameter copy; they therefore establish the tested descriptor path conditional on that stub, not an entire refresh environment. Other tests run the specified actual instruction closure, including getters where used. These are host qualification results, not observed controller invocations.

## Complete selector and conditional slot-age relation

The full selector occupies `0x18ce0..0x18d18`, followed by literal `0x18d18=CPU0x20253000`. It reads the byte at that address and returns:

```text
CPU0x20253002 + ((u8(rawIndex) + (tag==0 ? 1 : 0)) % 3) * 0xb68
```

All nonzero 32-bit tags select the same branch; tag1 is not a distinct hardware channel. The tag0 increment occurs after widening the byte: raw255 becomes256 before modulo. The function has no callees, nonstack stores, or aperture access. The three slot headers are `0x20253002`, `0x20253b6a`, `0x202546d2`; each has eight header bytes followed by `0xb60` payload bytes. The three-slot extent ends at `0x2025523a`, exclusive.

Dispatcher `0xb80c..0xb81e` calls with tags1/0 and stores dynamic A/B slot pointers at CPU`0x20000494/498`. A bounded halfword BL candidate index also finds calls at `0xb67a`, `0xc4fa`, `0x18c02`, `0x18c0a`, `0x19822`, `0x199a4`, `0x1bfda`. These are positive syntactic edges, not a complete reachable call graph or exclusion of computed/cross-core callers.

## CPU copy, source arithmetic, and remaining hardware boundary

Producer `0x18ae8..0x18c14` loops over descriptor bases CPU`0x2000a60c` and `0x2000a616` (stride10 decimal). It computes:

```text
source = (0x60000000 + u8(descriptor+2)*0x1950000
                        + s16(descriptor+6)*0xc00) mod 2^32
```

At `0x18b3a/3c` it passes count`0x5b` to real routine`0x334..0x368`, which copies eight u32 per iteration: `91*32=2912=0xb60` bytes. This is a positive CPU-load/store producer for the software ring; it does not explain who fills the aperture. No channel/row/source-range guard appears in this bounded producer. The 20 stopped-prefix cases include signed negative rows and channel255, so the formula must not be repurposed as a safe live aperture-read recipe. Channel/row units and physical validity are unknown.

For each iteration the payload copy precedes header stores: header+0=loop index, +1=boolean descriptor byte0, +2=descriptor channel, +4=descriptor u16+4, +6=descriptor u16+6. Header byte3 is not written by this body. The raw selector is used for the first destination, then incremented modulo3 after each copy. The full-copy cases assume initial selector0..2; the body does not normalize an arbitrary initial byte before its first destination write. The getter returning a valid pointer therefore does not prove the producer had a valid initial selector.

Conditional on a serialized call beginning at index i, it writes slots i and i+1, leaves selector i+2, and an immediate tag1/tag0 lookup yields remaining slot i+2 and first-written slot i. The most recently written slot i+1 is neither lookup. The final two lookups inside the producer put those addresses in temporary r7/r6, then the epilogue restores those callee-saved registers; this is not a publication of the dispatcher's pointer variables. Actual callback/dispatcher interleaving and slot consistency remain unobserved.

## Descriptor refresh: old versus filtered current metadata

Let D=CPU`0x2000a60a`. Refresh`0x3934` first copies old scratch bytes D+0x16..0x1d into D+4..0x0b. It then samples these **source register constants**, without proposing live MMIO reads:

| Source word | Retained destination / narrowing |
|---|---|
|`0x58601408`|low8 at D+0x2a|
|`0x5860140c`|low8 channel at D+0x16|
|`0x58601410`|low16 at D+0x18|
|`0x58601414`|signed16 bits at D+0x1a, used as source row|
|`0x5860146c`|low16 auxiliary at D+0x1c|

At `0x3a12..0x3a52`, the conjunction C8==3, provider byte+1!=10, saved D+0x1e>=1440, sampled channel==2, and saved D+0x1e==sampled D+0x18 sets D+0x2b=1 and clears channel/value/row. The auxiliary halfword remains. At `0x3a54..0x3a62`, the resulting scratch tail is copied into D+0x0e..0x15. Thus descriptor0's channel/value/row at D+4/+6/+8 describe the **old** scratch tail, while descriptor1's D+0x0e/+0x10/+0x12 describe the **filtered current** tail. Neither is an untouched, atomic register snapshot. D+0x2b is also consumed into D+0x2f at the next refresh.

Wrapper`0x18c94` calls refresh, requires C8==3 and (D+0x2a or D+0x2b), conditionally initializes state, then calls change-marker`0x18d84` and producer`0x18ae8`. The marker compares D+0x18 against saved D+0x1e or pending D+0x2b, writes descriptor0 flag D+2, and updates D+0x1e. On the wrapper's inactive branch D+0, D+2 and D+0x0c are cleared. Initialization`0x18d1c` invokes the existing zero routine with D/0x30 and resets selector/header state. No stock MODE2 execution of these particular bodies is established.

EJ's already proven callback chain installs Thumb`0x18c95` at CPU`0x2000046c`, with configured root240c copied into CPU468, and calls it indirectly at`0x195a8`. Registration and source eligibility do not establish runtime period, invocation count or ordering against comparison. The provider/C7/C8 chain remains the separately reviewed AP_EXCO context copy; no persisted/high-bank operation path was followed here.

## Final A and diagnostic arrays remain distinct

Dispatcher `0xb82c..0xb88a` can skip processing when reference counter CPU4c4 is nonzero. Otherwise C7 plus **actual B header+6** selects top/bottom fixed A payload CPU`0x20015000/15f10`; the ordinary branch uses dynamic A+8. B is selected dynamic B+8. Existing P shows the stored dynamic slots, not final A. Routine`0x1c12c` can copy B+8 into a fixed reference and advances/resets the reference counter under its separate conditions. There is no new alias from these slots to the X/Y/RGB/B/Diff diagnostic arrays, H aggregate, N ordinal, RTP root or event ring proven here. A numeric resemblance or zero count is insufficient.

## Smallest next observations and stop boundary

`fixed-read-proposal.json` specifies a **design-only** seven-pair sequence R/M/C/D-before/P/D-after/R. D48 at bus`0x4700a60a` is already a fixed DM read; P16 at`0x47000490` is already a fixed DF/onset read. The real tag1 mapper`0x1bb74` accepts these low-SRAM ranges and rejects CPU`0x20253000/02`. The high ring must not be assigned a guessed`0x4725...` alias. No new MMIO/aperture/header dereference is proposed.

D-before/P/D-after can reveal changed descriptor metadata around selected slots. Equal D does not exclude a producer lap, ABA change, interrupted copy or mixed slot header/payload. It does not supply an input timestamp or actual B header. The minimal metadata-only proposal excludes N/H; a separate reviewed eight-read onset family could replace diagnostic L with D and retain P/N/H to correlate metadata changes with publication, with truthful partial-cycle/deadline accounting. No frozen recorder is changed. Seven/two-second pairs have a 28-second bulk budget; eight pairs have32. Those arithmetic bounds are not a completed helper admission or proof all operations fit under an outer deadline.

The next evidence boundary is the aperture's physical writer/commit protocol, a source-qualified high-ring/header read mapping, and actual final-A/epoch provenance. D/P can improve discrimination without claiming to close that boundary. This task stops at the concrete descriptor registers and software ring; indirect/DMA/cross-core writers and computed aliases are not exhaustively excluded. Publication censoring remains separately qualified by GN. Global R+0x10=4 and RTP category1 remain distinct namespaces per GR; no global-mode1 claim is added.
