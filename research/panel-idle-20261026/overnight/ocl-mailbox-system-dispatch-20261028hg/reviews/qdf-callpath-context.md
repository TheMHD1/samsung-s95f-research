# QDF embedded printk label and OCL provider path

This narrow source clarification explains the parent's retained HF post-MODE2 messages without changing GZ/HG history. The source checker pins the retained QDF/API/FRC/OCL modules and the existing private HF post-kernel snapshot; it performs no target call. This is not an independent replay of that acquisition's root transport.

The QDF ELF function at `.text+0x11848` is named `m_set_power_control`. It uses a common label base loaded from `.rodata+0x1228`, but the printed `%s` label receives a further instruction-derived offset:

| Site | Actual string address | Printed label |
| --- | --- | --- |
| Ordinary power message, `.text+0x11880` | `0x1228 + 0xca0 = 0x1ec8` | `m_set_power_control` |
| Reset0 callback message, `.text+0x11a0c` | `0x1228 + 0xcb8 = 0x1ee0` | `m_set_elvdd_onoff` |
| Reset1 callback message, `.text+0x11b30` | same `0x1ee0` | `m_set_elvdd_onoff` |

Thus the observed `m_set_elvdd_onoff` text is an embedded label at the reset-callback print sites inside this function. It is not sufficient evidence that the alternative `tztv_frc_tcon_set_elvdd` callback was selected.

Under correspondence to this retained code, the on path first checks the QDF monitor word at BSS+`0x1a8`; the non-monitor branch tests BSS+`0x1ac == 4` at `0x11954..0x1195c`. That branch reaches the optional `tztv_set_sdp_jp_tcon_power_reset` pointer, calls it with0 at `0x119f0`, and prints the reset0 message at `0x11a18`. The off path analogously tests the platform word at `0x11ac4..0x11acc`, calls with1 at `0x11b14`, and prints the reset1 message at `0x11b3c`. NULL checks remain. This identifies source branch conditions; it does not sample those BSS words.

There is also a positive source provider-registration bridge:

1. API exports `tztv_set_sdp_jp_tcon_power_reset` as an eight-byte BSS object at `0x88`.
2. FRC-TCON `get_fn_ad` loads the exact string `sdp_ocl_reset_tcon_power` from `.rodata.str1.8+0x51b8` at `.text+0x57d8/0x57dc`, calls `resolve_symbol` at `0x57e4`, and stores the result into that API pointer object at `0x57f8`.
3. `resolve_symbol` uses `find_symbol` at `0x2ab0`, then resolves the returned PREL32 symbol record using `ldrsw`/address addition at `0x2ac4/0x2ac8`. Missing lookup can return NULL.
4. The retained JP module exports `sdp_ocl_reset_tcon_power` at `.text+0x2b38`, size80. HE already pins its one-byte mailbox command3f sender, and HG closes the candidate receiver/secondary handoff.

This is a source lookup/store/provider chain, not a read of the current live function pointer or proof of its active provider. The retained HF post-kernel file contains exactly two PID6586 reset-callback printks with the embedded `m_set_elvdd_onoff` label, covering roles1 and0. The checker records their line hashes and the whole input hash without reproducing private raw text. The parent's separate actual-kernel analysis owns the complete invocation/time/result reconstruction.

The source and retained messages are compatible with the OCL reset-callback path and normal recovery tail. They do not prove rail levels, current loaded MCU identity, shared-root fault clearing, instruction reload, image0 restart, or optical recovery. No callback, symbol lookup, mailbox or GPIO operation was invoked by this review.
