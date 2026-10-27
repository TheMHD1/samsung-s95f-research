set -eu
umask 077
RES=/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res
APPS=/opt/usr/apps/com.samsung.tv.store/shared/res/CompAppsTab.dll
TERRA=/opt/usr/apps/com.samsung.tv.ContentsBrowser/shared/res/CompTerra.dll
STAGE=/home/researcher/share/tmp/sdk_tools/researcher-live-cast
SHARED=/opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted
BACKUP=/opt/usr/home/owner/researcher-live-cast/apps-only-20261026-backup4
VISIBLE=/opt/usr/home/owner/researcher-live-cast/apps-only-20261026-backup3
hash() { sha256sum "$1" | cut -d' ' -f1; }
test "$(hash "$APPS")" = a1b2dfaad4d93fa5e1ed74867335c7e2d87f7f5712f1738a87bcfa815a51fdaf
test "$(hash "$RES/HabibiHomeShortcuts.dll")" = fea1274ae4b29a490400f5863aecd27eadce149eb86f03d59cf9ac5a7b926418
test "$(hash "$TERRA")" = 6b6c9fab9281bc97b785000d52e3e788da64ca2c6cf7773878afa2310e3ebe3e
test "$(hash "$STAGE/CompAppsTab.native4.dll")" = 5c164daf0737bfa91c451ea6a1e6bae9d08de057259fb4a1d057aa6f02e4b887
test "$(hash "$STAGE/HabibiHomeShortcuts.dll")" = c4c766703b6bd9643b5abe9713f59ee8fe1ea6991af66b33e9c94e16d1e22fa9
test "$(hash "$STAGE/HabibiNativeApps.json")" = 68c563d5f9b889373e678ffa2d8783db57a5cae58ca9fd0179f698a675c040bf
test ! -e "$BACKUP"
test ! -e "$RES/HabibiNativeApps.json"
mkdir -m 700 "$BACKUP"
cp -a "$APPS" "$BACKUP/CompAppsTab.dll"
cp -a "$RES/HabibiHomeShortcuts.dll" "$BACKUP/HabibiHomeShortcuts.dll"
app_launcher -k com.samsung.tv.home.media
sleep 1
cp -a "$SHARED/sqlite.db" "$BACKUP/sqlite.db"
if [ -f "$SHARED/db_ready" ]; then cp -a "$SHARED/db_ready" "$BACKUP/db_ready"; fi
rollback() {
 trap - EXIT
 sqlite3 -readonly "$SHARED/sqlite.db" "select componentID,visible,UIJson from TableEntity;" > "$BACKUP/failure-layout.txt" || true
 cat "$BACKUP/failure-layout.txt"
 app_launcher -k com.samsung.tv.home.media || true
 cat "$VISIBLE/CompAppsTab.dll" > "$APPS"
 cat "$VISIBLE/HabibiHomeShortcuts.dll" > "$RES/HabibiHomeShortcuts.dll"
 cat "$VISIBLE/CompTerra.dll" > "$TERRA"
 rm -f "$RES/HabibiNativeApps.json"
 rm -f "$SHARED/sqlite.db" "$SHARED/sqlite.db-journal" "$SHARED/sqlite.db-wal" "$SHARED/sqlite.db-shm" "$SHARED/db_ready"
 cp -a "$VISIBLE/sqlite.db" "$SHARED/sqlite.db"
 if [ -f "$VISIBLE/db_ready" ]; then cp -a "$VISIBLE/db_ready" "$SHARED/db_ready"; fi
 app_launcher -s com.samsung.tv.home.media
 echo PREVIOUS_NATIVE_HOME_RESTORED
}
trap rollback EXIT
cat "$STAGE/CompAppsTab.native4.dll" > "$APPS"
cat "$STAGE/HabibiHomeShortcuts.dll" > "$RES/HabibiHomeShortcuts.dll"
cp -a "$RES/researcher-settings.svg" "$RES/HabibiNativeApps.json"
cat "$STAGE/HabibiNativeApps.json" > "$RES/HabibiNativeApps.json"
rm -f "$SHARED/sqlite.db" "$SHARED/sqlite.db-journal" "$SHARED/db_ready"
app_launcher -s com.samsung.tv.home.media
sleep 7
query() { sqlite3 -readonly "$SHARED/sqlite.db" "$1"; }
query "select componentID,visible,elementFocusable,UIJson from TableEntity;"
test "$(query "select count(*) from TableEntity where componentID like 'd/ug.tab%';")" = 0
test "$(query "select count(*) from TableEntity where componentID='d/apps.tab' and visible=1;")" = 1
test "$(query "select count(*) from TableEntity where componentID like 'd/apps.tab.content@%' and componentID!='d/apps.tab.content@CategoryID_Content_DOWNLOADED';")" = 0
test "$(query "select count(*) from TableEntity where componentID like 'd/apps.tab.content.layer.tile@%' and visible=1 and elementFocusable=1;")" = 5
test "$(query "select count(*) from TableEntity where componentID like 'd/apps.tab.content.layer.tile@%' and (UIJson is null or length(UIJson)<30);")" = 0
sha256sum "$APPS" "$RES/HabibiHomeShortcuts.dll" "$RES/HabibiNativeApps.json"
trap - EXIT
app_launcher -k com.samsung.tv.csfs
sleep 1
app_launcher -s com.samsung.tv.csfs
echo NATIVE_APPS_ONLY_APPLIED
