set -eu
STATE=/opt/usr/home/owner/researcher-live-cast
DB=/opt/dbspace/.pkgmgr_parser.db
test -f "$STATE/apps.before"
# Activate only entries originally enabled and changed by this operation.
while IFS= read -r app; do
    grep -Fx "$app|false" "$STATE/apps.before" >/dev/null
    current=$(sqlite3 -readonly "$DB" "select app_disable from package_app_info where app_id='$app';")
    if [ "$current" = true ]; then
        pkgcmd -A -t app -n "$app" --uid 5001
    else
        test "$current" = false
    fi
    test "$(sqlite3 -readonly "$DB" "select app_disable from package_app_info where app_id='$app';")" = false
done < "$STATE/apps.changed"
printf '%s\n' RESTORED > "$STATE/apply.status"
echo RESTORE_COMPLETE
