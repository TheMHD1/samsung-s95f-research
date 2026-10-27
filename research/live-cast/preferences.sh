set -eu
echo HOME_PREFS
for key in db/appfw/home_appid db/appfw/startup_appid db/appfw/booting_appid_backup db/first_screen/type db/menu/smart_hub/ontvsetting/auto_start; do
    echo KEY:$key
    vconftool get "$key" || true
done
vconftool get -r db/menu/smart_hub | grep -Ei 'home|auto|recommend|ad|promo|content|last|start|type' || true
echo PLATFORM_INFO
cat /etc/tizen-release
ls -l /usr/lib/libapp*operation* /usr/lib/libapp*preference* /usr/lib/libapp*common* 2>/dev/null || true
echo ONBOOT_PACKAGES
sqlite3 -readonly -header -separator '|' /opt/dbspace/.pkgmgr_parser.db "select app_id,app_type,app_root_path,app_exec,app_onboot from package_app_info where app_type like 'dotnet%' and (app_onboot='true' or app_id like '%ghservice%' or app_id like '%gaminghub%' or app_id like '%home.%');"
echo APP_BOOT_UNIT
systemctl cat app-boot-manager.service
echo HOME_FILES
ls -lh /opt/usr/apps/com.samsung.tv.home.media/bin/HomeMedia.dll /opt/usr/apps/com.samsung.tv.home.sidebar/bin/HomeSidebar.dll /opt/usr/apps/com.samsung.tv.csfs/bin/* /usr/apps/com.samsung.tv.csfs/bin/* 2>/dev/null || true
echo ROOT_UID_NAME
getent passwd 5001 || true
