set -eu
echo PLANSTATE
sqlite3 -readonly -header -separator "|" /opt/dbspace/.pkgmgr_parser.db "select app_id,package,app_disable from package_app_info where app_id in ('com.samsung.tizen.samsung-analytics','com.samsung.tv.acr','com.samsung.tv.adagent-service','com.samsung.tv.pisa-service','com.samsung.tv.targeted-ad-service','org.tizen.voice-app','org.tizen.voice-app-service','org.tizen.multi-assistant-service','com.samsung.tv.farfieldvoice','com.samsung.tv.alexa-client','com.samsung.tv.alexa-fullscreen-app','com.samsung.tv.wakeup-engine-bixby','com.samsung.tv.wakeup-engine-alexa','com.samsung.tv.ondevice-voice','com.samsung.tv.bixby-prov','com.samsung.tv.wakeupless','com.samsung.tv.voiceid-service','com.samsung.tv.voice-instant-app','org.tizen.voice-client','com.samsung.tv.AICompanionAgent','com.samsung.tv.AICompanionUILauncher','com.samsung.tv.AICompanionUI','com.samsung.tv.AICompanionUINotice','com.samsung.tv.gaminghub','com.samsung.tv.ghdaemon','com.samsung.tv.samsung-health','samsunghealth-service-tv','com.samsung.tv.health-mde-service','com.samsung.tv.health-mde-service-view','com.samsung.tv.health-mde-workout-tracker','com.samsung.tv.health-mde-setting') order by app_id;"
echo ASSISTANTMANIFEST
cat /opt/usr/apps/org.tizen.multi-assistant-service/tizen-manifest.xml
echo ANALYTICSBINARY
base64 /usr/bin/media-analytics-service
