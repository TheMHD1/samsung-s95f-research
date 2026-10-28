# Fixed RTP reference qualification — DR

2026-10-28. Frozen host-only source qualification and proposed read plan. No TV, root client, USB, MMIO, OEM execution, or deployment was performed by this work. The only executable additions are pure host models and retained-file checks.

The fixed references are **packed 12-bit sample streams**, with four lanes in six bytes. They are not linear arrays of u16 amplitudes. Their bases point directly to payload; they have no retained eight-byte ring header. Therefore the initially suggested linear-u16 windows at bus `0x47015470` and `0x47016380` do not select the requested candidate samples.

## Exact source and indexing

The selected official 5 MiB package is the same asset already qualified by DF and DE: SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. Image1 file offset is VA+0x40200. [qualification.json](qualification.json) records full source range hashes, decisive instruction bytes, literal values, and input hashes. This proves selected-asset semantics, not whole running-image identity.

At image1 VA0xbd58 the pushed r0/r1 arguments remain available at the new sp+0xf1c/+0xf20. VA0xbe3a..0xbe46 forms `A+byte_offset` in r7 and `B+byte_offset` in r8. The B stream is unpacked at0xbe4a..0xbe88; corresponding A operands are extracted at0xbed4..0xbedc,0xbf0c..0xbf18,0xbf3c..0xbf5a and0xbf8a..0xbf90. For little-endian `word=u32[p]`, `tail=u16[p+4]`, the four values are:

```
lane0 = word & 0xfff
lane1 = (word >> 12) & 0xfff
lane2 = (word >> 24) | ((tail & 15) << 8)
lane3 = tail >> 4
```

VA0xbf98 increments the lane index by4;0xbf9a..0xbf9e increments the byte offset by6. VA0xbfa2..0xbfa8 compares that offset against u16[CPU0x200004a6]. The retained M reports2880 packed bytes and1920 lanes. At VA0xbbc0..0xbbc4, comparator arguments are A, B, lane index. Its formatter calls carry B, lane, row metadata, channel metadata, absolute difference, type. VA0xc652..0xc666 publishes `x=(lane+u16[CPU0x200004c0])&0xffff`. Thus inversion is `lane=(x-xBase)&0xffff`, followed by a strict lane<1920 check. Actual DM xBase is0. No channel-dependent offset is added to either A or B in this unpacker. RGB is a separate formatter metadata argument; its name is not proof of physical pixel/channel meaning.

| Captured x / lane | Packed group | Within group | Conditional reconstructed A |
| --- | ---: | --- | ---: |
| 570,571 | 142 | 2,3 | 1861 |
| 622,623 | 155 | 2,3 | 550 |
| 624,625 | 156 | 0,1 | 3052 |
| 632,633 | 158 | 0,1 | 1718 |

The first41 retained rows have y2159, RGB0, B<500 and diff>500. Under the explicit same-epoch/type1/12-bit-input premise, A cannot be B−diff because it would be negative; B+diff gives exactly the table above across the prefix. The arrays have no type/epoch tags and may retain stale data. This computation does not establish the premise.

## Fixed bases, lifecycle, and branch conditions

VA0xb84a loads literal[0xb8a0]=CPU0x20015000 for the first-row branch. VA0xb872 loads literal[0xb8a4]=CPU0x20015f10 for the terminal-row branch. B is passed as its selected ring pointer+8; fixed A is passed **without** +8. The dispatcher first saves dynamic pointers and may call0x1c12c when actual B header byte+1 is nonzero. After that call, u16[CPU0x200004c4] must be zero or the dispatcher skips all comparison. With zero counter, C+7 nonzero and **actual B header u16+6==0** select top. Actual B header u16+6==u16[C+0]−1 and C+7 nonzero select bottom. Other rows, or zero C+7, use dynamic A. Source row/channel arguments are separately propagated; a later M row mirror or D descriptor is not the actual B header at the branch.

Snapshot writer VA0x1c12c requires counter4c4 nonzero and C+7 nonzero. For actual B header row0 or terminal row, it increments the counter and calls raw byte copy0x70c with destination fixed top/bottom, source B+8 and length0xb60 (2912). It resets the counter when it exceeds2. The inspected raw-copy paths at0x752..0x75c and0x79e..0x7ac preserve byte order and contain no unpacking. This overwrites the same destination without a channel tag; no per-RGB subdivision is shown. Caller/header/counter timing determines snapshot age and identity. Neither fixed buffer has a source-proven embedded header.

Fixed payload extents are top CPU[0x20015000,0x20015b60) and bottom[0x20015f10,0x20016a70). The ordinary unpack span is only their first2880 bytes; the last32 copied bytes are not extra ordinary lanes. Selected image1 address translator VA0x1bb9c..0x1bbc4 maps CPU[0x20000000,0x20020000) by adding0x27000000. These windows remain wholly inside that low-SRAM source mapping. No alias for dynamic ring CPU0x20253002, aperture0x60000000, or unrelated MMIO is introduced.

## Qualified windows and exact read headers

The proposed narrow choice uses one104-byte window per fixed buffer: groups142..158 contain lanes568..635 in102 bytes, plus two ignored tail bytes to keep both address and length four-byte aligned. This is a small group-complete aligned window, not a claim of absolute byte-minimal transport. A120-byte option gives exactly20 complete groups/lanes568..647. Future code must select one variant at build time, not expose address/length arguments.

| Choice | CPU start | Bus start | Bytes | Target0x101 header, little endian |
| --- | --- | --- | ---: | --- |
| narrow top | 0x20015354 | 0x47015354 | 104 | `010100005453014768000000` |
| narrow bottom | 0x20016264 | 0x47016264 | 104 | `010100006462014768000000` |
| broad top | 0x20015354 | 0x47015354 | 120 | `010100005453014778000000` |
| broad bottom | 0x20016264 | 0x47016264 | 120 | `010100006462014778000000` |

Decoder [reference_model.py](reference_model.py) requires the exact advertised count and xBase0, decodes only complete declared groups, ignores the narrow option's two tail bytes, and selects the eight explicit coordinates. A match supports fixed-reference consistency at capture time. A mismatch weakens that explanation at capture time. Neither outcome identifies the historical A branch, fixes epoch ambiguity, proves an aperture producer defect, or proves prevention.

## Proposed additive reader; not implemented or deployed

After parent review, a new derivative of frozen DM can retain its exact12 windows and add narrow top/bottom immediately after Diff, before end-N/end-R. That gives14 fixed read headers and28 endpoint bulk calls on full success, zero target0x102 writes, zero keys/UI, zero controller control transfers/reset. The existing cached kernel GETDRIVER ownership ioctl remains a metadata guard, separate from USB protocol traffic. Preserve the DM/DQ source contract: one fixed boot/device/interface/descriptors, read-only pinned source/manifest, exclusive receipt, native FD identity, preclaim unbound checks, Revalidate after opening and after claim, matching pending IN even after late timing/error observations, no second header in Unknown phase, release/close in finally, no retry.

Before either new header, require completed exact-count M/C reads and the captured packing premise: M root pointer0x20010000, u16[M+6]=2880, u16[M+8]=1920, u16[M+0x20]=0, C geometry2160/1920/2880. Unexpected geometry/xBase must refuse at ReadyForHeader. First R is a fault/control classification, not an automatic clean-state requirement: this reader must permit explicitly qualified postfault capture as DM already did. Preserve40-second global deadline and >=4-second remaining pair budget; do not silently extend the lifetime. Add fixed104 length to both allowlists and exact parser/count/frame contracts, then prove receipt worst-case size before deployment. The controller callback/whole-image identity remains the existing source/runtime-qualification limitation: the12 DM windows do not newly attest code callbacks. Any stronger callback claim requires a separately retained exact code/callback pin, not a fabricated field in M/R.

All reads are sequential, so bracket R/N and report each pair's monotonic timestamps. A later recovery may replace these fixed references. New reference reads after recovery cannot retroactively attest the fault-time bytes; repeat-at-fault evidence would require a separately reviewed coordinator action. Parent is the sole TV coordinator. No helper implementation is authorized by this source checkpoint until parent review of this plan.

## Host validation

`python3 qualify.py` checks source/disassembly bytes, literals, retained fixture sizes/geometry, alias arithmetic and conditional A reconstruction. `python3 -m unittest -v test_reference.py` covers a mixed-nibble golden vector, each bit in all four lanes, saturation, wrong lengths, coordinate wrap/range checks, exact headers, chosen-lane decoding, ignored-tail independence, geometry drift refusal and absolute-difference ambiguity. Repeat both with `python3 -O`; checks are explicit exceptions/unittest methods, not optimization-sensitive Python asserts. [host-validation.json](host-validation.json) records results. OEM/private inputs remain in their existing directories; this directory contains no OEM binary or full disassembly dump.
