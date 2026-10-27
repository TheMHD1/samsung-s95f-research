set -eu
umask 077
STATE=/opt/usr/home/owner/researcher-live-cast
APP=/opt/usr/apps/com.samsung.tv.home.media/bin/HomeMedia.dll
SHARED=/opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted
PATCH=/home/researcher/share/tmp/sdk_tools/researcher-live-cast/HomeMedia.clean.dll
ORIGINAL=9cae06a13d771f98aaaf4ce476b5d6ada12e99f9e4d035512bf49c600008699b
CLEAN=b060915f3be4f2313b26bcedfd90d3700e8e47e2a0a0edc7a250513c5cdbd1ef
test "$(sha256sum "$APP" | cut -d' ' -f1)" = "$ORIGINAL"
test "$(sha256sum "$PATCH" | cut -d' ' -f1)" = "$CLEAN"
test ! -e "$STATE/provider-backup"
mkdir -m 700 "$STATE/provider-backup"
cp -a "$APP" "$STATE/provider-backup/HomeMedia.original.dll"
app_launcher -k com.samsung.tv.home.media
sleep 1
restore_provider() {
    trap - EXIT
    app_launcher -k com.samsung.tv.home.media || true
    cat "$STATE/provider-backup/HomeMedia.original.dll" > "$APP"
    # Restore the original cache inode, with its original permissions/labels.
    if [ -f "$STATE/provider-backup/sqlite.db" ]; then
        rm -f "$SHARED/sqlite.db-journal" "$SHARED/sqlite.db-wal" "$SHARED/sqlite.db-shm"
        mv -f "$STATE/provider-backup/sqlite.db" "$SHARED/sqlite.db"
    fi
    if [ -f "$STATE/provider-backup/db_ready" ]; then
        mv -f "$STATE/provider-backup/db_ready" "$SHARED/db_ready"
    fi
    app_launcher -s com.samsung.tv.home.media
    test "$(sha256sum "$APP" | cut -d' ' -f1)" = "$ORIGINAL"
    echo ORIGINAL_PROVIDER_RESTORED
}
trap restore_provider EXIT
mv "$SHARED/sqlite.db" "$STATE/provider-backup/sqlite.db"
if [ -f "$SHARED/sqlite.db-journal" ]; then mv "$SHARED/sqlite.db-journal" "$STATE/provider-backup/"; fi
if [ -f "$SHARED/db_ready" ]; then mv "$SHARED/db_ready" "$STATE/provider-backup/db_ready"; fi
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
printf 'COMPLETE\n' > "$STATE/home-provider.applied"
trap - EXIT
echo CLEAN_PROVIDER_ACTIVE
