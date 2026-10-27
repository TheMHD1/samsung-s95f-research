set -eu
STATE=/opt/usr/home/owner/researcher-debloat-20261025
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
if [ -f "$STATE/markers.created" ]; then
    while IFS= read -r marker; do
        case "$marker" in
            pisa-service) ;;
            com.samsung.tv.AICompanionAgent) ;;
            com.samsung.tv.ghdaemon) ;;
            samsunghealth-service-tv) ;;
            com.samsung.tv.farfieldvoice) ;;
            com.samsung.tv.ondevice-voice) ;;
            com.samsung.tv.wakeupless) ;;
            com.samsung.tv.bixby-prov) ;;
            com.samsung.tv.voiceid-service) ;;
            *) echo 'Unexpected marker; refusing restoration' >&2; exit 1 ;;
        esac
        target=/opt/usr/share/systemd/system/$marker
        if [ -e "$target" ] || [ -L "$target" ]; then
            test ! -L "$target"
            test "$(cat "$target")" = researcher-debloat-20261025
            rm -- "$target"
        fi
    done < "$STATE/markers.created"
fi
while IFS='|' read -r unit active; do
    case "$active" in active|activating) systemctl --no-block start "$unit" ;; esac
done < "$STATE/units.before"
while IFS= read -r app; do
    if awk -v a="$app" '$1 == a { found=1 } END { exit !found }' "$STATE/running.before"; then
        app_launcher -s "$app"
    fi
done < "$STATE/apps.changed"
printf '%s
' RESTORED > "$STATE/apply.status"
echo RESTORE_COMPLETE
