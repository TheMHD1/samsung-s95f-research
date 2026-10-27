set -eu
RES=/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res
BACKUP=/opt/usr/home/owner/researcher-live-cast/streaming-20261026-backup
hash() { sha256sum "$1" | cut -d' ' -f1; }
test "$(hash "$RES/HabibiHomeShortcuts.dll")" = 52a122b374a696d932d8cc0bba25078271234db18927ada4ad2a9b3157f1beb8
test "$(hash "$BACKUP/HabibiHomeShortcuts.dll")" = 37e5ff4b5befa6e48d74a746b8a658d30266b47298af30420292a46447697391
app_launcher -k com.samsung.tv.home.media
sleep 1
cat "$BACKUP/HabibiHomeShortcuts.dll" > "$RES/HabibiHomeShortcuts.dll"
rm -f "$RES/researcher-netflix.svg" "$RES/researcher-prime.svg"
app_launcher -s com.samsung.tv.home.media
