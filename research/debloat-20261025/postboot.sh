set -eu
echo BOOT_ID
cat /proc/sys/kernel/random/boot_id
set -eu
STATE=/opt/usr/home/owner/researcher-debloat-20261025
echo DISABLE_FLAGS
sqlite3 -readonly -header -separator '|' /opt/dbspace/.pkgmgr_parser.db "select app_id,app_disable from package_app_info where app_id in ('com.samsung.tizen.samsung-analytics','com.samsung.tv.acr','com.samsung.tv.adagent-service','com.samsung.tv.pisa-service','com.samsung.tv.targeted-ad-service','org.tizen.voice-app','org.tizen.voice-app-service','org.tizen.multi-assistant-service','com.samsung.tv.farfieldvoice','com.samsung.tv.alexa-client','com.samsung.tv.alexa-fullscreen-app','com.samsung.tv.wakeup-engine-bixby','com.samsung.tv.wakeup-engine-alexa','com.samsung.tv.ondevice-voice','com.samsung.tv.bixby-prov','com.samsung.tv.wakeupless','com.samsung.tv.voiceid-service','com.samsung.tv.voice-instant-app','org.tizen.voice-client','com.samsung.tv.AICompanionAgent','com.samsung.tv.AICompanionUILauncher','com.samsung.tv.AICompanionUI','com.samsung.tv.AICompanionUINotice','com.samsung.tv.gaminghub','com.samsung.tv.ghdaemon','com.samsung.tv.samsung-health','samsunghealth-service-tv','com.samsung.tv.health-mde-service','com.samsung.tv.health-mde-service-view','com.samsung.tv.health-mde-workout-tracker','com.samsung.tv.health-mde-setting') order by app_id;"
echo RUNNING_APPS
app_launcher --status
echo PROCESS_SNAPSHOT
ps -eo pid,uid,rss,comm
echo CORE_UNITS
systemctl show muse-server.service connman.service sdbd.service display-manager.service source-service.service sound-server.service org.tizen.ssoservice.service org.tizen.webappservice.service com.samsung.tv.airplay-service-2.service com.samsung.tv.googlecast-service.service -p Id -p LoadState -p ActiveState -p MainPID -p NRestarts
echo FAILED_UNITS
systemctl --failed --no-pager --no-legend
echo SELECTED_UNITS
while IFS='|' read -r unit active; do
    systemctl show "$unit" -p Id -p ActiveState -p MainPID
done < "$STATE/units.before"
echo PRESERVED_FLAGS
sqlite3 -readonly -header -separator '|' /opt/dbspace/.pkgmgr_parser.db "select app_id,app_disable from package_app_info where app_id in ('org.tizen.netflix-app','org.tizen.primevideo','com.samsung.tv.cobalt-yt','org.tizen.menu','org.tizen.browser','org.tizen.tv-viewer','org.tizen.tts-engine-neural','com.samsung.tv.airplay-app-2','org.tizen.ScreenMirroring-app-tv','com.samsung.tv.coba.edenview','com.samsung.tv.home.media');"
echo BACKUP_FILES
for name in apps.before apps.changed units.before markers.created running.before running.after-disable apply.status; do
    echo FILE:$name
    cat "$STATE/$name"
done
echo MEMORY
head -6 /proc/meminfo
echo UPTIME
cat /proc/uptime

echo REBOOT_UNIT
systemctl show researcher-debloat-reboot.service -p LoadState -p ActiveState -p Result -p ExecMainCode -p ExecMainStatus -p ExecStart
