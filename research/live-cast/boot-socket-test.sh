set -eu
umask 077
APP=/opt/usr/apps/com.samsung.tv.ghservice
STATE=/opt/usr/home/owner/researcher-root-persistence
DLL=$APP/bin/com.samsung.tv.ghservice.dll
STAGE=/home/researcher/share/tmp/sdk_tools/researcher-live-cast
EXPECTED=3ce6c9b3eafd039728b2471e8349fedd5d3de5598ebec10d8425f716aef034e4
test "$(sha256sum "$DLL" | cut -d' ' -f1)" = "$EXPECTED"
test -f "$STATE/ghservice.original.dll"
test "$(sqlite3 -readonly /opt/dbspace/.pkgmgr_parser.db "select app_onboot||'|'||app_disable from package_app_info where app_id='com.samsung.tv.ghservice';")" = 'false|false'
app_launcher --status > /tmp/researcher-gh-before.txt
if grep -F 'com.samsung.tv.ghservice (' /tmp/researcher-gh-before.txt; then
    echo 'Gaming Hub service is already running; refusing replacement.' >&2
    exit 1
fi
test -d "$STATE"



restore_original() {
    cat "$STATE/ghservice.original.dll" > "$DLL"
    test "$(sha256sum "$DLL" | cut -d' ' -f1)" = "$EXPECTED"
}
trap restore_original EXIT
cat "$STAGE/com.samsung.tv.ghservice.dll" > "$DLL"
echo PROBE_LAUNCH
app_launcher -s com.samsung.tv.ghservice
sleep 7
echo PROBE_RESULT
find /opt/usr/home/owner/apps_rw/com.samsung.tv.ghservice /opt/usr/apps/com.samsung.tv.ghservice -name researcher-root-suitability.json -type f -exec cat '{}' ';' 2>/dev/null || true
echo PROBE_PROCESS
app_launcher --status | grep -F com.samsung.tv.ghservice || true
# Restore even if the probe cannot run on this firmware.
app_launcher -k com.samsung.tv.ghservice || true
restore_original
trap - EXIT
echo ORIGINAL_RESTORED
sha256sum "$DLL"
