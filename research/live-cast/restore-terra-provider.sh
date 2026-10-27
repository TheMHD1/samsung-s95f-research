set -eu
STATE=/opt/usr/home/owner/researcher-live-cast
APP=/opt/usr/apps/com.samsung.tv.ContentsBrowser/shared/res/CompTerra.dll
SHARED=/opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted
test "$(sha256sum "$APP" | cut -d' ' -f1)" = b23f5e1797e846b0b55bba582dcdd1cf5582036a7d4320b446cfb942c836a066
test "$(sha256sum "$STATE/terra-backup/CompTerra.original.dll" | cut -d' ' -f1)" = b05655edcc7de8557e306cb980d4098ae2a1f79db69b0b215b2dfafc7b7fe9f1
app_launcher -k com.samsung.tv.home.media
sleep 1
cat "$STATE/terra-backup/CompTerra.original.dll" > "$APP"
rm -f "$SHARED/sqlite.db-journal" "$SHARED/sqlite.db-wal" "$SHARED/sqlite.db-shm"
mv -f "$STATE/terra-backup/sqlite.db" "$SHARED/sqlite.db"
if [ -f "$STATE/terra-backup/db_ready" ]; then mv -f "$STATE/terra-backup/db_ready" "$SHARED/db_ready"; fi
app_launcher -s com.samsung.tv.home.media
sleep 3
app_launcher -s com.samsung.tv.csfs
test "$(sha256sum "$APP" | cut -d' ' -f1)" = b05655edcc7de8557e306cb980d4098ae2a1f79db69b0b215b2dfafc7b7fe9f1
mv "$STATE/terra-provider.applied" "$STATE/terra-provider.reverted"
echo ORIGINAL_HOME_PROVIDER_RESTORED
