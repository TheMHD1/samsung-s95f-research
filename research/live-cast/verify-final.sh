set -eu
DB=/opt/dbspace/.pkgmgr_parser.db
STATE=/opt/usr/home/owner/researcher-live-cast
INITIAL=/opt/usr/home/owner/researcher-debloat-20261025
app_launcher --status > "$STATE/running.final"
count=0
for record in "$INITIAL/apps.changed" "$STATE/apps.changed"; do
    while IFS= read -r app; do
        test "$(sqlite3 -readonly "$DB" "select app_disable from package_app_info where app_id='$app';")" = true
        if awk -v a="$app" '$1==a { found=1 } END { exit !found }' "$STATE/running.final"; then
            echo UNEXPECTED_RUNNING:$app
            exit 1
        fi
        count=$((count+1))
    done < "$record"
done
test "$count" = 78
echo VERIFIED_DISABLED_AND_NOT_RUNNING:$count
while IFS= read -r marker; do
    test "$(cat "/opt/usr/share/systemd/system/$marker")" = researcher-debloat-20261025
done < "$INITIAL/markers.created"
echo VERIFIED_STARTUP_MARKERS
for app in HEPsqFNie0.tvplusstandalone ByJlgt0XeD.CastSettingsApp com.samsung.tv.googlecast-app com.samsung.tv.googlecast-service com.samsung.tv.airplay-app-2 org.tizen.ScreenMirroring-app-tv org.tizen.tv-viewer org.tizen.menu; do
    test "$(sqlite3 -readonly "$DB" "select app_disable from package_app_info where app_id='$app';")" = false
    echo RETAINED:$app
done
echo CORE_UNITS
for unit in muse-server.service connman.service source-service.service pulseaudio.service com.samsung.tv.airplay-service-2.service com.samsung.tv.googlecast-service.service; do
    test "$(systemctl show "$unit" -p ActiveState --value)" = active
    systemctl show "$unit" -p Id -p ActiveState -p MainPID -p NRestarts
done
echo HOME_PREFS
vconftool get db/appfw/home_appid
vconftool get db/eden/homeRecommendation
vconftool get db/eden/launcher/list
echo HOME_GRAPH
UI=/opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted/sqlite.db
sqlite3 -readonly -header "$UI" "select componentID,visible,childEntityList from TableEntity where componentID in ('s/firstscreen','d/tabs','d/launcher','s/livetv@TVPLUS') or componentID like 'd/ug.tab%';"
test "$(sqlite3 -readonly "$UI" "select count(*) from TableEntity where componentID like 'd/dhcategory%' or componentID like 'd/topbanner%';")" = 0
test "$(sqlite3 -readonly "$UI" "select count(*) from TableEntity where componentID='d/tabs' and visible=1;")" = 1
test "$(sqlite3 -readonly "$UI" "select count(*) from TableEntity where componentID='s/livetv@TVPLUS';")" -ge 1
echo VERIFIED_NO_RECOMMENDATION_ROWS_OR_TOP_BANNER
echo SOFTWARE_HASHES
sha256sum /opt/usr/apps/com.samsung.tv.ContentsBrowser/shared/res/CompTerra.dll /opt/usr/apps/com.samsung.tv.coba.newhome/shared/res/CompHome.dll /opt/usr/apps/com.samsung.tv.home.media/bin/HomeMedia.dll /opt/usr/apps/com.samsung.tv.ghservice/bin/com.samsung.tv.ghservice.dll
echo FAILED_UNITS
systemctl --failed --no-legend --no-pager
echo BOOT_ID
cat /proc/sys/kernel/random/boot_id
echo VERIFY_COMPLETE
