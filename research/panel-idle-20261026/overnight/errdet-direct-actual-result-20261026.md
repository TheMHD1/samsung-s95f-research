# Independent ERR_DET input sample: actual result

One deliberately executed, separately reviewed input-only GPIO sample returned
**logic1** from bankgpio15/line5, mapped by the current device tree to Samsung's
TCON `ERR_DET` signal (global125). Samsung's stock monitor treats nonzero from
this input as its fault predicate. This new sample bypasses QDF's cached-power
shortcut and optional diagnostic debug override. It does not retroactively
establish raw provenance for the earlier vendor getter result at a different
time.

## Actual execution and provenance

[Retained result](managed-errpin-cdev/input-result-20261026a.json), SHA256
`59116acf54ebd8e492f6f94d792a1b40e33e78cc6acdbb72b4161d656f46ae5f`.
The parent ran exactly one input sample, without retry. All11 authenticated root
calls succeeded, postflight passed, helper stderr was empty and private-file
cleanup returned `PRIVATE_REMOVED`.

- Same boot `00000000-0000-4000-8000-000000000000` as the earlier fault queries.
- Preflight uptime78292.71 / UTC1793056683; execute end78294.22 / UTC1793056685.
- Helper PID8654/start19573487, ARM32/little-endian, UID/EUID0.
- Current-run checks join ERR_DET phandle36/offset5/flags0 to DT gpio15,
  gpiochip120/base120/8lines, device4630000.pinctrl and cdev15 major254/minor15.
- Chip open fd26; CHIPINFO gpiochip15/gpio15/8, LINEINFO offset5 flags0 and
  empty name/consumer. This is point-in-time metadata, not an ownership lock.
- One input-only handle request `0xc16cb403`: flags1, lines1, handlefd27.
- One GET `0xc040b408`: value0=1, the remaining63 bytes zero.
- Both handle and chip closes returned0; every recorded errno was0.
- Reviewed runner SHA `cd0a34ffd719945bb369ecae16f4ca0672dbbaddea11be068e0f31465e185cde`;
  manifest SHA `2c9b1283e718c34e40656099ff9181c9481208fd669d6adda0d4558cc5a46d9f`.

The [independent input runtime audit](managed-errpin-cdev/input-runtime-audit.md)
replayed all11 retained raw responses and reproduced the frozen parser results.
It accepts this one-shot execution within the limits below.

The earlier [metadata-only compatibility result](managed-errpin-cdev/metadata-result-20261026a.json)
was accepted and independently audited. It did not acquire a line or sample a
value. The input invocation above rechecked those identities rather than
assuming the earlier metadata remained current.

## Meaning and limits

The exact driver getter reads the bank's GPIO data bit. DT/request/line flags
have no active-low setting, so this is an un-inverted GPIO logic-level sample.
It is independent of the QDF vendor-query output transformations. It is not a
measurement of connector voltage, waveform, emitted light or physical connector
polarity.

The latest owner report was that the panel was off/black. There was no fresh,
read-calibrated physical annotation at the sample instant; the machine record
correctly retains `physical_state=unobserved`. Do not label this a controlled
visible-versus-black comparison. The earlier controller `0x10`/RT Protect
sample was not simultaneous, and its live-versus-latched semantics remain
unknown. Neither observation alone identifies the initiating component or
establishes a recovery/prevention method.

## Concrete side effects and cleanup

The line request temporarily acquires the descriptor, sets input direction,
reads once, and closes/frees the handle. Input direction performs the same
vendor MMIO read/modify/write path used by the stock getter. The cdev path
also clears Linux's software `FLAG_TRANSITORY`, which close does not restore.
The [paired-kernel analysis](../tcon-research/sdp-pinctrl-v2-config-binary.md)
shows a null `set_config` callback, so this extra persistence step does not
invoke vendor hardware configuration in that Image. The acquired paired Image
is not a hash of executing kernel text. Direction/descriptor side effects are
therefore retained explicitly; this was not passive memory inspection.

No output/SET operation, protection change, monitor-latch/counter write,
firmware/factory modification, power/reset command, retry or polling loop was
performed. Close0 synchronously releases the line handle under the reviewed
kernel path; successful private-file cleanup was separately confirmed. No
reader or test loop remains active. No permanent repair is claimed.

## Next discriminating experiment

Obtain an owner-confirmed populated Apps visible/staying-on control, then take
one bounded corresponding fault-state sample. Confirm the physical picture
afterwards. A subsequent controlled transition to the fault-provoking sparse
page would need aligned observation before attributing assertion to onset.
First clarify whether the owner's latest black report followed the requested
ordinary off/on or the prior persistent-black state; do not request repeated
power cycling without that clarification.
