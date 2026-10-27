# Independent audit: paired For You black-state fault reads

Date: 2026-10-27 UTC

Scope: offline review only. I made no TV, root, network, GPIO, ioctl, or display-control call. The three source records and their sidecars were not changed.

## Outcome

The two one-shot reads are internally accepted and their retained transport evidence supports the recorded results:

- the stock TCON status query returned `0x00000010`;
- the independent GPIO-cdev input sample returned `1` for gpiochip15 line 5;
- the later retained kernel-log snapshot binds the status query to helper PID 13669 and contains the raw QDF line `ERR DET Status:0x10` at uptime `84517.921691`.

This is a useful same-boot state association. It reproduces the earlier black-state `0x10`/`1` pair and differs from the immediately preceding owner-reported working Apps state, whose separately accepted reads were `0`/`0`. It does **not** prove that entering For You caused the condition, establish exact transition latency, or by itself identify the failing electrical component.

## Frozen inputs

| File | Bytes | SHA-256 |
|---|---:|---|
| `paired-restart-20261027a/black-foryou-status.json` | 125373 | `5e53af507ffac67cd33a709900275bee72d6c5510e9b29011d6e740551205830` |
| `paired-restart-20261027a/black-foryou-pin.json` | 143318 | `1a7edb74f6d1580c4e50415df87aafead1cfb1273b6892c994e852436e4c4e72` |
| `paired-restart-20261027a/black-foryou-kernel.json` | 23966 | `fbb4d2c9acb98133c8a2c632e858c38886b44d1b2045c0c8e1c225a16ce0c1aa` |
| `paired-restart-20261027a/black-foryou-kernel.txt` | 8970 | `af08e1d09120a08121bb4471ec049b7a2a8e873dae74c69c31b829e78e1e9714` |

## Status-read evidence

`black-foryou-status.json` is schema `managed-tcon-status-read-result-v1` and records `accepted=true`, `read_usable=true`, `one_shot=true`, `retry_permitted=false`, and `cleanup_confirmed=true`.

- Boot ID remained `00000000-0000-4000-8000-000000000000` from preflight through execution.
- Preflight uptime was `84516.57`; execution uptime was `84517.99`.
- The guarded ARM32 helper was PID 13669, start ticks 21129431, UID/EUID 0, pointer size 4, and structure size 16.
- There was one `O_RDWR|O_CLOEXEC` open of `/dev/tztv_tcon` (`0x80002`, fd 26), one ioctl `0xc010749f`, and one close. All returned zero at the operation level except the successful open fd; all retained errno values were zero.
- The exact payload changed from `[0x1f, 0xa55a5aa5, 0, 0]` to `[0x1f, 0x10, 0, 0]`. The classification `kernel_output_written` is therefore grounded; it remains narrower than controller-transaction or hardware-freshness proof.
- The run pins manifest `3241a1b6106c0447ba33a57b2b223d6ef88fc71daf444b3e4c03b2d880a34943`, the ABI report, the managed runtime/core libraries, and the installed TCON/API/QDF module identities.

All 10 retained root calls passed the same checks independently: base64 transport bytes reproduce the stored root response; transport exit is zero; transport stderr is empty; there is one echoed command equal to the requested command; remote exit is zero; remote timeout is false; remote stderr is empty; the response is authenticated as UID/EUID 0 for model `QN77S95FAFXZC`; root persistence is `host-assisted`; and `global_system_files_unchanged_at_acquisition` is true. The source constructs the fixed `--persistent-only --timeout 25 --command ...` argv and pins root client SHA-256 `3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5`. The result proves the echoed remote command and authenticated response, but does not separately serialize the host argv vector.

## GPIO evidence

`black-foryou-pin.json` is schema `managed-errpin-cdev-input-once-result-v1` and likewise records accepted/read-usable/one-shot/cleanup true and retry false.

- It stayed on the same boot. Preflight uptime was `84547.83`; execution uptime was `84549.36`.
- Helper PID/start were 13994/21137275, ARM32 UID/EUID 0.
- Preflight binds `/dev/gpiochip15` (`fe:f`, root-owned mode 0600), sysfs gpiochip120 (`gpio15`, base 120, 8 lines), platform device `4630000.pinctrl`, and the DT `samsung,err_det` tuple phandle 36, offset 5, flags 0 to gpio15's matching phandle and two-cell controller.
- CHIPINFO and LINEINFO returned zero with line 5 flags 0 and an empty consumer. A single input handle was requested with flags 1 and one line; GET returned zero and `VALUE0=1`; all unused value bytes were zero. The handle and chip fds both closed with return/errno zero. No GPIO SET occurred.
- The run pins manifest `2c9b1283e718c34e40656099ff9181c9481208fd669d6adda0d4558cc5a46d9f`, the cdev ABI report, and the paired-Image provider report.

All 11 root calls pass the same raw transport, command echo, authenticated-root, no-error, timeout, model, persistence, and global-baseline checks described above. The result is a direct input sample but remains a point sample; it does not establish when the line asserted.

## Kernel-log binding

The one-call `black-foryou-kernel.json` is accepted. Its exact command SHA-256 is `06eda316d658f56ef9d61870116017a0ec3e411b56d0a8366db7c496a78438e8`; the retained raw envelope authenticates root, exact command echo, exit zero, empty stderr, no timeout, the same boot before/after, and uptime `84555.46..84555.52`.

The output contains exactly one line for helper PID 13669:

`[84517.921691] [TCON:QDF] QDFTcon_GetErrDetStatus[13669:TconStatusRead.]: ERR DET Status:0x10`

This timestamp precedes the status helper's summarized execution uptime only by normal rounding and matches its PID. The pinned static ABI analysis places this QDF log at the raw-word site before the optional debug override; no subsequent debug-override line appears in the retained filter. Therefore the log positively binds raw QDF word `0x10` to this query. It still does not independently prove the lower wire transaction, the age of controller state, or a physical fault mechanism.

## Chronology and physical limits

- The preceding 30-second For You observer finished and verified cleanup at `2026-10-27T01:01:22.080768Z`.
- The status record began at `01:01:44.849963Z` and finished at `01:01:47.062404Z`.
- The GPIO record began at `01:02:16.142767Z` and finished at `01:02:18.361099Z`.
- The kernel-log read began at `01:02:23.854137Z`.

Thus these reads did not overlap the observer, and the status and GPIO queries did not overlap each other. The owner's black-screen report logically preceded the reads, but its chat reaction and screen-transition times are not calibrated to target monotonic time; the machine records correctly retain `physical_state="unobserved"` rather than manufacturing a timed annotation.

The prior working-Apps pair and this black-For-You pair were obtained on the same boot and show `0/0 -> 0x10/1`. That is strong repeatable state-correlated evidence. It is not sufficient to say that For You caused the assertion, that menu population is the electrical trigger, or that either read proves a fresh lower-controller sample. No repair, protection bypass, recovery action, or persistent change is established by this audit.
