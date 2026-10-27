set -eu
umask 077
RES=/opt/usr/apps/com.samsung.tv.coba.newhome/shared/res
APPS=/opt/usr/apps/com.samsung.tv.store/shared/res/CompAppsTab.dll
TERRA=/opt/usr/apps/com.samsung.tv.ContentsBrowser/shared/res/CompTerra.dll
SHARED=/opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted
BASE=/opt/usr/home/owner/researcher-live-cast/apps-only-20261026-backup3
SAVE=/opt/usr/home/owner/researcher-live-cast/apps-only-20261026-restored
hash() { sha256sum "$1" | cut -d' ' -f1; }
test "$(hash "$APPS")" = 5c164daf0737bfa91c451ea6a1e6bae9d08de057259fb4a1d057aa6f02e4b887
test "$(hash "$TERRA")" = 6b6c9fab9281bc97b785000d52e3e788da64ca2c6cf7773878afa2310e3ebe3e
test "$(hash "$RES/HabibiHomeShortcuts.dll")" = c4c766703b6bd9643b5abe9713f59ee8fe1ea6991af66b33e9c94e16d1e22fa9
test "$(hash "$RES/HabibiNativeApps.json")" = 68c563d5f9b889373e678ffa2d8783db57a5cae58ca9fd0179f698a675c040bf
test "$(hash "$BASE/CompAppsTab.dll")" = 3775f9034395384399fb312c47d937497aa145e8618bbcfdac3eeb48c566d10d
test "$(hash "$BASE/CompTerra.dll")" = f743083fc773fa4507717db42414c0b01f860cd89098eaca5d6db80ecb9657fc
test "$(hash "$BASE/HabibiHomeShortcuts.dll")" = 52a122b374a696d932d8cc0bba25078271234db18927ada4ad2a9b3157f1beb8
test -s "$BASE/sqlite.db"
test ! -e "$SAVE"
mkdir -m 700 "$SAVE"
cp -a "$APPS" "$SAVE/CompAppsTab.dll"
cp -a "$TERRA" "$SAVE/CompTerra.dll"
cp -a "$RES/HabibiHomeShortcuts.dll" "$RES/HabibiNativeApps.json" "$SAVE/"
app_launcher -k com.samsung.tv.csfs || true
app_launcher -k com.samsung.tv.home.media || true
sleep 1
cp -a "$SHARED/sqlite.db" "$SAVE/sqlite.db"
if [ -f "$SHARED/db_ready" ]; then cp -a "$SHARED/db_ready" "$SAVE/db_ready"; fi
# Preserve application ownership and SMACK labels by writing existing files in place.
cat "$BASE/CompAppsTab.dll" > "$APPS"
cat "$BASE/CompTerra.dll" > "$TERRA"
cat "$BASE/HabibiHomeShortcuts.dll" > "$RES/HabibiHomeShortcuts.dll"
rm -f "$RES/HabibiNativeApps.json"
for icon in researcher-spotify.svg researcher-jellyfin.svg researcher-tvplus.svg; do
 if [ -f "$RES/$icon" ]; then mv "$RES/$icon" "$SAVE/$icon"; fi
done
rm -f "$SHARED/sqlite.db" "$SHARED/sqlite.db-journal" "$SHARED/sqlite.db-wal" "$SHARED/sqlite.db-shm" "$SHARED/db_ready"
cp -a "$BASE/sqlite.db" "$SHARED/sqlite.db"
if [ -f "$BASE/db_ready" ]; then cp -a "$BASE/db_ready" "$SHARED/db_ready"; fi
app_launcher -s com.samsung.tv.home.media
sleep 3
app_launcher -s com.samsung.tv.csfs
sha256sum "$APPS" "$TERRA" "$RES/HabibiHomeShortcuts.dll"
echo PRE_APPS_ONLY_NATIVE_HOME_RESTORED_APPS_REMAIN_ENABLED
