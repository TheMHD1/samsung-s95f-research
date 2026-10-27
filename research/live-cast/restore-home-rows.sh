set -eu
STATE=/opt/usr/home/owner/researcher-live-cast
TERRA=/opt/usr/apps/com.samsung.tv.ContentsBrowser/shared/res/CompTerra.dll
HOME=/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res/CompHome.dll
SHARED=/opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted
BACKUP=$STATE/rows-backup
hash() { sha256sum "$1" | cut -d' ' -f1; }
test "$(hash "$TERRA")" = b085608b9da114f46b4cf162d9faf73f552fb5fe27d74cb37f8b6edc3ddf9c4f
test "$(hash "$HOME")" = a459badb5665b6c1b60da459f4676cff0da1d231e63381fe83695331a4a4cade
test "$(hash "$BACKUP/CompTerra.original.dll")" = b05655edcc7de8557e306cb980d4098ae2a1f79db69b0b215b2dfafc7b7fe9f1
test "$(hash "$BACKUP/CompHome.original.dll")" = ec4541301a818efd308461c900efde0524f2243226c2db951b1f63674fcff35f
app_launcher -k com.samsung.tv.home.media
sleep 1
cat "$BACKUP/CompTerra.original.dll" > "$TERRA"
cat "$BACKUP/CompHome.original.dll" > "$HOME"
if [ -f "$BACKUP/sqlite.db" ]; then
    rm -f "$SHARED/sqlite.db-journal" "$SHARED/sqlite.db-wal" "$SHARED/sqlite.db-shm"
    mv -f "$BACKUP/sqlite.db" "$SHARED/sqlite.db"
fi
if [ -f "$BACKUP/db_ready" ]; then mv -f "$BACKUP/db_ready" "$SHARED/db_ready"; fi
app_launcher -s com.samsung.tv.home.media
sleep 3
app_launcher -s com.samsung.tv.csfs
test "$(hash "$TERRA")" = b05655edcc7de8557e306cb980d4098ae2a1f79db69b0b215b2dfafc7b7fe9f1
test "$(hash "$HOME")" = ec4541301a818efd308461c900efde0524f2243226c2db951b1f63674fcff35f
mv "$STATE/home-rows.applied" "$STATE/home-rows.reverted"
echo ORIGINAL_HOME_ROWS_RESTORED
