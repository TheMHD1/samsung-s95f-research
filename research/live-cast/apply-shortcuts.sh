set -eu
umask 077
STATE=/opt/usr/home/owner/researcher-live-cast
RES=/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res
TERRA=/opt/usr/apps/com.samsung.tv.ContentsBrowser/shared/res/CompTerra.dll
SHARED=/opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted
STAGE=/home/researcher/share/tmp/sdk_tools/researcher-live-cast
BACKUP=$STATE/shortcuts-backup
hash() { sha256sum "$1" | cut -d' ' -f1; }
test "$(hash "$TERRA")" = b085608b9da114f46b4cf162d9faf73f552fb5fe27d74cb37f8b6edc3ddf9c4f
test "$(hash "$RES/CompHome.dll")" = a459badb5665b6c1b60da459f4676cff0da1d231e63381fe83695331a4a4cade
test "$(hash "$STAGE/CompHome.shortcuts.dll")" = 925041eb259e9229cdda92f00211bca7dcac7dee7cf2b91a305d3b55e32e9209
test "$(hash "$STAGE/CompTerra.shortcuts.dll")" = f743083fc773fa4507717db42414c0b01f860cd89098eaca5d6db80ecb9657fc
test "$(hash "$STAGE/HabibiHomeShortcuts.dll")" = b206a6e13241d2da590a53a5ccbab571d8e508a6fb31b6b87409d27e1e6d1a61
test ! -e "$BACKUP"
mkdir -m 700 "$BACKUP"
cp -a "$TERRA" "$BACKUP/CompTerra.before.dll"
cp -a "$RES/CompHome.dll" "$BACKUP/CompHome.before.dll"
app_launcher -k com.samsung.tv.home.media
sleep 1
restore_shortcuts() {
    trap - EXIT
    app_launcher -k com.samsung.tv.home.media || true
    cat "$BACKUP/CompTerra.before.dll" > "$TERRA"
    cat "$BACKUP/CompHome.before.dll" > "$RES/CompHome.dll"
    rm -f "$RES/HabibiHomeShortcuts.dll" "$RES/researcher-hdmi.svg" "$RES/researcher-cast.svg" "$RES/researcher-settings.svg"
    if [ -f "$BACKUP/sqlite.db" ]; then
        rm -f "$SHARED/sqlite.db-journal" "$SHARED/sqlite.db-wal" "$SHARED/sqlite.db-shm"
        cp -a "$BACKUP/sqlite.db" "$SHARED/sqlite.db"
    fi
    if [ -f "$BACKUP/db_ready" ]; then cp -a "$BACKUP/db_ready" "$SHARED/db_ready"; fi
    app_launcher -s com.samsung.tv.home.media
    echo PREVIOUS_CLEAN_HOME_RESTORED
}
trap restore_shortcuts EXIT
cp -a "$SHARED/sqlite.db" "$BACKUP/sqlite.db"
if [ -f "$SHARED/db_ready" ]; then cp -a "$SHARED/db_ready" "$BACKUP/db_ready"; fi
rm -f "$SHARED/sqlite.db" "$SHARED/sqlite.db-journal" "$SHARED/db_ready"
for FILE in HabibiHomeShortcuts.dll researcher-hdmi.svg researcher-cast.svg researcher-settings.svg; do
    test ! -e "$RES/$FILE"
    cp -a "$RES/CompHome.dll" "$RES/$FILE"
    cat "$STAGE/$FILE" > "$RES/$FILE"
done
cat "$STAGE/CompHome.shortcuts.dll" > "$RES/CompHome.dll"
cat "$STAGE/CompTerra.shortcuts.dll" > "$TERRA"
app_launcher -s com.samsung.tv.home.media
sleep 7
query() { sqlite3 -readonly "$SHARED/sqlite.db" "$1"; }
echo HOME_GRAPH
query "select componentID,visible,elementCount,elementFocusable from TableEntity where componentID in ('d/tabs','d/launcher','s/livetv@TVPLUS') or componentID like 'h/shortcut%';"
test "$(query "select count(*) from TableEntity where componentID='d/tabs' and visible=1;")" = 1
test "$(query "select count(*) from TableEntity where componentID='d/launcher' and visible=1;")" -ge 1
test "$(query "select count(*) from TableEntity where componentID='s/livetv@TVPLUS' and visible=1;")" -ge 1
for ITEM in HDMI1 HDMI2 HDMI3 HDMI4 Cast AirPlay Settings; do
    test "$(query "select count(*) from TableEntity where componentID='h/shortcut@$ITEM' and visible=1 and elementCount=1;")" -ge 1
done
test "$(query "select count(*) from TableEntity where componentID like 'd/dhcategory%' or componentID like 'd/topbanner%' or componentID='d/recent.row@OnNow';")" = 0
systemctl is-active muse-server.service connman.service source-service.service pulseaudio.service com.samsung.tv.airplay-service-2.service com.samsung.tv.googlecast-service.service
printf 'COMPLETE\n' > "$STATE/shortcuts.applied"
trap - EXIT
app_launcher -k com.samsung.tv.csfs
sleep 1
app_launcher -s com.samsung.tv.csfs
echo USEFUL_HOME_SHORTCUTS_APPLIED
