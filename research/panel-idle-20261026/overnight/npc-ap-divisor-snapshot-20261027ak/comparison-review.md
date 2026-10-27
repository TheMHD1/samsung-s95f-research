# AK arithmetic and scope review

2026-10-27 UTC. Independent read-only review PASS, no material findings.
Root records the returned result here.

Reviewed verifier SHA-256
`b94628cfa363611b8b693dc2e9648dadef514cbf88248801bffd5b692faadcc7`;
identical normal/optimized outputs
`f154615e8300de95a79d0ca9af06575956cba3b9d4227cee70660ec2fe7ab400`.

The reviewer reproduced 2700/118+0.5 -> trunc23 -> low16/cap6 and the
stored1024 substitution ->3, retained indexes6, exact17657centisecond terminal
separation and meaningful halfword-before-cap regression. All pinned inputs
and the explicit non-atomic/conditional-identity/no-runtime-branch/no-physical-
cause limitations passed. No target, network or configuration action occurred.
