set -eu
STATE=/opt/usr/home/owner/researcher-live-cast
BACKUP=$STATE/shortcuts3-backup
RES=/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res
TERRA=/opt/usr/apps/com.samsung.tv.ContentsBrowser/shared/res/CompTerra.dll
SHARED=/opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted
hash() { sha256sum "$1" | cut -d' ' -f1; }
test -f "$STATE/shortcuts.applied"
test "$(hash "$RES/CompHome.dll")" = 925041eb259e9229cdda92f00211bca7dcac7dee7cf2b91a305d3b55e32e9209
test "$(hash "$TERRA")" = f743083fc773fa4507717db42414c0b01f860cd89098eaca5d6db80ecb9657fc
test "$(hash "$BACKUP/CompHome.before.dll")" = a459badb5665b6c1b60da459f4676cff0da1d231e63381fe83695331a4a4cade
test "$(hash "$BACKUP/CompTerra.before.dll")" = b085608b9da114f46b4cf162d9faf73f552fb5fe27d74cb37f8b6edc3ddf9c4f
app_launcher -k com.samsung.tv.home.media
sleep 1
cat "$BACKUP/CompHome.before.dll" > "$RES/CompHome.dll"
cat "$BACKUP/CompTerra.before.dll" > "$TERRA"
rm -f "$RES/HabibiHomeShortcuts.dll" "$RES/researcher-hdmi.svg" "$RES/researcher-cast.svg" "$RES/researcher-settings.svg"
rm -f "$SHARED/sqlite.db" "$SHARED/sqlite.db-journal" "$SHARED/db_ready"
cp -a "$BACKUP/sqlite.db" "$SHARED/sqlite.db"
if [ -f "$BACKUP/db_ready" ]; then cp -a "$BACKUP/db_ready" "$SHARED/db_ready"; fi
app_launcher -s com.samsung.tv.home.media
sleep 3
app_launcher -k com.samsung.tv.csfs
sleep 1
app_launcher -s com.samsung.tv.csfs
mv "$STATE/shortcuts.applied" "$STATE/shortcuts.restored"
echo CLEAN_TV_PLUS_HOME_RESTORED
