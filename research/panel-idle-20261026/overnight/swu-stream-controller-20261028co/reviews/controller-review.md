# CO/CP bounded controller integration review

Result: no blocking integration defect found in the reviewed fixed1002 foreground path. Host-only read/qualification; root/TV/TEE/network operations0. This independently reviews CO/CP integration; the reviewer authored CJ, so this is not an independent review of CJ itself.

Reviewed pins:

- CO run-cn.py SHA256 e614e33415fa887718bc579ee858ca029befa5ce4458afe2755509c30326b67f
- CO extraction.py SHA256 dcbf7d2dede5aa89e501e3e25f61a0b5f02f6d572d26450bb58d6116640122f8
- CP root-with-margin.py SHA256 be9c5362fa40b52be2b824e6cc3e11013bdaafd44b1710f010bbccebac2bdc55
- CF private plan expected SHA256 f7946a96e36bff095ea20e28b4aaea1e40901b3005f863188d2e05b0ff8a4ee8
- CJ client source expected SHA256 8e0cf5c2b94508f7b3be424631af5611da7b017b3970cd9dab81622429d4260e
- CJ server source expected SHA256 80b1ca50b2dfa9f32fd012af2d5ce494d1082ddf982ae911ce40b5814ba22ae9

CO uses the callable CJ ServerConfig/serve API correctly, with a fixed whole-MSD path and CF-derived exact offset/count/cipher SHA. No wire-selected path, section or command exists. Maximum output equals11892544 cipher bytes. The listener starts after staging and must return exact configured address/port before native dispatch; the nonce/certificate bindings match private host/client state. A deployment digest anchors controller/extractor/adapter/server/target sources and payload/private connection material. Source range hashing is performed before listener readiness and again while streamed; source full-file duplication is unnecessary.

Actual pinned CF1002 data and72-byte binary-plan equality were checked offline. Native parsing requires exactly one SWU_STREAM_RAW line, exact fields and successful cleanup/wipe/counts.182 updates equals ceil(11892544/65536);188 guards equals CG186 plus CN2 pre-sequence guards. Cipher/raw/confirmed counts all require11892544. The host independently requires one connection and identical stream counts. A failed or ambiguous root/native/server result stops without another invoke or target cleanup; completed quarantine can remain after an acknowledgement failure, which is not treated as peer acceptance.

The extraction gate reads exactly11892528 original bytes, checks the authenticated expected original CRC, requires exactly sixteen0x10 padding bytes and EOF, then independently rehashes/counts the copied original scope. Exclusive temporary output plus link promotion cannot overwrite an existing official-name file. Ciphertext-RSA qualification is inherited from the pinned CF plan; no plaintext RSA or complete firmware applicability claim is introduced. The public name is only created after these local checks. Native cleanup is required before target-stage deletion. A failure of later cleanup retains evidence and stops, with no retry.

CP pins the unchanged base root runner/access identities and retains response/model/root/command framing checks. Remote120sec is within the access CLI's1..120 bound; host150sec exceeds the remote120 plus persistent request15sec margin. CN100sec native alarm and CJ90sec session are nested inside these margins. CJ's regular-file syscall cancellation limit and the fact that native termination cannot undo TA state remain practical limits; this controller introduces no reset/install/panel/UI operation. Uploads use guarded exact append offsets and final payload size/hash/owner/mode/inventory checks; one native invocation is recorded conservatively as inflight/unknown before dispatch.

Bounded host checks: AST parse of three reviewed Python files; actual pinned CF/binary-plan binding; generated boot/stage/exact-inventory shell parsed with sh -n only; one valid native fixture and five rejected mutations (updates, raw count, closed state, elapsed deadline, uncertain ownership). All passed. No root module was loaded and no root command was executed. CN final build/artifact freeze remains the owning agent's responsibility; this report does not substitute for that pin.
