set -eu
umask 077
STATE=/opt/usr/home/owner/researcher-live-cast
APP=/opt/usr/apps/com.samsung.tv.ContentsBrowser/shared/res/CompTerra.dll
SHARED=/opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted
PATCH=/home/researcher/share/tmp/sdk_tools/researcher-live-cast/CompTerra.clean.dll
ORIGINAL=b05655edcc7de8557e306cb980d4098ae2a1f79db69b0b215b2dfafc7b7fe9f1
CLEAN=b23f5e1797e846b0b55bba582dcdd1cf5582036a7d4320b446cfb942c836a066
test "$(sha256sum "$APP" | cut -d' ' -f1)" = "$ORIGINAL"
test "$(sha256sum "$PATCH" | cut -d' ' -f1)" = "$CLEAN"
test ! -e "$STATE/terra-backup"
mkdir -m 700 "$STATE/terra-backup"
cp -a "$APP" "$STATE/terra-backup/CompTerra.original.dll"
app_launcher -k com.samsung.tv.home.media
sleep 1
restore_provider() {
    trap - EXIT
    app_launcher -k com.samsung.tv.home.media || true
    cat "$STATE/terra-backup/CompTerra.original.dll" > "$APP"
    # Restore the original cache inode, with its original permissions/labels.
    if [ -f "$STATE/terra-backup/sqlite.db" ]; then
        rm -f "$SHARED/sqlite.db-journal" "$SHARED/sqlite.db-wal" "$SHARED/sqlite.db-shm"
        mv -f "$STATE/terra-backup/sqlite.db" "$SHARED/sqlite.db"
    fi
    if [ -f "$STATE/terra-backup/db_ready" ]; then
        mv -f "$STATE/terra-backup/db_ready" "$SHARED/db_ready"
    fi
    app_launcher -s com.samsung.tv.home.media
    test "$(sha256sum "$APP" | cut -d' ' -f1)" = "$ORIGINAL"
    echo ORIGINAL_PROVIDER_RESTORED
}
trap restore_provider EXIT
mv "$SHARED/sqlite.db" "$STATE/terra-backup/sqlite.db"
if [ -f "$SHARED/sqlite.db-journal" ]; then mv "$SHARED/sqlite.db-journal" "$STATE/terra-backup/"; fi
if [ -f "$SHARED/db_ready" ]; then mv "$SHARED/db_ready" "$STATE/terra-backup/db_ready"; fi
cat "$PATCH" > "$APP"
app_launcher -s com.samsung.tv.home.media
sleep 5
echo REBUILT_HOME
test -f "$SHARED/sqlite.db"
sqlite3 -readonly -header "$SHARED/sqlite.db" "select componentID,visible,elementCount from TableEntity where componentID not like '%.tile@%' limit 35;"
test "$(sqlite3 -readonly "$SHARED/sqlite.db" "select count(*) from TableEntity where componentID='s/firstscreen';")" = 1
test "$(sqlite3 -readonly "$SHARED/sqlite.db" "select count(*) from TableEntity where componentID like 'd/ug.tab%' or componentID like 'd/dhcategory@TerraCategory_22_%';")" = 0
app_launcher --status | grep -F 'com.samsung.tv.home.media ('
test "$(sha256sum "$APP" | cut -d' ' -f1)" = "$CLEAN"
printf 'COMPLETE\n' > "$STATE/terra-provider.applied"
trap - EXIT
echo CLEAN_PROVIDER_ACTIVE
