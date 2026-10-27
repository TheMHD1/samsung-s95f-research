set -eu
umask 077
RES=/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res
APPS=/opt/usr/apps/com.samsung.tv.store/shared/res/CompAppsTab.dll
STAGE=/home/researcher/share/tmp/sdk_tools/researcher-live-cast
SHARED=/opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted
BACKUP=/opt/usr/home/owner/researcher-live-cast/apps-only-20261026-backup2
PKGDB=/opt/dbspace/.pkgmgr_parser.db
hash() { sha256sum "$1" | cut -d' ' -f1; }
test "$(hash "$RES/CompHome.dll")" = 925041eb259e9229cdda92f00211bca7dcac7dee7cf2b91a305d3b55e32e9209
test "$(hash "$APPS")" = 3775f9034395384399fb312c47d937497aa145e8618bbcfdac3eeb48c566d10d
test "$(hash "$RES/HabibiHomeShortcuts.dll")" = 52a122b374a696d932d8cc0bba25078271234db18927ada4ad2a9b3157f1beb8
test "$(hash "$STAGE/CompHome.apps-only.dll")" = bccf9543e5e8475e9885c4e361c51ff901501632f181117d007954694a0ee890
test "$(hash "$STAGE/CompAppsTab.apps-only.dll")" = 00979765df87108eb2a416febd5950b8b6a337fdf31d39096cdcc21ef9f5fdbb
test "$(hash "$STAGE/HabibiHomeShortcuts.dll")" = fea1274ae4b29a490400f5863aecd27eadce149eb86f03d59cf9ac5a7b926418
test "$(hash "$STAGE/researcher-spotify.svg")" = bb22b83ad31a7a5fd6b84f1d001c8d4d6ef33b4915bd568e7eb4744ded737073
test "$(hash "$STAGE/researcher-jellyfin.svg")" = c44e09882dd10aae6fb3c37c0685a1d92178d281c2282e043e84b1853dc9c8c9
test "$(hash "$STAGE/researcher-tvplus.svg")" = c73dd62c86c5a7219c20f1cf23e4fa2dd8b8c32747b1701220a01dd68eaa7e86
test ! -e "$BACKUP"
for NAME in spotify jellyfin tvplus; do test ! -e "$RES/researcher-$NAME.svg"; done
for APP in rJeHak5zRg.Spotify rTn6ClEurC.Jellyfin; do test "$(sqlite3 -readonly "$PKGDB" "select app_disable from package_app_info where app_id='$APP';")" = true; done
mkdir -m 700 "$BACKUP"
cp -a "$RES/CompHome.dll" "$BACKUP/CompHome.dll"
cp -a "$RES/HabibiHomeShortcuts.dll" "$BACKUP/HabibiHomeShortcuts.dll"
cp -a "$APPS" "$BACKUP/CompAppsTab.dll"
sqlite3 -readonly "$PKGDB" "select app_id,app_disable from package_app_info where app_id in ('rJeHak5zRg.Spotify','rTn6ClEurC.Jellyfin');" > "$BACKUP/apps.before"
app_launcher -k com.samsung.tv.home.media
sleep 1
test ! -s "$SHARED/sqlite.db-wal"
cp -a "$SHARED/sqlite.db" "$BACKUP/sqlite.db"
if [ -f "$SHARED/db_ready" ]; then cp -a "$SHARED/db_ready" "$BACKUP/db_ready"; fi
rollback() {
 trap - EXIT
 sqlite3 -readonly "$SHARED/sqlite.db" "select componentID,visible,elementFocusable,childEntityList from TableEntity;" > "$BACKUP/failure-layout.txt" || true
 cat "$BACKUP/failure-layout.txt"
 app_launcher -k com.samsung.tv.home.media || true
 cat "$BACKUP/CompHome.dll" > "$RES/CompHome.dll"
 cat "$BACKUP/HabibiHomeShortcuts.dll" > "$RES/HabibiHomeShortcuts.dll"
 cat "$BACKUP/CompAppsTab.dll" > "$APPS"
 for NAME in spotify jellyfin tvplus; do rm -f "$RES/researcher-$NAME.svg"; done
 rm -f "$SHARED/sqlite.db" "$SHARED/sqlite.db-journal" "$SHARED/sqlite.db-wal" "$SHARED/sqlite.db-shm" "$SHARED/db_ready"
 cp -a "$BACKUP/sqlite.db" "$SHARED/sqlite.db"
 if [ -f "$BACKUP/db_ready" ]; then cp -a "$BACKUP/db_ready" "$SHARED/db_ready"; fi
 for APP in rJeHak5zRg.Spotify rTn6ClEurC.Jellyfin; do pkgcmd -D -t app -n "$APP" --uid 5001 || true; done
 app_launcher -s com.samsung.tv.home.media
 echo APPS_ONLY_AUTOMATICALLY_ROLLED_BACK
}
trap rollback EXIT
for APP in rJeHak5zRg.Spotify rTn6ClEurC.Jellyfin; do pkgcmd -A -t app -n "$APP" --uid 5001; done
for NAME in spotify jellyfin tvplus; do cp -a "$RES/researcher-settings.svg" "$RES/researcher-$NAME.svg"; cat "$STAGE/researcher-$NAME.svg" > "$RES/researcher-$NAME.svg"; done
cat "$STAGE/CompHome.apps-only.dll" > "$RES/CompHome.dll"
cat "$STAGE/CompAppsTab.apps-only.dll" > "$APPS"
cat "$STAGE/HabibiHomeShortcuts.dll" > "$RES/HabibiHomeShortcuts.dll"
rm -f "$SHARED/sqlite.db" "$SHARED/sqlite.db-journal" "$SHARED/db_ready"
app_launcher -s com.samsung.tv.home.media
sleep 7
query() { sqlite3 -readonly "$SHARED/sqlite.db" "$1"; }
echo CHECK_APPS_TAB
query "select componentID,visible,elementFocusable,childEntityList from TableEntity;"
test "$(query "select count(*) from TableEntity where componentID='d/apps.tab' and visible=1;")" = 1
echo CHECK_OLD_TABS
test "$(query "select count(*) from TableEntity where componentID like 'd/ug.tab%';")" = 0
echo CHECK_RECOMMENDATIONS
test "$(query "select count(*) from TableEntity where componentID like 'd/apps.tab.content%' or componentID like 'd/dhcategory%' or componentID like 'd/topbanner%';")" = 0
echo CHECK_FIVE_TILES
test "$(query "select count(*) from TableEntity where componentID like 'd/owner.shortcut@%' and visible=1 and elementFocusable=1;")" = 5
for NAME in Spotify Prime Netflix Jellyfin TVPlus; do test "$(query "select count(*) from TableEntity where componentID='d/owner.shortcut@$NAME' and visible=1 and elementFocusable=1;")" = 1; done
for APP in rJeHak5zRg.Spotify rTn6ClEurC.Jellyfin; do test "$(sqlite3 -readonly "$PKGDB" "select app_disable from package_app_info where app_id='$APP';")" = false; done
query "select componentID,visible,childEntityList,elementIndex,elementID from TableEntity;"
systemctl is-active muse-server.service source-service.service pulseaudio.service connman.service com.samsung.tv.airplay-service-2.service com.samsung.tv.googlecast-service.service
sha256sum "$RES/CompHome.dll" "$APPS" "$RES/HabibiHomeShortcuts.dll"
trap - EXIT
app_launcher -k com.samsung.tv.csfs
sleep 1
app_launcher -s com.samsung.tv.csfs
echo APPS_ONLY_APPLIED
