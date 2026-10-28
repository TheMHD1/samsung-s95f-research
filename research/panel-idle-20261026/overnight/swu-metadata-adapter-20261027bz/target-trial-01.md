# BZ first target attempt: fixed decryption sequence completed

The central reviewed BZ adapter completed exactly one metadata-only
TEE0/1/2 sequence with exit0, result0, origin4 and localerror0. All five selector
checks returned0/value0. Command counts were1,1,1; output counts and observed
counts were4032,0. The adapter reported session closed, three shared buffers
released and context finalized. Strict runner framing/native cleanup checks
passed and the exact staging directory was removed.

DLL SHA256cbacf03db8f50cbc8728e4869bca2360f995ef8c39f7ee4c2c15dfe55e1df974;
deployment manifestde81b2303dd50667c4a37908dee65796e92725361691a07e24c53b56c08491a7;
runner4a69be38f81d24faa889a6f87b255995de239bd764b6171554e884b3b06fc43e.
Full authenticated records remain private in s95f-live-trials/swu-bz-01.
The original BX/BY refusals and their sources remain unchanged.

This demonstrates that the exact installed decryption service accepts the
bounded metadata call sequence and returns4032bytes. Those private output
buffers were quarantined and wiped by the unchanged Core. No plaintext was
saved, CRC/schema/RSA validation was not attempted by this adapter and no
metadata or payload name was published. Service result0 alone is not proof
of valid decrypted metadata or firmware applicability.

No UI key, controller power action, vendor USB transfer, update, firmware
write or flash was part of this test. The previously recovered Apps picture
was left alone. The complete official encrypted archive is separately
available at firmware-acquisition-20261028 for future extraction after the
metadata validation gates are met.
