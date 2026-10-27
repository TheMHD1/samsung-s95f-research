set -eu
echo CSFS_BEGIN
base64 /opt/usr/apps/com.samsung.tv.csfs/bin/Com.Samsung.TV.CSFS.dll
echo CSFS_END
echo DEV_PATHS
find /opt/etc /opt/usr/home/owner/share /opt/usr/home/owner/apps_rw/com.samsung.tv.store -maxdepth 3 -iname '*develop*' -o -iname '*devmode*' -o -iname '*sdk*' 2>/dev/null | head -50
echo CORE_UNITS
systemctl show muse-server.service connman.service source-service.service sound-server.service com.samsung.tv.airplay-service-2.service com.samsung.tv.googlecast-service.service -p Id -p LoadState -p ActiveState -p MainPID -p NRestarts
