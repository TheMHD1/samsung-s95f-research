set -eu
RES=/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res
NEW=/home/researcher/share/tmp/sdk_tools/researcher-live-cast/HabibiHomeShortcuts.dll
test "$(sha256sum "$RES/HabibiHomeShortcuts.dll" | cut -d' ' -f1)" = 340d51e124ebc7f61d103d22c50542d1649d3925ef26ff443dfbdd83bacc9e07
test "$(sha256sum "$NEW" | cut -d' ' -f1)" = 37e5ff4b5befa6e48d74a746b8a658d30266b47298af30420292a46447697391
app_launcher -k com.samsung.tv.home.media
sleep 1
cp -a "$RES/HabibiHomeShortcuts.dll" /opt/usr/home/owner/researcher-live-cast/shortcuts3-backup/HabibiHomeShortcuts.v1.dll
cat "$NEW" > "$RES/HabibiHomeShortcuts.dll"
app_launcher -s com.samsung.tv.home.media
sleep 4
sqlite3 -readonly /opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted/sqlite.db "select componentID,visible from TableEntity where componentID like 'd/owner.shortcut%' limit 7;"
sha256sum "$RES/HabibiHomeShortcuts.dll"
