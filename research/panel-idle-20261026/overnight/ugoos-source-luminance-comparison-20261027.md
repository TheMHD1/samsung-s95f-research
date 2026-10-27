# Source opening-frame luminance check

Recorded 2026-10-27 UTC. This small, read-only check tests only whether the
beginning of the source file is unusually dark. It is not a measurement of the
Samsung panel, HDMI output, Kodi display-mode selection, or the precise frame
at which the reported blackout occurred.

## Method

The established Jellyfin container's ffmpeg was invoked once per source with
one decoding thread at nice 19, input offset zero, a 60-second limit, one
sample per second, and a 160-pixel-wide analysis scale. It emitted
signalstats Y values to standard output only. It did not attach to the
owner's session, create a Jellyfin transcode session, write a media file, or
change TV/server settings.

## PROGRAM_LABEL result

The 60 samples from the local SDR H.264 source completed in 14.66 seconds.
For samples 0 through 9, decoded 8-bit YAVG stayed at 16.00--17.62, with a
mean of **16.65**. Samples 10 through 29 averaged 39.12, and samples 30
through 59 averaged 41.29. The full-minute mean was 36.46 (range 16.00 to
58.20).

This supports the narrow statement that the beginning contains about ten
seconds of near-black *encoded SDR luma*. It does not establish that the TV
blackout was caused by dark material: the owner reported a persistent black
panel with continuing audio, while this source data has no access to the
physical panel state or exact fault onset.

## PROGRAM_A limit

The matched PROGRAM_A comparison is HDR10+ HEVC. Its separate low-priority
single-thread decode was bounded to 25 seconds and expired before a complete
metadata stream flushed, so no PROGRAM_A statistic is retained. That is a
deliberate resource bound while the owner is using the server.

Raw HDR PQ code values would not be comparable to SDR YAVG as physical
brightness without a defined tone-mapping and normalization method. No
cross-HDR brightness claim is made.

The compact values are in ugoos-source-luminance-comparison-20261027.json.

