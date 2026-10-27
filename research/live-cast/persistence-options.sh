set -eu
echo DEVELOPER_KEYS
vconftool get -r db/sdk || true
vconftool get -r db/menu/system/developer || true
echo SDB_UNIT
systemctl cat sdbd.service sdbd_tcp.socket
echo SDB_CONFIG_REFERENCES
grep -aoE 'db/[A-Za-z0-9_/]{3,100}|memory/[A-Za-z0-9_/]{3,100}' /usr/sbin/sdbd | sort -u | head -40 || true
echo PROBE_PATH
find /opt/usr/home/owner/apps_rw/com.samsung.tv.ghservice -name researcher-root-suitability.json -print
echo GH_METADATA
sqlite3 -readonly -header /opt/dbspace/.pkgmgr_parser.db "select app_id,app_component,app_exec,app_type,app_onboot,app_disable,app_nodisplay,app_autorestart from package_app_info where app_id='com.samsung.tv.ghservice';"
echo HOME_STATUS
vconftool get db/appfw/home_appid
vconftool get db/menu/smart_hub/ontvsetting/auto_start
app_launcher --status
