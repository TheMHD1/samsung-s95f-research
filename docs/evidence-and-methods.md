# Evidence and methods

Each conclusion should be read with its evidence class:

| Class | Establishes | Does not establish |
| --- | --- | --- |
| Owner physical observation | Visible or black panel behavior at the reported time | Exact software state or event operands unless contemporaneously captured |
| Target observation | A recorded return, timing bracket, register/window value or process state | Emitted light, complete causal chain or portability |
| Stored-image reverse engineering | Instructions, layouts and possible paths for the retained hash | That the whole image was executing on the target |
| Matching executing function / runtime fingerprint | Identity of the sampled function bytes or selected boundaries | Whole-image identity or other unsampled functions |
| Host-only reproduction or mock | Decoder, state-machine, ABI storage or failure handling under supplied inputs | Target acceptance, daemon policy, callback requirements or hardware effect |
| Upstream source / external documentation | A documented interface or implementation in the cited lineage | Independent reproduction on this S95F |
| Hypothesis | A discriminator worth testing | A confirmed explanation |

Rejected collectors, unsafe drafts and superseded claims are deliberately retained. For example, a late owner key action can miss an observer's capture window; a collector that exports forbidden logs or violates a qualified phase cannot be accepted just because selected rows look plausible. Later checksum-retry analysis can narrow one failure mechanism without retrospectively accepting an entire earlier collector.

Protocol pairs and evidence qualification matter. Once an OUT header has been accepted, a deadline or asynchronous action failure cannot justify sending a second OUT without consuming the required IN. A timeout, short transfer or unknown phase ends the read sequence without retry. Cleanup is separately recorded.

The exported JSON scientific observations are derived records, labeled with `public-scientific-observations-v1`. Authentication/session envelopes, host identity and encoded staging copies were removed. They preserve command/result observations where publishable; they are not byte-identical originals. Original and public hashes are separate in the disposition manifest. Redacted identities cannot be used to reproduce a device session.
