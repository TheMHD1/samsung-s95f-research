# RT selector-to-wire chain: image-load-map correction

## Scope and result

This is a narrow coordinate audit of the already decoded **packaged image-0**
RT selector-to-`F3:80` path.  It does not re-evaluate whether that package is
the controller image running on this TV.  No TV, root, network, controller,
or firmware operation occurred.

The selected package remains:

```text
overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin
SHA-256 bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
```

The earlier selector-chain work decoded real bytes at **stored file offsets**.
Those local instruction sequences, direct relative branches, and TBB-relative
walks remain valid as file-coordinate analysis.  The correction is that the
image-0 vector table is stored at file `0x200`, while its vector values are
linked relative to zero.  Therefore:

```text
image 0: stored_file = 0x200 + linked_address
         linked_address = stored_file - 0x200

image 1: stored_file = 0x40200 + linked_address
         linked_address = stored_file - 0x40200
```

For example, image-0 reset vector `0x00000345` selects Thumb link address
`0x344` and maps to stored file `0x544`, not stored `0x344`.  Image-1 reset
vector `0x00000369` maps to stored file `0x40568`, not `0x40368`.

## Corrected image-0 map for the packaged RT/F3:80 chain

The left column is the existing, byte-verified stored coordinate; the middle
column is the corrected linked address.  The listed hashes recompute over the
stored byte ranges and match the previous raw-byte analysis.

| role | stored file range | corrected linked range | bytes / SHA-256 |
|---|---:|---:|---|
| EEPROM-labelled RT check | `0x99e8..0x9a69` | `0x97e8..0x9869` | 129 / `e973a84d3238753e1e0cbd0be58a055e1cb3144c7057e6e41c782ccb30df46cf` |
| common error entry | `0xb860..0xb8fa` | `0xb660..0xb6fa` | 154 / `40e434612828833aa7b433798a352a99c766cbb47351d2cb42ba364a868d2c6a` |
| selector-`0x10` action | `0x14b10..0x14bbc` | `0x14910..0x149bc` | 172 / `5fcc7bea9301c9aa6b815a92fff05ac97769daf64e9eccbe1bac23f5667e3d18` |
| common-selector setter | `0x2b964..0x2b97a` | `0x2b764..0x2b77a` | 22 / `3d538c104bca6958c66173c7d56a095ded57e9453134e78933ee6d0e26fffb03` |
| receive/parser state machine | `0x12ac4..0x12dbe` | `0x128c4..0x12bbe` | 762 / `5b2cbcbac9d03ba3a1dd175568a5cbc8cb7e74a75264a17fd354833d1f4e9c85` |
| `f380` dispatcher | `0x21824..0x21876` | `0x21624..0x21676` | 82 / `5f9a3da21a8aff22610a23c58b4e79bc20836d4111a456ccb393044616abacbe` |
| selector table/getter | `0x21ff8..0x220ea` | `0x21df8..0x21eea` | 242 / `7b7038d870a46b9f897a44d3368618a13a61025ed86a9c5c61b6dccddba23aa0` |
| response checksum helper | `0x5b24..0x5b5a` | `0x5924..0x595a` | 54 / `a8dc7f55717424be6f692640e86c7961f4e226936f9852ac4887d6d7a4286607` |
| common-object accessor | `0xe870..0xe878` | `0xe670..0xe678` | 8 / `2f24cbd0d31aea9c8e387aac1ce94e6aa00ea1a72dff69c96f6a5c6e752ccf54` |

## What remains proven in stored coordinates

The following chain is a relationship among bytes in one packaged image and
does not depend on treating those stored offsets as absolute flash addresses:

```text
stored 0x99e8 RT check
  -> stored 0xb860 common error (selector 0x10)
  -> stored 0x2b964 writes common-object halfword +0x10

host bytes F3 80 00 00 00 08
  -> stored 0x12ac4 parser assembles command 0xf380, selector 8
  -> stored 0x21824 dispatcher
  -> stored 0x21ff8 table case 8 reads the same common-object +0x10 halfword
  -> response serialization emits the resulting 32-bit value big-endian
```

The RAM-object offsets and the literal RAM addresses already recovered from
the decoded instructions are not shifted by this file-layout correction.  In
particular, the selector field is still the halfword at `common_object+0x10`.
The direct relative control-flow and TBB calculations are likewise invariant
when their code and table are both expressed in stored-file coordinates.

## What must be corrected or not inferred

1. Any prior prose that called these stored offsets “linked addresses” is
   inaccurate.  A linked function pointer or a vector-derived flash target
   needs the mapping above.
2. A raw `BL`, literal, or function-pointer value cannot be compared to a
   stored offset without first identifying which coordinate system it uses.
   This audit does not recover a loader, relocation policy, VTOR placement, or
   current flash address.
3. This correction neither proves nor disproves the package-to-running-image
   bridge, an RT-protection producer in the live controller, a controller
   reset, or a physical cause of the black panel.
4. It deliberately does not bless every other profile reverse-engineering
   report.  Each report that makes an absolute-image, vector, literal,
   function-pointer, or cross-image claim needs its own coordinate review.

## Consequence

The useful producer-to-wire result survives only as a **stored-file-relative
packaged-byte path**.  Future reports should cite stored offsets for this
chain, and supply corrected linked coordinates only where an actual vector,
function pointer, flash address, or loader relation is being interpreted.
