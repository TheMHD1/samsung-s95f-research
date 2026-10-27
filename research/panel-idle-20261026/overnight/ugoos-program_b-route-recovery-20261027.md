# Jellyfin administrative-route recovery for the program_b observation

Recorded 2026-10-27 UTC. This is local, read-only route recovery after the
single failed `MediaCT102` name-resolution attempt. The failed-attempt
artifacts were not edited, and no further server or TV request was made.

## Recovered route

The documented administrative path to Media CT102 is **through the Proxmox
host, then `pct exec 102`**, rather than direct SSH to an independently
resolvable `MediaCT102` name:

    existing key SSH to Proxmox LAN management address
      -> pct exec 102 -- <read-only command inside Media CT102>
      -> loopback/LAN Jellyfin API

This is the route to use if the parent authorizes one new, separately counted
session observation. It is not an authorization to run it now.

## Local evidence

- `researcher-server/exec-jellyfin-plugin-overhaul-2026-05-18.md`, lines 52–53,
  states that CT102 is reached only via Proxmox and shows the `pct exec 102`
  pattern. Its historical credential literal is intentionally not repeated.
- `researcher-server/post-media-lxc.txt`, line 4, records access via the Proxmox
  host followed by `pct exec 102`.
- `researcher-server/exec-performance-2026-10-08.md`, line 15, records existing
  key SSH to the Proxmox LAN-management route. The current network inventory
  identifies Media-LXC as CT102 and its Jellyfin service as port 8096
  (`researcher-server/exec-jellyfin-deep-dive-2026-05-18.md`, lines 24 and 273).
- The current local SSH expansion for the attempted `MediaCT102` target has
  `hostname mediact102`, but local name resolution returned no address. That
  explains the failed direct attempt; it does not challenge the established
  Proxmox/CT route.

No passwords, key material, API token, account ID, media path, or endpoint
credential is retained here. This report only establishes a documented route;
it makes no current connectivity or Jellyfin-session claim.
