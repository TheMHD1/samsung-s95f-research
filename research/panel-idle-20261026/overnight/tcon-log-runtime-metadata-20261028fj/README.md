# TCON log runtime metadata qualification

One fixed cached root request verified the candidate debugfs file exists, debugfs is mounted, sdp_tcon is listed Live, and the226262-byte on-disk driver hashes exactly to the FD/FF audited module. Boot matches the fresh FH identity. No special-device or debugfs payload read, USB vendor transfer, ioctl, config/MMIO write, module load, or reset occurred.

On-disk module equality does not attest loaded executable bytes. A debugfs zero file size is normal metadata, not evidence of an empty producer buffer. FD's single4096-byte read is still a separately implemented/reviewed probe. Complete logs, producer freshness, and an external RTP bridge remain unproven.

The private metadata and authenticated envelope are retained for replay. Do not publish identifying mount/network/boot data directly. qualification.json is a narrow derived result.
