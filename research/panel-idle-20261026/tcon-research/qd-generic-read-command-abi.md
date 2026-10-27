# QD generic one-command read ABI

## Result

The copied exact-build stack contains a supported generic read route.  It is
not the `SendOneCommand` route:

```text
ARM32 libave ave_tcon_api_read_onecommand(unsigned long long, unsigned *)
  ioctl 0xc010749f, operation 19, 16-byte in/out envelope
    tztv_frc_tcon_api TCON_Request operation 19
      mapped QDF callback-table slot +0x3a8
        QDFTcon_ReadOneCommand(uint64_t command, uint32_t *result)
          m_read_cmd(command, result)
```

The adjacent operation 18 selects callback slot `+0x3a0` and
`QDFTcon_SendOneCommand`; it is a separate write path and is not evidence for
a read.

For the specific future question in scope, the read ABI can represent packed
command `0x0000f30000000128`.  With an ordinary positive low word, the API
reconstructs that value and QDF emits exactly these six command bytes before
requesting four response bytes:

```text
f3 00 00 00 01 28  ->  four-byte controller response
```

Thus there is no missing host ABI edge for asking the QDF `m_read_cmd` path to
perform an `F3 00`, selector-`0x128`, four-byte read.  This conclusion is about
the host/kernel direction and byte packing only.  It does **not** establish
what selector `0x128` means in the controller, whether reading it changes
controller state, whether it is implemented by the currently running
controller image, or what any returned word means.  No helper was prepared,
no ioctl was invoked, and no TV, root, server, network, controller, or bus
operation was performed for this report.

An earlier offline-only draft of this report (SHA-256
`7e7373e2f411c432f63b5b44f9e15f7514f8548edb8cca66e4de9ba50513bf19`)
misread the shorthand “selector128” as decimal128 and used `0x80` in its
example.  That was not the intended selector.  The `0x80` example was never
transmitted or used to build a helper; this revision supersedes it with exact
hexadecimal selector `0x128` throughout.

## Exact local inputs

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `binaries/libave.so.0.1` | 6,657,066 | `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` |
| `binaries/tztv_frc_tcon.ko` | 254,406 | `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd` |
| `binaries/tztv_frc_tcon_api.ko` | 317,998 | `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6` |
| `binaries/qdf_tcon.ko` | 403,294 | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` |

Addresses below are ELF virtual addresses within `libave` and section-relative
addresses within the relocatable kernel modules.  The existing full module
listings `overnight/tztv_frc_tcon_api.disasm` and
`overnight/qdf_tcon.full.disasm` were used only as local static evidence.

## ARM32 caller and 16-byte envelope

The exported Thumb symbol
`ave_tcon_api_read_onecommand(unsigned long long,unsigned*)` is at
`0x251ab9`, size 232.  Under the ARM32 calling convention, `r0` is the low
command word, `r1` the high command word, and `r2` the caller's result pointer.
Its complete bounded body establishes:

| Address | Instruction/dataflow |
| --- | --- |
| `0x251ac8` | saves the caller result pointer in `r4` |
| `0x251ad4` | rejects a null result pointer before the ioctl |
| `0x251ad6` | loads the caller's initial 32-bit result value |
| `0x251ada..0x251ade` | forms request `0xc010749f` |
| `0x251ae2` | truncates/zero-extends the command high word to 16 bits |
| `0x251ae4` | stores command high16 and command low32 |
| `0x251ae8..0x251aea` | stores operation19 and the initial result word |
| `0x251aee` | calls `tcon_ioctl` |
| `0x251af4` | rejects a negative ioctl result |
| `0x251af6..0x251af8` | copies envelope word1 back to the caller |

The exact envelope copied in and back is therefore:

| Byte offset | ARM32 word | Read operation19 meaning |
| ---: | --- | --- |
| `+0` | word0 | `19` |
| `+4` | word1 | caller's initial result value; returned result location |
| `+8` | word2 | zero-extended command bits `47..32` |
| `+12` | word3 | command bits `31..0` |

The wrapper copies word1 back whenever the ioctl return is nonnegative.  It
does not prove that the kernel wrote word1.  A future evidentiary use therefore
needs a pre-call sentinel and must distinguish `return == 0, sentinel
unchanged` from a freshly written four-byte response.  This is the same
freshness principle already established for the bounded status query, but no
sentinel value or runnable invocation is prescribed here.

For comparison, `ave_tcon_api_send_onecommand` at `0x2519d9`, size 224,
uses operation18.  It consumes the pointed scalar as input and has no caller
copyback.  The two wrappers cannot be substituted for one another.

## Driver and API copy boundary

The exact `tztv_frc_tcon.ko` exports the no-op open at `+0x26a8`, native
ioctl at `+0x28e8`, and ARM32 compat ioctl at `+0x2758`.  As established by
the separately reviewed status-read ABI, ordinary compat request
`0xc010749f` is forwarded unchanged through the dynamically resolved
`tztv_tcon_ioctl` callback.

In `tztv_frc_tcon_api.ko`, `fop_tcon_ioctl_export` copies exactly 16 bytes
from userspace at `+0x3be4..0x3bec`, calls `TCON_Request` at `+0x3bfc`, and
copies the same 16-byte local object back.  No userspace result pointer is
passed into QDF; QDF receives a kernel pointer to word1 of this local object.
Copy faults become `-EFAULT`.

`TCON_Request` at `+0xe7b0` subtracts one from word0 and indexes the signed
halfword table at `.rodata+0x6a0`.  The exact table entries separate the two
operations:

| Operation | Table halfword | Case target | Callback slot | Arguments |
| ---: | ---: | ---: | ---: | --- |
| 18 | `0x025b` | `+0xf170` | `+0x3a0` (928) | reconstructed command, `request+4` |
| 19 | `0x0251` | `+0xf148` | `+0x3a8` (936) | reconstructed command, `request+4` |

At operation19, `+0xf14c` loads words2 and3 with signed word loads and
`+0xf154` reconstructs `x0 = word3 | (word2 << 32)`.  For the in-scope
envelope words `word2=0x0000f300` and `word3=0x00000128`, the result is
unambiguously `0x0000f30000000128`.  This reconstruction has a general ABI
limitation: a word3 with bit31 set is sign-extended before the OR and can set
the upper 32 bits.  That limitation does not affect this command, but it is a
reason not to claim arbitrary 64-bit command fidelity.

If the mapped interface pointer or operation19 slot is absent, this case
returns `-1` and leaves word1 unchanged.

## Positive callback binding

The QDF module initializer constructs a `0x758`-byte function table whose
base is held in `x19` (`.init.text+0x14..0x24`).  The relevant relocation and
store sequence is exact:

```text
+0x1e0  x11 = x19 + 0x390
+0x2ac/+0x2b4  form QDFTcon_SendOneCommand
+0x2b0/+0x2b8  form QDFTcon_ReadOneCommand
+0x2bc  stp send,read,[x11,#0x10]
```

This places the send callback at table `+0x3a0` and the read callback at
table `+0x3a8`, exactly matching the operation18/19 loads above.  At
`.init.text+0x528`, the table base is passed to `map_tcon_functions`; the API
implementation at `+0x7c58` stores that pointer in the same BSS interface
location read by `TCON_Request`.

This proves the static intended exact-build binding.  The report did not
sample the live interface pointer or module lifetime, so it does not by
itself prove that this callback table remained installed at any later instant.

## QDF read and wire packing

`QDFTcon_ReadOneCommand` is exported at QDF `.text+0xa140`, size108.  It
preserves `x0` as the 64-bit command, preserves `x1` as the output pointer,
and directly calls `m_read_cmd` at `+0xa158`.  It returns the lower call's
integer result.  The rest of the body logs the command and dereferences the
output pointer for that log; the stock API path always supplies the valid
kernel `request+4` pointer.

There is no command-prefix whitelist or selector check in this wrapper.
There is also no `tcon_flash_update` check in this generic wrapper; the
separate `QDFTcon_GetErrDetStatus` wrapper has such a gate, but it must not be
projected onto `QDFTcon_ReadOneCommand`.

The locking lower routine `m_read_cmd.constprop.0` is QDF
`.text+0x9b88`, size748.  Its command construction at `+0x9c08..0x9c20` is:

1. byte0 = command bits `47..40`;
2. byte1 = command bits `39..32`;
3. bytes2..5 = the byte-reversed low 32-bit word, i.e. bits
   `31..24`, `23..16`, `15..8`, and `7..0`.

It then uses one of two configured transports:

* raw write of six bytes followed by raw read of four bytes at
  `+0x9c3c..0x9c80`; or
* one combined common-read call with transmit length6 and receive length4 at
  `+0x9ce4..0x9d0c`.

Both are fixed to adapter5 and address `0x76`.  Only a zero aggregate lower
result reaches `+0x9c88..0x9c90`, which byte-reverses the received four bytes
and stores the 32-bit value through the output pointer.  If the raw reply is
`aa bb cc dd`, word1 becomes numeric `0xaabbccdd`.

For `0x0000f30000000128`, the packing above is direct positive proof of wire
request bytes `f3 00 00 00 01 28`.  The independently corrected mute
readback supplies a useful direction check: its fixed packed command
`0xf30000000164` reaches this same `m_read_cmd` and produces
`F3 00 00 00 01 64` followed by a four-byte read.  That evidence shows why an
`F3 00` prefix alone does not identify a write.  Direction here comes from
the recovered call to `m_read_cmd`, not from guessing based on the prefix.

## Host-side gates and effects

The candidate command is subject to these exact lower-path gates:

| Condition | Result for `F3 00 ... 01 28` | Word1 |
| --- | ---: | --- |
| API interface/read slot absent | `-1` | unchanged |
| QDF `m_suspend_status` at BSS `+0x0` equals1 | `0` | unchanged |
| QDF `m_command_skip` at BSS `+0x10c` equals1 | `0` | unchanged |
| QDF `m_tcon_state` at BSS `+0x10` is not1 | `-1` | unchanged |
| required transport callback absent or transfer fails | nonzero | unchanged |
| lower write/read succeeds | `0` | four response bytes written |

The skip gate has one exact exception for packed command
`0xf3800000000c`; the state gate has one exact exception for
`0xf38000000000`.  Neither exception applies to `0xf30000000128`.

The generic wrapper does not invoke a named reset, recovery, power, GPIO,
flash-update, or setting routine, and it does not write these gate words.  It
does, however, actively write a six-byte request to the controller before
reading four bytes.  Calling this a “read” describes the protocol transaction
and output direction, not the absence of physical bus output or proof of
non-mutating controller semantics.  A selector may be read-to-clear or have
other controller-side behavior; no such behavior was proved or excluded for
selector `0x128` here.

The driver-level dynamically resolved ioctl callback also has a distinct
success-without-dispatch possibility documented by the status-read ABI: a
missing base callback can return zero with the envelope unchanged.  Therefore
ioctl return zero alone is never fresh-response evidence.  Exact source
identity, a nonnegative return, and a changed sentinel would establish only
that the kernel wrote a four-byte result; controller meaning and state effects
would still require separate source evidence.

## Offline reproduction

The existing local verifier covers the complete ARM32 send/read wrapper
bodies and the operation19 load/copyback landmarks.  It is deterministic
under normal and optimized Python:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 \
  tcon-research/qd-onecommand-buffer-reproduce.py > /tmp/one.normal
PYTHONPATH=/tmp/tcon-capstone python3 -O \
  tcon-research/qd-onecommand-buffer-reproduce.py > /tmp/one.optimized
cmp /tmp/one.normal /tmp/one.optimized
```

The additional bounded check below hash-gates the relevant inputs, decodes the
operation18/19 table targets, pins the QDF read/lower symbols and initializer
relocations, checks the callback-pair store opcode, and checks the corrected
six-byte packing.  It reads local files only:

```python
from pathlib import Path
from elftools.elf.elffile import ELFFile
import hashlib, struct

hashes = {
    'binaries/libave.so.0.1':
        'a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777',
    'binaries/tztv_frc_tcon_api.ko':
        '3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6',
    'binaries/qdf_tcon.ko':
        '97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63',
}
for path, expected in hashes.items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected

with open('binaries/tztv_frc_tcon_api.ko', 'rb') as source:
    elf = ELFFile(source)
    rodata = elf.get_section_by_name('.rodata').data()
    targets = [0xe804 + 4 * struct.unpack_from(
        '<h', rodata, 0x6a0 + 2 * (operation - 1))[0]
        for operation in (18, 19)]
    assert targets == [0xf170, 0xf148]

with open('binaries/qdf_tcon.ko', 'rb') as source:
    elf = ELFFile(source)
    symtab = elf.get_section_by_name('.symtab')
    symbols = {symbol.name: (int(symbol['st_value']), int(symbol['st_size']))
               for symbol in symtab.iter_symbols()}
    assert symbols['QDFTcon_ReadOneCommand'] == (0xa140, 108)
    assert symbols['m_read_cmd.constprop.0'] == (0x9b88, 748)
    relocs = elf.get_section_by_name('.rela.init.text')
    dynsym = elf.get_section(relocs['sh_link'])
    names = {int(reloc['r_offset']):
             dynsym.get_symbol(reloc['r_info_sym']).name
             for reloc in relocs.iter_relocations()}
    assert [names[offset] for offset in (0x2ac, 0x2b0, 0x2b4, 0x2b8)] == [
        'QDFTcon_SendOneCommand', 'QDFTcon_ReadOneCommand',
        'QDFTcon_SendOneCommand', 'QDFTcon_ReadOneCommand']
    init = elf.get_section_by_name('.init.text').data()
    assert init[0x2bc:0x2c0].hex() == '641d01a9'

command = 0x0000f30000000128
assert command.to_bytes(8, 'big')[2:] == bytes.fromhex('f3 00 00 00 01 28')
print('PASS op18=f170 op19=f148 read=a140 m_read=9b88 '
      'wire=f30000000128')
```

Both checks passed locally.  The second check intentionally establishes
layout/packing only; it does not execute the recovered functions or establish
controller semantics.

## Bounded conclusion and limits

The previously missing ABI edge is closed statically for the exact copied
build: operation19 is a real read callback, is bound to
`QDFTcon_ReadOneCommand`, accepts the split 48-bit command in the ARM32
envelope, and reaches a fixed six-byte-command/four-byte-response QDF
transaction.  `F3 00 00 00 01 28` is representable without the signed-low-word
corner case.

This report does not:

* establish selector `0x128` semantics or output layout;
* prove the current controller firmware equals a packaged profile image;
* prove that a read is non-clearing or otherwise side-effect free;
* prove live callback-table presence at a future instant;
* turn a zero return with unchanged output into success;
* authorize, construct, stage, or run a userspace helper; or
* infer a panel, rail, protection, mute, dimming, or physical-light state.

The exact controller getter/payload interpretation remains a separate source
analysis, as intended.
