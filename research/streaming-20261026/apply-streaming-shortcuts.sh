set -eu
umask 077
RES=/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res
STAGE=/home/researcher/share/tmp/sdk_tools/researcher-live-cast
BACKUP=/opt/usr/home/owner/researcher-live-cast/streaming-20261026-backup
DB=/opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted/sqlite.db
hash() { sha256sum "$1" | cut -d' ' -f1; }
test "$(hash "$RES/HabibiHomeShortcuts.dll")" = 37e5ff4b5befa6e48d74a746b8a658d30266b47298af30420292a46447697391
test "$(hash "$STAGE/HabibiHomeShortcuts.dll")" = 52a122b374a696d932d8cc0bba25078271234db18927ada4ad2a9b3157f1beb8
test ! -e "$BACKUP"
test ! -e "$RES/researcher-netflix.svg"
test ! -e "$RES/researcher-prime.svg"
mkdir -m 700 "$BACKUP"
cp -a "$RES/HabibiHomeShortcuts.dll" "$BACKUP/HabibiHomeShortcuts.dll"
app_launcher -k com.samsung.tv.home.media
sleep 1
rollback() {
 trap - EXIT
 app_launcher -k com.samsung.tv.home.media || true
 cat "$BACKUP/HabibiHomeShortcuts.dll" > "$RES/HabibiHomeShortcuts.dll"
 rm -f "$RES/researcher-netflix.svg" "$RES/researcher-prime.svg"
 app_launcher -s com.samsung.tv.home.media
 echo STREAMING_SHORTCUTS_ROLLED_BACK
}
trap rollback EXIT
for NAME in netflix prime; do
 cp -a "$RES/researcher-settings.svg" "$RES/researcher-$NAME.svg"
 cat "$STAGE/researcher-$NAME.svg" > "$RES/researcher-$NAME.svg"
done
cat "$STAGE/HabibiHomeShortcuts.dll" > "$RES/HabibiHomeShortcuts.dll"
app_launcher -s com.samsung.tv.home.media
sleep 5
for NAME in Netflix Prime; do
 test "$(sqlite3 -readonly "$DB" "select count(*) from TableEntity where componentID='d/owner.shortcut@$NAME' and visible=1 and elementCount=1;")" -ge 1
done
test "$(sqlite3 -readonly "$DB" "select count(*) from TableEntity where componentID like 'd/dhcategory%' or componentID like 'd/topbanner%' or componentID='d/recent.row@OnNow';")" = 0
sqlite3 -readonly "$DB" "select componentID,visible,elementCount,elementFocusable from TableEntity where componentID like 'd/owner.shortcut%' or componentID='s/livetv@TVPLUS';"
systemctl is-active muse-server.service source-service.service com.samsung.tv.googlecast-service.service com.samsung.tv.airplay-service-2.service
sha256sum "$RES/HabibiHomeShortcuts.dll"
trap - EXIT
echo STREAMING_SHORTCUTS_APPLIED
