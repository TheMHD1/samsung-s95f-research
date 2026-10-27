set -eu
echo RESTORE_TEST
test "$(cat /opt/usr/home/owner/researcher-debloat-20261025/acr-before.txt)" = 'com.samsung.tv.acr|false'
pkgcmd -A -t app -n com.samsung.tv.acr --uid 5001
test "$(sqlite3 -readonly /opt/dbspace/.pkgmgr_parser.db "select app_disable from package_app_info where app_id='com.samsung.tv.acr';")" = false
echo RESTORE_VERIFIED
echo EXTRAS
sqlite3 -readonly -header -separator '|' /opt/dbspace/.pkgmgr_parser.db "select app_id,package,app_disable,app_onboot,app_autorestart from package_app_info where app_id like '%voice%' or app_id like '%alexa%' or app_id like '%bixby%' or app_id like '%AICompanion%' or app_id like '%health%' or app_id like '%ghdaemon%' or app_id like '%gaming%' or app_id like '%ambient%' or app_id like '%wakeupless%' or app_id like '%remoteless%';"
echo UNITS
for u in com.samsung.tv.AICompanionAgent.service com.samsung.tv.ghdaemon.service samsunghealth-service-tv.service com.samsung.tv.farfieldvoice.service com.samsung.tv.ondevice-voice.service com.samsung.tv.wakeupless.service com.samsung.tv.bixby-prov.service com.samsung.tv.voiceid-service.service org.tizen.multi-assistant-service.service; do
    echo UNIT:$u
    systemctl cat "$u"
    systemctl show "$u" -p ActiveState -p MainPID -p RequiredBy -p BindsTo -p PartOf -p Triggers -p TriggeredBy
done
