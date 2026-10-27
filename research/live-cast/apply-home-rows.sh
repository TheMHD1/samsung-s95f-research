set -eu
umask 077
STATE=/opt/usr/home/owner/researcher-live-cast
TERRA=/opt/usr/apps/com.samsung.tv.ContentsBrowser/shared/res/CompTerra.dll
HOME=/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res/CompHome.dll
SHARED=/opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted
STAGE=/home/researcher/share/tmp/sdk_tools/researcher-live-cast
BACKUP=$STATE/rows-backup
hash() { sha256sum "$1" | cut -d' ' -f1; }
test "$(hash "$TERRA")" = b05655edcc7de8557e306cb980d4098ae2a1f79db69b0b215b2dfafc7b7fe9f1
test "$(hash "$HOME")" = ec4541301a818efd308461c900efde0524f2243226c2db951b1f63674fcff35f
test "$(hash "$STAGE/CompTerra.rows.dll")" = b085608b9da114f46b4cf162d9faf73f552fb5fe27d74cb37f8b6edc3ddf9c4f
test "$(hash "$STAGE/CompHome.rows.dll")" = a459badb5665b6c1b60da459f4676cff0da1d231e63381fe83695331a4a4cade
test ! -e "$BACKUP"
mkdir -m 700 "$BACKUP"
cp -a "$TERRA" "$BACKUP/CompTerra.original.dll"
cp -a "$HOME" "$BACKUP/CompHome.original.dll"
app_launcher -k com.samsung.tv.home.media
sleep 1
restore_rows() {
    trap - EXIT
    app_launcher -k com.samsung.tv.home.media || true
    cat "$BACKUP/CompTerra.original.dll" > "$TERRA"
    cat "$BACKUP/CompHome.original.dll" > "$HOME"
    if [ -f "$BACKUP/sqlite.db" ]; then
        rm -f "$SHARED/sqlite.db-journal" "$SHARED/sqlite.db-wal" "$SHARED/sqlite.db-shm"
        mv -f "$BACKUP/sqlite.db" "$SHARED/sqlite.db"
    fi
    if [ -f "$BACKUP/db_ready" ]; then mv -f "$BACKUP/db_ready" "$SHARED/db_ready"; fi
    app_launcher -s com.samsung.tv.home.media
    echo ORIGINAL_HOME_ROWS_RESTORED
}
trap restore_rows EXIT
mv "$SHARED/sqlite.db" "$BACKUP/sqlite.db"
if [ -f "$SHARED/sqlite.db-journal" ]; then mv "$SHARED/sqlite.db-journal" "$BACKUP/"; fi
if [ -f "$SHARED/db_ready" ]; then mv "$SHARED/db_ready" "$BACKUP/db_ready"; fi
cat "$STAGE/CompTerra.rows.dll" > "$TERRA"
cat "$STAGE/CompHome.rows.dll" > "$HOME"
app_launcher -s com.samsung.tv.home.media
sleep 5
test -f "$SHARED/sqlite.db"
query() { sqlite3 -readonly "$SHARED/sqlite.db" "$1"; }
echo NATIVE_HOME_GRAPH
sqlite3 -readonly -header "$SHARED/sqlite.db" "select componentID,visible,elementCount,childEntityList from TableEntity where componentID not like '%.tile@%' limit 35;"
test "$(query "select count(*) from TableEntity where componentID='s/firstscreen';")" = 1
test "$(query "select count(*) from TableEntity where componentID='d/tabs' and visible=1;")" = 1
test "$(query "select count(*) from TableEntity where componentID='d/launcher' and visible=1;")" -ge 1
test "$(query "select count(*) from TableEntity where componentID='s/livetv@TVPLUS';")" -ge 1
test "$(query "select count(*) from TableEntity where componentID like 'd/dhcategory%' or componentID like 'd/topbanner%';")" = 0
app_launcher --status | grep -F 'com.samsung.tv.home.media ('
test "$(hash "$TERRA")" = b085608b9da114f46b4cf162d9faf73f552fb5fe27d74cb37f8b6edc3ddf9c4f
test "$(hash "$HOME")" = a459badb5665b6c1b60da459f4676cff0da1d231e63381fe83695331a4a4cade
printf 'COMPLETE\n' > "$STATE/home-rows.applied"
trap - EXIT
app_launcher -s com.samsung.tv.csfs
echo FILTERED_HOME_ROWS_ACTIVE
