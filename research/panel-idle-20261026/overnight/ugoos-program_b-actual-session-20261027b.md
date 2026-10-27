# PROGRAM_B current-session observation — 20261027b

At the owner-rearmed, parent-coordinated PROGRAM_B test, this agent
used the recovered Proxmox → `pct exec 102` route for one authorized,
read-only Jellyfin `Sessions` request. The request was attempted at
**2026-10-27T02:46:10Z**. It returned HTTP **401 Unauthorized**.

## Result

No session payload was returned, so no current Ugoos/Kodi item, Person of
Interest match, server clock, position, delivery method, transcoding state, or
stream metadata was observed. In particular, this does **not** establish that
PROGRAM_B EPISODE_REDACTED was absent, that it was not DirectPlay, or that the
owner's reported dark screen did not occur.

The prior malformed shell invocation failed before the remote session-query
program could run. This document records the one actual HTTP `Sessions` GET;
there was no retry or polling loop after its 401 result.

No playback, seek, pause, stop, server/client setting change, transcoding,
TV call, or device modification was made. The Proxmox route was used only to
run the failed read-only request. The original direct-DNS-failure artifacts
remain unchanged.

## Interpretation boundary

The owner reported that PROGRAM_B was running when the physical
screen went dark. That is an owner physical observation, not a Jellyfin
response captured here. This failed authentication response neither confirms
nor refutes a physical-panel, HDMI-output, or media-mode mechanism.

Credentials, account identifiers, remote endpoints, media paths, and streaming
URLs were not retained.
