set -eu
umask 077
RECOVERY=/opt/usr/home/owner/researcher-live-cast/populated-home-recovery-20261026
RES=/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res
APPS=/opt/usr/apps/com.samsung.tv.store/shared/res/CompAppsTab.dll
TERRA=/opt/usr/apps/com.samsung.tv.ContentsBrowser/shared/res/CompTerra.dll
ROWS=/opt/usr/home/owner/researcher-live-cast/rows-backup
hash() { sha256sum "$1" | cut -d' ' -f1; }
test ! -e "$RECOVERY"
test "$(hash "$APPS")" = 3775f9034395384399fb312c47d937497aa145e8618bbcfdac3eeb48c566d10d
test "$(hash "$RES/CompHome.dll")" = 925041eb259e9229cdda92f00211bca7dcac7dee7cf2b91a305d3b55e32e9209
test "$(hash "$TERRA")" = f743083fc773fa4507717db42414c0b01f860cd89098eaca5d6db80ecb9657fc
test "$(hash "$ROWS/CompHome.original.dll")" = ec4541301a818efd308461c900efde0524f2243226c2db951b1f63674fcff35f
test "$(hash "$ROWS/CompTerra.original.dll")" = b05655edcc7de8557e306cb980d4098ae2a1f79db69b0b215b2dfafc7b7fe9f1
mkdir -m 700 "$RECOVERY"
cp -a "$RES/CompHome.dll" "$RES/HabibiHomeShortcuts.dll" "$TERRA" "$APPS" "$RECOVERY/"
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

set -eu
STATE=/opt/usr/home/owner/researcher-live-cast
TERRA=/opt/usr/apps/com.samsung.tv.ContentsBrowser/shared/res/CompTerra.dll
APP_HOME=/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res/CompHome.dll
SHARED=/opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted
BACKUP=$STATE/rows-backup
hash() { sha256sum "$1" | cut -d' ' -f1; }
test "$(hash "$TERRA")" = b085608b9da114f46b4cf162d9faf73f552fb5fe27d74cb37f8b6edc3ddf9c4f
test "$(hash "$APP_HOME")" = a459badb5665b6c1b60da459f4676cff0da1d231e63381fe83695331a4a4cade
test "$(hash "$BACKUP/CompTerra.original.dll")" = b05655edcc7de8557e306cb980d4098ae2a1f79db69b0b215b2dfafc7b7fe9f1
test "$(hash "$BACKUP/CompHome.original.dll")" = ec4541301a818efd308461c900efde0524f2243226c2db951b1f63674fcff35f
app_launcher -k com.samsung.tv.home.media
sleep 1
cat "$BACKUP/CompTerra.original.dll" > "$TERRA"
cat "$BACKUP/CompHome.original.dll" > "$APP_HOME"
if [ -f "$BACKUP/sqlite.db" ]; then
    rm -f "$SHARED/sqlite.db-journal" "$SHARED/sqlite.db-wal" "$SHARED/sqlite.db-shm"
    cp -a "$BACKUP/sqlite.db" "$SHARED/sqlite.db"
fi
if [ -f "$BACKUP/db_ready" ]; then cp -a "$BACKUP/db_ready" "$SHARED/db_ready"; fi
app_launcher -s com.samsung.tv.home.media
sleep 3
app_launcher -s com.samsung.tv.csfs
test "$(hash "$TERRA")" = b05655edcc7de8557e306cb980d4098ae2a1f79db69b0b215b2dfafc7b7fe9f1
test "$(hash "$APP_HOME")" = ec4541301a818efd308461c900efde0524f2243226c2db951b1f63674fcff35f
mv "$STATE/home-rows.applied" "$STATE/home-rows.reverted"
echo ORIGINAL_HOME_ROWS_RESTORED
