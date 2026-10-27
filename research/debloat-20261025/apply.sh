set -eu
umask 077
STATE=/opt/usr/home/owner/researcher-debloat-20261025
DB=/opt/dbspace/.pkgmgr_parser.db
test -d "$STATE"
test ! -L "$STATE"
test ! -e "$STATE/apps.before"
APPS='com.samsung.tizen.samsung-analytics
com.samsung.tv.acr
com.samsung.tv.adagent-service
com.samsung.tv.pisa-service
com.samsung.tv.targeted-ad-service
org.tizen.voice-app
org.tizen.voice-app-service
org.tizen.multi-assistant-service
com.samsung.tv.farfieldvoice
com.samsung.tv.alexa-client
com.samsung.tv.alexa-fullscreen-app
com.samsung.tv.wakeup-engine-bixby
com.samsung.tv.wakeup-engine-alexa
com.samsung.tv.ondevice-voice
com.samsung.tv.bixby-prov
com.samsung.tv.wakeupless
com.samsung.tv.voiceid-service
com.samsung.tv.voice-instant-app
org.tizen.voice-client
com.samsung.tv.AICompanionAgent
com.samsung.tv.AICompanionUILauncher
com.samsung.tv.AICompanionUI
com.samsung.tv.AICompanionUINotice
com.samsung.tv.gaminghub
com.samsung.tv.ghdaemon
com.samsung.tv.samsung-health
samsunghealth-service-tv
com.samsung.tv.health-mde-service
com.samsung.tv.health-mde-service-view
com.samsung.tv.health-mde-workout-tracker
com.samsung.tv.health-mde-setting'
MARKERS='pisa-service
com.samsung.tv.AICompanionAgent
com.samsung.tv.ghdaemon
samsunghealth-service-tv
com.samsung.tv.farfieldvoice
com.samsung.tv.ondevice-voice
com.samsung.tv.wakeupless
com.samsung.tv.bixby-prov
com.samsung.tv.voiceid-service'
UNITS='adagent-service.service
pisa-service.service
pisa-service.socket
com.samsung.tv.AICompanionAgent.service
com.samsung.tv.ghdaemon.service
samsunghealth-service-tv.service
com.samsung.tv.farfieldvoice.service
com.samsung.tv.ondevice-voice.service
com.samsung.tv.wakeupless.service
com.samsung.tv.bixby-prov.service
com.samsung.tv.voiceid-service.service
org.tizen.multi-assistant-service.service'

# Validate every selected original state before making the first change.
for app in $APPS; do
    flag=$(sqlite3 -readonly "$DB" "select app_disable from package_app_info where app_id='$app';")
    test "$flag" = false
    printf '%s|%s
' "$app" "$flag" >> "$STATE/apps.pending"
done
mv "$STATE/apps.pending" "$STATE/apps.before"
app_launcher --status > "$STATE/running.before"
for unit in $UNITS; do
    active=$(systemctl show "$unit" -p ActiveState --value)
    printf '%s|%s
' "$unit" "$active" >> "$STATE/units.before"
done
for marker in $MARKERS; do
    target=/opt/usr/share/systemd/system/$marker
    if [ ! -e "$target" ] && [ ! -L "$target" ]; then
        # Record intent before writing. Restoration checks our exact content.
        printf '%s
' "$marker" >> "$STATE/markers.created"
        (set -C; printf '%s
' researcher-debloat-20261025 > "$target")
    fi
done
for app in $APPS; do
    printf '%s
' "$app" >> "$STATE/apps.changed"
    pkgcmd -D -t app -n "$app" --uid 5001
    flag=$(sqlite3 -readonly "$DB" "select app_disable from package_app_info where app_id='$app';")
    test "$flag" = true
    echo DISABLED:$app
done
# Stop only the approved components. Package contents remain installed.
for unit in $UNITS; do
    echo STOP_UNIT:$unit
    systemctl --no-block stop "$unit"
done
app_launcher --status > "$STATE/running.after-disable"
for app in $APPS; do
    if awk -v a="$app" '$1 == a { found=1 } END { exit !found }' "$STATE/running.after-disable"; then
        echo STOP_APP:$app
        app_launcher -k "$app"
    fi
done
printf '%s
' COMPLETE > "$STATE/apply.status"
echo APPLY_COMPLETE
