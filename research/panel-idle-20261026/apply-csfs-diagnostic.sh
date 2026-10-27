set -eu
umask 077
LIVE=/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll
STAGE=/home/researcher/share/tmp/sdk_tools/researcher-live-cast/csfs-idle-reset-diagnostic.dll
SAVE=/opt/usr/home/owner/researcher-live-cast/csfs-idle-diagnostic-20261026
LOG=/tmp/researcher-csfs-idle-trial.log
hash() { sha256sum "$1" | cut -d' ' -f1; }
test "$(hash "$LIVE")" = a58a755d0761c2f6328ff8efdcd7e5af0a2a0c7a02b2fc3992374506e13ac4d0
test "$(hash "$STAGE")" = cde3ed6fd3428de32943eda39452b37749d1896c8d91a9615c3d8af5ae8cd565
test ! -e "$SAVE"
test ! -e "$LOG"
mkdir -m 700 "$SAVE"
cp -a "$LIVE" "$SAVE/csfs.dll"
rollback() {
 trap - EXIT
 app_launcher -k com.samsung.tv.csfs || true
 cat "$SAVE/csfs.dll" > "$LIVE"
 app_launcher -s com.samsung.tv.csfs
 echo CSFS_ORIGINAL_RESTORED
}
trap rollback EXIT
app_launcher -k com.samsung.tv.csfs
sleep 1
cat "$STAGE" > "$LIVE"
app_launcher -s com.samsung.tv.csfs
sleep 13
test -f "$LOG"
cat "$LOG"
grep -q 'result=0' "$LOG"
sha256sum "$LIVE"
cat /proc/uptime
trap - EXIT
echo CSFS_SINGLE_RESET_COMPLETED
