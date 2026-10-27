set -eu
DB=/opt/dbspace/.pkgmgr_parser.db
test "$(sqlite3 -readonly "$DB" "select app_disable from package_app_info where app_id='com.samsung.tv.csfs';")" = false
echo BEFORE_HOME_UI
app_launcher --status | grep -F 'com.samsung.tv.csfs ('
app_launcher -k com.samsung.tv.csfs
sleep 1
app_launcher -s com.samsung.tv.csfs
sleep 3
echo AFTER_HOME_UI
app_launcher --status | grep -F 'com.samsung.tv.csfs ('
echo CORE_MEDIA_AND_CASTING
systemctl is-active muse-server.service connman.service source-service.service pulseaudio.service com.samsung.tv.airplay-service-2.service com.samsung.tv.googlecast-service.service
echo HOME_GRAPH
sqlite3 -readonly -header /opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted/sqlite.db "select componentID,visible from TableEntity where componentID in ('d/tabs','d/launcher','s/livetv@TVPLUS');"
