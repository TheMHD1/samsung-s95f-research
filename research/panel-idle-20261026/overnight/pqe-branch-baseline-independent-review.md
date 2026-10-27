# Expanded branch baseline: parent-preserved independent audit

This note preserves the independent runtime-reader review delivered to the parent after the actual capture. The reviewer performed read-only local verification and did not create this file because its review role prohibited edits. The parent wrote this record from the delivered audit. The reviewer made no TV call or target/control invocation.

## Exact reviewed artifacts

- Reader SHA256: `84ff5138a7c4551b932b10360eb6b98d806dc2ef385497b4ec2f7123d6c27acb` (27601 bytes).
- Tests SHA256: `750195a7a6f691cb209046406cb47301378cde2e5d6bc1942c2f3fae92bf8df6` (17657 bytes).
- Archived/generated command SHA256: `8e8e3ef9e8e4bd928122040bbfdaa884c8e4496a46303bab86fdcfc8a9f50364` (4661 bytes).
- Actual [181903Z record](pqe-branch-baseline-20261026T181903Z.json) SHA256: `cbe095e744204e89d855996f5fa8d66bb7226966146723679a0b93ed0faa57c8`.

The exact source/tests/command match the new immutable review archive. Independent pre-run checks included 17 passing tests, Python compilation, generated Bash syntax, dry default, persistent-only single-command/no-retry behavior, output-path refusal including the CLI dangling-symlink boundary, raw failed/timeout retention, exact source and identity guards, base-class-only field eligibility and MNT omission, source/vptr/memory-range checks, and complete raw-read accounting. Clearance was for exactly one finite parent-operated passive physically unobserved baseline, not a control or diagnostic conclusion.

## Actual-result verification

The reviewer parsed the retained root response and re-ran the hash-pinned validator locally. Its computed summary equals the saved summary exactly. The recorded command equals the generated and archived command.

The authenticated response identifies the expected model, uid/euid zero, host-assisted root and the recorded global-system-files invariant. There is exactly one command with exit0 and no timeout; outer transport is exit0 with no stderr. No retry is recorded.

Both endpoint identity records agree on boot `00000000-0000-4000-8000-000000000000`, PID706, `/usr/bin/avocd`, start tick603, and exact AVOC/AVE installed hashes. Both maps are byte-identical, with 1345 lines. Both pointer blocks match. Load bias is `0xf6b77000`; QDDimming object/vptr/inner are `0xf7203698` / `0xf71162e8` / `0xf63895d8`; backend object/vptr/captured slot target are `0xf7203630` / `0xf711852c` / `0xf6d3d275`. The base AutoPowerOff static resolves to `0xf7135420`. QD outer-header words rebind the guarded object/inner/backend chain.

All 33 expected sections are present without extras. The stderr inventory has exactly 141 lines: 47 dd operations, 73 words, 292 bytes. It comprises 12 initial pointer reads, 35 common words, 13 added base-branch words, one typed-backend cache word, and 12 final pointer reads. No extra error line is present.

UTC1793038745..1793038746 and uptime60354.20..60355.08 are monotonic. The measured window is 0.88 seconds.

Raw values independently match: condition aligned word256/low byte0; weights102/102; floor0; sources f8/fc100/17; model0/control0xffffffff; gain1024/AutoDim0; product0; AutoPowerOff counter0; working256/256; Weber gain1023; backend requested cache256.

## Review outcome and limits

The review found no blocker to accepting this as a complete read-only software baseline. All values remain sequential/non-atomic and physically unobserved. Endpoint agreement cannot exclude changes away and back. The snapshot does not identify an active calculation branch, prove a send or lower application, establish physical light, or identify blackout causality. Host-assisted root is not untethered persistence. No physical recovery/prevention or permanent repair is established.
